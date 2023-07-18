import discord
import json
import os
import datetime
from discord import app_commands
from discord.ext import tasks
from time import sleep

"""
    J.A.R.V.I.S.
    Just A Rather Very Intelligent System

    A Discord bot for:
        - Auto-pinning forum OPs
        - Logging reaction usage of specified emotes
        - Publicly posting replies to forum threads
            from a specified role
"""

class ConfirmView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.value = None

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Proceeding..', ephemeral=True)
        self.value = True
        await self.on_timeout()
        self.stop()

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Aborting', ephemeral=True)
        self.value = False
        await self.on_timeout()
        self.stop()


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

def load_config():
    global config
    config_file = 'config.json' if env == 'prod' else 'config.test.json'
    with open(config_file, encoding='utf8') as stream:
        config = json.load(stream)
    config = dotdict(config)

env = os.getenv('JARVIS_ENV')
load_config()

GREEN = 5763719
RED = 15548997
BLUE = 3447003

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

### Helper functions
def get_message_link(p):
    return f'https://discord.com/channels/{p.guild_id}/{p.channel_id}/{p.message_id}'

def check_member_age(member):
    now = datetime.datetime.now(datetime.timezone.utc)
    diff = now - member.created_at

    return diff.days > config.new_acct_days

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
    try: await sent.add_reaction(config.plus_emoji)
    except: print('Could not add plus emote')
    try: await sent.publish()
    except: print('Could not Publish message')
    sleep(1)
    try: await sent.add_reaction(config.minus_emoji)
    except: print('Could not add minus emote')

### Tasks
@tasks.loop(seconds=10)
async def check_mute_roles():
    try: server = [g for g in bot.guilds if g.id == config.server][0]
    except: return
    try: role = [r for r in server.roles if r.name == config.new_acct_role][0]
    except: return

    members = [m for m in server.members if role in m.roles]
    if len(members) > 0:
        for member in members:
            if check_member_age(member):
                await member.remove_roles(role)

### Commands
@tree.context_menu(name='Post Dev Reply', guild=discord.Object(id=config.server))
async def dev_reply_command(interaction, message: discord.Message):
    # make sure it's on a forum or the rest won't work
    if not (message.channel.type == discord.ChannelType.public_thread and\
        message.channel.parent.type == discord.ChannelType.forum):
        return

    # check message is from snap team
    guild = bot.get_guild(config.server)
    author = await guild.fetch_member(message.author.id)
    if config.dev_role.lower() not in [y.name.lower() for y in author.roles]:
        return

    # get the channel it's actually posted to
    chan = bot.get_channel(message.channel.parent.id)
    thread = chan.get_thread(message.channel.id)
    async for m in thread.history(limit=1, oldest_first=True):
        thread_open = m.content

    # send prompt to user
    drv = ConfirmView(timeout=10)
    await interaction.response.send_message('Post reply?', embed=discord.Embed(description=message.content), ephemeral=True, view=drv)
    await drv.wait()
    # update buttons to disabled when finished
    await interaction.edit_original_response(view=drv)
    if drv.value:
        # yes was picked, post
        await send_devreply_embed(message, thread_open)

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
    if config.dev_role.lower() not in [y.name.lower() for y in author.roles]:
        return

    # get the channel it's actually posted to
    chan = bot.get_channel(message.channel.parent.id)
    thread = chan.get_thread(message.channel.id)
    async for m in thread.history(limit=1, oldest_first=True):
        thread_open = m.content

    # send prompt to user
    drv = ConfirmView(timeout=10)
    await interaction.response.send_message('Post reply?', embed=discord.Embed(description=message.content), ephemeral=True, view=drv)
    await drv.wait()
    # update buttons to disabled when finished
    await interaction.edit_original_response(view=drv)
    if drv.value:
        # yes was picked, post
        await send_devreply_embed(message, thread_open)

### Events
@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=config.server))
    check_mute_roles.start()
    print(f"{config.env.upper()} JARVIS is ready for duty")

@bot.event
async def on_member_join(member):
    if not check_member_age(member):
        try: server = [g for g in bot.guilds if g.id == config.server][0]
        except: return
        try: role = [r for r in server.roles if r.name == config.new_acct_role][0]
        except: return

        await member.add_roles(role)

@bot.event
async def on_raw_reaction_add(payload):
    # checks
    if payload.guild_id != config.server:
        return
    if payload.emoji.name in config.monitor_emoji:
        # monitor logic
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

    if payload.emoji.name in config.remove_emoji:
        # auto remove logic
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = await bot.fetch_user(payload.user_id)
        await message.remove_reaction(payload.emoji.name, user)

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

    # snap team reply logic
    if config.dev_role.lower() in [y.name.lower() for y in message.author.roles]:
        chan = bot.get_channel(config.monitor_channel)
        thread = chan.get_thread(message.channel.id)
        async for m in thread.history(limit=1, oldest_first=True):
            thread_open = m.content

        await send_devreply_embed(message, thread_open)

        for tag in chan.available_tags:
            if 'team response' in tag.name.lower():
                answered = tag
        try: await thread.add_tags(answered)
        except: print('Could not add answered tag')

    if config.mod_role in [y.name.lower() for y in message.author.roles]:
        chan = bot.get_channel(config.monitor_channel)
        thread = chan.get_thread(message.channel.id)
        for tag in chan.available_tags:
            if 'moderator reply' in tag.name.lower():
                answered = tag
        try: await thread.add_tags(answered)
        except: print('Could not add answered tag')

@bot.event
async def on_thread_create(thread):
    if thread.parent.type != discord.ChannelType.forum:
        return
    if thread.parent.id in config.auto_pin_channels:
        async for message in thread.history(limit=1, oldest_first=True):
            await message.pin()
    if thread.parent.id in config.auto_react_channels:
        async for message in thread.history(limit=1, oldest_first=True):
            for emoji in config.auto_react_emoji:
                await message.add_reaction(emoji)
                sleep(0.5)

bot.run(config.token)
