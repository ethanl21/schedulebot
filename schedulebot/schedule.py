import discord
from discord.ext import commands
from discord_components import DiscordComponents, ComponentsBot, Button, ButtonStyle, Interaction, InteractionEventType

import asyncio
import re

from datetime import datetime, timedelta, date, timezone
from dateutil.parser import parse
from dateutil.tz import gettz
from dateutil.utils import default_tzinfo

from utils import random_color


class ScheduleCog(commands.Cog, name='Scheduling'):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.TZINFOS = {
            'PST': gettz('US/Pacific'),
            'PDT': gettz('US/Pacific'),
            'MST': gettz('US/Mountain'),
            'MDT': gettz('US/Mountain'),
            'CST': gettz('US/Central'),
            'CDT': gettz('US/Central'),
            'EST': gettz('US/Eastern'),
            'EDT': gettz('US/Eastern'),
        }
    
    async def _generate_zone_embed(self, event_title: str, time: datetime, author: discord.user) -> discord.Embed:
        
        zones = []
        # generate datetime objects
        for zone in ['PST', 'MST', 'CST', 'EST']:
            zones.append(time.astimezone(self.TZINFOS[zone]))

        zone_strs = []
        # generate time string
        for time_local in zones:
            if time_local.second == 0:
                zone_strs.append(time_local.strftime('%I:%M %p'))
            else:
                zone_strs.append(time_local.strftime('%I:%M:%S %p'))

        # Add special emojis
        keywords = {
            'study': ['school', 'textbook', 'study', 'exam', 'project', 'homework'],
            'video_game': ['gaming', 'xbox', 'ps4', 'ps5', 'steam', 'epic', 'tournament', 'siege', 'valorant'],
            'party_game': ['jackbox', 'jack box', 'party', 'quiplash', 'drawful', 'party game'],
            'sports': ['sports', 'football', 'basketball', 'tennis', 'baseball', 'soccer'],
            'rocket_league': ['rocket league'],
            'league_of_legends': ['league', 'lol', 'league of legends', 'warcraft', 'raid', 'wow']
        }
        emojis = {
            'study': '📚',
            'video_game': '🎮',
            'party_game': '🎉',
            'sports': '🏟️',
            'rocket_league': '⚽🚗',
            'league_of_legends': '🤢🤮'
        }

        # test for keywords
        for list in keywords.keys():
            if any(x.lower() in event_title.lower() for x in keywords[list]):
                event_title += '\t' + emojis[list]
                # print(f'new title: {event_title}')
                break
        
        # construct embed
        embed=discord.Embed(title=event_title, description=f'Scheduled by {author.mention}\n{date.today()}', color=random_color(), timestamp=datetime.utcnow())
        embed.set_thumbnail(url=author.avatar_url)
        embed.set_footer(text='Schedule Bot')
        embed.add_field(name=f'Pacific Time ({zones[0].strftime("%Z")})', value=zone_strs[0], inline=False)
        embed.add_field(name=f'Mountain Time ({zones[1].strftime("%Z")})', value=zone_strs[1], inline=False)
        embed.add_field(name=f'Central Time ({zones[2].strftime("%Z")})', value=zone_strs[2], inline=False)
        embed.add_field(name=f'Eastern Time ({zones[3].strftime("%Z")})', value=zone_strs[3], inline=False)

        return embed


    @commands.command()
    async def schedule(self, ctx, time, *args):
        async def accept_callback(interaction: Interaction):
            new_embed = embed
            if interaction.user.mention in attendees_denied:
                attendees_denied.remove(interaction.user.mention)
                if not attendees_denied:
                        new_embed.set_field_at(index=1, name='Not Attending', value='-')
                else:
                    new_embed.set_field_at(index=1, name='Not Attending', value='\n'.join(attendees_denied))

            if interaction.user.mention not in attendees_registered:
                attendees_registered.append(interaction.user.mention)
                new_embed.set_field_at(index=0, name='Attendees', value='\n'.join(attendees_registered))
                await interaction.respond(type=6)
                await interaction.edit_origin(embed=new_embed)
            else:
                await interaction.respond(content='You already joined this event!')


        async def reject_callback(interaction: Interaction):
            new_embed = embed
            if interaction.user.mention in attendees_registered:
                attendees_registered.remove(interaction.user.mention)
                if not attendees_registered:
                        new_embed.set_field_at(index=0, name='Attendees', value='-')
                else:
                    new_embed.set_field_at(index=0, name='Attendees', value='\n'.join(attendees_registered))


            if interaction.user.mention not in attendees_denied:
                attendees_denied.append(interaction.user.mention)
                new_embed.set_field_at(index=1, name='Not Attending', value='\n'.join(attendees_denied))
                await interaction.respond(type=6)
                await interaction.edit_origin(embed=new_embed)
            else:
                await interaction.respond(content='You already rejected this event!')


        async def cancel_callback(interaction: Interaction):
            if interaction.user == host:
                # construct new embed to modify the description
                attending_embed_dict['description'] = '**This event has been cancelled.**'
                new_embed = discord.Embed.from_dict(attending_embed_dict)
                new_embed.set_field_at(0, name='Attending', value=embed.fields[0].value)
                new_embed.set_field_at(1, name='Not Attending', value=embed.fields[1].value)

                await interaction.respond(type=6)
                await interaction.edit_origin(components=[], embed = new_embed)
            else:
                await interaction.respond(content='Only the host may cancel the event.')


        attending_embed_dict = {
            'title': 'Attendees',
            'description': "*join the list using the buttons below!*",
            'fields': [
                {
                    'name': 'Attendees',
                    'value': '-',
                    'inline': True
                },
                {
                    'name': 'Not Attending',
                    'value': '-',
                    'inline': True
                }
            ]
        }
        
        # save the host so they may cancel the event
        host = ctx.author

        # format the title from input
        event_title = ' '.join(args)

        # parse time input
        if any(x.lower() in time.lower() for x in ['d', 'h', 'm', 's']) and ':' not in time:
            delta = parse_dhms(time)
            utc = datetime.now(timezone.utc) + delta
        else:
            utc = parse_time(time, self.TZINFOS)
        
        # generate time zone embed
        tzones_embed = await self._generate_zone_embed(event_title, utc, ctx.author)
        await ctx.send(embed=tzones_embed)

        # generate attendee list embed
        attendees_registered = []
        attendees_denied = []
        
        # generate the initial embed from dict
        embed = discord.Embed.from_dict(attending_embed_dict)

        msg = await ctx.send(
            embed=embed,
            components=[
                [
                    self.bot.components_manager.add_callback(
                        Button(style=ButtonStyle.green, label="Accept"), accept_callback
                    ),
                    self.bot.components_manager.add_callback(
                        Button(style=ButtonStyle.red, label="Reject"), reject_callback
                    ),
                    self.bot.components_manager.add_callback(
                        Button(style=ButtonStyle.gray, label="Cancel Event"), cancel_callback
                    )
                        
                ]
            ]
        )


def parse_time(time_str: str, tzinfos: dict) -> datetime:

    default_tz = gettz('UTC')

    # parse time, default to UTC time
    out = default_tzinfo(parse(time_str, tzinfos=tzinfos), default_tz)

    # convert to UTC time if necessary
    if out.tzinfo != default_tz:
        out = out.astimezone(default_tz)

    return out


def parse_dhms(dhms_str: str):
    # https://stackoverflow.com/a/51916936/
    regex = re.compile(
        r'^((?P<days>[\.\d]+?)d)?((?P<hours>[\.\d]+?)h)?((?P<minutes>[\.\d]+?)m)?((?P<seconds>[\.\d]+?)s)?$')

    parts = regex.match(dhms_str)
    assert parts is not None, 'Could not parse time string'
    time_params = {name: float(param)
                   for name, param in parts.groupdict().items() if param}

    return timedelta(**time_params)