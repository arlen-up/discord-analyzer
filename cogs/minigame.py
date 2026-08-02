import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

class Minigame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.footer_text = "쪼맹이 봇 • Created by tella._."
        
        # 📌 진행 중인 세션 저장소 (채널 ID를 Key로 사용)
        # { channel_id: { "type": "369" or "baskin", "players": [user_id, ...], "current_num": int } }
        self.active_games = {}

    # ----------------------------------------------------
    # 🛠️ 헬퍼 함수
    # ----------------------------------------------------
    def _check_369(self, num: int) -> str:
        """숫자를 369 규칙에 맞게 '짝' 문자열로 변환"""
        s_num = str(num)
        clap_count = sum(s_num.count(d) for d in ['3', '6', '9'])
        return "짝" * clap_count if clap_count > 0 else s_num

    # ----------------------------------------------------
    # 🎮 1. 채팅 감지 이벤트 (on_message)
    # ----------------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 봇 자신의 메시지나 봇의 명령어는 무시
        if message.author.bot:
            return

        channel_id = message.channel.id

        # 해당 채널에 진행 중인 게임이 없으면 패스
        if channel_id not in self.active_games:
            return

        game = self.active_games[channel_id]

        # 🎯 "해당 플레이어"의 채팅이 아니면 무시!
        if message.author.id not in game["players"]:
            return

        content = message.content.strip()

        # ====================================================
        # 👏 [369 게임 진행 로직]
        # ====================================================
        if game["type"] == "369":
            next_num = game["current_num"] + 1
            expected_answer = self._check_369(next_num)

            # ❌ 틀렸을 때 (게임 종료)
            if content != expected_answer:
                score = game["current_num"]
                del self.active_games[channel_id]  # 게임 세션 제거

                embed = discord.Embed(
                    title="❌ 땡! 틀렸다!",
                    description=(
                        f"{message.author.mention} 너 딱 걸렸어! 😜\n"
                        f"👉 **정답**: `{expected_answer}` | **네가 낸 값**: `{content}`\n\n"
                        f"🏆 **최종 기록**: **{score}**번 연속 성공!"
                    ),
                    color=discord.Color(0xE74C3C)
                )
                embed.set_footer(text=self.footer_text)
                await message.channel.send(embed=embed)
                return

            # ⭕ 유저 정답 성공!
            game["current_num"] = next_num
            await message.add_reaction("⭕")  # 정답 반응 표시

            # 🤖 쪼맹이(봇) 차례
            bot_next_num = next_num + 1
            bot_answer = self._check_369(bot_next_num)
            game["current_num"] = bot_next_num

            # 쪼맹이가 정답 채팅을 치며 턴 넘김
            await message.channel.send(f"🤖 **쪼맹이**: {bot_answer}")

        # ====================================================
        # 🍧 [베스킨라빈스 31 진행 로직]
        # ====================================================
        elif game["type"] == "baskin":
            # 입력된 메시지 분석 (예: "1 2 3" -> 3개 / "15 16" -> 2개 / "21" -> 1개)
            tokens = content.split()
            
            # 숫자만 들어왔는지 검증
            if not all(t.isdigit() for t in tokens):
                return  # 게임 관련 숫자가 아니면 일반 대화로 간주하고 무시

            called_nums = [int(t) for t in tokens]
            count = len(called_nums)

            # 1~3개 범위를 벗어나거나 순서가 틀린 경우 무시
            if count < 1 or count > 3:
                await message.channel.send("⚠️ 숫자는 한 번에 **1개에서 3개**까지만 부를 수 있어!", delete_after=3)
                return

            expected_nums = list(range(game["current_num"] + 1, game["current_num"] + count + 1))
            if called_nums != expected_nums:
                await message.channel.send(f"⚠️ 순서에 맞는 숫자를 불러줘! (다음 차례: **{game['current_num'] + 1}**부터)", delete_after=3)
                return

            # 유저 숫자 반영
            game["current_num"] = called_nums[-1]

            # ❌ 유저가 31 이상을 불러서 패배한 경우
            if game["current_num"] >= 31:
                del self.active_games[channel_id]
                embed = discord.Embed(
                    title="🎉 쪼맹이 승리!",
                    description=f"{message.author.mention} 유저가 마지막 **31**을 불러버렸네! 쪼맹이가 이겼지롱! 😜",
                    color=discord.Color(0x2ECC71)
                )
                embed.set_footer(text=self.footer_text)
                await message.channel.send(embed=embed)
                return

            # 🤖 쪼맹이(봇) 턴
            bot_count = random.randint(1, 3)
            if game["current_num"] + bot_count >= 31:
                bot_count = 31 - game["current_num"]

            bot_called = list(range(game["current_num"] + 1, game["current_num"] + bot_count + 1))
            game["current_num"] = bot_called[-1]
            bot_called_str = " ".join(map(str, bot_called))

            # 😭 쪼맹이가 31을 불러서 패배한 경우
            if game["current_num"] >= 31:
                del self.active_games[channel_id]
                embed = discord.Embed(
                    title="😭 쪼맹이 패배...",
                    description=f"🤖 **쪼맹이**: {bot_called_str}\n\n아이쿠! 쪼맹이가 31을 불러버렸어... 네가 이겼다! 👏",
                    color=discord.Color(0xE74C3C)
                )
                embed.set_footer(text=self.footer_text)
                await message.channel.send(embed=embed)
                return

            # 쪼맹이 진행 상태 채팅
            await message.channel.send(f"🤖 **쪼맹이**: {bot_called_str}")

    # ====================================================
    # 🚀 명령어 1: 369 게임 시작
    # ====================================================
    @app_commands.command(name="369시작", description="[쪼맹이] 채팅으로 바로 진행하는 369 게임을 시작합니다!")
    async def start_369(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id

        if channel_id in self.active_games:
            await interaction.response.send_message("⚠️ 이미 이 채널에서 게임이 진행 중이야! 먼저 게임을 끝내줘!", ephemeral=True)
            return

        # 게임 세션 등록 (시작한 유저의 ID 저장)
        self.active_games[channel_id] = {
            "type": "369",
            "players": [interaction.user.id],
            "current_num": 0
        }

        embed = discord.Embed(
            title="👏 369 게임 시작!",
            description=(
                f"🎮 **플레이어**: {interaction.user.mention}\n\n"
                f"이제부터 슬래시(`/`) 입력 필요 없이 **채팅창에 숫자나 '짝'을 치면 인식**해!\n"
                f"👉 첫 번째 숫자 **`1`**을 채팅으로 입력해줘!"
            ),
            color=discord.Color(0x90BAFF)
        )
        embed.set_footer(text=self.footer_text)
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # 🚀 명령어 2: 베스킨라빈스 31 시작
    # ====================================================
    @app_commands.command(name="베스킨시작", description="[쪼맹이] 채팅으로 바로 진행하는 베스킨라빈스 31 게임을 시작합니다!")
    async def start_baskin(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id

        if channel_id in self.active_games:
            await interaction.response.send_message("⚠️ 이미 이 채널에서 게임이 진행 중이야!", ephemeral=True)
            return

        self.active_games[channel_id] = {
            "type": "baskin",
            "players": [interaction.user.id],
            "current_num": 0
        }

        embed = discord.Embed(
            title="🍧 베스킨라빈스 31 시작!",
            description=(
                f"🎮 **플레이어**: {interaction.user.mention}\n\n"
                f"이제부터 슬래시(`/`) 필요 없이 **채팅창에 숫자(1~3개)를 치면 인식**해!\n"
                f"예시: `1` 또는 `1 2` 또는 `1 2 3`\n"
                f"👉 먼저 숫자를 채팅으로 불러줘!"
            ),
            color=discord.Color(0x90BAFF)
        )
        embed.set_footer(text=self.footer_text)
        await interaction.response.send_message(embed=embed)

    # ====================================================
    # 🛑 명령어 3: 게임 강제 종료
    # ====================================================
    @app_commands.command(name="게임종료", description="[쪼맹이] 현재 진행 중인 미니게임을 강제로 종료합니다.")
    async def stop_game(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id

        if channel_id not in self.active_games:
            await interaction.response.send_message("⚠️ 지금 이 채널에서 진행 중인 게임이 없어!", ephemeral=True)
            return

        del self.active_games[channel_id]

        embed = discord.Embed(
            title="🛑 미니게임 강제 종료",
            description="진행 중이던 게임을 멈췄어! 이제 다시 자유롭게 대화하면 돼~",
            color=discord.Color(0xE74C3C)
        )
        embed.set_footer(text=self.footer_text)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Minigame(bot))