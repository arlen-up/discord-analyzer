import os
import discord
from discord import app_commands
from discord.ext import commands
import pandas as pd

class DataCollector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    @app_commands.command(name="수집", description="지정한 채널의 최근 메시지를 수집하여 저장합니다.")
    @app_commands.describe(
        channel="수집할 디스코드 채널을 선택하세요",
        limit="수집할 메시지 최대 개수 (기본값: 1000)"
    )
    async def collect_command(self, interaction: discord.Interaction, channel: discord.TextChannel, limit: int = 1000):
        await interaction.response.defer()

        messages_data = []
        try:
            async for message in channel.history(limit=limit):
                # 봇 메시지 제외 (필요 시 주석 해제)
                # if message.author.bot:
                #     continue

                messages_data.append({
                    "message_id": message.id,
                    "created_at": message.created_at,
                    "author_id": message.author.id,          # 👈 클릭 가능한 멘션 핵심 데이터
                    "author_name": message.author.name,
                    "content": message.content,
                    "attachments_count": len(message.attachments),
                    "reactions_count": sum(r.count for r in message.reactions) if message.reactions else 0
                })

            df = pd.DataFrame(messages_data)
            file_path = os.path.join(self.data_dir, f"{channel.name}_messages.csv")
            
            # utf-8-sig 인코딩으로 한글 및 특수문자 깨짐 방지
            df.to_csv(file_path, index=False, encoding="utf-8-sig")

            embed = discord.Embed(
                title="✅ 데이터 수집 완료",
                description=f"{channel.mention} 채널에서 **{len(df):,}개**의 메시지를 수집했습니다.\n`data/{channel.name}_messages.csv` 경로에 저장되었습니다.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ 데이터 수집 실패",
                description=f"오류가 발생했습니다: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DataCollector(bot))