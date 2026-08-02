import discord
from discord import app_commands
from discord.ext import commands
import pandas as pd
import sqlite3
import database

class DataAnalyzer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_channel_data(self, channel_name: str) -> pd.DataFrame:
        rows = database.get_channel_messages(channel_name)
        if not rows:
            return pd.DataFrame()
        
        columns = ["message_id", "channel_id", "channel_name", "author_id", "author_name", "content", "reactions_count", "created_at"]
        df = pd.DataFrame(rows, columns=columns)
        
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'])
        return df

    # [신규 커맨드] /db현황 - 디스코드 DB 수집 상태 확인
    @app_commands.command(name="db현황", description="SQLite 데이터베이스에 누적 저장된 메시지 수와 채널별 현황을 확인합니다.")
    async def db_status_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            conn = sqlite3.connect(database.DB_PATH)
            cursor = conn.cursor()

            # 1. 전체 메시지 수 조회
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_count = cursor.fetchone()[0]

            if total_count == 0:
                embed = discord.Embed(
                    title="💾 DB 데이터 현황",
                    description="현재 데이터베이스에 저장된 메시지가 없습니다.\n먼저 `/수집` 커맨드를 실행해 주세요!",
                    color=discord.Color.gold()
                )
                await interaction.followup.send(embed=embed)
                conn.close()
                return

            # 2. 채널별 메시지 수 조회
            cursor.execute("SELECT channel_name, COUNT(*) FROM messages GROUP BY channel_name ORDER BY COUNT(*) DESC")
            channel_stats = cursor.fetchall()
            
            # 3. 전체 유저 수 조회
            cursor.execute("SELECT COUNT(DISTINCT author_id) FROM messages")
            total_users = cursor.fetchone()[0]

            conn.close()

            # 채널별 저장 현황 텍스트 생성
            channel_text = ""
            for ch_name, count in channel_stats:
                channel_text += f"• **#{ch_name}**: {count:,}개 메시지\n"

            embed = discord.Embed(
                title="💾 DB 저장 및 수집 현황",
                color=discord.Color.green()
            )
            embed.add_field(name="📊 총 누적 메시지", value=f"**{total_count:,}**개", inline=True)
            embed.add_field(name="👥 총 참여 유저", value=f"**{total_users:,}**명", inline=True)
            embed.add_field(name="📁 채널별 수집 내역", value=channel_text if channel_text else "내역 없음", inline=False)
            embed.set_footer(text="SQLite Database Status • bot_database.db")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ DB 현황을 조회하는 중 오류가 발생했습니다: {str(e)}")

    # [슬래시 커맨드] /분석
    @app_commands.command(name="분석", description="DB 데이터를 기반으로 채널 대화 통계를 출력합니다.")
    @app_commands.describe(channel="분석할 디스코드 채널을 선택하세요")
    async def analyze_command(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()

        df = self.load_channel_data(channel.name)

        if df.empty:
            embed = discord.Embed(
                title="⚠️ 데이터 없음",
                description=f"{channel.mention} 채널의 DB 수집 데이터가 없습니다.",
                color=discord.Color.gold()
            )
            await interaction.followup.send(embed=embed)
            return

        total_messages = len(df)
        total_users = df['author_id'].nunique()
        top_users = df['author_id'].value_counts().head(3)
        
        top_users_text = ""
        medals = ["🥇", "🥈", "🥉"]
        for idx, (user_id, count) in enumerate(top_users.items()):
            percentage = (count / total_messages) * 100
            top_users_text += f"{medals[idx]} <@{user_id}>: {count}개 ({percentage:.1f}%)\n"

        df['hour'] = df['created_at'].dt.hour
        peak_hour = df['hour'].mode()[0] if not df['hour'].empty else 0
        peak_hour_count = (df['hour'] == peak_hour).sum()
        avg_reactions = df['reactions_count'].mean() if 'reactions_count' in df.columns else 0

        embed = discord.Embed(
            title=f"📊 #{channel.name} 채널 대화 분석 리포트 (DB 기반)",
            color=discord.Color.blue()
        )
        embed.add_field(name="💬 총 메시지 수", value=f"{total_messages:,}개", inline=True)
        embed.add_field(name="👥 참여 유저 수", value=f"{total_users:,}명", inline=True)
        embed.add_field(name="⏰ 가장 활발한 시간", value=f"{peak_hour}시 ~ {peak_hour+1}시\n({peak_hour_count}개 메시지)", inline=True)
        embed.add_field(name="🏆 최다 대화 유저 TOP 3", value=top_users_text if top_users_text else "데이터 없음", inline=False)
        embed.add_field(name="❤️ 메시지당 평균 리액션", value=f"{avg_reactions:.2f}개", inline=True)
        embed.set_footer(text="Discord Channel Analyzer • DB Powered")

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DataAnalyzer(bot))