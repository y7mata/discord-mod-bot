import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
import database


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _log(self, guild: discord.Guild, embed: discord.Embed):
        cfg = await database.get_config(guild.id)
        ch_id = cfg.get("log_channel")
        if ch_id:
            ch = guild.get_channel(ch_id)
            if ch:
                await ch.send(embed=embed)

    def _embed(
        self,
        action: str,
        mod: discord.Member,
        target: discord.Member | discord.User,
        reason: str,
        color: discord.Color = discord.Color.orange(),
        extra: str = "",
    ) -> discord.Embed:
        e = discord.Embed(
            title=f"🔨 {action}",
            color=color,
            timestamp=datetime.now(timezone.utc),
        )
        e.add_field(name="Alvo", value=f"{target} (`{target.id}`)", inline=False)
        e.add_field(name="Moderador", value=f"{mod} (`{mod.id}`)", inline=False)
        e.add_field(name="Motivo", value=reason or "Não informado", inline=False)
        if extra:
            e.add_field(name="Info", value=extra, inline=False)
        return e

    @app_commands.command(name="kick", description="Expulsa um membro do servidor.")
    @app_commands.describe(membro="Quem expulsar", motivo="Motivo (opcional)")
    @app_commands.default_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: str = "Não informado",
    ):
        await membro.kick(reason=f"{interaction.user}: {motivo}")
        embed = self._embed("Kick", interaction.user, membro, motivo, discord.Color.yellow())
        await interaction.response.send_message(embed=embed)
        await self._log(interaction.guild, embed)

    @app_commands.command(name="ban", description="Bane um membro do servidor.")
    @app_commands.describe(
        membro="Quem banir",
        motivo="Motivo (opcional)",
        deletar_msgs="Dias de mensagens para deletar (0-7)",
    )
    @app_commands.default_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: str = "Não informado",
        deletar_msgs: app_commands.Range[int, 0, 7] = 0,
    ):
        await membro.ban(reason=f"{interaction.user}: {motivo}", delete_message_days=deletar_msgs)
        embed = self._embed("Ban", interaction.user, membro, motivo, discord.Color.red())
        await interaction.response.send_message(embed=embed)
        await self._log(interaction.guild, embed)

    @app_commands.command(name="unban", description="Remove o ban de um usuário pelo ID.")
    @app_commands.describe(user_id="ID do usuário banido", motivo="Motivo (opcional)")
    @app_commands.default_permissions(ban_members=True)
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
        motivo: str = "Não informado",
    ):
        await interaction.response.defer()
        try:
            uid = int(user_id)
        except ValueError:
            await interaction.followup.send("❌ ID inválido.", ephemeral=True)
            return
        try:
            user = await self.bot.fetch_user(uid)
            await interaction.guild.unban(user, reason=f"{interaction.user}: {motivo}")
        except discord.NotFound:
            await interaction.followup.send("❌ Usuário não encontrado ou não está banido.", ephemeral=True)
            return
        embed = self._embed("Unban", interaction.user, user, motivo, discord.Color.green())
        await interaction.followup.send(embed=embed)
        await self._log(interaction.guild, embed)

    @app_commands.command(name="timeout", description="Aplica timeout (silêncio) a um membro.")
    @app_commands.describe(
        membro="Quem silenciar",
        minutos="Duração em minutos (1-40320)",
        motivo="Motivo (opcional)",
    )
    @app_commands.default_permissions(moderate_members=True)
    async def timeout(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        minutos: app_commands.Range[int, 1, 40320],
        motivo: str = "Não informado",
    ):
        from datetime import timedelta
        await membro.timeout(timedelta(minutes=minutos), reason=f"{interaction.user}: {motivo}")
        embed = self._embed(
            "Timeout", interaction.user, membro, motivo,
            discord.Color.orange(), extra=f"{minutos} minuto(s)",
        )
        await interaction.response.send_message(embed=embed)
        await self._log(interaction.guild, embed)

    @app_commands.command(name="clear", description="Apaga mensagens do canal.")
    @app_commands.describe(
        quantidade="Número de mensagens (1-100)",
        membro="Filtrar por membro (opcional)",
    )
    @app_commands.default_permissions(manage_messages=True)
    async def clear(
        self,
        interaction: discord.Interaction,
        quantidade: app_commands.Range[int, 1, 100],
        membro: discord.Member | None = None,
    ):
        await interaction.response.defer(ephemeral=True)

        def check(m: discord.Message):
            return membro is None or m.author == membro

        deleted = await interaction.channel.purge(limit=quantidade, check=check)
        suffix = f" de {membro.mention}" if membro else ""
        await interaction.followup.send(f"🗑️ {len(deleted)} mensagem(ns) apagada(s){suffix}.", ephemeral=True)

        embed = discord.Embed(title="🗑️ Clear", color=discord.Color.blurple(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Canal", value=interaction.channel.mention)
        embed.add_field(name="Quantidade", value=str(len(deleted)))
        embed.add_field(name="Moderador", value=str(interaction.user))
        if membro:
            embed.add_field(name="Filtro", value=str(membro))
        await self._log(interaction.guild, embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
