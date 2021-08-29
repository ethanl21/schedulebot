import discord
import discord.ext
from discord_components import ComponentsBot
import utils
from schedule import ScheduleCog
import os

def main():
    # Get config values
    if 'DYNO' in os.environ:
        token = os.environ['token']
        prefix = os.environ['prefix']
    else:
        token, prefix = utils.get_config()

    # Create bot object
    activity = discord.Game(name=f'{prefix}PLACEHOLDER')
    bot = ComponentsBot(command_prefix=prefix, activity=activity)

    # Register events
    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user} (ID: {bot.user.id})')
        print(f'Connected to {len(bot.guilds)} server(s).')
        print(f'Running Discord.py {discord.__version__} {discord.version_info[3]}.')

    # Add commands
    # (none)

    # Add cogs
    bot.add_cog(ScheduleCog(bot))

    # Run bot
    try:
        bot.run(token)
    except discord.LoginFailure as msg:
        print(
            f"Error: {msg}.\nEnsure your credentials contained in config.ini are correct and try again.")

if __name__ == '__main__':
    main()