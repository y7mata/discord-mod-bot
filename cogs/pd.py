import discord
from discord import app_commands
from discord.ext import commands

PD_ROLE_ID = 1553282110352007168


class PD(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_pd_role(self, guild: discord.Guild) -> discord.Role | None:
        return guild.get_role(PD_ROLE_ID)

    @app_commands.command(name="pd", description="Dá o cargo PD a um membro.")
    @app_commands.describe(membro="Membro que vai receber o cargo PD")
    @app_commands.default_permissions(manage_roles=True)
    async def pd(self, interaction: discord.Interaction, membro: discord.Member):
        role = self._get_pd_role(interaction.guild)
        if not role:
            await interaction.response.send_message("❌ Cargo PD não encontrado.", ephemeral=True)
            return
        if role in membro.roles:
            await interaction.response.send_message(
                f"⚠️ {membro.mention} já tem o cargo {role.mention}.", ephemeral=True
            )
            return
        await membro.add_roles(role)
        await interaction.response.send_message(f"✅ {membro.mention} recebeu {role.mention}.")

    @app_commands.command(name="unpd", description="Remove o cargo PD de um membro.")
    @app_commands.describe(membro="Membro que vai perder o cargo PD")
    @app_commands.default_permissions(manage_roles=True)
    async def unpd(self, interaction: discord.Interaction, membro: discord.Member):
        role = self._get_pd_role(interaction.guild)
        if not role:
            await interaction.response.send_message("❌ Cargo PD não encontrado.", ephemeral=True)
            return
        if role not in membro.roles:
            await interaction.response.send_message(
                f"⚠️ {membro.mention} não tem o cargo {role.mention}.", ephemeral=True
            )
            return
        await membro.remove_roles(role)
        await interaction.response.send_message(f"✅ {role.mention} removido de {membro.mention}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(PD(bot))
