import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print("---------------------------------------")

async def main():
    async with bot:
        # cogs 폴더 안의 collector.py 로드
        await bot.load_extension("cogs.collector")
        
        # 나중에 cogs 폴더에 다른 기능(예: cogs/analyzer.py)을 추가하면
        # 아래처럼 한 줄만 추가하면 됩니다.
        # await bot.load_extension("cogs.analyzer")

        # 슬래시 커맨드 동기화
        @bot.event
        async def on_ready():
            await bot.tree.sync()
            print(f'Logged in as {bot.user.name}')
            print("모든 Cog 로드 및 슬래시 커맨드 동기화 완료!")

        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())