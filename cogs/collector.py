import os
import discord
from discord import app_commands
from discord.ext import commands
import pandas as pd

class DataCollector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"

    async def fetch_channel_messages(self, channel: discord.TextChannel, limit: int):
        messages_data = []
        async for message in channel.history(limit=limit):
            if not message.author.bot:
                messages_data.append({
                    'created_at': message.created_at,
                    'author_id': message.author.id,
                    'author_name': str(message.author),
                    'content': message.content,
                    'reactions_count': sum(r.count for r in message.reactions),
                    'mentions_count': len(message.mentions)
                })
        return pd.DataFrame(messages_data)

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
        channel="수집할 디스코드 채널",
        limit="수집할 메시지 개수 (기본값: 100개)"
    )
    async def collect_command(self, interaction: discord.Interaction, channel: discord.TextChannel, limit: int = 100):
        await interaction.response.defer()

        df = await self.fetch_channel_messages(channel, limit)
        file_path = self.save_to_csv(df, channel.name)

        embed = discord.Embed(
            title="📥 메시지 데이터 수집 완료",
            description=f"{channel.mention} 채널의 데이터 수집이 성공적으로 마무리되었습니다.",
            color=discord.Color.teal()
        )
        embed.add_field(name="📍 수집 대상", value=f"`#{channel.name}`", inline=True)
        embed.add_field(name="💬 수집된 메시지", value=f"`{len(df):,}개`", inline=True)
        embed.add_field(name="📁 저장 파일", value=f"`{file_path}`", inline=False)

        if not df.empty:
            top_user = df['author_name'].value_counts().idxmax()
            embed.add_field(name="👑 최고 기여자", value=f"**{top_user}**", inline=False)

        embed.set_footer(text="Discord Data Engine • /분석 및 /요약 커맨드로 연결됩니다.")
        await interaction.followup.send(embed=embed)

    # [슬래시 커맨드] /종료
    @app_commands.command(name="종료", description="디스코드 봇을 안전하게 종료합니다. (개발자 전용)")
    async def stop_bot(self, interaction: discord.Interaction):
        app_info = await self.bot.application_info()

        if interaction.user.id == app_info.owner.id:
            embed = discord.Embed(
                title="👋 시스템 종료 시퀀스",
                description="개발자 인증이 완료되었습니다. 봇 프로세스를 안전하게 종료합니다.",
                color=discord.Color.dark_grey()
            )
            await interaction.response.send_message(embed=embed)
            await self.bot.close()
        else:
            embed = discord.Embed(
                title="🚫 접근 권한 제한",
                description="이 명령어는 **봇 소유자(개발자)** 전용 커맨드입니다.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(DataCollector(bot))