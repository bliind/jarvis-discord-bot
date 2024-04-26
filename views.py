import discord
import jarvisdb

class QuizButton(discord.ui.Button):
    def __init__(self, label, value):
        self.value = value
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        response = await self.view.record_answer(interaction.message.id, interaction.user.id, self.value)
        await interaction.response.send_message(content=response, ephemeral=True)

class QuizView(discord.ui.View):
    def __init__(self, interaction, quiz_options, timeout=None):
        super().__init__(timeout=timeout)
        self.interaction = interaction

        for idx, option in enumerate(quiz_options):
            self.add_item(QuizButton(idx+1, option))

    async def on_timeout(self) -> None:
        # disable voting buttons on timeout
        for child in self.children:
            child.disabled = True
        await self.interaction.edit_original_response(view=self)
        return await super().on_timeout()

    async def record_answer(self, message_id, user_id, value):
        answered = await jarvisdb.check_quiz_answered(message_id, user_id)
        if answered:
            return f'You have already answered this quiz.\nYou answered: {answered["answer"]}'

        saved_vote = await jarvisdb.record_quiz_answer(message_id, user_id, value)
        if saved_vote:
            return f'You have answered {value}! Please wait for the quiz to end to see the results!'
        else:
            return 'Error recording your answer, please try again!'

