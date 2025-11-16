from discord.ext import commands
from .general import General
from .admin import Admin
from .ai import AI

async def setup(bot):
    await bot.add_cog(General(bot))
    await bot.add_cog(Admin(bot))
    await bot.add_cog(AI(bot))
