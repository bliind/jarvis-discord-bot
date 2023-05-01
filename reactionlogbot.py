import discord
import os

TOKEN = os.getenv('MARVIN_TOKEN')
SERVER_ID = int(os.getenv('MARVIN_SERVER_ID'))
CHANNEL_ID = int(os.getenv('MARVIN_CHANNEL_ID'))

EXCLUDE_LIST = ['💩', '🤡', '🖕', '🏳️‍🌈', '🏳️‍⚧️']

GREEN = 5763719
RED = 15548997

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def get_message_link(p):
    return f'https://discord.com/channels/{p.guild_id}/{p.channel_id}/{p.message_id}'

@bot.event
async def on_ready():
    print('Reaction Log Bot is ready for duty')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.guild_id == SERVER_ID:
        if payload.emoji.name in EXCLUDE_LIST:
            output_channel = bot.get_channel(CHANNEL_ID)
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
            output_channel = bot.get_channel(CHANNEL_ID)
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

bot.run(TOKEN)
