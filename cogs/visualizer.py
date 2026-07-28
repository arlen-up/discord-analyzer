import os
import io
import discord
from discord import app_commands
from discord.ext import commands
import pandas as pd
from kiwipiepy import Kiwi
from wordcloud import WordCloud
import matplotlib.pyplot as plt

class DataVisualizer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.kiwi = Kiwi()

    def load_channel_data(self, channel_name: str) -> pd.DataFrame:
        file_path = os.path.join(self.data_dir, f"{channel_name}_messages.csv")
        if not os.path.exists(file_path):
            return pd.DataFrame()
        return pd.read_csv(file_path)

    def extract_nouns(self, text_list):
        nouns = []
        for text in text_list:
            if isinstance(text, str) and text.strip():
                tokens = self.kiwi.tokenize(text)
                for token in tokens:
                    if token.tag in ['NNG', 'NNP', 'SL'] and len(token.form) > 1:
                        nouns.append(token.form)
        return " ".join(nouns)

    # [슬래시 커맨드] /워드클라우드
    @app_commands.command(name="워드클라우드", description="수집된 대화 데이터를 기반으로 키워드 워드클라우드 이미지를 생성합니다.")
    @app_commands.describe(channel="분석할 디스코드 채널")
    async def wordcloud_command(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()

        df = self.load_channel_data(channel.name)

        if df.empty or 'content' not in df.columns:
            embed = discord.Embed(
                title="⚠️ 데이터 탐색 실패",
                description=f"{channel.mention} 채널의 데이터가 존재하지 않습니다.\n먼저 `/수집` 커맨드로 데이터를 수집해 주세요!",
                color=discord.Color.gold()
            )
            await interaction.followup.send(embed=embed)
            return

        words_text = self.extract_nouns(df['content'].dropna())

        if not words_text.strip():
            await interaction.followup.send("❌ 워드클라우드를 생성할 만한 충분한 명사 단어가 데이터에 없습니다.")
            return

        font_path = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
        if not os.path.exists(font_path):
            font_path = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

        wc = WordCloud(
            font_path=font_path,
            background_color="white",
            width=800,
            height=500,
            max_words=100
        ).generate(words_text)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)

        discord_file = discord.File(fp=buf, filename=f"{channel.name}_wordcloud.png")

        embed = discord.Embed(
            title=f"🎨 #{channel.name} 주요 키워드 시각화",
            description="한국어 형태소 분석기(Kiwi)로 추출된 주요 핵심 단어 구름입니다.",
            color=discord.Color.fuchsia()
        )
        embed.set_image(url=f"attachment://{channel.name}_wordcloud.png")
        embed.set_footer(text="Kiwi Morphological Analyzer & WordCloud Engine")

        await interaction.followup.send(embed=embed, file=discord_file)

async def setup(bot):
    await bot.add_cog(DataVisualizer(bot))