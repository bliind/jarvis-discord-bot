import discord
import json
import os
import re
import datetime
import random
import asyncio
from ConfigModal import ConfigModal
from discord import app_commands
from discord.ext import tasks
import configdb
import AutoMod

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

AutoMod.set_token(config.token)
AutoMod.set_guild(config.server)

GREEN = 5763719
RED = 15548997
BLUE = 3447003

# I'm sorry
flags = ["🇦🇨","🇦🇩","🇦🇪","🇦🇫","🇦🇬","🇦🇮","🇦🇱","🇦🇲","🇦🇴","🇦🇶","🇦🇷","🇦🇸","🇦🇹","🇦🇺","🇦🇼","🇦🇽","🇦🇿","🇧🇦","🇧🇧","🇧🇩","🇧🇪","🇧🇫","🇧🇬","🇧🇭","🇧🇮","🇧🇯","🇧🇱","🇧🇲","🇧🇳","🇧🇴","🇧🇶","🇧🇷","🇧🇸","🇧🇹","🇧🇻","🇧🇼","🇧🇾","🇧🇿","🇨🇦","🇨🇨","🇨🇩","🇨🇫","🇨🇬","🇨🇭","🇨🇮","🇨🇰","🇨🇱","🇨🇲","🇨🇳","🇨🇴","🇨🇵","🇨🇷","🇨🇺","🇨🇻","🇨🇼","🇨🇽","🇨🇾","🇨🇿","🇩🇪","🇩🇬","🇩🇯","🇩🇰","🇩🇲","🇩🇴","🇩🇿","🇪🇦","🇪🇨","🇪🇪","🇪🇬","🇪🇭","🇪🇷","🇪🇸","🇪🇹","🇪🇺","🇫🇮","🇫🇯","🇫🇰","🇫🇲","🇫🇴","🇫🇷","🇬🇦","🇬🇧","🇬🇩","🇬🇪","🇬🇫","🇬🇬","🇬🇭","🇬🇮","🇬🇱","🇬🇲","🇬🇳","🇬🇵","🇬🇶","🇬🇷","🇬🇸","🇬🇹","🇬🇺","🇬🇼","🇬🇾","🇭🇰","🇭🇲","🇭🇳","🇭🇷","🇭🇹","🇭🇺","🇮🇨","🇮🇩","🇮🇪","🇮🇱","🇮🇲","🇮🇳","🇮🇴","🇮🇶","🇮🇷","🇮🇸","🇮🇹","🇯🇪","🇯🇲","🇯🇴","🇯🇵","🇰🇪","🇰🇬","🇰🇭","🇰🇮","🇰🇲","🇰🇳","🇰🇵","🇰🇷","🇰🇼","🇰🇾","🇰🇿","🇱🇦","🇱🇧","🇱🇨","🇱🇮","🇱🇰","🇱🇷","🇱🇸","🇱🇹","🇱🇺","🇱🇻","🇱🇾","🇲🇦","🇲🇨","🇲🇩","🇲🇪","🇲🇫","🇲🇬","🇲🇭","🇲🇰","🇲🇱","🇲🇲","🇲🇳","🇲🇴","🇲🇵","🇲🇶","🇲🇷","🇲🇸","🇲🇹","🇲🇺","🇲🇻","🇲🇼","🇲🇽","🇲🇾","🇲🇿","🇳🇦","🇳🇨","🇳🇪","🇳🇫","🇳🇬","🇳🇮","🇳🇱","🇳🇴","🇳🇵","🇳🇷","🇳🇺","🇳🇿","🇴🇲","🇵🇦","🇵🇪","🇵🇫","🇵🇬","🇵🇭","🇵🇰","🇵🇱","🇵🇲","🇵🇳","🇵🇷","🇵🇸","🇵🇹","🇵🇼","🇵🇾","🇶🇦","🇷🇪","🇷🇴","🇷🇸","🇷🇺","🇷🇼","🇸🇦","🇸🇧","🇸🇨","🇸🇩","🇸🇪","🇸🇬","🇸🇭","🇸🇮","🇸🇯","🇸🇰","🇸🇱","🇸🇲","🇸🇳","🇸🇴","🇸🇷","🇸🇸","🇸🇹","🇸🇻","🇸🇽","🇸🇾","🇸🇿","🇹🇦","🇹🇨","🇹🇩","🇹🇫","🇹🇬","🇹🇭","🇹🇯","🇹🇰","🇹🇱","🇹🇲","🇹🇳","🇹🇴","🇹🇷","🇹🇹","🇹🇻","🇹🇼","🇹🇿","🇺🇦","🇺🇬","🇺🇲","🇺🇸","🇺🇾","🇺🇿","🇻🇦","🇻🇨","🇻🇪","🇻🇬","🇻🇮","🇻🇳","🇻🇺","🇼🇫","🇼🇸","🇽🇰","🇾🇪","🇾🇹","🇿🇦","🇿🇲","🇿🇼"]

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

def timestamp():
    now = datetime.datetime.now()
    return int(round(now.timestamp()))

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
    try: await sent.publish()
    except: print('Could not Publish message')
    # try: await sent.add_reaction(config.plus_emoji)
    # except: print('Could not add plus emote')
    # sleep(1)
    # try: await sent.add_reaction(config.minus_emoji)
    # except: print('Could not add minus emote')

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
                try: sent = await message.reply(config.caps_prot_message)
                except Exception as e:
                    print(e, message)

                await message.delete()
                await asyncio.sleep(5)
                try: await sent.delete()
                except: pass
    except AttributeError:
        pass

### Tasks
@tasks.loop(seconds=3600)
async def bump_archived_wiki_posts():
    try:
        forum = bot.get_channel(config.wiki_forum_channel)
        async for old_thread in forum.archived_threads(limit=None):
            await old_thread.edit(archived=False)
    except Exception as e:
        print(f'{timestamp()}: Error bumping archived wiki posts:')
        print(e)

@tasks.loop(seconds=300)
async def delete_old_streaming_posts():
    try:
        chan = bot.get_channel(config.streaming_post_channel)
        cutoff_time = discord.utils.utcnow() - datetime.timedelta(seconds=config.streaming_post_time_limit)
        async for message in chan.history(limit=100, before=cutoff_time):
            if message.author.id != config.streaming_post_bot:
                await message.delete()
    except Exception as e:
        print(f'{timestamp()}: Error during delete_old_streaming_posts:')
        print(e)

@tasks.loop(seconds=3600)
async def check_mute_roles():
    try: server = [g for g in bot.guilds if g.id == config.server][0]
    except:
        print('Not on the right server?')
        return
    try: role = [r for r in server.roles if r.name.lower() == config.new_acct_role.lower()][0]
    except:
        print('New Account Role not found')
        return

    try:
        members = [m for m in server.members if role in m.roles]
        if len(members) > 0:
            for member in members:
                if check_member_age(member):
                    await member.remove_roles(role)
    except Exception as e:
        print(f'{timestamp()}: Failed to check New Account roles')
        print(e)

@tasks.loop(seconds=3600)
async def check_member_roles():
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

    try:
        members = [m for m in server.members if role not in m.roles]
        if len(members) > 0:
            for member in members:
                if check_server_age(member):
                    if new_acct_role not in member.roles:
                        await member.add_roles(role)
    except Exception as e:
        print(f'{timestamp()}: Failed to check Member roles')
        print(e)

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
            ## Please, read the FAQ before asking your question.

            * **1. All the general rules from the server apply here:**
              * Don't ping the Developers or other users.
              * Be respectful and polite when doing your question, etc.
            * **2. Feedback, Game discussions and Bug Reports should be posted in their respective channels:**
              * <#1067974227816366150>  
              * <#1020474756543303690>   
              * <#1020475179085865000>  
            * **3. No questions that can be answered by anyone in another channel. (Things we already know.)**
              * Board state posts
              * "Is this a bug" posts
              * "Why did this happen?" posts.
            * **4. No "When is X happening". The developers will announce when things will go live, not in a Q&A forum.**
            * **5. Repost Questions will be removed if there is a currently unlocked post with the same question.**
            * **6. No questions containing datamined content or spoilers.** Your question will be deleted on the spot and you will get a warn, even if you spoiler tag it.
            * **7. No questions about matchmaking in ladder or conquest.**

            If your post was Closed, it means it violated one, or more, of our guide lines.
        '''.replace(' '*12, '').strip()
    )

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message('Done', ephemeral=True)

@tree.command(name='wiki', description='Links to common wiki pages', guild=discord.Object(id=config.server))
async def wiki_command(interaction: discord.Interaction, page: str, ping: discord.User = None):
    message=f'{ping.mention if ping else ""} {config.wiki_links[page]}'
    await interaction.response.send_message(message)

@wiki_command.autocomplete('page')
async def autocomplete_wiki_page(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=page, value=page) for page in config.wiki_links.keys() if page.startswith(current)
    ]

@tree.command(name='update_config', description='Update ReactionRole config', guild=discord.Object(id=config.server))
async def update_config_command(interaction):
    modal = ConfigModal(config.reaction_role_reaction, config.reaction_role_role)
    await interaction.response.send_modal(modal)
    await modal.wait()
    config.reaction_role_reaction = modal.reaction.value
    config.reaction_role_role = modal.role.value

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
    delete_old_streaming_posts.start()
    bump_archived_wiki_posts.start()

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
    
    if payload.channel_id in config.no_flag_channels \
    and payload.emoji.name in flags:
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.clear_reaction(payload.emoji.name)
        
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

    if config.reaction_role_active and\
    payload.member.id in config.reaction_role_users and\
    payload.emoji.name.lower() == config.reaction_role_reaction:
        # role reaction
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = await bot.fetch_user(payload.user_id)
        await message.remove_reaction(payload.emoji, user)

        try: server = [g for g in bot.guilds if g.id == config.server][0]
        except: return
        try: role = [r for r in server.roles if r.name.lower() == config.reaction_role_role.lower()][0]
        except: return

        await message.author.add_roles(role)

    if payload.message_id == config.reaction_message_id:
        # under 100
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        for reaction in message.reactions:
            if reaction.emoji.name == config.reaction_message_emoji_name: break

        if reaction.emoji.name == config.reaction_message_emoji_name\
        and reaction.count > config.reaction_message_threshold:
            users = []
            async for user in reaction.users():
                users.append(user)
            remove = random.choice(users)
            await message.remove_reaction(payload.emoji, remove)

@bot.event
async def on_scheduled_event_create(event):
    guild = bot.get_guild(config.server)
    events = await guild.fetch_scheduled_events()
    white_list = [f"*event={e.url.split('/')[-1]}" for e in events]

    rules = AutoMod.get_automod_rules()
    for rule in rules:
        if rule['name'] == config.automod_links_name:
            the_rule = rule
            break

    try:
        the_rule['trigger_metadata']['allow_list'] = white_list
        AutoMod.update_automod_rule(the_rule['id'], the_rule)
    except Exception as e:
        print(f'{timestamp()}: Failed to update event whitelists:')
        print(e)

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

async def check_owner_call(message):
    if bot.user.mentioned_in(message):
        if message.author.id == 145971157902950401:
            await message.reply('At your service, sir.')

@bot.event
async def on_message(message):
    # check for owner call
    await check_owner_call(message)

    # caps checking
    await check_caps_percent(message)

    # auto reaction
    try:
        if message.channel.id in config.full_auto_react_channels\
        or message.channel.parent.id in config.full_auto_react_channels:
            for emoji in config.full_auto_react_emoji:
                await message.add_reaction(emoji)
                await asyncio.sleep(0.5)
    except AttributeError:
        pass

    # auto publish
    try:
        if message.channel.id in config.auto_publish_channels:
            await message.publish()
    except Exception as e:
        print(f'{timestamp()}: Auto-publish error:')
        print(e)

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
    await check_caps_percent(after)

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

async def check_lfg_post(thread):
    lfg_channel_id = await configdb.get_config('lfg_channel_id')
    lfg_channel_id = [int(id) for id in lfg_channel_id]

    if thread.parent.type != discord.ChannelType.forum:
        return
    if thread.parent.id not in lfg_channel_id:
        return

    patterns = [
        r'Name: (.+)$',
        r'Tag: (.+)$',
        r'Language: (.+)$',
        r'[\*-] Minimum Ladder Rank: (.+)$',
        r'[\*-] Minimum Collection Level: (.+)$'
    ]

    # sleep to wait for the message, discord will send this event before the message is there?
    await asyncio.sleep(2)
    thread_open = [m async for m in thread.history(limit=1, oldest_first=True)][0]

    if None in [re.search(p, thread_open.content, re.MULTILINE | re.IGNORECASE) for p in patterns]:
        message = '''
            ## Post Not Successful <:Ohno:980195981888999525>
            Hey there! It looks like your post doesn't follow the correct formatting for alliance posts. Please make sure to follow the guidelines provided in the forum channel's guidelines.

            Please recreate your post when your slowmode expires to match the format provided. Thanks for helping keep our community organized!

            For reference, the proper formatting is:

            ```
            > Name: **Clan Name**
            > Tag: **[Clan Tag]**
            > Language: **Language**

            > **Join Requirements**
            > * Minimum Ladder Rank: **Rank**
            > * Minimum Collection Level: **CL**

            **About us:**
            **Additional Info:**
            **How to Apply:**
            ```

            For ease of use, you can copy [this template](https://discord.com/channels/978545345715908668/1267912521671770132/1267912521671770132) following the instructions in the post.
        '''.replace(' '*12, '').strip()
        embed = discord.Embed(
            color=discord.Color.red(),
            description=message
        )
        await thread.send(embed=embed)
        await thread.edit(archived=True, locked=True)

@bot.event
async def on_thread_create(thread):
    # lfg format checker
    await check_lfg_post(thread)

    if thread.parent.type != discord.ChannelType.forum:
        return
    if thread.parent.id in config.auto_pin_channels:
        async for message in thread.history(limit=1, oldest_first=True):
            await message.pin()

    if str(thread.parent.id) in config.forum_op_auto_react:
        async for message in thread.history(limit=1, oldest_first=True):
            for emoji in config.forum_op_auto_react[str(thread.parent.id)]:
                await message.add_reaction(emoji)
                await asyncio.sleep(0.5)

@bot.event
async def on_member_update(before, after):
    # remove Booster-specific roles from non-boosters
    b_roles = [r.name for r in before.roles]
    a_roles = [r.name for r in after.roles]
    removed = [r for r in b_roles if r not in a_roles]
    if '[Booster]' in removed:
        remove = [a for a in after.roles if a.name.startswith('[B]')]
        if remove: await after.remove_roles(*remove)

bot.run(config.token)
