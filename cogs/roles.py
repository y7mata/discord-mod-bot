import discord
from discord import app_commands
from discord.ext import commands
import database


class RoleButton(discord.ui.Button):
    def __init__(self, role_id: int, label: str, emoji: str | None, style: discord.ButtonStyle):
        super().__init__(label=label, emoji=emoji, style=style, custom_id=f"role:{role_id}")
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ Cargo não encontrado.", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"✅ Cargo **{role.name}** removido.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Cargo **{role.name}** adicionado.", ephemeral=True)


class RoleView(discord.ui.View):
    def __init__(self, roles: list[dict]):
        super().__init__(timeout=None)
        style_map = {
            "primary":   discord.ButtonStyle.primary,
            "secondary": discord.ButtonStyle.secondary,
            "success":   discord.ButtonStyle.success,
            "danger":    discord.ButtonStyle.danger,
        }
        for r in roles:
            style = style_map.get(r.get("style", "primary"), discord.ButtonStyle.primary)
            self.add_item(RoleButton(r["role_id"], r["label"], r.get("emoji"), style))


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        for guild in self.bot.guilds:
            rows = await database.get_button_roles(guild.id)
            msgs: dict[int, list[dict]] = {}
            for r in rows:
                mid = r.get("message_id")
                if mid:
                    msgs.setdefault(mid, []).append(r)
            for mid, role_rows in msgs.items():
                self.bot.add_view(RoleView(role_rows), message_id=mid)

    # ── /cargo ────────────────────────────────────────────────────────────────

    cargo_group = app_commands.Group(name="cargo", description="Gerencia cargos de membros.")

    @cargo_group.command(name="dar", description="Dá um cargo a um membro.")
    @app_commands.describe(membro="Membro alvo", cargo="Cargo a dar")
    @app_commands.default_permissions(manage_roles=True)
    async def cargo_dar(self, interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
        if cargo in membro.roles:
            await interaction.response.send_message(f"⚠️ {membro.mention} já tem {cargo.mention}.", ephemeral=True)
            return
        await membro.add_roles(cargo)
        await interaction.response.send_message(f"✅ Cargo {cargo.mention} adicionado a {membro.mention}.")

    @cargo_group.command(name="tirar", description="Tira um cargo de um membro.")
    @app_commands.describe(membro="Membro alvo", cargo="Cargo a remover")
    @app_commands.default_permissions(manage_roles=True)
    async def cargo_tirar(self, interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role):
        if cargo not in membro.roles:
            await interaction.response.send_message(f"⚠️ {membro.mention} não tem {cargo.mention}.", ephemeral=True)
            return
        await membro.remove_roles(cargo)
        await interaction.response.send_message(f"✅ Cargo {cargo.mention} removido de {membro.mention}.")

    # ── /buttonrole ───────────────────────────────────────────────────────────

    br_group = app_commands.Group(name="buttonrole", description="Painel de button roles.")

    @br_group.command(name="criar", description="Cria um botão para membros pegarem cargo.")
    @app_commands.describe(
        cargo="Cargo que o botão vai dar/tirar",
        label="Texto no botão",
        emoji="Emoji (opcional)",
        estilo="Cor do botão",
    )
    @app_commands.choices(estilo=[
        app_commands.Choice(name="Azul (primary)",      value="primary"),
        app_commands.Choice(name="Cinza (secondary)",   value="secondary"),
        app_commands.Choice(name="Verde (success)",     value="success"),
        app_commands.Choice(name="Vermelho (danger)",   value="danger"),
    ])
    @app_commands.default_permissions(manage_roles=True)
    async def br_criar(
        self,
        interaction: discord.Interaction,
        cargo: discord.Role,
        label: str,
        emoji: str | None = None,
        estilo: str = "primary",
    ):
        row_id = await database.add_button_role(interaction.guild.id, cargo.id, label, emoji, estilo)
        rows = await database.get_button_roles(interaction.guild.id)
        view = RoleView(rows)
        embed = discord.Embed(
            title="🎭 Painel de Cargos",
            description="Clique num botão para obter ou remover um cargo.",
            color=discord.Color.blurple(),
        )
        msg = await interaction.channel.send(embed=embed, view=view)
        await database.set_button_role_message(row_id, msg.id)
        self.bot.add_view(view, message_id=msg.id)
        await interaction.response.send_message(f"✅ Botão criado para {cargo.mention}.", ephemeral=True)

    @br_group.command(name="remover", description="Remove um button role pelo ID.")
    @app_commands.describe(id="ID do botão (veja /buttonrole listar)")
    @app_commands.default_permissions(manage_roles=True)
    async def br_remover(self, interaction: discord.Interaction, id: int):
        await database.remove_button_role(id)
        await interaction.response.send_message(f"✅ Button role `{id}` removido.", ephemeral=True)

    @br_group.command(name="listar", description="Lista os button roles do servidor.")
    @app_commands.default_permissions(manage_roles=True)
    async def br_listar(self, interaction: discord.Interaction):
        rows = await database.get_button_roles(interaction.guild.id)
        if not rows:
            await interaction.response.send_message("Nenhum button role configurado.", ephemeral=True)
            return
        lines = [f"`{r['id']}` — <@&{r['role_id']}> — **{r['label']}**" for r in rows]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    # ── auto-role ──────────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        cfg = await database.get_config(member.guild.id)
        role_id = cfg.get("auto_role")
        if not role_id:
            return
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role, reason="Auto-role")
            except discord.Forbidden:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
