import os
import discord
from discord import app_commands
from discord.ext import commands
import pandas as pd

class DataCollector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"

    # [내부 함수] 채널 메시지 수집 로직
    async def fetch_channel_messages(self, channel: discord.TextChannel, limit: int):
        messages_data = []
        async for message in channel.history(limit=limit):
            if not message.author.bot:  # 봇 메시지 제외
                messages_data.append({
                    'created_at': message.created_at,
                    'author_id': message.author.id,
                    'author_name': str(message.author),
                    'content': message.content,
                    'reactions_count': sum(r.count for r in message.reactions),
                    'mentions_count': len(message.mentions)
                })
        return pd.DataFrame(messages_data)

    # [내부 함수] CSV 저장 로직 (data/ 폴더 자동 생성)
    def save_to_csv(self, df: pd.DataFrame, channel_name: str) -> str:
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        file_name = f"{channel_name}_messages.csv"
        file_path = os.path.join(self.data_dir, file_name)
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        return file_path

    # [슬래시 커맨드] /수집
    @app_commands.command(name="수집", description="지정한 채널의 과거 메시지를 수집하여 CSV로 저장합니다.")
    @app_commands.describe(
        channel="수집할 디스코드 채널을 선택하세요",
        limit="수집할 메시지 개수 (기본값: 100개)"
    )
    async def collect_command(self, interaction: discord.Interaction, channel: discord.TextChannel, limit: int = 100):
        await interaction.response.defer()

        # 데이터 수집 및 저장
        df = await self.fetch_channel_messages(channel, limit)
        file_path = self.save_to_csv(df, channel.name)

        # 결과 임베드 메시지
        embed = discord.Embed(
            title="✅ 데이터 수집 완료!",
            description="채널 메시지가 성공적으로 저장되었습니다.",
            color=discord.Color.green()
        )
        embed.add_field(name="수집 채널", value=channel.mention, inline=True)
        embed.add_field(name="수집된 메시지", value=f"{len(df)}개", inline=True)
        embed.add_field(name="저장 경로", value=f"`{file_path}`", inline=False)

        if not df.empty:
            top_user = df['author_name'].value_counts().idxmax()
            embed.add_field(name="👑 최다 작성자", value=top_user, inline=False)

        await interaction.followup.send(embed=embed)

    # [슬래시 커맨드] /종료 (봇 제작자/개발자 전용)
    @app_commands.command(name="종료", description="디스코드 봇을 종료합니다. (개발자 전용)")
    async def stop_bot(self, interaction: discord.Interaction):
        # 봇 애플리케이션 소유자(개발자 본인) ID 확인
        app_info = await self.bot.application_info()

        if interaction.user.id == app_info.owner.id:
            await interaction.response.send_message("👋 개발자 확인 완료. 봇을 안전하게 종료합니다!")
            await self.bot.close()
        else:
            embed = discord.Embed(
                title="🚫 접근 거부",
                description="이 명령어는 **봇 개발자**만 사용할 수 있습니다.",
                color=discord.Color.red()
            )
            # ephemeral=True: 명령어 입력 유저에게만 비밀 메시지로 출력
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(DataCollector(bot))