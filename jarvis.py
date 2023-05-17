import discord
import json
import os
from discord import app_commands

"""
    J.A.R.V.I.S.
    Just A Rather Very Intelligent System

    A Discord bot for:
        - Auto-pinning forum OPs
        - Logging reaction usage of specified emotes
        - Publicly posting replies to forum threads
            from a specified role
"""

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

env = os.getenv('JARVIS_ENV')
config_file = 'config.json' if env == 'prod' else 'config.test.json'
with open(config_file, encoding='utf8') as stream:
    config = json.load(stream)
config = dotdict(config)

GREEN = 5763719
RED = 15548997
BLUE = 3447003

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

### Helper functions

def get_message_link(p):
    return f'https://discord.com/channels/{p.guild_id}/{p.channel_id}/{p.message_id}'

async def send_devreply_embed(message, thread_open):
    output_channel = await bot.fetch_channel(config.reply_channel)
    link = f"https://discord.com/channels/{config.server}/{message.channel.id}/{message.id}"
    embed = discord.Embed(
        colour=BLUE,
        title=message.channel.name,
        description = f'''
            {thread_open}

            ------

            ***Replied to by <@{message.author.id}>:***
            {message.content}

            [See reply here]({link})'''.replace(' '*12, '')
    )

    embed.set_thumbnail(url=message.author.display_avatar.url)
    sent = await output_channel.send(embed=embed)
    await sent.add_reaction(config.upvote_emoji)
    await sent.add_reaction(config.downvote_emoji)
    await sent.publish()

### Commands

@tree.command(name='post_dev_reply', description='Paste the link to the actual dev reply message', guild=discord.Object(id=config.server))
async def first_command(interaction, message_link: str):
    try:
        msg_list = message_link.split('/')
        msg_list.reverse()
        message_id = int(msg_list[0])
        thread_id = int(msg_list[1])
        server_id = int(msg_list[2])
    except:
        print(f'Could not parse link: {message_link}')
        await interaction.response.send_message(f'Could not parse link: {message_link}')
        return

    # check the message link is actually on the server
    if server_id != config.server:
        return

    # fetch the message
    thread = await bot.fetch_channel(thread_id)
    message = await thread.fetch_message(message_id)

    # make sure it's on a forum or the rest won't work
    if not (message.channel.type == discord.ChannelType.public_thread and\
        message.channel.parent.type == discord.ChannelType.forum):
        return

    # check message is from snap team
    guild = bot.get_guild(config.server)
    author = await guild.fetch_member(message.author.id)
    if config.role_check.lower() not in [y.name.lower() for y in author.roles]:
        return

    # get the channel it's actually posted to
    chan = bot.get_channel(message.channel.parent.id)
    thread = chan.get_thread(message.channel.id)
    async for m in thread.history(limit=1, oldest_first=True):
        thread_open = m.content

    # send reply to user, send embed
    await interaction.response.send_message('Posting reply', embed=discord.Embed(description=message.content))
    await send_devreply_embed(message, thread_open)

### Events

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=config.server))
    print(f"{config.env.upper()} JARVIS is ready for duty")

@bot.event
async def on_raw_reaction_add(payload):
    # checks
    if payload.guild_id != config.server:
        return
    if payload.emoji.name not in config.monitor_emoji:
        return

    # logic
    output_channel = bot.get_channel(config.emoji_channel)
    message_link = get_message_link(payload)
    user = await bot.fetch_user(payload.user_id)

    embed = discord.Embed(
        colour=GREEN,
        description=f"""
            {payload.emoji.name} **added** by <@{payload.user_id}> in <#{payload.channel_id}>\n
            {user.name}#{user.discriminator}\n
            [Jump to Message]({message_link})
        """.replace(' '*12, '')
    )

    await output_channel.send(embed=embed)

@bot.event
async def on_raw_reaction_remove(payload):
    # checks
    if payload.guild_id != config.server:
        return
    if payload.emoji.name not in config.monitor_emoji:
        return

    # logic
    output_channel = bot.get_channel(config.emoji_channel)
    message_link = get_message_link(payload)
    user = await bot.fetch_user(payload.user_id)

    embed = discord.Embed(
        colour=RED,
        description=f"""
            {payload.emoji.name} by <@{payload.user_id}> in <#{payload.channel_id}> **removed**\n
            {user.name}#{user.discriminator}\n
            [Jump to Message]({message_link})
        """.replace(' '*12, '')
    )

    await output_channel.send(embed=embed)

@bot.event
async def on_message(message):
    # checks
    if message.channel.type != discord.ChannelType.public_thread:
        return
    if message.channel.parent.type != discord.ChannelType.forum:
        return
    if message.channel.parent.id != config.monitor_channel:
        return
    if config.role_check.lower() not in [y.name.lower() for y in message.author.roles]:
        return

    # logic
    chan = bot.get_channel(config.monitor_channel)
    thread = chan.get_thread(message.channel.id)
    async for m in thread.history(limit=1, oldest_first=True):
        thread_open = m.content

    await send_devreply_embed(message, thread_open)

    for tag in chan.available_tags:
        if 'answered' in tag.name.lower():
            answered = tag
        if 'question' in tag.name.lower():
            question = tag

    try: await thread.add_tags(answered)
    except: print('Could not add answered tag')
    try: await thread.remove_tags(question)
    except: print('Could not remove question tag')

@bot.event
async def on_thread_create(thread):
    if thread.parent.type != discord.ChannelType.forum:
        return
    if thread.parent.id not in config.auto_pin_channels:
        return

    async for message in thread.history(limit=1, oldest_first=True):
        await message.pin()

bot.run(config.token)
