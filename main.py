import os
import asyncio
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

initial_extensions = [
    "cogs.collector",
    "cogs.analyzer",
    "cogs.visualizer",
    "cogs.summarizer",
    "cogs.help",
    "cogs.auto_collector"
]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

async def main():
    async with bot:
        for extension in initial_extensions:
            try:
                await bot.load_extension(extension)
                print(f"Loaded extension '{extension}'")
            except Exception as e:
                print(f"Failed to load extension {extension}: {e}")
        
        # BOT TOKEN 환경 변수 혹은 문자열 입력
        token = os.getenv("DISCORD_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())