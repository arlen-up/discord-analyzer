import discord
from discord import app_commands
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="도움말", description="봇의 모든 슬래시 커맨드 기능과 사용법을 확인합니다.")
    async def help_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        embed = discord.Embed(
            title="📖 디스코드 채널 분석 봇 명령어 안내",
            description="아래 명령어를 사용하여 채널의 대화 데이터를 수집, 분석, 시각화할 수 있습니다.",
            color=discord.Color.blue()
        )

        # 📥 1. 데이터 수집 및 DB 관리 커맨드
        embed.add_field(
            name="📥 데이터 수집 & DB 관리",
            value=(
                "• `~/수집 [채널] [수집 개수]` : 지정한 채널의 최근 메시지를 수집하여 DB에 저장합니다.\n"
                "• `~/db현황` : DB에 누적 저장된 전체 메시지 수와 채널별 저장 내역을 확인합니다.\n"
                "• `⏰ (자동 수집)` : 매일 자정 12시마다 각 채널의 최신 대화가 자동 갱신됩니다."
            ),
            inline=False
        )

        # 📊 2. 통계 및 요약 커맨드
        embed.add_field(
            name="📊 통계 & 요약",
            value=(
                "• `~/분석 [채널]` : 채널의 총 메시지, 활동 유저 순위, 피크 타임 통계를 출력합니다.\n"
                "• `~/요약 [채널]` : 대화 구성 비율 및 리액션이 많았던 주요 메시지를 요약합니다."
            ),
            inline=False
        )

        # 🎨 3. 시각화 커맨드
        embed.add_field(
            name="🎨 시각화 리포트",
            value=(
                "• `~/워드클라우드 [채널]` : 채널 대화의 주요 키워드를 워드클라우드 이미지로 생성합니다.\n"
                "• `~/차트 [채널]` : 시간대별 대화 활성도를 그래프 차트로 출력합니다."
            ),
            inline=False
        )

        embed.set_footer(text="Discord Channel Analyzer • SQLite DB Powered")

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))