import aiohttp
import os
from io import BytesIO

@commands.command(name="cv")
async def cv_analysis(self, ctx):
    if not ctx.message.attachments:
        await ctx.send("Vui lòng gửi kèm file CV (PDF) sau lệnh `!cv`.")
        return

    # Chỉ xử lý file đầu tiên
    attachment = ctx.message.attachments[0]
    if not attachment.filename.lower().endswith('.pdf'):
        await ctx.send("Bot chỉ hỗ trợ phân tích file PDF.")
        return

    await ctx.send("Đã nhận file. Đang tiến hành phân tích CV...")
    
    # Tải file về bộ nhớ
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status != 200:
                    await ctx.send("Lỗi khi tải file.")
                    return
                pdf_content = await resp.read() # Nội dung file PDF dạng bytes
                
                # CHUYỂN SANG GIAI ĐOẠN 2: Xử lý OCR và Phân rã
                analysis_result = await self.bot.loop.run_in_executor(
                    None, # Sử dụng ThreadPoolExecutor mặc định
                    lambda: self.process_cv_data(pdf_content) # Gọi hàm OCR/Parsing
                )
                
                # CHUYỂN SANG GIAI ĐOẠN 3 & 4: So sánh và Trả lời
                await self.respond_to_cv_analysis(ctx, analysis_result)
                
    except Exception as e:
        await ctx.send(f"Đã xảy ra lỗi trong quá trình xử lý: {e}")
