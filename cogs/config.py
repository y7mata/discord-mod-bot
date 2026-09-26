import discord
from discord import app_commands
from discord.ext import commands
import database


class Config(commands.Cog):
    cfg_group = app_commands.Group(name="config", description="Configurações do bot no servidor.")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cfg_group.command(name="logs", description="Define o canal de logs de moderação.")
    @app_commands.describe(canal="Canal onde os logs serão enviados")
    @app_commands.default_permissions(administrator=True)
    async def cfg_logs(self, interaction: discord.Interaction, canal: discord.TextChannel):
        await database.set_config(interaction.guild.id, log_channel=canal.id)
        await interaction.response.send_message(f"✅ Canal de logs: {canal.mention}", ephemeral=True)

    @cfg_group.command(name="autorole", description="Define o cargo automático para novos membros.")
    @app_commands.describe(cargo="Cargo dado automaticamente ao entrar")
    @app_commands.default_permissions(administrator=True)
    async def cfg_autorole(self, interaction: discord.Interaction, cargo: discord.Role):
        await database.set_config(interaction.guild.id, auto_role=cargo.id)
        await interaction.response.send_message(f"✅ Auto-role: {cargo.mention}", ephemeral=True)

    @cfg_group.command(name="ver", description="Mostra a configuração atual do servidor.")
    @app_commands.default_permissions(administrator=True)
    async def cfg_ver(self, interaction: discord.Interaction):
        cfg = await database.get_config(interaction.guild.id)
        log_ch = (
            interaction.guild.get_channel(cfg["log_channel"]).mention
            if cfg.get("log_channel") else "Não configurado"
        )
        auto_role = (
            interaction.guild.get_role(cfg["auto_role"]).mention
            if cfg.get("auto_role") else "Não configurado"
        )
        embed = discord.Embed(title="⚙️ Configuração do Servidor", color=discord.Color.blurple())
        pd_role = (
            interaction.guild.get_role(cfg["pd_role"]).mention
            if cfg.get("pd_role") else "Não configurado"
        )
        embed.add_field(name="Canal de Logs", value=log_ch, inline=False)
        embed.add_field(name="Auto-role",     value=auto_role, inline=False)
        embed.add_field(name="Cargo PD",      value=pd_role, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @cfg_group.command(name="pd", description="Define o cargo PD usado em /pd dar e /pd tirar.")
    @app_commands.describe(cargo="Cargo PD")
    @app_commands.default_permissions(administrator=True)
    async def cfg_pd(self, interaction: discord.Interaction, cargo: discord.Role):
        await database.set_config(interaction.guild.id, pd_role=cargo.id)
        await interaction.response.send_message(f"✅ Cargo PD definido: {cargo.mention}", ephemeral=True)

    @cfg_group.command(name="reset", description="Reseta toda a configuração do servidor.")
    @app_commands.default_permissions(administrator=True)
    async def cfg_reset(self, interaction: discord.Interaction):
        await database.set_config(interaction.guild.id, log_channel=None, auto_role=None)
        await interaction.response.send_message("✅ Configuração resetada.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Config(bot))
