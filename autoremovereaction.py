import discord
import os

TOKEN = os.getenv('MARVIN_TOKEN')
SERVER_ID = int(os.getenv('MARVIN_SERVER_ID'))
CHANNEL_ID = int(os.getenv('MARVIN_CHANNEL_ID'))

EXCLUDE_LIST = ['🖕', '💩', '🤡']

client = discord.Client()

@client.event
async def on_ready():
    print('Reaction Remover Bot is ready for duty')
    print('Will auto remove the following reactions:')
    print('    ' + ', '.join(EXCLUDE_LIST))

@client.event
async def on_raw_reaction_add(payload):
    if payload.guild_id == SERVER_ID:
        if payload.emoji.name in EXCLUDE_LIST:
            channel = client.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            user = client.get_user(payload.user_id)
            await message.remove_reaction(payload.emoji.name, user)
