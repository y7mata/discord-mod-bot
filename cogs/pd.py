import discord
from discord import app_commands
from discord.ext import commands
import database


class PD(commands.Cog):
    pd_group = app_commands.Group(name="pd", description="Gerencia o cargo PD.")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _get_pd_role(self, guild: discord.Guild) -> discord.Role | None:
        cfg = await database.get_config(guild.id)
        role_id = cfg.get("pd_role")
        if not role_id:
            return None
        return guild.get_role(role_id)

    @pd_group.command(name="dar", description="Dá o cargo PD a um membro.")
    @app_commands.describe(membro="Membro que vai receber o cargo PD")
    @app_commands.default_permissions(manage_roles=True)
    async def pd_dar(self, interaction: discord.Interaction, membro: discord.Member):
        role = await self._get_pd_role(interaction.guild)
        if not role:
            await interaction.response.send_message(
                "❌ Cargo PD não configurado. Use `/config pd` primeiro.", ephemeral=True
            )
            return
        if role in membro.roles:
            await interaction.response.send_message(
                f"⚠️ {membro.mention} já tem o cargo {role.mention}.", ephemeral=True
            )
            return
        await membro.add_roles(role)
        await interaction.response.send_message(
            f"✅ Cargo {role.mention} adicionado a {membro.mention}."
        )

    @pd_group.command(name="tirar", description="Tira o cargo PD de um membro.")
    @app_commands.describe(membro="Membro que vai perder o cargo PD")
    @app_commands.default_permissions(manage_roles=True)
    async def pd_tirar(self, interaction: discord.Interaction, membro: discord.Member):
        role = await self._get_pd_role(interaction.guild)
        if not role:
            await interaction.response.send_message(
                "❌ Cargo PD não configurado. Use `/config pd` primeiro.", ephemeral=True
            )
            return
        if role not in membro.roles:
            await interaction.response.send_message(
                f"⚠️ {membro.mention} não tem o cargo {role.mention}.", ephemeral=True
            )
            return
        await membro.remove_roles(role)
        await interaction.response.send_message(
            f"✅ Cargo {role.mention} removido de {membro.mention}."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(PD(bot))
