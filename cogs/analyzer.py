import os
import time
import discord
from discord import app_commands
from discord.ext import commands
import pandas as pd

class DataAnalyzer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"

    # [내부 함수] 특정 채널의 CSV 데이터 로드
    def load_channel_data(self, channel_name: str) -> pd.DataFrame:
        file_path = os.path.join(self.data_dir, f"{channel_name}_messages.csv")
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        df = pd.read_csv(file_path)
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'])
        return df

    # [슬래시 커맨드] /분석
    @app_commands.command(name="분석", description="수집된 데이터를 기반으로 채널 대화 통계를 출력합니다.")
    @app_commands.describe(channel="분석할 디스코드 채널을 선택하세요")
    async def analyze_command(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()

        df = self.load_channel_data(channel.name)

        if df.empty:
            embed = discord.Embed(
                title="⚠️ 데이터 없음",
                description=f"{channel.mention} 채널의 수집 데이터가 없습니다.\n먼저 `/수집` 커맨드로 데이터를 수집해 주세요!",
                color=discord.Color.gold()
            )
            await interaction.followup.send(embed=embed)
            return

        total_messages = len(df)
        total_users = df['author_name'].nunique()
        
        top_users = df['author_name'].value_counts().head(3)
        top_users_text = ""
        medals = ["🥇", "🥈", "🥉"]
        for idx, (user, count) in enumerate(top_users.items()):
            percentage = (count / total_messages) * 100
            top_users_text += f"{medals[idx]} **{user}**: {count}개 ({percentage:.1f}%)\n"

        df['hour'] = df['created_at'].dt.hour
        peak_hour = df['hour'].mode()[0]
        peak_hour_count = (df['hour'] == peak_hour).sum()

        avg_reactions = df['reactions_count'].mean() if 'reactions_count' in df.columns else 0

        embed = discord.Embed(
            title=f"📊 #{channel.name} 채널 대화 분석 리포트",
            color=discord.Color.blue()
        )
        embed.add_field(name="💬 총 메시지 수", value=f"{total_messages:,}개", inline=True)
        embed.add_field(name="👥 참여 유저 수", value=f"{total_users:,}명", inline=True)
        embed.add_field(name="⏰ 가장 활발한 시간", value=f"{peak_hour}시 ~ {peak_hour+1}시\n({peak_hour_count}개 메시지)", inline=True)

        embed.add_field(name="🏆 최다 대화 유저 TOP 3", value=top_users_text if top_users_text else "데이터 없음", inline=False)
        embed.add_field(name="❤️ 메시지당 평균 리액션", value=f"{avg_reactions:.2f}개", inline=True)

        embed.set_footer(text="Discord Channel Analyzer")
        await interaction.followup.send(embed=embed)

    # ✨ [신규 슬래시 커맨드] /데이터목록
    @app_commands.command(name="데이터목록", description="저장된 CSV 데이터 파일 목록과 상세 정보를 확인합니다.")
    async def list_data_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not os.path.exists(self.data_dir):
            await interaction.followup.send("📁 저장된 데이터 폴더가 존재하지 않습니다.")
            return

        files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]

        if not files:
            embed = discord.Embed(
                title="📂 수집된 데이터 없음",
                description="현재 저장된 CSV 파일이 없습니다.\n`/수집` 커맨드로 채널 메시지를 먼저 수집해 주세요!",
                color=discord.Color.gold()
            )
            await interaction.followup.send(embed=embed)
            return

        embed = discord.Embed(
            title="📂 저장된 데이터 파일 목록",
            description=f"총 **{len(files)}개**의 데이터 파일이 `data/` 폴더에 저장되어 있습니다.\n",
            color=discord.Color.teal()
        )

        total_rows_all = 0

        for file_name in sorted(files):
            file_path = os.path.join(self.data_dir, file_name)
            file_size_kb = os.path.getsize(file_path) / 1024
            mtime = time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(file_path)))

            # 메시지 개수 읽기
            try:
                df = pd.read_csv(file_path)
                msg_count = len(df)
                total_rows_all += msg_count
            except Exception:
                msg_count = 0

            channel_display_name = file_name.replace("_messages.csv", "")

            embed.add_field(
                name=f"📄 #{channel_display_name}",
                value=f"• 메시지: `{msg_count:,}개`\n• 용량: `{file_size_kb:.1f} KB`\n• 수정일: `{mtime}`",
                inline=True
            )

        embed.set_footer(text=f"전체 메시지 총합: {total_rows_all:,}개")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DataAnalyzer(bot))