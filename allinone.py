import discord
import os

TOKEN = os.getenv('MARVIN_TOKEN')
SERVER_ID = int(os.getenv('MARVIN_SERVER_ID'))
EMOJI_CHANNEL = int(os.getenv('MARVIN_EMOJI_CHANNEL'))
DEVREPLY_CHANNEL = int(os.getenv('MARVIN_REPLY_CHANNEL'))
MONITOR_CHANNEL = int(os.getenv('MARVIN_MONITOR_CHANNEL'))

EXCLUDE_LIST = ['💩', '🤡', '🖕', '🏳️‍🌈', '🏳️‍⚧️']

GREEN = 5763719
RED = 15548997
BLUE = 3447003

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def get_message_link(p):
    return f'https://discord.com/channels/{p.guild_id}/{p.channel_id}/{p.message_id}'

@bot.event
async def on_ready():
    print('Marvin is ready for duty')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.guild_id == SERVER_ID:
        if payload.emoji.name in EXCLUDE_LIST:
            output_channel = bot.get_channel(EMOJI_CHANNEL)
            message_link = get_message_link(payload)
            user = await bot.fetch_user(payload.user_id)

            embed = discord.Embed(
                colour=GREEN,
                description=f"""
                    {payload.emoji.name} **added** by <@{payload.user_id}> in <#{payload.channel_id}>\n
                    {user.name}#{user.discriminator}\n
                    [Jump to Message]({message_link})
                """.replace(' '*20, '')
            )

            await output_channel.send(embed=embed)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.guild_id == SERVER_ID:
        if payload.emoji.name in EXCLUDE_LIST:
            output_channel = bot.get_channel(EMOJI_CHANNEL)
            message_link = get_message_link(payload)
            user = await bot.fetch_user(payload.user_id)

            embed = discord.Embed(
                colour=RED,
                description=f"""
                    {payload.emoji.name} by <@{payload.user_id}> in <#{payload.channel_id}> **removed**\n
                    {user.name}#{user.discriminator}\n
                    [Jump to Message]({message_link})
                """.replace(' '*20, '')
            )

            await output_channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.channel.type == discord.ChannelType.public_thread and\
        message.channel.parent.type == discord.ChannelType.forum and\
        message.channel.parent.id == MONITOR_CHANNEL:
        if 'snap team' in [y.name.lower() for y in message.author.roles]:
            dev_answer = message.content

            chan = bot.get_channel(MONITOR_CHANNEL)
            thread = chan.get_thread(message.channel.id)
            async for m in thread.history(limit=1, oldest_first=True):
                original_question = m.content

            dev = await bot.fetch_user(message.author.id)
            output_channel = await bot.fetch_channel(DEVREPLY_CHANNEL)
            link = f'https://discord.com/channels/{SERVER_ID}/{message.channel.id}/{message.id}'
            embed = discord.Embed(
                colour=BLUE,
                title='Snap Team Reply',
                description = f'''
                    _Question titled: {message.channel.name}_
                    {original_question}

                    ------

                    _Replied to by <@{dev.id}>:_
                    {dev_answer}

                    [See reply here]({link})
                '''.replace(' '*20, '')
            )

            await output_channel.send(embed=embed)

bot.run(TOKEN)
