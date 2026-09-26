import asyncio
import os
import discord
from discord.ext import commands
import database

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


GUILD_ID = discord.Object(id=1550666309388210256)

@bot.event
async def on_ready():
    await database.init_db()
    print(f"Online como {bot.user} ({bot.user.id})")
    try:
        bot.tree.copy_global_to(guild=GUILD_ID)
        synced = await bot.tree.sync(guild=GUILD_ID)
        print(f"Slash commands sincronizados no servidor: {len(synced)}")
    except Exception as e:
        print(f"Erro ao sincronizar: {e}")


async def load_cogs():
    for cog in ("cogs.moderation", "cogs.roles", "cogs.config", "cogs.pd"):
        await bot.load_extension(cog)
        print(f"Cog carregada: {cog}")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


asyncio.run(main())
