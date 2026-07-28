import os
import discord
from discord import app_commands
from discord.ext import commands
import pandas as pd
from google import genai

class DataSummarizer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    def load_channel_data(self, channel_name: str) -> pd.DataFrame:
        file_path = os.path.join(self.data_dir, f"{channel_name}_messages.csv")
        if not os.path.exists(file_path):
            return pd.DataFrame()
        return pd.read_csv(file_path)

    # [슬래시 커맨드] /요약
    @app_commands.command(name="요약", description="수집된 채널 대화 내용을 AI(Gemini)가 정밀 분석하여 요약해 줍니다.")
    @app_commands.describe(
        channel="요약할 디스코드 채널",
        limit="요약할 최근 메시지 수 (기본값: 50개)"
    )
    async def summarize_command(self, interaction: discord.Interaction, channel: discord.TextChannel, limit: int = 50):
        await interaction.response.defer()

        if not self.client:
            await interaction.followup.send("❌ Gemini API 키가 설정되지 않았습니다. `.env` 파일을 확인해 주세요.")
            return

        df = self.load_channel_data(channel.name)

        if df.empty or 'content' not in df.columns:
            embed = discord.Embed(
                title="⚠️ 데이터 탐색 실패",
                description=f"{channel.mention} 채널의 데이터가 존재하지 않습니다.\n먼저 `/수집` 커맨드로 데이터를 수집해 주세요!",
                color=discord.Color.gold()
            )
            await interaction.followup.send(embed=embed)
            return

        recent_df = df.tail(limit)
        
        conversation_text = ""
        for _, row in recent_df.iterrows():
            author = row.get('author_name', '익명')
            content = row.get('content', '')
            if isinstance(content, str) and content.strip():
                conversation_text += f"[{author}]: {content}\n"

        if not conversation_text.strip():
            await interaction.followup.send("❌ 요약할 만한 텍스트 대화가 존재하지 않습니다.")
            return

        # ✨ 고도화된 고급 프롬프트 작성
        prompt = f"""
당신은 디스코드 커뮤니티 대화 분석 전문 AI입니다.
제공된 대화 내역을 바탕으로 맥락을 정밀 분석하여 보고서를 작성해 주세요.

[대화 원본]
채널명: #{channel.name}
분석 대상 메시지 수: 최근 {len(recent_df)}개
---
{conversation_text}
---

[작성 가이드라인]
다음 4가지 항목으로 나누어 디스코드 마크다운 형식으로 작성하세요.

1. **📌 대화 개요**
   - 대화 전체를 관통하는 핵심 주제를 한 줄로 요약해 주세요.

2. **💡 주요 논의 및 핵심 내용**
   - 오간 대화 중 가장 중요한 이슈, 정보, 질문 및 답변, 결정 사항을 2~4개 불렛포인트로 작성하세요.
   - 단순 대화 나열이 아닌, 결과 및 결론 위주로 서술하세요.

3. **👥 주요 참여자 및 역할**
   - 대화를 주도하거나 중요한 의견/답변을 제시한 인물(`@유저명`)과 그들의 핵심 주장/기여를 간략히 요약하세요.

4. **🔍 분위기 및 맥락 요약**
   - 대화의 분위기(예: 활발함, 문제 해결 중, 잡담, 정보 공유 등)와 특징을 한 줄로 정리하세요.

[주의사항]
- 대화 내용에 없는 사실을 억측하거나 지어내지(할루시네이션) 마세요.
- 가독성이 높도록 불렛포인트와 굵은 글씨(`**text**`)를 적극 활용하세요.
- 디스코드 임베드에 바로 표시되므로 깔끔하고 명확한 톤을 유지하세요.
"""

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            summary_result = response.text

            embed = discord.Embed(
                title=f"🤖 #{channel.name} AI 대화 정밀 리포트",
                description=summary_result,
                color=discord.Color.gold()
            )
            embed.set_footer(text=f"최근 {len(recent_df)}개 메시지 분석 완료 • Powered by Gemini 2.5 Flash")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Gemini API 연동 중 오류가 발생했습니다:\n`{e}`")

async def setup(bot):
    await bot.add_cog(DataSummarizer(bot))