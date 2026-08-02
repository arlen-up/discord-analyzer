import os
import discord
from discord import app_commands
from discord.ext import commands
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud

class DataVisualizer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"

    def load_data(self, channel_name: str) -> pd.DataFrame:
        file_path = os.path.join(self.data_dir, f"{channel_name}_messages.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
            return df
        return pd.DataFrame()

    @app_commands.command(name="워드클라우드", description="채널의 대화 데이터로 워드클라우드 이미지를 생성합니다.")
    @app_commands.describe(channel="시각화할 채널을 선택하세요")
    async def wordcloud_command(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()

        df = self.load_data(channel.name)
        if df.empty or 'content' not in df.columns:
            await interaction.followup.send("⚠️ 분석할 데이터가 없습니다. 먼저 `/수집`을 실행해 주세요.")
            return

        # 텍스트 병합 및 불용어/빈값 처리
        text_data = " ".join(df['content'].dropna().astype(str))
        if not text_data.strip():
            await interaction.followup.send("⚠️ 수집된 메시지에 텍스트 내용이 없습니다.")
            return

        # 시스템 한글 폰트 경로 설정 (Windows: malgun.ttf / Linux: NanumGothic.ttf)
        font_path = "C:/Windows/Fonts/malgun.ttf" if os.name == 'nt' else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

        try:
            wc = WordCloud(
                font_path=font_path if os.path.exists(font_path) else None,
                width=800,
                height=400,
                background_color="white"
            ).generate(text_data)

            output_path = f"data/{channel.name}_wordcloud.png"
            wc.to_file(output_path)

            file = discord.File(output_path, filename="wordcloud.png")
            embed = discord.Embed(
                title=f"☁️ #{channel.name} 워드클라우드",
                color=discord.Color.purple()
            )
            embed.set_image(url="attachment://wordcloud.png")

            await interaction.followup.send(embed=embed, file=file)

        except Exception as e:
            await interaction.followup.send(f"❌ 워드클라우드 생성 중 오류 발생: {str(e)}")

    @app_commands.command(name="차트", description="채널 대화 활성도 시각화 차트를 출력합니다.")
    @app_commands.describe(channel="시각화할 채널을 선택하세요")
    async def chart_command(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()

        df = self.load_data(channel.name)
        if df.empty or 'created_at' not in df.columns:
            await interaction.followup.send("⚠️ 분석할 데이터가 없습니다. 먼저 `/수집`을 실행해 주세요.")
            return

        df['hour'] = df['created_at'].dt.hour
        hourly_counts = df['hour'].value_counts().sort_index()

        # 그래프 생성
        plt.figure(figsize=(10, 5))
        plt.bar(hourly_counts.index, hourly_counts.values, color='skyblue', edgecolor='blue')
        plt.xlabel('Hour (0-23)')
        plt.ylabel('Messages')
        plt.title(f'Hourly Activity for #{channel.name}')
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        chart_path = f"data/{channel.name}_chart.png"
        plt.savefig(chart_path, bbox_inches='tight')
        plt.close() # 메모리 해제

        file = discord.File(chart_path, filename="chart.png")
        embed = discord.Embed(
            title=f"📈 #{channel.name} 시간대별 대화량 차트",
            color=discord.Color.teal()
        )
        embed.set_image(url="attachment://chart.png")

        await interaction.followup.send(embed=embed, file=file)

async def setup(bot):
    await bot.add_cog(DataVisualizer(bot))