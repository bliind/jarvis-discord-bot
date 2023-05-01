# J.A.R.V.I.S.
### Just A Rather Very Intelligent System

A Discord bot for:
- Auto-pinning forum OPs
- Logging reaction usage of specified emotes
- Publicly posting replies to forum threads
    from a specified role

### Instructions

**Test Server Instructions**
1) Create a copy of the `config.json.template` named `config.test.json` and adjust the values to suit your server.
2) Run `python jarvis.py`

**Live Server Instructions**
1) Create a copy of the `config.json.template` named `config.json` and adjust the values to suit your server.
2) Run `JARVIS_ENV=prod python jarvis.py`


### Config values

| config key | description |
| --- | --- |
| env | test or prod, prints when the bot connects |
| token | the discord token for your bot |
| server | the ID of the server to watch |
| emoji_channel | the channel to post the reaction log to |
| reply_channel | the channel to post the forum replies to |
| monitor_channel | the channel to monitor for forum replies |
| role_check | the role to check for to post forum replies |
| upvote_emoji | the upvote emoji to be added to dev posts |
| downvote_emoji | the downvote emoji to be added to dev posts |
| monitor_emoji | a list of the emoji to log reaction usage for |
| auto_pin_channels | a list of channel IDs to auto pin forum OPs |
