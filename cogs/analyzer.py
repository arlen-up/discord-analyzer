import discord
from discord import app_commands
from discord.ext import commands
import pandas as pd
import sqlite3
import asyncio
import database

class DataAnalyzer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.footer_text = "쪼맹이 봇 • Created by tella._."

    def _get_channel_data_sync(self, channel_id: int) -> pd.DataFrame:
        rows = database.get_channel_messages(channel_id)
        if not rows:
            return pd.DataFrame()
        columns = ["message_id", "channel_id", "channel_name", "author_id", "author_name", "content", "reaction_count", "created_at"]
        df = pd.DataFrame(rows, columns=columns)
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'])
        return df

    @app_commands.command(name="db현황", description="[쪼맹이] DB에 차곡차곡 쌓인 전체 메시지 수와 채널별 현황을 점검합니다.")
    async def db_status_command(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        try:
            def query_status():
                conn = sqlite3.connect(database.DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM messages")
                total_count = cursor.fetchone()[0]

                if total_count == 0:
                    conn.close()
                    return 0, [], 0

                cursor.execute("SELECT channel_name, COUNT(*) FROM messages GROUP BY channel_name ORDER BY COUNT(*) DESC")
                channel_stats = cursor.fetchall()
                cursor.execute("SELECT COUNT(DISTINCT author_id) FROM messages")
                total_users = cursor.fetchone()[0]

                conn.close()
                return total_count, channel_stats, total_users

            total_count, channel_stats, total_users = await asyncio.to_thread(query_status)

            if total_count == 0:
                # 🔴 경고: 빨간색
                embed = discord.Embed(
                    title="🔍 쪼맹이의 DB 점검 결과... 텅~!",
                    description="지금 데이터베이스에 저장된 메시지가 하나도 없어!\n쪼맹이한테 먼저 `/수집`을 시켜서 데이터를 모아줘! 😤",
                    color=discord.Color(0xE74C3C)
                )
                embed.set_footer(text=self.footer_text)
                await interaction.followup.send(embed=embed)
                return

            channel_text = "".join([f"• **#{ch_name}**: {count:,}개 메시지\n" for ch_name, count in channel_stats])

            # 🟢 성공/결과: 초록색
            embed = discord.Embed(
                title="🔍 쪼맹이가 털어온 DB 저장 현황!",
                description="내가 돋보기 들고 구석구석 확인해 보니 데이터가 이렇게 쌓여있어! 돋보기 활약 중! 🕵️‍♂️",
                color=discord.Color(0x2ECC71)
            )
            embed.add_field(name="📊 총 누적 메시지", value=f"**{total_count:,}**개", inline=True)
            embed.add_field(name="👥 총 참여 유저", value=f"**{total_users:,}**명", inline=True)
            embed.add_field(name="📁 채널별 수집 내역", value=channel_text if channel_text else "내역 없음", inline=False)
            embed.set_footer(text=self.footer_text)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ 쪼맹이가 DB 보다가 넘어졌어! 오류 발생: `{str(e)}`")

    @app_commands.command(name="분석", description="[쪼맹이] DB 데이터를 싹 훑어서 채널 대화 통계를 분석해 드립니다.")
    @app_commands.describe(channel="분석할 디스코드 채널을 선택해줘! (미선택 시 현재 채널)")
    async def analyze_command(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        await interaction.response.defer(thinking=True)

        target_channel = channel or interaction.channel
        df = await asyncio.to_thread(self._get_channel_data_sync, target_channel.id)

        if df.empty:
            # 🔴 경고: 빨간색
            embed = discord.Embed(
                title="⚠️ 쪼맹이 경고: 데이터 부족!",
                description=f"{target_channel.mention} 채널은 아직 쪼맹이가 수집한 데이터가 없어!\n먼저 `/수집` 커맨드로 데이터를 쌓아줘~ 맘껏 분석해 줄게!",
                color=discord.Color(0xE74C3C)
            )
            embed.set_footer(text=self.footer_text)
            await interaction.followup.send(embed=embed)
            return

        total_messages = len(df)
        total_users = df['author_id'].nunique()
        top_users = df['author_id'].value_counts().head(3)
        
        top_users_text = ""
        medals = ["🥇", "🥈", "🥉"]
        for idx, (user_id, count) in enumerate(top_users.items()):
            percentage = (count / total_messages) * 100
            top_users_text += f"{medals[idx]} <@{user_id}>: {count:,}개 ({percentage:.1f}%)\n"

        df['hour'] = df['created_at'].dt.hour
        peak_hour = df['hour'].mode()[0] if not df['hour'].empty else 0
        peak_hour_count = (df['hour'] == peak_hour).sum()
        avg_reactions = df['reaction_count'].mean() if 'reaction_count' in df.columns else 0.0

        # 🟢 성공/결과: 초록색
        embed = discord.Embed(
            title=f"📊 쪼맹이의 #{target_channel.name} 대화 분석 리포트!",
            description="작다고 무시하지 마라! 쪼맹이가 열심히 계산한 채널 통계라고! 🤓",
            color=discord.Color(0x2ECC71)
        )
        embed.add_field(name="💬 총 메시지 수", value=f"{total_messages:,}개", inline=True)
        embed.add_field(name="👥 대화 참여자", value=f"{total_users:,}명", inline=True)
        embed.add_field(name="⏰ 제일 핫했던 시간", value=f"{peak_hour}시 ~ {peak_hour+1}시\n({peak_hour_count:,}개 쏟아짐!)", inline=True)
        embed.add_field(name="🏆 수다쟁이 TOP 3", value=top_users_text if top_users_text else "데이터 없음", inline=False)
        embed.add_field(name="❤️ 평균 반응 이모지", value=f"메시지당 {avg_reactions:.2f}개", inline=True)
        embed.set_footer(text=self.footer_text)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DataAnalyzer(bot))