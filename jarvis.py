import discord
import json
import os
import re
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
        - Auto removing specified emote reactions
        - Auto reacting with specified emotes
        - Publicly posting replies to forum threads
            from a specified role
        - Managing a "new account" role for accounts
            under 14 days old
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

    return diff.days >= config.new_acct_days

def check_server_age(member):
    now = datetime.datetime.now(datetime.timezone.utc)
    diff = now - member.joined_at

    return (diff.total_seconds() / 3600) >= config.member_hours

def check_is_dev(member):
    for dev_role in config.dev_role:
        if dev_role.lower() in [y.name.lower() for y in member.roles]:
            return True
    return False

def check_is_mod(member):
    for mod_role in config.mod_role:
        if mod_role.lower() in [y.name.lower() for y in member.roles]:
            return True
    return False

async def create_devreply_embed(message, thread_open):
    link = f"https://discord.com/channels/{config.server}/{message.channel.id}/{message.id}"
    embed = discord.Embed(
        colour=BLUE,
        title=message.channel.name,
        description = f'''
            {thread_open}

            ------

            ***Replied to by <@{message.author.id}>:***
            {message.content}

            [See reply here]({link})'''.replace(' '*12, '').strip()
    )

    embed.set_thumbnail(url=message.author.display_avatar.url)

    return embed

async def send_devreply_embed(message, thread_open):
    output_channel = await bot.fetch_channel(config.reply_channel)
    embed = await create_devreply_embed(message, thread_open)
    sent = await output_channel.send(embed=embed)
    try: await sent.add_reaction(config.plus_emoji)
    except: print('Could not add plus emote')
    try: await sent.publish()
    except: print('Could not Publish message')
    sleep(1)
    try: await sent.add_reaction(config.minus_emoji)
    except: print('Could not add minus emote')

async def check_caps_percent(message):
    try:
        author_roles = [y.name.lower() for y in message.author.roles]
        for role in config.caps_prot_exclude_roles:
            if role in author_roles:
                return
        if message.channel.id in config.caps_prot_exclude_channels:
            return

        # remove emotes
        content = re.sub(r':[\w\d]+:', '', message.content)

        alph = list(filter(str.isalpha, content))
        if len(alph) >= 4:
            percent = (sum(map(str.isupper, alph)) / len(alph) * 100)
            if percent >= config.caps_prot_percent:
                sent = await message.reply(config.caps_prot_message)
                await message.delete()
                sleep(5)
                await sent.delete()
    except AttributeError:
        pass

### Tasks
@tasks.loop(seconds=3600)
async def check_mute_roles():
    print('Checking New Account roles')
    try: server = [g for g in bot.guilds if g.id == config.server][0]
    except:
        print('Not on the right server?')
        return
    try: role = [r for r in server.roles if r.name.lower() == config.new_acct_role.lower()][0]
    except:
        print('New Account Role not found')
        return

    members = [m for m in server.members if role in m.roles]
    if len(members) > 0:
        for member in members:
            if check_member_age(member):
                await member.remove_roles(role)
    print('Done!')

@tasks.loop(seconds=3600)
async def check_member_roles():
    print('Checking Member roles')
    try: server = [g for g in bot.guilds if g.id == config.server][0]
    except:
        print('Not on the right server?')
        return
    try: role = [r for r in server.roles if r.name.lower() == config.member_role.lower()][0]
    except:
        print('Member Role not found')
        return
    try: new_acct_role = [r for r in server.roles if r.name.lower() == config.new_acct_role.lower()][0]
    except:
        print('New Account Role not found')
        return

    members = [m for m in server.members if role not in m.roles]
    if len(members) > 0:
        for member in members:
            if check_server_age(member):
                if new_acct_role not in member.roles:
                    await member.add_roles(role)
    print('Done!')

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
    if not check_is_dev(author):
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
    if not check_is_dev(author):
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

@tree.command(name='askdevs', description='Post the ask-the-team guidelines', guild=discord.Object(id=config.server))
async def askdevs_command(interaction):
    embed = discord.Embed(
        colour=discord.Color.yellow(),
        description = f'''
            We have the right to remove any post we deem is not fit for this forum
            Please read the pinned FAQ post before asking your question. 

            _1:_ No "Leading" or "Suggestive" questions. Post your question, don't try to get the answer you want.
            _2:_ Feedback, suggestions and bug reports should be posted in their respective channels. * <#1067974227816366150>, <#1020474756543303690> and <#1020475179085865000>
            _3:_ Board State posts, "Is this a bug" posts, "why did this happen?" posts, and questions that can be answered by anyone in another channel are not allowed
            _4:_ Repost Questions will be removed if there is a currently unlocked post with the same question
            _5:_ If your post was Closed & Locked, it means it violated one of our guide lines.
            _6:_ No "When is X happening" The developers will announce when things will go live, not in the Q&A forum.
            _7:_ No questions about matchmaking.
        '''.replace(' '*12, '').strip()
    )

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message('Done', ephemeral=True)

@tree.command(name='series', description='Explain the Card Series', guild=discord.Object(id=config.server))
async def series_command(interaction: discord.Interaction, ping: discord.User = None):
    message=f'''
        {ping.mention if ping else ''}
        The card Series (Pools) are the groupings that cards are in. You can only open cards on the collection track from a given Series once you hit the collection level (CL) necessary to unlock them. You can find your collection level underneath your avatar on the Home Screen in the green bar (mobile) or on the top navigation bar titled "Level" (PC).
        - Series 1 - CL 18-214
        - Series 2 - CL 222-474
        - Series 3 - CL 486+
        - Series 4/5 - CL 610+ (Spotlight Caches)

        Series 4 and 5 cards can also be obtained from the Token Shop starting at CL 500
    '''.replace(' '*8, '').strip()
    await interaction.channel.send(message)
    await interaction.response.send_message('Done', ephemeral=True)

@tree.command(name='reset', description='Explain rank reset', guild=discord.Object(id=config.server))
async def reset_command(interaction: discord.Interaction, ping: discord.User = None):
    message=f'''
        {ping.mention if ping else ''}
        Rank reset works as follows:
        - Deduct 30 ranks from your final rank in the previous season
        - Round down to the closest integer divisible by 5
        - Add 3 bonus ranks

        Rank 10, Iron, is the rank floor and you can not go below it.
        No matter how high you rank at Infinite, you will always reset to rank 73.

        _Example: If you are rank 77, your rank would be reset to 48 (77-30=47, rounded down to 45, +3 to 48)_

    '''.replace(' '*8, '').strip()
    await interaction.channel.send(message)
    await interaction.response.send_message('Done', ephemeral=True)

@tree.command(name='bigbads', description='Explain Big Bads™', guild=discord.Object(id=config.server))
async def bigbad_command(interaction: discord.Interaction, ping: discord.User = None):
    message=f'''
        {ping.mention if ping else ''}
        The "big bads" are cards that are not subject to Series drops, and are therefore "permanently Series 5" (subject to change by Second Dinner). A card is a big bad only if Second Dinner announces that the card is one, there is no other criteria for it.
        The current Big Bads are Thanos, Galactus, Kang, and the High Evolutionary.
    '''.replace(' '*8, '').strip()
    await interaction.channel.send(message)
    await interaction.response.send_message('Done', ephemeral=True)

@tree.command(name='priority', description='Explain Priority', guild=discord.Object(id=config.server))
async def priority_command(interaction: discord.Interaction, ping: discord.User = None):
    message=f'''
        {ping.mention if ping else ''}
        **The player with priority will have a glowing border around their name** 
 
        Priority is determined using the following steps:
        1. Priority goes to the player who is winning the most locations. If there is a tie then,
        2. Priority goes to the player who has the higher point differential (this calculation is inverted on Bar With No Name). If there is a tie then,
        3. Priority goes to a player randomly.

        Priority is checked at the beginning of every turn, so if you are at a complete tie two turns in a row, it will randomly assign priority on the second turn independent of who had priority in the first turn.
    '''.replace(' '*8, '').strip()
    await interaction.channel.send(message)
    await interaction.response.send_message('Done', ephemeral=True)

@tree.command(name='reload_config', description='Reload the bot config', guild=discord.Object(id=config.server))
async def reload_config_command(interaction):
    load_config()
    await interaction.response.send_message('Reloaded', ephemeral=True)

### Events
@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=config.server))
    print(f"{config.env.upper()} JARVIS is ready for duty")
    check_mute_roles.start()
    check_member_roles.start()

@bot.event
async def on_member_join(member):
    if not check_member_age(member):
        try: server = [g for g in bot.guilds if g.id == config.server][0]
        except:
            print('Not on the right server?')
            return
        try: role = [r for r in server.roles if r.name.lower() == config.new_acct_role.lower()][0]
        except:
            print('New Account Role not found')
            return

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
    # caps checking
    await check_caps_percent(message)

    # auto reaction
    try:
        if message.channel.id in config.full_auto_react_channels\
        or message.channel.parent.id in config.full_auto_react_channels:
            for emoji in config.full_auto_react_emoji:
                await message.add_reaction(emoji)
                sleep(0.5)
    except AttributeError:
        pass

    # auto publish
    try:
        if message.channel.id in config.auto_publish_channels:
            await message.publish()
    except Exception as e:
        print('Auto-publish error:')
        print(e)
        pass

    # snap team reply logic
    # checks
    if message.channel.type != discord.ChannelType.public_thread:
        return
    if message.channel.parent.type != discord.ChannelType.forum:
        return
    if message.channel.parent.id != config.monitor_channel:
        return

    if check_is_dev(message.author):
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

    if check_is_mod(message.author):
        chan = bot.get_channel(config.monitor_channel)
        thread = chan.get_thread(message.channel.id)
        for tag in chan.available_tags:
            if 'moderator reply' in tag.name.lower():
                answered = tag
        try: await thread.add_tags(answered)
        except: print('Could not add answered tag')

@bot.event
async def on_message_delete(message):
    # checks
    if message.channel.type != discord.ChannelType.public_thread:
        return
    if message.channel.parent.type != discord.ChannelType.forum:
        return
    if message.channel.parent.id != config.monitor_channel:
        return

    # ensure dev role post
    if check_is_dev(message.author):
        # pull the thread for the thread_open to find the answer post
        chan = bot.get_channel(config.monitor_channel)
        thread = chan.get_thread(message.channel.id)
        async for tm in thread.history(limit=1, oldest_first=True):
            thread_open = tm.content
        # loop through reply channel to find the answer post
        reply_channel = bot.get_channel(config.reply_channel)
        async for m in reply_channel.history(limit=50):
            try:
                # create an embed from the message and ensure this is the same
                embed = await create_devreply_embed(message, thread_open)
                if embed.title == m.embeds[0].title\
                and embed.description == m.embeds[0].description:
                    await m.delete()
                    break
            except:
                pass

@bot.event
async def on_message_edit(before, after):
    # checks
    if before.channel.type != discord.ChannelType.public_thread:
        return
    if before.channel.parent.type != discord.ChannelType.forum:
        return
    if before.channel.parent.id != config.monitor_channel:
        return

    # ensure dev role post
    if check_is_dev(before.author):
        # pull the thread for the thread_open to find the answer post
        chan = bot.get_channel(config.monitor_channel)
        thread = chan.get_thread(before.channel.id)
        async for tm in thread.history(limit=1, oldest_first=True):
            thread_open = tm.content
        # loop through reply channel to find the answer post
        reply_channel = bot.get_channel(config.reply_channel)
        async for m in reply_channel.history(limit=50):
            try:
                befembed = await create_devreply_embed(before, thread_open)
                if befembed.title == m.embeds[0].title\
                and befembed.description == m.embeds[0].description:
                    newembed = await create_devreply_embed(after, thread_open)
                    await m.edit(embed=newembed)
                    break
            except:
                pass

@bot.event
async def on_thread_create(thread):
    if thread.parent.type != discord.ChannelType.forum:
        return
    if thread.parent.id in config.auto_pin_channels:
        async for message in thread.history(limit=1, oldest_first=True):
            await message.pin()

    if str(thread.parent.id) in config.forum_op_auto_react:
        async for message in thread.history(limit=1, oldest_first=True):
            for emoji in config.forum_op_auto_react[str(thread.parent.id)]:
                await message.add_reaction(emoji)
                sleep(0.5)

bot.run(config.token)
