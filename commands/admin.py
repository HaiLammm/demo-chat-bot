import discord
from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='clear')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 5):
        if amount > 100:
            await ctx.send("Tối đa 100 tin nhắn!")
            return
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 để xóa lệnh clear
        await ctx.send(f'Đã xóa {len(deleted)-1} tin nhắn.', delete_after=5)

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Bạn không có quyền manage_messages!")

    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="Không có lý do"):
        await member.ban(reason=reason)
        await ctx.send(f'Đã ban {member} vì: {reason}')

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Bạn không có quyền ban_members!")

    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="Không có lý do"):
        await member.kick(reason=reason)
        await ctx.send(f'Đã kick {member} vì: {reason}')

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Bạn không có quyền kick_members!")

async def setup(bot):
    await bot.add_cog(Admin(bot))
