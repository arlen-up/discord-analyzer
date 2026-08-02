import discord
from discord.ext import commands, tasks
from datetime import datetime, time
import database

# 자정 12:00 (KST 기준시)
MIDNIGHT = time(hour=0, minute=0, second=0)

class AutoCollector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        database.init_db()  # DB 초기화
        self.daily_collect_task.start()  # 쪼맹이의 야간 순찰 스케줄러 시작!

    def cog_unload(self):
        self.daily_collect_task.cancel()  # Cog 언로드 시 순찰 종료

    # 매일 지정된 시각(자정)에 실행되는 자동 루프
    @tasks.loop(time=MIDNIGHT)
    async def daily_collect_task(self):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🌙 자정이다! 쪼맹이가 야간 데이터 수집을 시작한다... (돋보기 장착 🔍)")
        
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                # 봇의 읽기 권한이 있는 텍스트 채널만 수집
                if channel.permissions_for(guild.me).read_message_history:
                    try:
                        messages_data = []
                        async for message in channel.history(limit=500): # 자정 주기 수집 (최근 메시지 위주)
                            messages_data.append((
                                message.id,
                                channel.id,
                                channel.name,
                                message.author.id,
                                message.author.name,
                                message.content,
                                sum(r.count for r in message.reactions) if message.reactions else 0,
                                message.created_at.isoformat()
                            ))
                        
                        # DB 저장
                        database.save_messages(messages_data)
                    except Exception as e:
                        print(f"⚠️ 쪼맹이가 #{channel.name} 채널 둘러보다가 삐끗했어: {e}")
                        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🎉 자정 자동 수집 완료! 쪼맹이의 비밀 장부에 잘 넣어뒀지!")

    @daily_collect_task.before_loop
    async def before_daily_task(self):
        # 봇이 완전히 켜질 때까지 기다렸다가 루프 시작
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AutoCollector(bot))