import discord
from discord.ext import commands
from utils.database import init_db
import asyncio
import config
import events
from utils.logger import setup_logger
from commands import setup as setup_commands
from events import on_ready
from events import on_message
from events import on_member_join
import logging

init_db()
logging.basicConfig(
    filename="logs/bot.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger = setup_logger()

intents = config.INTENTS
bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.HTTPException):
        print(f"Lỗi HTTP: {error.status} - {error.code} - {error.text}")  # In chi tiết lỗi
    raise error

@bot.event
async def on_ready():
    await events.on_ready.on_ready(bot)


@bot.event
async def on_message(message):
    await events.on_message.on_message(message, bot)


@bot.event
async def on_member_join(member):
    await events.on_member_join.on_member_join(member, bot)


async def main():
    async with bot:
        await setup_commands(bot)  # Đảm bảo async
        await bot.start(config.DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
