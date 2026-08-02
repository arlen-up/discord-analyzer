import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# .env 환경변수 로드
load_dotenv(override=True)

# 디스코드 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 📌 프로젝트의 모든 Cog 모듈 목록 (누락 없이 전체 포함)
initial_extensions = [
    "cogs.collector",
    "cogs.auto_collector",
    "cogs.analyzer",
    "cogs.visualizer",
    "cogs.summarizer",
    "cogs.help",
    "cogs.status"
]

@bot.event
async def on_ready():
    print("\n" + "=" * 50)
    print(f"🤖 봇 로그인 완료: {bot.user.name} (ID: {bot.user.id})")
    print("=" * 50)
    
    # 디스코드 서버와 슬래시 커맨드 동기화 및 상세 목록 출력
    try:
        synced = await bot.tree.sync()
        print(f"🔄 [슬래시 커맨드 동기화 성공] 총 {len(synced)}개 명령어 등록 완료:")
        for cmd in synced:
            print(f"   └ ⚙️ /{cmd.name} : {cmd.description}")
    except Exception as e:
        print(f"❌ [슬래시 커맨드 동기화 실패]: {e}")
        
    print("=" * 50)
    print("🚀 모든 시스템 준비 완료! 대기 중...\n")

async def main():
    async with bot:
        print("\n📦 [Cog 모듈 로딩 시작]")
        for extension in initial_extensions:
            try:
                await bot.load_extension(extension)
                print(f"   ├ 🧩 {extension} 모듈 로드 완료")
            except Exception as e:
                print(f"   ├ ❌ {extension} 모듈 로드 실패: {e}")
        print("└ ----------------------------------------")
        
        # .env 파일에서 토큰 읽어오기
        token = os.getenv("BOT_TOKEN")
        
        if not token:
            print("\n❌ [오류] .env 파일에서 BOT_TOKEN을 찾을 수 없습니다!")
            return

        print(f"🔑 [인증 토큰] 정상 감지됨 (길이: {len(token)}자)")
        print("🌐 디스코드 서버 연결 시도 중...")
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())