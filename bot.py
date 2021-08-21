import os
import discord
import asyncio
import os
import time

import numpy as np
from matplotlib import pyplot as plt

from discord import channel
import youtube_dl

from discord.channel import VoiceChannel
from discord.ext import commands,tasks
from dotenv import load_dotenv
from edupage_api import Edupage, BadCredentialsException, LoginDataParsingException, EduDate, EduTime



load_dotenv()
TOKEN = str(os.getenv('DISCORD_TOKEN'))
TOKEN = TOKEN.strip("{ }")

EDUPAGE_PASS = str(os.getenv('EDUPAGE_PASS'))
EDUPAGE_PASS = EDUPAGE_PASS.strip("{ }")

EDUPAGE_NAME = str(os.getenv('EDUPAGE_NAME'))
EDUPAGE_NAME = EDUPAGE_NAME.strip("{ }")

EDUPAGE_SCHOOL = str(os.getenv('EDUPAGE_SCHOOL'))
EDUPAGE_SCHOOL = EDUPAGE_SCHOOL.strip("{ }")


bot = commands.Bot(command_prefix='-')


youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'options': '-vn'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.3):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

async def loggin(ctx):
    edupage = Edupage(EDUPAGE_SCHOOL, EDUPAGE_NAME, EDUPAGE_PASS)

    try:
        edupage.login()
        print("Login successfully!")
        return edupage
    except BadCredentialsException:
        print("Wrong username or password!")
    except LoginDataParsingException:
        print("Try again or open an issue!")

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()
@bot.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()

@bot.command()
async def kde(ctx):
    try:
        await join(ctx)
    except:
        pass
    try :
        server = ctx.message.guild
        voice_channel = server.voice_client
        async with ctx.typing():
            filename = await YTDLSource.from_url("https://www.youtube.com/watch?v=AlwgAcH9V7A", loop=bot.loop)
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
            time.sleep(10)
            await leave(ctx)
    except:
        await ctx.send("The bot is not connected to a voice channel.")

@bot.command()
async def sad(ctx):
    nm = ctx.username
    await ctx.edit(username=nm + "-sad")

@bot.command()
async def play(ctx, url):
    try:
        await join(ctx)
    except:
        pass
    try :
        server = ctx.message.guild
        voice_channel = server.voice_client
        async with ctx.typing():
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
    except:
        await ctx.send("The bot is not connected to a voice channel.")

@bot.command()
async def hour(ctx):
    try:
        edupage = await loggin(ctx)
    except:
        print("failed to loggin")
        await ctx.send("failed to loggin")
    

    today = EduDate.today()
    timetable = edupage.get_timetable(today)

    current_time = EduTime.now()
    current_lesson = timetable.get_lesson_at_time(current_time)

    current_lesson = str(current_lesson).strip("{ }").split(", ")[0:2]
    current_lesson_split = []
    for key_and_value in current_lesson:
        current_lesson_split.append(key_and_value.split(": ")[1])
    await ctx.send(f"{str(current_lesson_split[0])} {str(current_lesson_split[1])}")



@bot.command()
async def home(ctx):
    try:
        edupage = await loggin(ctx)
    except:
        print("failed to loggin")
        await ctx.send("failed to loggin")
    
    try :
        homework = edupage.get_homework()
        
        for hw in range(10):
            print(f"| {homework[hw].due_date} | {homework[hw].subject} | {homework[hw].title} | ")
            await ctx.send(f"| {homework[hw].due_date} | {homework[hw].subject} | {homework[hw].title} | \n")


    except:
        await ctx.send("Error")


@bot.command()
async def graph(ctx, x, y):
    x = x.strip("[]").split(",")
    holderx = []
    for i in x:
        holderx.append(float(i))

    y = y.strip("[]() ").split(",")    
    holdery = []
    for i in y:
        holdery.append(float(i))
    xpoints = np.array(holderx)
    ypoints = np.array(holdery)
    plt.plot(xpoints, ypoints, marker="x", color="black")
    plt.grid(True, "both")
    plt.savefig('figure.png')
    await ctx.send(file=discord.File('figure.png'))
    os.remove("./figure.png")

bot.run(TOKEN)


"""-graph
[0,0,15.9,24.7,25.6,26.9,27.7,28.9,29.8,31.0,31.9,32.8,33.9,21.8,21.7,21.6,21.6,21.5,21.5]
[0,0,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,2.6,2.8,3.0,3.1,3.5,3.6]

-graph [0,5,10.1,24.3,25.7,27,27.8,29,29.8,30.8,32,32.8,33.9,22,22,21.9,21.8,21.7,21.7] [0,0,0,0.,0.,0.,0.,0.,0.,0.,0.,0.,0,2.5,2.7,3.0,3.2,3.4,3.6]
"""