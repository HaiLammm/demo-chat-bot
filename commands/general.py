import discord
from discord.ext import commands
import config
import asyncio
from rag.rag_chain import get_rag_chain

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping')
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f'Pong! Latency: {latency}ms')

    @commands.command(name='info')
    async def info(self, ctx):
        embed = discord.Embed(title="Thông tin Bot", description="Bot chat Discord với RAG Ollama Phi-3", color=0x0099ff)
        embed.add_field(name="Phiên bản", value="1.0", inline=True)
        embed.add_field(name="Lương Hải Lâm", value="Lem", inline=True)
        await ctx.send(embed=embed)
async def setup(bot):
    await bot.add_cog(General(bot))
