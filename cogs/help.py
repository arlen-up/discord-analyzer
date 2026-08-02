import discord
from discord import app_commands
from discord.ext import commands

# ----------------------------------------------------
# 🔘 페이지 이동용 드롭다운 UI 클래스
# ----------------------------------------------------
class HelpView(discord.ui.View):
    def __init__(self, theme_color, footer_text):
        super().__init__(timeout=120)  # 2분간 상호작용 가능
        self.theme_color = theme_color
        self.footer_text = footer_text

    @discord.ui.select(
        placeholder="원하는 도움말 페이지를 선택해줘!",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="1페이지: 데이터 분석 & 요약",
                value="page1",
                description="수집, 분석, 요약, 차트, 워드클라우드 기능",
                emoji="📊",
                default=True
            ),
            discord.SelectOption(
                label="2페이지: 쪼맹이 미니게임",
                value="page2",
                description="369, 베스킨라빈스31, 경마 레이스 기능",
                emoji="🎮"
            )
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        selected_value = select.values[0]

        # 기본 드롭다운의 default 상태 업데이트
        for option in select.options:
            option.default = (option.value == selected_value)

        if selected_value == "page1":
            embed = self.get_page1_embed()
        else:
            embed = self.get_page2_embed()

        # 메시지 임베드 업데이트
        await interaction.response.edit_message(embed=embed, view=self)

    # 📄 1페이지: 데이터 분석 & 요약 기능
    def get_page1_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🔍 [1페이지] 데이터 분석 & 요약 기능",
            description="안녕! 나는 돋보기 들고 대화를 분석하는 **쪼맹이**야! 🤓\n수집하고 분석하는 야무진 기능들을 알려줄게!",
            color=self.theme_color
        )
        embed.add_field(
            name="📥 /수집 [채널] [개수]", 
            value="쪼맹이가 돋보기를 들고 출동해서 채널 대화를 DB 장부에 쓱싹 수집해 와!", 
            inline=False
        )
        embed.add_field(
            name="💾 /db현황", 
            value="쪼맹이의 비밀 장부에 메시지가 얼마나 쌓였는지 탈탈 털어서 보여줄게!", 
            inline=False
        )
        embed.add_field(
            name="📊 /분석 [채널]", 
            value="채널의 수다쟁이 TOP 3랑 제일 핫했던 시간대를 쪼맹이가 싹 계산해 줘!", 
            inline=False
        )
        embed.add_field(
            name="📝 /요약 [채널]", 
            value="길고 긴 대화 내용을 쪼맹이가 핵심만 쏙쏙 뽑아서 깔끔하게 요약해 줄게!", 
            inline=False
        )
        embed.add_field(
            name="📈 /차트 [채널]", 
            value="채널 대화가 어느 시간대에 몰렸는지 알록달록한 그래프로 그려줄게!", 
            inline=False
        )
        embed.add_field(
            name="☁️ /워드클라우드 [채널]", 
            value="사람들이 제일 많이 쓴 단어들을 몽실몽실한 워드클라우드로 시각화해 줘!", 
            inline=False
        )
        embed.set_footer(text=f"{self.footer_text} • (1/2 페이지)")
        return embed

    # 📄 2페이지: 미니게임 기능
    def get_page2_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎮 [2페이지] 쪼맹이 우당탕탕 미니게임",
            description="분석만 하면 심심하잖아! 쪼맹이랑 같이 즐겁게 놀아보자구! 🎲",
            color=self.theme_color
        )
        embed.add_field(
            name="👏 /369시작", 
            value="채팅으로 바로 진행하는 369 게임! 슬래시 없이 채팅으로 `1`, `2`, `짝`을 바로 쳐서 대결해!", 
            inline=False
        )
        embed.add_field(
            name="🍧 /베스킨시작", 
            value="채팅으로 바로 진행하는 베스킨라빈스 31! `1 2`나 `3 4 5`처럼 숫자를 채팅으로 불러 대결해!", 
            inline=False
        )
        embed.add_field(
            name="🐎 /경마 [말 수] [응원할 말 번호]", 
            value="출전시킬 말의 수(2~8마리)를 정해서 열리는 우당탕탕 실시간 경마 레이스!", 
            inline=False
        )
        embed.add_field(
            name="🛑 /게임종료", 
            value="현재 채널에서 진행 중인 369나 베스킨라빈스 게임을 멈추고 종료해!", 
            inline=False
        )
        embed.set_footer(text=f"{self.footer_text} • (2/2 페이지)")
        return embed

# ----------------------------------------------------
# 📌 도움말 코그 (Cog)
# ----------------------------------------------------
class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.theme_color = discord.Color(0x90BAFF)
        self.footer_text = "쪼맹이 봇 • Created by tella._."

    @app_commands.command(name="도움말", description="[쪼맹이] 작지만 야무진 쪼맹이 봇의 모든 사용법을 소개해 드립니다!")
    async def help_command(self, interaction: discord.Interaction):
        # UI 뷰 생성
        view = HelpView(self.theme_color, self.footer_text)
        # 기본 1페이지 임베드 가져오기
        first_embed = view.get_page1_embed()

        await interaction.response.send_message(embed=first_embed, view=view)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))