import discord
import os
from discord import app_commands

TOKEN = os.getenv('MARVIN_TOKEN')
SERVER_ID = int(os.getenv('MARVIN_SERVER_ID'))
EMOJI_CHANNEL = int(os.getenv('MARVIN_EMOJI_CHANNEL'))
DEVREPLY_CHANNEL = int(os.getenv('MARVIN_REPLY_CHANNEL'))
MONITOR_CHANNEL = int(os.getenv('MARVIN_MONITOR_CHANNEL'))

UPVOTE_EMOJI = os.getenv('MARVIN_UPVOTE_EMOJI')
DOWNVOTE_EMOJI = os.getenv('MARVIN_DOWNVOTE_EMOJI')

EXCLUDE_LIST = ['💩', '🤡', '🖕', '🏳️‍🌈', '🏳️‍⚧️', '🤮']

GREEN = 5763719
RED = 15548997
BLUE = 3447003

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

def get_message_link(p):
    return f'https://discord.com/channels/{p.guild_id}/{p.channel_id}/{p.message_id}'

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=SERVER_ID))
    print('Marvin is ready for duty')

@tree.command(name='post_dev_reply', description='Paste the link to the actual dev reply message', guild=discord.Object(id=SERVER_ID))
async def first_command(interaction, message_link: str):
    msg_list = message_link.split('/')
    msg_list.reverse()
    message_id = msg_list[0]
    thread_id = msg_list[1]
    server_id = msg_list[2]

    if int(server_id) == SERVER_ID:
        thread = await bot.fetch_channel(thread_id)
        message = await thread.fetch_message(message_id)
        await interaction.response.send_message('Posting reply', embed=discord.Embed(description=message.content))
        await on_message(message)

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
        guild = bot.get_guild(SERVER_ID)
        author = await guild.fetch_member(message.author.id)
        if 'snap team' in [y.name.lower() for y in author.roles]:
            dev_answer = message.content

            chan = bot.get_channel(MONITOR_CHANNEL)
            thread = chan.get_thread(message.channel.id)
            async for m in thread.history(limit=1, oldest_first=True):
                original_question = m.content

            output_channel = await bot.fetch_channel(DEVREPLY_CHANNEL)
            link = f'https://discord.com/channels/{SERVER_ID}/{message.channel.id}/{message.id}'
            embed = discord.Embed(
                colour=BLUE,
                title=message.channel.name,
                description = f'''
                    {original_question}

                    ------

                    ***Replied to by <@{message.author.id}>:***
                    {dev_answer}

                    [See reply here]({link})'''.replace(' '*20, '')
            )

            embed.set_thumbnail(url=message.author.display_avatar.url)
            sent = await output_channel.send(embed=embed)
            await sent.add_reaction(UPVOTE_EMOJI)
            await sent.add_reaction(DOWNVOTE_EMOJI)

            for tag in chan.available_tags:
                if 'answered' in tag.name.lower():
                    answered = tag

            await thread.add_tags(answered)

bot.run(TOKEN)
