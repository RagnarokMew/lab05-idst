#!./.venv/bin/python

import discord      # base discord module
import code         # code.interact
import os           # environment variables
import inspect      # call stack inspection
import random       # dumb random number generator
import asyncio
import re
from discord.ext import commands    # Bot class and utils

################################################################################
############################### HELPER FUNCTIONS ###############################
################################################################################

# log_msg - fancy print
#   @msg   : string to print
#   @level : log level from {'debug', 'info', 'warning', 'error'}
def log_msg(msg: str, level: str):
    # user selectable display config (prompt symbol, color)
    dsp_sel = {
        'debug'   : ('\033[34m', '-'),
        'info'    : ('\033[32m', '*'),
        'warning' : ('\033[33m', '?'),
        'error'   : ('\033[31m', '!'),
    }

    # internal ansi codes
    _extra_ansi = {
        'critical' : '\033[35m',
        'bold'     : '\033[1m',
        'unbold'   : '\033[2m',
        'clear'    : '\033[0m',
    }

    # get information about call site
    caller = inspect.stack()[1]

    # input sanity check
    if level not in dsp_sel:
        print('%s%s[@] %s:%d %sBad log level: "%s"%s' % \
            (_extra_ansi['critical'], _extra_ansi['bold'],
             caller.function, caller.lineno,
             _extra_ansi['unbold'], level, _extra_ansi['clear']))
        return

    # print the damn message already
    print('%s%s[%s] %s:%d %s%s%s' % \
        (_extra_ansi['bold'], *dsp_sel[level],
         caller.function, caller.lineno,
         _extra_ansi['unbold'], msg, _extra_ansi['clear']))

################################################################################
############################## BOT IMPLEMENTATION ##############################
################################################################################

# bot instantiation
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# on_ready - called after connection to server is established
@bot.event
async def on_ready():
    log_msg('logged on as <%s>' % bot.user, 'info')

# on_message - called when a new message is posted to the server
#   @msg : discord.message.Message
@bot.event
async def on_message(msg):
    # filter out our own messages

    if msg.author == bot.user:
        return
    
    log_msg('message from <%s>: "%s"' % (msg.author, msg.content), 'debug')

    # overriding the default on_message handler blocks commands from executing
    # manually call the bot's command processor on given message
    await bot.process_commands(msg)

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is not None:
        if len(before.channel.members) == 1 and before.channel.members[0].id == bot.user.id:
            await before.channel.guild.voice_client.disconnect()

# roll - rng chat command
#   @ctx     : command invocation context
#   @max_val : upper bound for number generation (must be at least 1)
@bot.command(brief='Generate random number between 1 and <arg>')
async def roll(ctx, max_val: int):
    # argument sanity check
    if max_val < 1:
        raise Exception('argument <max_val> must be at least 1')

    await ctx.send(random.randint(1, max_val))

# roll_error - error handler for the <roll> command
#   @ctx     : command that crashed invocation context
#   @error   : ...
@roll.error
async def roll_error(ctx, error):
    await ctx.send(str(error))

@bot.command(brief='Leave a voice channel')
async def scram(ctx):
    voice = ctx.voice_client

    if voice is None:
        await ctx.send("Not connected to any channel")
        return None

    await voice.disconnect()
    await ctx.send("Left the voice channel")
    return 1

@bot.command(brief='Join a voice channel')
async def join(ctx):
    voice = ctx.message.author.voice

    if voice is None:
        await ctx.send("You need to be connected to a voice channel")
        return None

    connection = await voice.channel.connect()
    await ctx.send(f"Connected to {voice.channel.mention}.")
    return connection

@bot.command(brief='Lists available songs')
async def list(ctx):
    msg = "Available songs: "
    
    for file in os.listdir('./songs/'):
        if file.endswith(".mp3"):
            msg+=file[:-4]+", "
    msg=msg[:-2]
    await ctx.send(msg)

# play - playing a song command
#   @ctx : command context
#   @string : song to be played
@bot.command(brief='Play a song in voice channel')
async def play(ctx, song: str):
    found=False
    for file in os.listdir('./songs/'):
        if file.endswith(".mp3") and song == file[:-4]:
            found = True

    if not found:
        await ctx.send(f"{song} not found, check !list")
        return
    
    voice_channel = await join(ctx)

    if voice_channel is None:
        return

    await ctx.send(f"Now playing {song}.mp3")
    voice_channel.play(
            discord.FFmpegPCMAudio(
                executable="/usr/bin/ffmpeg",
                source=f"songs/{song}.mp3"
                )
        )

    while voice_channel.is_playing():
        await asyncio.sleep(1)

################################################################################
############################# PROGRAM ENTRY POINT ##############################
################################################################################

# FOR DEBUGGING USE 
# code.interact(local=dict(globals(), **locals()))
# WILL PAUSE CODE EXECUTION
# PUT IT WHERE YOU NEED IT

if __name__ == '__main__':
    # check that token exists in environment
    if 'BOT_TOKEN' not in os.environ:
        log_msg('save your token in the BOT_TOKEN env variable!', 'error')
        exit(-1)

    # launch bot (blocking operation)
    bot.run(os.environ['BOT_TOKEN'])
