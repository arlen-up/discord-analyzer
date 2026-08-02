import os
import discord
from discord import app_commands
from discord.ext import commands
import pandas as pd
import asyncio
import openai
import database

class DataSummarizer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=api_key) if api_key else None
        self.footer_text = "쪼맹이 봇 • Created by tella._."

    def _load_data_from_db(self, channel_id: int) -> pd.DataFrame:
        rows = database.get_channel_messages(channel_id)
        if not rows:
            return pd.DataFrame()
        columns = ["message_id", "channel_id", "channel_name", "author_id", "author_name", "content", "reaction_count", "created_at"]
        return pd.DataFrame(rows, columns=columns)

    def _generate_gpt_summary(self, chat_text: str, channel_name: str) -> str:
        if not self.client:
            return "⚠️ OpenAI API 키가 설정되지 않아 쪼맹이가 요약할 수 없어! (.env 파일 확인 필요)"

        system_prompt = (
            "당신은 작지만 야무진 디스코드 대화 요약 전문가 '쪼맹이'입니다. "
            "약간의 귀엽고 야무진 말투(예: ~했지, ~했어!, ~더라고)를 살려 제시된 대화 내용을 명확하고 친절하게 마크다운 포맷으로 요약해 주세요."
        )
        user_prompt = f"다음은 #{channel_name} 채널의 최근 대화 내역입니다:\n\n{chat_text}\n\n위 대화를 바탕으로 아래 구조에 맞춰 요약해 주세요:\n1. 📌 핵심 대화 주제 (2~3개)\n2. 📝 상세 내용 요약\n3. 💡 전체적인 대화 분위기/특징"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ 쪼맹이가 대화 읽다가 머리가 아파졌어! (오류: {str(e)})"

    @app_commands.command(name="요약", description="[쪼맹이] GPT를 사용해 채널의 대화 내용을 야무지게 요약해 드립니다.")
    @app_commands.describe(channel="요약할 디스코드 채널을 선택해줘! (미선택 시 현재 채널)")
    async def summarize_command(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        await interaction.response.defer(thinking=True)
        target_channel = channel or interaction.channel

        df = await asyncio.to_thread(self._load_data_from_db, target_channel.id)

        if df.empty or 'content' not in df.columns:
            # 🔴 경고: 빨간색
            embed = discord.Embed(
                title="⚠️ 쪼맹이 당황: 요약할 데이터가 없어!",
                description=f"{target_channel.mention} 채널은 쪼맹이가 모은 데이터가 없어!\n먼저 `/수집` 커맨드로 대화를 장부에 적어줘!",
                color=discord.Color(0xE74C3C)
            )
            embed.set_footer(text=self.footer_text)
            await interaction.followup.send(embed=embed)
            return

        valid_df = df.dropna(subset=['content'])
        valid_df = valid_df[valid_df['content'].str.strip() != ""]

        if valid_df.empty:
            await interaction.followup.send("⚠️ 요약할 만한 글자 메시지가 없더라고!")
            return

        recent_df = valid_df.tail(80)
        chat_lines = [f"{row['author_name']}: {row['content']}" for _, row in recent_df.iterrows()]
        chat_text = "\n".join(chat_lines)

        ai_summary = await asyncio.to_thread(self._generate_gpt_summary, chat_text, target_channel.name)

        # ----------------------------------------------------
        # 💡 참여자 명단을 클릭 가능한 멘션(<@user_id>) 형태로 변환
        # ----------------------------------------------------
        user_mentions = []
        if 'author_id' in df.columns:
            unique_users = df.drop_duplicates(subset=['author_id'])
            for _, row in unique_users.iterrows():
                user_id = row['author_id']
                author_name = row['author_name']
                if pd.notna(user_id) and str(user_id).isdigit():
                    user_mentions.append(f"<@{int(user_id)}>")
                elif pd.notna(author_name):
                    user_mentions.append(f"`{author_name}`")

        user_names_str = ", ".join(user_mentions) if user_mentions else "없음"

        top_reacted = ""
        if 'reaction_count' in df.columns:
            top_msg_df = df.sort_values(by='reaction_count', ascending=False).head(3)
            for idx, row in top_msg_df.iterrows():
                if row['reaction_count'] > 0:
                    author = f"<@{row['author_id']}>" if 'author_id' in row and pd.notna(row['author_id']) else row['author_name']
                    content_str = str(row['content']) if pd.notna(row['content']) else ""
                    content_preview = content_str[:40] + ("..." if len(content_str) > 40 else "")
                    top_reacted += f"• {author}: \"{content_preview}\" (❤️ {row['reaction_count']}개)\n"

        # 🟢 성공/결과: 초록색
        embed = discord.Embed(
            title=f"📝 쪼맹이의 #{target_channel.name} 대화 요약 리포트!",
            description=ai_summary,
            color=discord.Color(0x2ECC71)
        )
        embed.add_field(name="📊 데이터 통계", value=f"• 요약한 메시지 수: 총 {len(df):,}개 중 최근 {len(recent_df)}개\n• 참여자 수: 총 {len(user_mentions)}명", inline=False)
        embed.add_field(name="👥 대화 참여자 명단", value=user_names_str, inline=False)

        if top_reacted:
            embed.add_field(name="🔥 제일 반응이 핫했던 메시지 TOP 3", value=top_reacted, inline=False)

        embed.set_footer(text=self.footer_text)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="db상세", description="[관리자 전용] 쪼맹이의 비밀 DB 장부(참여 유저, 수집 기간 등)를 자세히 열람합니다.")
    @app_commands.describe(channel="조회할 채널을 선택해줘! (미선택 시 현재 채널)")
    @app_commands.default_permissions(manage_channels=True)
    async def db_detail_command(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        await interaction.response.defer(thinking=True, ephemeral=True)
        target_channel = channel or interaction.channel

        df = await asyncio.to_thread(self._load_data_from_db, target_channel.id)

        if df.empty:
            # 🔴 경고: 빨간색
            embed = discord.Embed(
                title="⚠️ 쪼맹이의 장부가 비어있어!",
                description=f"{target_channel.mention} 채널에 저장된 데이터가 아직 없네!",
                color=discord.Color(0xE74C3C)
            )
            embed.set_footer(text=self.footer_text)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # ----------------------------------------------------
        # 💡 DB 상세 장부 유저 지분 목록도 클릭 가능한 멘션 형태로 변환
        # ----------------------------------------------------
        user_list_str = ""
        if 'author_id' in df.columns:
            user_counts = df.groupby(['author_id', 'author_name']).size().sort_values(ascending=False)
            for (user_id, author_name), count in user_counts.items():
                mention = f"<@{int(user_id)}>" if pd.notna(user_id) and str(user_id).isdigit() else f"**{author_name}**"
                user_list_str += f"• {mention}: {count:,}개\n"
        else:
            user_counts = df['author_name'].value_counts()
            user_list_str = "\n".join([f"• **{author}**: {count:,}개" for author, count in user_counts.items()])

        first_time = str(df['created_at'].min())[:19].replace("T", " ")
        last_time = str(df['created_at'].max())[:19].replace("T", " ")

        recent_samples = df.tail(5)
        sample_str = ""
        for _, row in recent_samples.iterrows():
            content_str = str(row['content'])[:30] + ("..." if len(str(row['content'])) > 30 else "")
            author_mention = f"<@{int(row['author_id'])}>" if 'author_id' in row and pd.notna(row['author_id']) else row['author_name']
            created_at_str = str(row['created_at'])[:16].replace('T', ' ')
            sample_str += f"• [{created_at_str}] {author_mention}: {content_str}\n"

        # 🔵 정보 조회: 기본 시그니처 하늘색 (#90BAFF)
        embed = discord.Embed(
            title=f"🔍 쪼맹이의 #{target_channel.name} DB 상세 장부 (관리자 전용)",
            description="웻! 아무한테나 안 보여주는 쪼맹이의 비밀 상세 장부야! 🤫",
            color=discord.Color(0x90BAFF)
        )
        embed.add_field(name="📅 수집 기록 기간", value=f"{first_time}\n~ {last_time}", inline=False)
        embed.add_field(name=f"👥 참여자 및 지분 (총 {len(df['author_id'].unique()) if 'author_id' in df.columns else len(df['author_name'].unique())}명)", value=user_list_str if user_list_str else "없음", inline=False)
        embed.add_field(name="💬 최근 장부에 적힌 메시지 (5개)", value=sample_str if sample_str else "내용 없음", inline=False)
        embed.set_footer(text=self.footer_text)

        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(DataSummarizer(bot))