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
        # 한국어 형태소 분석기 초기화
        self.kiwi = Kiwi()

    # [내부 함수] 특정 채널의 CSV 데이터 로드
    def load_channel_data(self, channel_name: str) -> pd.DataFrame:
        file_path = os.path.join(self.data_dir, f"{channel_name}_messages.csv")
        if not os.path.exists(file_path):
            return pd.DataFrame()
        return pd.read_csv(file_path)

    # [내부 함수] 텍스트에서 명사 추출
    def extract_nouns(self, text_list):
        nouns = []
        for text in text_list:
            if isinstance(text, str) and text.strip():
                # Kiwi 분석기로 명사(NNG, NNP) 및 외국어(SL) 추출
                tokens = self.kiwi.tokenize(text)
                for token in tokens:
                    # 2글자 이상의 명사/단어만 선택
                    if token.tag in ['NNG', 'NNP', 'SL'] and len(token.form) > 1:
                        nouns.append(token.form)
        return " ".join(nouns)

    # [슬래시 커맨드] /워드클라우드
    @app_commands.command(name="워드클라우드", description="수집된 대화 데이터를 기반으로 키워드 워드클라우드 이미지를 생성합니다.")
    @app_commands.describe(channel="분석할 디스코드 채널을 선택하세요")
    async def wordcloud_command(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()

        # 1. 데이터 로드
        df = self.load_channel_data(channel.name)

        if df.empty or 'content' not in df.columns:
            embed = discord.Embed(
                title="⚠️ 데이터 없음",
                description=f"{channel.mention} 채널의 수집 데이터가 없습니다.\n먼저 `/수집` 커맨드로 데이터를 수집해 주세요!",
                color=discord.Color.gold()
            )
            await interaction.followup.send(embed=embed)
            return

        # 2. 명사 추출
        words_text = self.extract_nouns(df['content'].dropna())

        if not words_text.strip():
            await interaction.followup.send("❌ 워드클라우드를 생성할 만한 충분한 단어가 데이터에 없습니다.")
            return

        # 3. 워드클라우드 생성 (맥 한글 폰트 적용)
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

        # 4. 이미지를 메모리 버퍼(In-Memory)에 저장
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")

        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)

        # 5. 디스코드 메시지 첨부 파일로 전송
        discord_file = discord.File(fp=buf, filename=f"{channel.name}_wordcloud.png")

        embed = discord.Embed(
            title=f"☁️ #{channel.name} 채널 키워드 워드클라우드",
            description="대화 내용 중 가장 자주 쓰인 주요 단어 시각화 결과입니다.",
            color=discord.Color.purple()
        )
        embed.set_image(url=f"attachment://{channel.name}_wordcloud.png")

        await interaction.followup.send(embed=embed, file=discord_file)

async def setup(bot):
    await bot.add_cog(DataVisualizer(bot))