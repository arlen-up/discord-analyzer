import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ 에러: .env 파일에서 BOT_TOKEN을 읽어오지 못했습니다.")
    exit()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def main():
    async with bot:
        # 모듈 로드
        await bot.load_extension("cogs.collector")
        await bot.load_extension("cogs.analyzer")
        await bot.load_extension("cogs.visualizer")

        @bot.event
        async def on_ready():
            print(f"Logged in as {bot.user.name}")
            print("---------------------------------------")
            
            # ✨ 슬래시 커맨드 강제 동기화 및 출력
            try:
                synced = await bot.tree.sync()
                print(f"✨ 총 {len(synced)}개의 슬래시 커맨드가 동기화되었습니다.")
                for command in synced:
                    print(f" - /{command.name}")
            except Exception as e:
                print(f"동기화 에러 발생: {e}")
                
            print("준비 완료!")

        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())