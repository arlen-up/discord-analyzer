import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import database

class Collector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        database.init_db()
        self.footer_text = "쪼맹이 봇 • Created by tella._."

    @app_commands.command(name="수집", description="[쪼맹이] 지정한 채널의 대화 데이터를 돋보기로 열심히 수집해서 DB에 적어둡니다.")
    @app_commands.describe(channel="수집할 채널을 선택해줘! (미선택 시 현재 채널)", limit="수집할 메시지 개수 (기본값: 100개)")
    async def collect_messages(self, interaction: discord.Interaction, channel: discord.TextChannel = None, limit: int = 100):
        await interaction.response.defer(thinking=True)

        target_channel = channel or interaction.channel
        messages_data = []

        try:
            print(f"📥 쪼맹이 출동! #{target_channel.name} 채널 메시지 수집 시작 (목표: {limit}개)...")

            async for message in target_channel.history(limit=limit):
                if message.type in (discord.MessageType.default, discord.MessageType.reply):
                    messages_data.append((
                        message.id,
                        target_channel.id,
                        target_channel.name,
                        message.author.id,
                        message.author.name,
                        message.content,
                        sum(r.count for r in message.reactions) if message.reactions else 0,
                        message.created_at.isoformat()
                    ))

            if messages_data:
                await asyncio.to_thread(database.save_messages, messages_data)
                
                # 🟢 성공: 초록색
                embed = discord.Embed(
                    title="📥 쪼맹이의 대화 수집 완료!",
                    description=f"**#{target_channel.name}** 채널에서 총 **{len(messages_data):,}개**의 메시지를 돋보기로 싹 훑어서 DB 장부에 잘 넣어뒀어! 📝",
                    color=discord.Color(0x2ECC71)
                )
                embed.set_footer(text=self.footer_text)
                await interaction.followup.send(embed=embed)
            else:
                # 🔴 경고: 빨간색
                embed = discord.Embed(
                    title="⚠️ 쪼맹이 당황... 수집할 게 없어!",
                    description=f"**#{target_channel.name}** 채널에 수집할 메시지가 없거나 쪼맹이가 읽을 수 없는 상태야! 확인해 줘!",
                    color=discord.Color(0xE74C3C)
                )
                embed.set_footer(text=self.footer_text)
                await interaction.followup.send(embed=embed)

        except discord.Forbidden:
            # 🔴 경고: 빨간색
            embed = discord.Embed(
                title="❌ 쪼맹이 접근 금지!",
                description=f"쪼맹이한테 **#{target_channel.name}** 채널의 **'메시지 기록 읽기'** 권한이 없어! 권한 좀 줄래? 😤",
                color=discord.Color(0xE74C3C)
            )
            embed.set_footer(text=self.footer_text)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ 쪼맹이가 메시지 적다가 연필심이 부러졌어! 오류 발생: `{e}`")

async def setup(bot):
    await bot.add_cog(Collector(bot))