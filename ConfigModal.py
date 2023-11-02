import discord
from discord import ui

class ConfigModal(ui.Modal, title="ReactionRole Config"):
    reaction = ui.TextInput(label='Emoji to Check')
    role = ui.TextInput(label='Role to Add')
    def __init__(self, reaction, role):
        super().__init__()
        self.reaction.default = reaction
        self.role.default = role

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'''
            Setting new config values:
            Emoji: {self.reaction.value}
            Role: {self.role.value}
        '''.replace(' '*12, '').strip(), ephemeral=True)
