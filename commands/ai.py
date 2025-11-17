import discord
from discord.ext import commands
import aiohttp
import json
from config import OLLAMA_MODEL, PREFIX
from langchain_community.llms import Ollama

# Imports cho RAG & CV
from rag.rag_chain import get_rag_chain
from rag.vectorstore import get_vectorstore
from rag.cv_parser import process_cv_data
from rag.analysis_logic import analyze_and_suggest_skills
from utils.database import save_chat


class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Cho lệnh !chat
        self.rag_chain = get_rag_chain()

        # Cho lệnh !cv (Phân tích)
        self.vectorstore = get_vectorstore()
        self.llm = Ollama(model=OLLAMA_MODEL)

    @commands.command(name='chat')
    async def chat(self, ctx, *, query: str):
        try:
            # Giữ nguyên logic cũ của bạn (chain cổ điển)
            response = self.rag_chain.invoke({"input": query})['answer']
            await ctx.send(response)
            save_chat(ctx.author.id, query, response)
        except Exception as e:
            await ctx.send(f"Lỗi RAG: {type(e).__name__}: {str(e)}")

    @commands.command(name="cv")
    async def cv_analysis(self, ctx):
        if not ctx.message.attachments or not ctx.message.attachments[0].filename.lower().endswith('.pdf'):
            await ctx.send(f"Vui lòng gửi kèm **file CV (PDF)** sau lệnh `{PREFIX}cv`.")
            return

        attachment = ctx.message.attachments[0]
        await ctx.send(f"Đã nhận file **{attachment.filename}**. Đang tiến hành phân tích CV và so sánh kỹ năng...")

        try:
            # 1. Tải file từ Discord (Bất đồng bộ)
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    pdf_content = await resp.read()

            # 2. Xử lý OCR và Parsing JSON (Chạy trong thread pool)
            cv_result = await self.bot.loop.run_in_executor(
                None,
                lambda: process_cv_data(pdf_content)
            )

            print("\n--- KẾT QUẢ CV JSON ĐÃ PARSE (DEBUG) ---")
            print(json.dumps(cv_result, indent=4, ensure_ascii=False))
            print("---------------------------------------\n")

            if "error" in cv_result:
                await ctx.send(f"❌ Lỗi Parsing CV: {cv_result['error']}")
                return

            # 💡 SỬA LỖI FINAL: Dùng '_embedding_function' để làm ấm mô hình
            # (khắc phục lỗi AttributeError và lỗi 400 Bad Request khởi tạo)
            self.vectorstore._embedding_function.embed_query("warmup query")

            # 3. Phân tích và Đề xuất Kỹ năng
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
            suggestions = await self.bot.loop.run_in_executor(
                None,
                lambda: analyze_and_suggest_skills(
                    cv_result, self.llm, retriever)
            )

            # 4. Tổng hợp và Trả lời
            await self._respond_to_cv_analysis(ctx, cv_result, suggestions)

        except Exception as e:
            await ctx.send(f"Đã xảy ra lỗi nghiêm trọng trong quá trình xử lý CV: ```{type(e).__name__}: {str(e)[:250]}...```")

    async def _respond_to_cv_analysis(self, ctx, cv_data: dict, suggestions: str):
        info = cv_data.get("personal_info", {})
        experience = cv_data.get("experience", [])
        summary = (
            f"** Phân tích CV hoàn tất cho {info.get('name', 'Ứng viên')}:**\n"
            f"**- Vị trí:** {info.get('title', 'N/A')}\n"
            f"**- Email:** {info.get('email', 'N/A')}\n"
            f"**- Tổng công việc:** {len(experience)} vị trí.\n"
            f"**- Số điện thoại:** {info.get('phone', 'N/A')}\n"
        )
        if experience:
            summary += f"**- Công việc gần nhất:** {experience[0].get('company', 'N/A')} ({
                experience[0].get('role', 'N/A')}) - {experience[0].get('duration', 'N/A')}\n\n"

        response = summary + \
            "**💡 Đề xuất cải thiện kỹ năng (Dựa trên Kiến thức nền):**\n" + \
            suggestions

        await ctx.send(response)


async def setup(bot):
    await bot.add_cog(AI(bot))
