import discord
from discord.ext import commands
from rag.rag_chain import get_rag_chain
from utils.database import save_chat

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rag_chain = get_rag_chain()

    @commands.command(name='chat')
    async def chat(self, ctx, *, query: str):
        try:
            response = self.rag_chain.invoke({"input": query})['answer']
            await ctx.send(response)
            save_chat(ctx.author.id, query, response)  # Lưu lịch sử
        except Exception as e:
            await ctx.send(f"Lỗi: {str(e)}")

async def setup(bot):
    await bot.add_cog(AI(bot))
