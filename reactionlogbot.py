import discord
import os

TOKEN = os.getenv('BOT_TOKEN')
SERVER_ID = int(os.getenv('BOT_SERVER_ID'))
CHANNEL_ID = int(os.getenv('BOT_CHANNEL_ID'))

EXCLUDE_LIST = ['🖕', '💩', '🤡']

client = discord.Client()

def get_message_link(p):
    return f'https://discord.com/channels/{p.guild_id}/{p.channel_id}/{p.message_id}'

async def make_embed(action, payload):
    color = 5763719 if action == 'added' else 15548997
    message_link = get_message_link(payload)
    user = await client.fetch_user(payload.user_id)

    return discord.Embed(
        description='''
            {} **{}** in <#{}> by <@{}>

            {}#{}

            [Jump to message]({})
        '''.format(
            payload.emoji.name,
            action,
            payload.channel_id,
            payload.user_id,
            user.name,
            user.discriminator,
            message_link
        ).replace('            ', ''),
        colour=color
    )


@client.event
async def on_ready():
    print('Test bot is ready to go baby')

### logging code
@client.event
async def on_raw_reaction_add(payload):
    if payload.guild_id == SERVER_ID:
        if payload.emoji.name in EXCLUDE_LIST:
            output_channel = client.get_channel(CHANNEL_ID)
            embed = await make_embed('added', payload)

            await output_channel.send(embed=embed)

@client.event
async def on_raw_reaction_remove(payload):
    if payload.guild_id == SERVER_ID:
        if payload.emoji.name in EXCLUDE_LIST:
            output_channel = client.get_channel(CHANNEL_ID)
            embed = await make_embed('removed', payload)

            await output_channel.send(embed=embed)


### auto-remove code
# @client.event
# async def on_raw_reaction_add(payload):
#     if payload.guild_id == SERVER_ID:
#         if payload.emoji.name in EXCLUDE_LIST:
#             channel = client.get_channel(payload.channel_id)
#             message = await channel.fetch_message(payload.message_id)
#             user = client.get_user(payload.user_id)
#             await message.remove_reaction(payload.emoji.name, user)

client.run(TOKEN)
