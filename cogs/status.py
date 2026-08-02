import discord
from discord.ext import commands, tasks
from itertools import cycle

class BotStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 🔄 쪼맹이의 귀여운 상태 메시지 로테이션 목록
        self.status_list = cycle([
            discord.CustomActivity(name="🔍 쪼맹이 돋보기로 대화 탐색 중..."),
            discord.CustomActivity(name="💡 명령어는 /도움말 시켜줘!"),
            discord.CustomActivity(name="📏 키 자라는 중... 무시 금지! 😤"),
            discord.CustomActivity(name="📝 장부에 비밀 대화 적는 중..."),
            discord.Game(name="작지만 야무진 돋보기 순찰")
        ])

    @commands.Cog.listener()
    async def on_ready(self):
        # 봇이 준비되면 쪼맹이의 상태 메시지 순찰 루프 시작!
        if not self.change_status.is_running():
            self.change_status.start()
            print("✅ 쪼맹이의 상태 메시지 순찰 루프가 시작되었습니다! 🔍")

    # 15초마다 쪼맹이의 상태 변경
    @tasks.loop(seconds=15)
    async def change_status(self):
        new_activity = next(self.status_list)
        await self.bot.change_presence(status=discord.Status.online, activity=new_activity)

async def setup(bot):
    await bot.add_cog(BotStatus(bot))