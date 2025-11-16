import discord
import config

async def on_member_join(member, bot):
    if config.WELCOME_CHANNEL_ID == 0:
        return  # Không có kênh
    
    channel = bot.get_channel(config.WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f'Chào mừng {member.mention} đến với server!')
