import os
import discord
from discord import app_commands
from discord.ext import commands
import pandas as pd

class DataSummarizer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"

    def load_data(self, channel_name: str) -> pd.DataFrame:
        file_path = os.path.join(self.data_dir, f"{channel_name}_messages.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            return df
        return pd.DataFrame()

    @app_commands.command(name="요약", description="채널의 최근 주요 대화 요약 리포트를 출력합니다.")
    @app_commands.describe(channel="요약할 디스코드 채널을 선택하세요")
    async def summarize_command(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()

        df = self.load_data(channel.name)
        if df.empty or 'content' not in df.columns:
            embed = discord.Embed(
                title="⚠️ 데이터 없음",
                description=f"{channel.mention} 채널의 수집 데이터가 없습니다.\n먼저 `/수집` 커맨드로 데이터를 수집해 주세요!",
                color=discord.Color.gold()
            )
            await interaction.followup.send(embed=embed)
            return

        # 텍스트 데이터 정제
        valid_messages = df['content'].dropna().astype(str)
        valid_messages = valid_messages[valid_messages.str.strip() != ""]

        if valid_messages.empty:
            await interaction.followup.send("⚠️ 요약할 수 있는 텍스트 메시지가 없습니다.")
            return

        # 리액션 반응이 가장 많았던 상위 메시지 샘플 추출
        top_reacted = ""
        if 'reactions_count' in df.columns:
            top_msg_df = df.sort_values(by='reactions_count', ascending=False).head(3)
            for idx, row in top_msg_df.iterrows():
                if row['reactions_count'] > 0:
                    author = f"<@{row['author_id']}>" if 'author_id' in row and pd.notna(row['author_id']) else row['author_name']
                    content_preview = row['content'][:50] + ("..." if len(str(row['content'])) > 50 else "")
                    top_reacted += f"• {author}: \"{content_preview}\" (❤️ {row['reactions_count']}개)\n"

        embed = discord.Embed(
            title=f"📝 #{channel.name} 대화 요약 리포트",
            description=f"총 **{len(df):,}개**의 대화 내역을 분석한 결과입니다.",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📊 메시지 구성",
            value=f"• 전체 메시지: {len(df):,}개\n• 텍스트 메시지: {len(valid_messages):,}개\n• 첨부파일 포함: {df['attachments_count'].sum() if 'attachments_count' in df.columns else 0:,}개",
            inline=False
        )

        if top_reacted:
            embed.add_field(
                name="🔥 가장 반응이 뜨거웠던 메시지 TOP 3",
                value=top_reacted,
                inline=False
            )

        embed.set_footer(text="Discord Channel Summarizer")

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DataSummarizer(bot))