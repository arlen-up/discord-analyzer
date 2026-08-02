import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import sqlite3
import io
import os
import platform

# 🔴 [중요] matplotlib.pyplot을 import하기 전에 반드시 백엔드를 'Agg'로 변경해야 합니다!
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from wordcloud import WordCloud
import database

def get_system_font():
    os_name = platform.system()
    if os_name == "Windows":
        return "c:/Windows/Fonts/malgun.ttf"
    elif os_name == "Darwin":
        return "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
    else:
        return "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

FONT_PATH = get_system_font()
plt.rc('font', family='AppleGothic' if platform.system() == 'Darwin' else 'Malgun Gothic')
plt.rc('axes', unicode_minus=False)

class Visualizer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.footer_text = "쪼맹이 봇 • Created by tella._."

    def _get_channel_data_for_viz(self, channel_id: int):
        conn = sqlite3.connect(database.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT author_name, strftime('%H', created_at) as hour, content FROM messages WHERE channel_id = ?", (channel_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    @app_commands.command(name="차트", description="[쪼맹이] DB 데이터를 기반으로 시간대별 대화량 그래프를 그려드립니다.")
    @app_commands.describe(channel="시각화할 채널을 선택해줘! (미선택 시 현재 채널)")
    async def visualize_command(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        await interaction.response.defer(thinking=True)

        target_channel = channel or interaction.channel
        rows = await asyncio.to_thread(self._get_channel_data_for_viz, target_channel.id)

        if not rows:
            # 🔴 경고: 빨간색
            embed = discord.Embed(
                title="⚠️ 쪼맹이 당황: 그려줄 그래프가 없어!",
                description=f"{target_channel.mention} 채널은 쪼맹이가 모은 데이터가 없어!\n먼저 `/수집` 커맨드로 대화를 장부에 적어줘!",
                color=discord.Color(0xE74C3C)
            )
            embed.set_footer(text=self.footer_text)
            await interaction.followup.send(embed=embed)
            return

        image_buf = await asyncio.to_thread(self._create_chart, rows, target_channel.name)
        file = discord.File(image_buf, filename="chart.png")

        # 🟢 성공/결과: 초록색
        embed = discord.Embed(
            title=f"📈 쪼맹이가 그린 #{target_channel.name} 시간대별 대화량 차트!",
            description="언제 대화가 제일 많이 쏟아졌는지 쪼맹이가 깔끔하게 그래프로 그려왔지! 📊",
            color=discord.Color(0x2ECC71)
        )
        embed.set_image(url="attachment://chart.png")
        embed.set_footer(text=self.footer_text)

        await interaction.followup.send(embed=embed, file=file)

    @app_commands.command(name="워드클라우드", description="[쪼맹이] DB 데이터를 기반으로 자주 사용된 키워드 워드클라우드를 생성합니다.")
    @app_commands.describe(channel="시각화할 채널을 선택해줘! (미선택 시 현재 채널)")
    async def wordcloud_command(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        await interaction.response.defer(thinking=True)

        target_channel = channel or interaction.channel
        rows = await asyncio.to_thread(self._get_channel_data_for_viz, target_channel.id)

        if not rows:
            # 🔴 경고: 빨간색
            embed = discord.Embed(
                title="⚠️ 쪼맹이 당황: 워드클라우드 재료가 없어!",
                description=f"{target_channel.mention} 채널의 데이터가 비어있어!\n먼저 `/수집` 커맨드로 데이터를 모아줘!",
                color=discord.Color(0xE74C3C)
            )
            embed.set_footer(text=self.footer_text)
            await interaction.followup.send(embed=embed)
            return

        contents = [str(r[2]) for r in rows if r[2] and str(r[2]).strip() != ""]
        combined_text = " ".join(contents)

        if not combined_text.strip():
            await interaction.followup.send("⚠️ 쪼맹이가 단어를 구름으로 만들기엔 메시지가 너무 부족해!")
            return

        try:
            image_buf = await asyncio.to_thread(self._create_wordcloud, combined_text)
            file = discord.File(image_buf, filename="wordcloud.png")

            # 🟢 성공/결과: 초록색
            embed = discord.Embed(
                title=f"☁️ 쪼맹이의 #{target_channel.name} 몽실몽실 워드클라우드!",
                description=f"총 **{len(contents):,}개**의 메시지에서 사람들이 제일 많이 쓴 단어들을 모아봤어! 커다란 단어일수록 많이 쓴 거래! 🔍",
                color=discord.Color(0x2ECC71)
            )
            embed.set_image(url="attachment://wordcloud.png")
            embed.set_footer(text=self.footer_text)

            await interaction.followup.send(embed=embed, file=file)
        except Exception as e:
            await interaction.followup.send(f"⚠️ 쪼맹이가 구름 만들다가 실수를 했어! 오류: `{str(e)}`")

    def _create_chart(self, rows, channel_name):
        hours = [int(r[1]) for r in rows if r[1] is not None]
        hour_counts = [hours.count(i) for i in range(24)]

        plt.figure(figsize=(10, 4.5))
        plt.bar(range(24), hour_counts, color='#90BAFF')
        plt.title(f"#{channel_name} 시간대별 메시지 작성 빈도", fontsize=14, fontweight='bold')
        plt.xlabel("시간 (0시 ~ 23시)")
        plt.ylabel("메시지 수")
        plt.xticks(range(0, 24))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        buf.seek(0)
        plt.close()
        return buf

    def _create_wordcloud(self, text):
        wc = WordCloud(
            font_path=FONT_PATH,
            width=800,
            height=400,
            background_color="white",
            max_words=100,
            colormap="Blues"
        )
        wc.generate(text)

        plt.figure(figsize=(10, 5))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout(pad=0)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        buf.seek(0)
        plt.close()
        return buf

async def setup(bot):
    await bot.add_cog(Visualizer(bot))