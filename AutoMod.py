import requests
import json

token = ''
guild = 0

# set the bot token to use for the api
def set_token(t):
    global token
    token = t

# set the guild id we'll be working in
def set_guild(g):
    global guild
    guild = g

# make a call to the API
def call(endpoint, method='GET', options={}):
    if 'headers' not in options: options['headers'] = {}
    options['headers']['Authorization'] = f'Bot {token}'

    url = f'https://discord.com/api/v10{endpoint}'
    res = requests.request(method, url, **options)

    return json.loads(res.text)

# get a list of automod rules
def get_automod_rules():
    return call(f'/guilds/{guild}/auto-moderation/rules')

# get a specific automod rule
def get_automod_rule(id: int):
    return call(f'/guilds/{guild}/auto-moderation/rules/{id}')

# update an automod rule
def update_automod_rule(id: int, params={}):
    return call(
        f'/guilds/{guild}/auto-moderation/rules/{id}',
        'PATCH',
        options={
            "headers": {"Content-Type": "application/json"},
            "data": json.dumps(params)
        }
    )
