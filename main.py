from discord.ext import commands, tasks
from discord.ext.commands import BucketType, cooldown
import discord
import json
import aiohttp
import requests
import random
import wikipedia
import datetime
import giphy_client
from giphy_client.rest import ApiException
from io import BytesIO
# from keep_alive import keep_alive
from PIL import Image, ImageFilter
from bs4 import BeautifulSoup
import inspect
import io
import textwrap
import traceback
from contextlib import redirect_stdout
from aiohttp import request
import aiofiles
from prsaw import RandomStuff
import platform
from PIL import Image, ImageFont, ImageDraw
import asyncio
import urllib.request
import re
import hashlib

def get_prefix(client, message):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

    return prefixes[str(message.guild.id)]

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix=get_prefix, intents=intents)


player1 = ""
player2 = ""
turn = ""
gameOver = True

board = []

winningConditions = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6]
]

client.remove_command("help")

client.sniped_messages = {}

client.version = 1.1

rs = RandomStuff(async_mode=True)

client.warnings = {} # guild_id : {member_id: [count, [(admin_id, reason)]]}

@client.event
async def on_ready():
  for guild in client.guilds:
    client.warnings[guild.id] = {}
        
    async with aiofiles.open(f"{guild.id}.txt", mode="a") as temp:
      pass

    async with aiofiles.open(f"{guild.id}.txt", mode="r") as file:
      lines = await file.readlines()

      for line in lines:
        data = line.split(" ")
        member_id = int(data[0])
        admin_id = int(data[1])
        reason = " ".join(data[2:]).strip("\n")

        try:
          client.warnings[guild.id][member_id][0] += 1
          client.warnings[guild.id][member_id][1].append((admin_id, reason))

        except KeyError:
          client.warnings[guild.id][member_id] = [1, [(admin_id, reason)]]

  change_status.start()
  print('Hello')

@client.event
async def on_guild_join(guild):
  client.warnings[guild.id] = {}
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  prefixes[str(guild.id)] = "a?"

  with open("prefixes.json", "w") as f:
    json.dump(prefixes, f, indent=4)

@client.event
async def on_guild_remove(guild):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  prefixes.pop(str(guild.id))

  with open("prefixes.json", "w") as f:
    json.dump(prefixes, f, indent=4)

@client.command()
# @commands.has_permissions(administrator=True)
async def changeprefix(ctx, prefix):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  prefixes[str(ctx.guild.id)] = prefix

  with open("prefixes.json", "w") as f:
    json.dump(prefixes, f, indent=4)

  await ctx.send(f"`Prefix changed to: {prefix}`")

status = ['Astra', 'servers']

@tasks.loop(seconds=10)
async def change_status():
  
  await client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game(random.choice(status)))

@client.command(name='eval')
async def _eval(ctx, *, body):
    """Evaluates python code"""
    env = {
        'ctx': ctx,
        'bot': client,
        'channel': ctx.channel,
        'author': ctx.author,
        'guild': ctx.guild,
        'message': ctx.message,
        'source': inspect.getsource
    }

    def cleanup_code(content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    env.update(globals())

    body = cleanup_code(body)
    stdout = io.StringIO()
    err = out = None

    to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

    def paginate(text: str):
        '''Simple generator that paginates text.'''
        last = 0
        pages = []
        for curr in range(0, len(text)):
            if curr % 1980 == 0:
                pages.append(text[last:curr])
                last = curr
                appd_index = curr
        if appd_index != len(text)-1:
            pages.append(text[last:curr])
        return list(filter(lambda a: a != '', pages))
    
    try:
        exec(to_compile, env)
    except Exception as e:
        err = await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')
        return await ctx.message.add_reaction('\u2049')

    func = env['func']
    try:
        with redirect_stdout(stdout):
            ret = await func()
    except Exception as e:
        value = stdout.getvalue()
        err = await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
    else:
        value = stdout.getvalue()
        if ret is None:
            if value:
                try:
                    
                    out = await ctx.send(f'```py\n{value}\n```')
                except:
                    paginated_text = paginate(value)
                    for page in paginated_text:
                        if page == paginated_text[-1]:
                            out = await ctx.send(f'```py\n{page}\n```')
                            break
                        await ctx.send(f'```py\n{page}\n```')
        else:
            try:
                out = await ctx.send(f'```py\n{value}{ret}\n```')
            except:
                paginated_text = paginate(f"{value}{ret}")
                for page in paginated_text:
                    if page == paginated_text[-1]:
                        out = await ctx.send(f'```py\n{page}\n```')
                        break
                    await ctx.send(f'```py\n{page}\n```')

    if out:
        await ctx.message.add_reaction('\u2705')  # tick
    elif err:
        await ctx.message.add_reaction('\u2049')  # x
    else:
        await ctx.message.add_reaction('\u2705')

@client.command(aliases=["mc"])
async def members(ctx):

    a=ctx.guild.member_count
    b=discord.Embed(title=f"members in {ctx.guild.name}",description=a,color=discord.Colour.purple())
    await ctx.send(embed=b)

@client.command()
async def covid(ctx, *, countryName = None):

  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  try:
    if countryName is None:
      embed=discord.Embed(title=f"This command is used like this: ```{pre}covid [country]```", colour=0xff0000,timestamp=ctx.message.created_at)
      await ctx.send(embed=embed)


    else:
      url = f"https://coronavirus-19-api.herokuapp.com/countries/{countryName}"
      stats = requests.get(url)
      json_stats = stats.json()
      country = json_stats["country"]
      totalCases = json_stats["cases"]
      todayCases = json_stats["todayCases"]
      totalDeaths = json_stats["deaths"]
      todayDeaths = json_stats["todayDeaths"]
      recovered = json_stats["recovered"]
      active = json_stats["active"]
      critical = json_stats["critical"]
      casesPerOneMillion = json_stats["casesPerOneMillion"]
      deathsPerOneMillion = json_stats["deathsPerOneMillion"]
      totalTests = json_stats["totalTests"]
      testsPerOneMillion = json_stats["testsPerOneMillion"]

      embed2 = discord.Embed(title=f"**COVID-19 Status Of {country}**!", description="This Information Isn't Live Always, Hence It May Not Be Accurate!", colour=0x0000ff, timestamp=ctx.message.created_at)
      embed2.add_field(name="**Total Cases**", value=totalCases, inline=True)
      embed2.add_field(name="**Today Cases**", value=todayCases, inline=True)
      embed2.add_field(name="**Total Deaths**", value=totalDeaths, inline=True)
      embed2.add_field(name="**Today Deaths**", value=todayDeaths, inline=True)
      embed2.add_field(name="**Recovered**", value=recovered, inline=True)
      embed2.add_field(name="**Active**", value=active, inline=True)
      embed2.add_field(name="**Critical**", value=critical, inline=True)
      embed2.add_field(name="**Cases Per One Million**", value=casesPerOneMillion, inline=True)
      embed2.add_field(name="**Deaths Per One Million**", value=deathsPerOneMillion, inline=True)
      embed2.add_field(name="**Total Tests**", value=totalTests, inline=True)
      embed2.add_field(name="**Tests Per One Million**", value=testsPerOneMillion, inline=True)

      embed2.set_thumbnail(url="https://cdn.discordapp.com/attachments/564520348821749766/701422183217365052/2Q.png")
      await ctx.send(embed=embed2)

  except:
    embed3 = discord.Embed(title="Invalid Country Name Or API Error! Try Again..!", colour=0xff0000, timestamp=ctx.message.created_at)
    embed3.set_author(name="Error!")
    await ctx.send(embed=embed3)

@client.command()
async def meme(ctx):
  async with aiohttp.ClientSession() as conn:
    async with conn.get("https://www.reddit.com/r/memes/random/.json") as r:
      content = await r.json()
      parent = content[0]['data']["children"][0]['data']
      link = f"https://reddit.com{parent['permalink']}"
      img = parent["url"]
      title = parent["title"]
      desc = parent["selftext"]
      up_votes = parent["ups"]
      down_votes = parent["downs"]
      comments = parent["num_comments"]
      author = parent["author"]

      await ctx.send({
        "link": link,
        "img_link": img,
        "title": title,
        "description": desc,
        "up_votes": up_votes,
        "down_votes": down_votes,
        "comments": comments,
        "author": author
      })

@client.command()
async def coin(ctx):
  await ctx.send(random.choice(["Heads", "Tails"]))


# @client.command()
# async def spam(ctx, num: int=None, content_msg=None):
#   if num == None:
#     await ctx.send("Please enter the number of times you have to spam the message")
#   elif content_msg == None:
#     await ctx.send("Please enter the content of the message")

#   else:
#     for i in range(num):
#       await ctx.send(content_msg)


@client.command()
async def quote(ctx):
  response = requests.get('https://zenquotes.io/api/random')
  json_data = json.loads(response.text)
  quote_generator = json_data[0]['q'] + ' - ' + json_data[0]['a']
  await ctx.send(quote_generator)


@client.command()
async def announce(ctx, content_user=None, channel: discord.TextChannel=None):
  if content_user == None:
    await ctx.send("Please enter the content of the message")
  elif channel == None:
    await ctx.send("Please enter the channel")
  else:
    await ctx.message.delete()
    msg = discord.Embed(title=content_user, timestamp=ctx.message.created_at, colour=discord.Colour.purple())
    await channel.send(embed=msg)


@client.command()
async def deletetextchannel(ctx, channel: discord.TextChannel=None):
  if channel == None:
    await ctx.send("Please enter the channel")
  else:
    msg = discord.Embed(title='Success', colour=discord.Colour.purple())
    msg.add_field(name='-', value=f'Channel: {channel} has been deleted', inline=True)

    if ctx.author.guild_permissions.manage_channels:
      await ctx.send(embed=msg)
      await channel.delete()


@client.command()
async def deletevoicechannel(ctx, channel: discord.VoiceChannel=None):
  if channel == None:
    await ctx.send("Please enter the channel")
  else:
    msg = discord.Embed(title='Success', colour=discord.Colour.purple())
    msg.add_field(name='-', value=f'Channel: {channel} has been deleted', inline=True)

    if ctx.author.guild_permissions.manage_channels:
      await ctx.send(embed=msg)
      await channel.delete()


@client.command()
async def createtextchannel(ctx, channel_name=None):
  if channel_name == None:
    await ctx.send("Please enter the channel")
  else:
    guild = ctx.guild
    msg = discord.Embed(title='Success', colour=discord.Colour.purple())
    msg.add_field(name='-', value=f'Channel: {channel_name} has been created', inline=True)

    await guild.create_text_channel(name='{}'.format(channel_name))
    await ctx.send(embed=msg)


@client.command()
async def createvoicechannel(ctx, channel_name=None):
  if channel_name == None:
    await ctx.send("Please enter the channel")
  else:
    guild = ctx.guild
    msg = discord.Embed(title='Success', colour=discord.Colour.purple())
    msg.add_field(name='-', value=f'Channel: {channel_name} has been created', inline=True)

    await guild.create_voice_channel(name='{}'.format(channel_name))
    await ctx.send(embed=msg)


@client.command()
async def vote(ctx, content_user=None):

  if content_user == None:
    await ctx.send("Please enter the content of the vote")

  else:
    ctx.message.add_reaction('✅')
    ctx.message.add_reaction('❌')

    embed = discord.Embed(title=content_user, colour=discord.Colour.purple())
    msg = await ctx.send(embed=embed)

    await msg.add_reaction('✅')
    await msg.add_reaction('❌')


@client.command()
async def wiki(ctx, query=None):
  if query == None:
    await ctx.send("Please the thing to search")

  else:
    try:
      query = wikipedia.summary(query, sentences=3)
      await ctx.send(query)
    except:
      await ctx.send("No search results found")


# @client.command()
# async def alarm(ctx, hour: int, minute: int, am_pm):
#   if am_pm == "pm" or am_pm == "Pm" or am_pm == "PM" or am_pm == "pM":
#     hour += 12

#   running_alarm = 1
#   while running_alarm == 1:
#     if hour == datetime.datetime.now().hour and minute == datetime.datetime.now().minute:
#       await ctx.send("Time is up")
#       break


@client.command()
async def gif(ctx, *, q="smile"):
  api_key = 'GbgR3AzbSmoPxGmhnrLQvUIQcOWRFIBw'
  api_instance = giphy_client.DefaultApi()

  try:

    api_response = api_instance.gifs_search_get(api_key, q, limit=5, rating='g')
    lst = list(api_response.data)
    giff = random.choice(lst)

    emb = discord.Embed(title=q)
    emb.set_image(url=f'https://media.giphy.com/media/{giff.id}/giphy.gif')

    await ctx.channel.send(embed=emb)

  except ApiException as e:
    print("Exception when calling DefaultApi->gifs_search_get: %s\n" % e)


@client.command()
async def createemoji(ctx, url: str=None, *, name=None):
  if url == None:
    await ctx.send("Please enter the url of the image")
  elif name == None:
    await ctx.send("Please enter the name of the emoji")
  else:
    guild = ctx.guild
    if ctx.author.guild_permissions.manage_emojis:
      async with aiohttp.ClientSession() as ses:
        async with ses.get(url) as r:

          try:
            img_or_gif = BytesIO(await r.read())
            b_value = img_or_gif.getvalue()
            if r.status in range(200, 299):
              emoji = await guild.create_custom_emoji(image=b_value, name=name)
              await ctx.send(f'Successfully created emoji: <:{name}:{emoji.id}>')
              await ses.close()
            else:
              await ctx.send(f'Error when making request | {r.status} response.')
              await ses.close()

          except discord.HTTPException:
            await ctx.send('File size is too big!')


@client.command()
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, role: discord.Role=None, user: discord.Member=None):
  if role == None:
    await ctx.send("Please enter the role")
  elif user == None:
    await ctx.send("Please enter the user")
  elif ctx.author.guild_permissions.administrator:
    await user.add_roles(role)
    embed = discord.Embed(title=f'Successfully given {role} to {user}',
                          colour=discord.Colour.purple())
    await ctx.send(embed=embed)


@client.command()
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, role: discord.Role=None, user: discord.Member=None):
  if role == None:
    await ctx.send("Please enter the role")
  elif user == None:
    await ctx.send("Please enter the user")
  elif ctx.author.guild_permissions.administrator:
    await user.remove_roles(role)
    embed = discord.Embed(title=f'Successfully removed {role} from {user}',
                          colour=discord.Colour.purple())
    await ctx.send(embed=embed)


@client.command()
async def clear(ctx, amount=5):
  await ctx.channel.purge(limit=amount)
  await ctx.send(f"{amount} messages cleared")


@client.command()
async def userinfo(ctx, member: discord.Member = None):
  member = ctx.author if not member else member
  roles = [role for role in member.roles]

  embed = discord.Embed(colour=member.color, timestamp=ctx.message.created_at)

  embed.set_author(name=f'User info - {member}')
  embed.set_thumbnail(url=member.avatar_url)
  embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)

  embed.add_field(name="Id:", value=member.id)
  embed.add_field(name="Guild name:", value=member.display_name)
  embed.add_field(name="Created at:", value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))

  embed.add_field(name="Joined at:", value=member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))
  embed.add_field(name=f"Roles ({len(roles)})", value=" ".join([role.mention for role in roles]))
  embed.add_field(name="Top roles:", value=member.top_role.mention)

  embed.add_field(name="Bot?", value=member.bot)

  await ctx.send(embed=embed)


@client.command(pass_context=True)
async def changenickname(ctx, member: discord.Member=None, nick=None):
  if member == None:
    await ctx.send("Please enter the user")
  elif nick == None:
    await ctx.send("Please enter the nickname")
  else:
     await member.edit(nick=nick)
     await ctx.send(f'Nickname was changed for {member.mention} ')


@client.command()
async def tictactoe(ctx, p1: discord.Member, p2: discord.Member):
    global count
    global player1
    global player2
    global turn
    global gameOver

    if gameOver:
        global board
        board = [":white_large_square:", ":white_large_square:", ":white_large_square:",
                 ":white_large_square:", ":white_large_square:", ":white_large_square:",
                 ":white_large_square:", ":white_large_square:", ":white_large_square:"]
        turn = ""
        gameOver = False
        count = 0

        player1 = p1
        player2 = p2

        # print the board
        line = ""
        for x in range(len(board)):
            if x == 2 or x == 5 or x == 8:
                line += " " + board[x]
                await ctx.send(line)
                line = ""
            else:
                line += " " + board[x]

        # determine who goes first
        num = random.randint(1, 2)
        if num == 1:
            turn = player1
            await ctx.send("It is <@" + str(player1.id) + ">'s turn.")
        elif num == 2:
            turn = player2
            await ctx.send("It is <@" + str(player2.id) + ">'s turn.")
    else:
        await ctx.send("A game is already in progress! Finish it before starting a new one.")

@client.command()
async def place(ctx, pos: int):
    global turn
    global player1
    global player2
    global board
    global count
    global gameOver

    if not gameOver:
        mark = ""
        if turn == ctx.author:
            if turn == player1:
                mark = ":regional_indicator_x:"
            elif turn == player2:
                mark = ":o2:"
            if 0 < pos < 10 and board[pos - 1] == ":white_large_square:" :
                board[pos - 1] = mark
                count += 1

                # print the board
                line = ""
                for x in range(len(board)):
                    if x == 2 or x == 5 or x == 8:
                        line += " " + board[x]
                        await ctx.send(line)
                        line = ""
                    else:
                        line += " " + board[x]

                checkWinner(winningConditions, mark)
                print(count)
                if gameOver == True:
                    await ctx.send(mark + " wins!")
                elif count >= 9:
                    gameOver = True
                    await ctx.send("It's a tie!")

                # switch turns
                if turn == player1:
                    turn = player2
                elif turn == player2:
                    turn = player1
            else:
                await ctx.send("Be sure to choose an integer between 1 and 9 (inclusive) and an unmarked tile.")
        else:
            await ctx.send("It is not your turn.")
    else:
        await ctx.send("Please start a new game using the !tictactoe command.")


def checkWinner(winningConditions, mark):
    global gameOver
    for condition in winningConditions:
        if board[condition[0]] == mark and board[condition[1]] == mark and board[condition[2]] == mark:
            gameOver = True

@tictactoe.error
async def tictactoe_error(ctx, error):
    print(error)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please mention 2 players for this command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Please make sure to mention/ping players (ie. <@688534433879556134>).")

@place.error
async def place_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please enter a position you would like to mark.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Please make sure to enter an integer.")

@client.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member=None, *, reason=None):
  if member == None:
    await ctx.send("Please enter the user")
  else:
    await member.kick(reason=reason)
    await ctx.send(f'Kicked {member.mention}')

@client.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member=None, *, reason=None):
  if member == None:
    await ctx.send("Please enter the user")
  else:
    await member.ban(reason=reason)
    await ctx.send(f'Banned {member.mention}')

@client.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member=None):
  if member == None:
    await ctx.send("Please enter the user")
  else:

    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
      user = ban_entry.user

    if (user.name, user.discriminator) == (member_name, member_discriminator):
      await ctx.guild.unban(user)
      await ctx.send(f'Unbanned {user.mention}')
      return

@client.command(description="Mutes the specified user.")
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    guild = ctx.guild
    mutedRole = discord.utils.get(guild.roles, name="Muted")

    if not mutedRole:
        mutedRole = await guild.create_role(name="Muted")

        for channel in guild.channels:
            await channel.set_permissions(mutedRole, speak=False, send_messages=False, read_message_history=True, read_messages=False)

    await member.add_roles(mutedRole, reason=reason)
    await ctx.send(f"Muted {member.mention} for reason {reason}")
    await member.send(f"You were muted in the server {guild.name} for {reason}")

@client.command(description="Unmutes a specified user.")
@commands.has_permissions(manage_messages=True)
async def unmute(ctx, member: discord.Member):
    mutedRole = discord.utils.get(ctx.guild.roles, name="Muted")

    await member.remove_roles(mutedRole)
    await ctx.send(f"Unmuted {member.mention}")
    await member.send(f"You were unmuted in the server {ctx.guild.name}")


@client.command(description="Gets the bot's latency.")
async def ping(ctx):
    latency = round(client.latency * 1000, 1)
    await ctx.send(f"Pong! {latency}ms")

@client.command()
async def avatar(ctx, member : discord.Member = None):

  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]

  if member is None:
    embed = discord.Embed(title=f"This command is used like this: ```{pre}avatar [member]```", colour=0xff0000, timestamp=ctx.message.created_at)
    await ctx.send(embed=embed)
    return

  else:
    embed2 = discord.Embed(title=f"{member}'s Avatar!", colour=0x0000ff, timestamp=ctx.message.created_at)
    embed2.add_field(name="Animated?", value=member.is_avatar_animated())
    embed2.set_image(url=member.avatar_url)
    await ctx.send(embed=embed2)

@client.command()
async def createrole(ctx, name=None, r: int=0, g: int=0, b: int=0):
  if name == None:
    await ctx.send("Please enter the name of the role.")
  else:
    guild = ctx.guild
    await guild.create_role(name=name, colour=discord.Color.from_rgb(r, g, b))
    await ctx.send(f"{name} role created successfully")

@client.command()
async def deleterole(ctx, name=None):
  if name == None:
    await ctx.send("Please enter the name of the role.")
  else:
    role_object = discord.utils.get(ctx.message.guild.roles, name=name)
    await role_object.delete()
    await ctx.send(f"{name} role deleted successfully")


@client.command()
async def wanted(ctx, user: discord.Member = None):
  if user == None:
    user = ctx.author

  wanted = Image.open("wanted.jpg")

  asset = user.avatar_url_as(size=128)
  data = BytesIO(await asset.read())
  pfp = Image.open(data)

  pfp = pfp.resize((177, 177))

  wanted.paste(pfp, (120, 212))
  wanted.save("profile.jpg")

  await ctx.send(file=discord.File("profile.jpg"))

@client.command()
async def trivia(ctx):
  URL = 'https://www.opinionstage.com/blog/trivia-questions/'
  page = requests.get(URL)
  questions = []
  soup = BeautifulSoup(page.content, 'html.parser')
  r = requests.get(URL, stream=True)
  for line in r.iter_lines():
    if "<p><strong>" in str(line):
      line = line.decode("utf-8")
      linesplit = line.split(".")
      theq = linesplit[1]
      theq = theq.replace("</strong></p>", "")
      questions.append(theq)
  question = random.choice(questions)
  ps = soup.find_all('p')
  for p in ps:
    if question in str(p):
      index = ps.index(p)
      answer = ps[index + 1]
      await ctx.send(question)
      answer = str(answer)
      answer = answer.replace("<p>Answer: ", "")
      answer = answer.replace("</p>", "")
      await ctx.send("`Enter your answer\nYou only have 30 seconds to do it!`")
      def check(m):
        if m.channel.id == ctx.channel.id:
          return ctx.author.id == m.author.id
        return False
      guess = await client.wait_for("message", timeout=30, check=check)
      if guess.content.lower() == answer.lower():
        await ctx.send("`You got it correct!`")
      else:
        await ctx.send("`You got it wrong!`")

@client.command()
async def guess(ctx, num: int=None):
  if num == None:
    await ctx.send("Please guess a number")

  if num < 0 or num > 5:
    await ctx.send("`guess a number between 1 and 5`")

  else:
    a = random.choice([1,2,3,4,5])
    if num == a:
      await ctx.send("`Correct!`")
    else:
      await ctx.send(f"`Better luck next time! {a} was the number`")

@client.command(help="Play with .rps [your choice]")
async def rps(ctx):
    rpsGame = ['rock', 'paper', 'scissors']
    await ctx.send(f"Rock, paper, or scissors? Choose wisely...")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() in rpsGame

    user_choice = (await client.wait_for('message', check=check)).content

    comp_choice = random.choice(rpsGame)
    if user_choice == 'rock':
        if comp_choice == 'rock':
            await ctx.send(f'Well, that was weird. We tied.\nYour choice: {user_choice}\nMy choice: {comp_choice}')
        elif comp_choice == 'paper':
            await ctx.send(f'Nice try, but I won that time!!\nYour choice: {user_choice}\nMy choice: {comp_choice}')
        elif comp_choice == 'scissors':
            await ctx.send(f"Aw, you beat me. It won't happen again!\nYour choice: {user_choice}\nMy choice: {comp_choice}")

    elif user_choice == 'paper':
        if comp_choice == 'rock':
            await ctx.send(f'The pen beats the sword? More like the paper beats the rock!!\nYour choice: {user_choice}\nMy choice: {comp_choice}')
        elif comp_choice == 'paper':
            await ctx.send(f'Oh, wacky. We just tied. I call a rematch!!\nYour choice: {user_choice}\nMy choice: {comp_choice}')
        elif comp_choice == 'scissors':
            await ctx.send(f"Aw man, you actually managed to beat me.\nYour choice: {user_choice}\nMy choice: {comp_choice}")

    elif user_choice == 'scissors':
        if comp_choice == 'rock':
            await ctx.send(f'HAHA!! I JUST CRUSHED YOU!! I rock!!\nYour choice: {user_choice}\nMy choice: {comp_choice}')
        elif comp_choice == 'paper':
            await ctx.send(f'Bruh. >: |\nYour choice: {user_choice}\nMy choice: {comp_choice}')
        elif comp_choice == 'scissors':
            await ctx.send(f"Oh well, we tied.\nYour choice: {user_choice}\nMy choice: {comp_choice}")

@client.command(brief="Random picture of a meow")
async def cat(ctx):
  async with ctx.channel.typing():
    async with aiohttp.ClientSession() as cs:
      async with cs.get("http://aws.random.cat/meow") as r:
        data = await r.json()

        embed = discord.Embed(title="Meow")
        embed.set_image(url=data['file'])
        embed.set_footer(text="http://random.cat/")

        await ctx.send(embed=embed)

@client.command(brief="Random picture of a woof")
async def dog(ctx):
  async with ctx.channel.typing():
    async with aiohttp.ClientSession() as cs:
      async with cs.get("https://random.dog/woof.json") as r:
        data = await r.json()

        embed = discord.Embed(title="Woof")
        embed.set_image(url=data['url'])
        embed.set_footer(text="http://random.dog/")

        await ctx.send(embed=embed)

@client.command(brief="Random picture of a floofy")
async def fox(ctx):
  async with ctx.channel.typing():
    async with aiohttp.ClientSession() as cs:
      async with cs.get("https://randomfox.ca/floof/") as r:
        data = await r.json()

        embed = discord.Embed(title="Floof")
        embed.set_image(url=data['image'])
        embed.set_footer(text="https://randomfox.ca/")

        await ctx.send(embed=embed)


@client.command(name="slap", aliases=["hit"])
async def slap_member(ctx, member: discord.Member=None, *, reason=None):
  if member == None:
    await ctx.send("Please enter the user")
  else:
    await ctx.send(f"{ctx.author.display_name} slapped {member.mention} for {reason}!")


@slap_member.error
async def slap_member_error(ctx, exc):
  if isinstance(exc, commands.BadArgument):
    await ctx.send("I can't find that member.")



@client.command(name="fact")


@commands.cooldown(3, 5, BucketType.guild)
async def animal_fact(ctx, animal: str):
  if (animal := animal.lower()) in ("dog", "cat", "panda", "fox", "bird", "koala", "racoon", "kangaroo"):
    fact_url = f"https://some-random-api.ml/facts/{animal}"
    image_url = f"https://some-random-api.ml/img/{'birb' if animal == 'bird' else animal}"

    async with request("GET", image_url, headers={}) as response:
      if response.status == 200:
        data = await response.json()
        image_link = data["link"]

      else:
        image_link = None

    async with request("GET", fact_url, headers={}) as response:
      if response.status == 200:
        data = await response.json()

        embed = discord.Embed(title=f"{animal.title()} fact",
                      description=data["fact"],
                      colour=ctx.author.colour)
        if image_link is not None:
          embed.set_image(url=image_link)
        await ctx.send(embed=embed)

      else:
        await ctx.send(f"API returned a {response.status} status.")

  else:
    await ctx.send("No facts are available for that animal.")

numbers = ("1️⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟")

@client.command()
async def poll(ctx, que=None, option1=None, option2=None, option3=None, option4=None):
  if que == None:
    await ctx.send("Please enter the question..")
  elif option1 == None and option2 == None and option3 == None and option4 == None:
    await ctx.channel.purge(limit=1)
    msg = discord.Embed(title="Poll: ", description=f"{que}\n", colour=ctx.author.colour, timestamp=ctx.message.created_at)
    msg.set_footer(text=f"\nPoll by {ctx.author}")
    message = await ctx.send(embed=msg)
    await message.add_reaction('❎')
    await message.add_reaction('✅')
  elif option2 == None and option3 == None and option4 == None:
    await ctx.channel.purge(limit=1)
    msg = discord.Embed(title="Poll: ", description=f"{que}\n\n1️⃣ = {option1}\n", colour=ctx.author.colour, timestamp=ctx.message.created_at)
    msg.set_footer(text=f"\nPoll by {ctx.author}")
    message = await ctx.send(embed=msg)
    await message.add_reaction('1️⃣')

  elif option3 == None and option4 == None:
    await ctx.channel.purge(limit=1)
    msg = discord.Embed(title="Poll: ", description=f"{que}\n\n1️⃣ = {option1}\n\n2⃣ = {option2}", colour=ctx.author.colour, timestamp=ctx.message.created_at)
    msg.set_footer(text=f"\nPoll by {ctx.author}")
    message = await ctx.send(embed=msg)
    await message.add_reaction('1️⃣')
    await message.add_reaction('2⃣')

  elif option4 == None:
    await ctx.channel.purge(limit=1)
    msg = discord.Embed(title="Poll: ", description=f"{que}\n\n1️⃣ = {option1}\n\n2⃣ = {option2}\n\n3⃣ = {option3}", colour=ctx.author.colour, timestamp=ctx.message.created_at)
    msg.set_footer(text=f"\nPoll by {ctx.author}")
    message = await ctx.send(embed=msg)
    await message.add_reaction('1️⃣')
    await message.add_reaction('2⃣')
    await message.add_reaction('3⃣')

  else:
    await ctx.channel.purge(limit=1)
    msg = discord.Embed(title="Poll: ", description=f"{que}\n\n1️⃣ = {option1}\n\n2⃣ = {option2}\n\n3⃣ = {option3}\n\n4⃣ = {option4}", colour=ctx.author.colour, timestamp=ctx.message.created_at)
    msg.set_footer(text=f"\nPoll by {ctx.author}")
    message = await ctx.send(embed=msg)
    await message.add_reaction('1️⃣')
    await message.add_reaction('2⃣')
    await message.add_reaction('3⃣')
    await message.add_reaction('4⃣')


@client.command()
@commands.has_permissions(manage_channels = True)
async def lockdown(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False, read_messages=False)
    await ctx.send( ctx.channel.mention + " ***is now in lockdown.***")

@client.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True, read_messages=True)
    await ctx.send(ctx.channel.mention + " ***has been unlocked.***")


@client.command()
async def dm(ctx, user_id=None, *, args=None):
  if user_id != None and args != None:
    try:
      target = await client.fetch_user(user_id)
      await target.send(args)

      await ctx.channel.send("'" + args + "' sent to: " + target.name)

    except:
      await ctx.channel.send("Couldn't dm the given user.")
        

  else:
    await ctx.channel.send("You didn't provide a user's id and/or a message.")

@client.event
async def on_message_delete(message):
    client.sniped_messages[message.guild.id] = (message.content, message.author, message.channel.name, message.created_at)

@client.command()
async def snipe(ctx):
    try:
        contents, author, channel_name, time = client.sniped_messages[ctx.guild.id]
        
    except:
        await ctx.channel.send("Couldn't find a message to snipe!")
        return

    embed = discord.Embed(description=contents, color=discord.Color.purple(), timestamp=time)
    embed.set_author(name=f"{author.name}#{author.discriminator}", icon_url=author.avatar_url)
    embed.set_footer(text=f"Deleted in : #{channel_name}")
    await ctx.send(embed=embed)

@client.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member=None, *, reason=None):
  if member is None:
    return await ctx.send("The provided member could not be found or you forgot to provide one.")
        
  if reason is None:
    return await ctx.send("Please provide a reason for warning this user.")

  try:
    first_warning = False
    client.warnings[ctx.guild.id][member.id][0] += 1
    client.warnings[ctx.guild.id][member.id][1].append((ctx.author.id, reason))

  except KeyError:
    first_warning = True
    client.warnings[ctx.guild.id][member.id] = [1, [(ctx.author.id, reason)]]

  count = client.warnings[ctx.guild.id][member.id][0]

  async with aiofiles.open(f"{ctx.guild.id}.txt", mode="a") as file:
    await file.write(f"{member.id} {ctx.author.id} {reason}\n")

  await ctx.send(f"{member.mention} has {count} {'warning' if first_warning else 'warnings'}.")

@client.command()
@commands.has_permissions(administrator=True)
async def warnings(ctx, member: discord.Member=None):
  if member is None:
    return await ctx.send("The provided member could not be found or you forgot to provide one.")
    
  embed = discord.Embed(title=f"Displaying Warnings for {member.name}", description="", colour=discord.Colour.red())
  try:
    i = 1
    for admin_id, reason in client.warnings[ctx.guild.id][member.id][1]:
      admin = ctx.guild.get_member(admin_id)
      embed.description += f"**Warning {i}** given by: {admin.mention} for: *'{reason}'*.\n"
      i += 1

    await ctx.send(embed=embed)

  except KeyError: # no warnings
    await ctx.send("This user has no warnings.")

@client.command(name='top_role', aliases=['toprole'])
@commands.guild_only()
async def show_toprole(ctx, *, member: discord.Member=None):
  """Simple command which shows the members Top Role."""

  if member is None:
    member = ctx.author

  await ctx.send(f'The top role for `{member.display_name}` is`{member.top_role.name}`')



@client.command(name='perms', aliases=['perms_for', 'permissions'])
@commands.guild_only()
async def check_permissions(ctx, *, member: discord.Member=None):
  """A simple command which checks a members Guild Permissions.
  If member is not provided, the author will be checked."""

  if not member:
    member = ctx.author

        # Here we check if the value of each permission is True.
  perms = '\n'.join(perm for perm, value in member.guild_permissions if value)

        # And to make it look nice, we wrap it in an Embed.
  embed = discord.Embed(title='Permissions for:', description=ctx.guild.name, colour=member.colour)
  embed.set_author(icon_url=member.avatar_url, name=str(member))

        # \uFEFF is a Zero-Width Space, which basically allows us to have an empty field name.
  embed.add_field(name='\uFEFF', value=perms)

  await ctx.send(content=None, embed=embed)
        # Thanks to Gio for the Command.

@client.command()
async def joke(ctx, name=None):
  try:
    joke = await rs.get_joke(name)
    await ctx.send(joke) 
  except:
    await ctx.send("There are only four types of joke - any, dev, spooky, pun")

@client.command()
async def lol(ctx, name=None):
  try:
    joke = await rs.get_image(name)
    await ctx.send(joke) 
  except:
    await ctx.send("There are only nine types of funny images/gifs/videos - aww, dog, cat, memes, dankmemes, holup, art, harrypottermemes, facepalm")

@client.command(name="emojiinfo", aliases=["ei"])
async def emoji_info(ctx, emoji: discord.Emoji = None):
  if not emoji:
    return await ctx.invoke("I cannot find this emoji")

  try:
    emoji = await emoji.guild.fetch_emoji(emoji.id)
  except discord.NotFound:
    return await ctx.send("I could not find this emoji in the given guild.")

  is_managed = "Yes" if emoji.managed else "No"
  is_animated = "Yes" if emoji.animated else "No"
  requires_colons = "Yes" if emoji.require_colons else "No"
  creation_time = emoji.created_at.strftime("%I:%M %p %B %d, %Y")
  can_use_emoji = (
  "Everyone"
  if not emoji.roles
  else " ".join(role.name for role in emoji.roles)
  )

  description = f"""
  **General:**
  **- Name:** {emoji.name}
  **- Id:** {emoji.id}
  **- URL:** [Link To Emoji]({emoji.url})
  **- Author:** {emoji.user.mention}
  **- Time Created:** {creation_time}
  **- Usable by:** {can_use_emoji}
        
  **Other:**
  **- Animated:** {is_animated}
  **- Managed:** {is_managed}
  **- Requires Colons:** {requires_colons}
  **- Guild Name:** {emoji.guild.name}
  **- Guild Id:** {emoji.guild.id}
  """

  embed = discord.Embed(
  title=f"**Emoji Information for:** `{emoji.name}`",
  description=description,
  colour=0xADD8E6,
  )
  embed.set_thumbnail(url=emoji.url)
  await ctx.send(embed=embed)

@client.command(
        name="stats", description="A useful command that displays bot statistics."
    )
async def stats(ctx):
  pythonVersion = platform.python_version()
  dpyVersion = discord.__version__
  serverCount = len(client.guilds)
  memberCount = len(set(client.get_all_members()))

  embed = discord.Embed(
  title=f"{client.user.name} Stats",
  description="\uFEFF",
  colour=ctx.author.colour,
  timestamp=ctx.message.created_at,
  )
  embed.add_field(name="Bot Version:", value=client.version)
  embed.add_field(name="Python Version:", value=pythonVersion)
  embed.add_field(name="Discord.Py Version", value=dpyVersion)
  embed.add_field(name="Total Guilds:", value=serverCount)
  embed.add_field(name="Total Users:", value=memberCount)
  embed.add_field(name="Bot Developer:", value="<@759713469816766485>")

  embed.set_footer(text=f"{client.user.name}")
  embed.set_author(name=client.user.name, icon_url=client.user.avatar_url)

  await ctx.send(embed=embed)

@client.command(name="serverinfo", aliases=["guildinfo", "si", "gi"])
async def server_info(ctx):
  embed = discord.Embed(title="Server information",
  colour=ctx.guild.owner.colour,
  timestamp=datetime.datetime.utcnow())
  embed.set_thumbnail(url=ctx.guild.icon_url)

  statuses = [len(list(filter(lambda m: str(m.status) == "online", ctx.guild.members))),
  len(list(filter(lambda m: str(m.status) == "idle", ctx.guild.members))),
  len(list(filter(lambda m: str(m.status) == "dnd", ctx.guild.members))),
  len(list(filter(lambda m: str(m.status) == "offline", ctx.guild.members)))]

  f = [("ID", ctx.guild.id, True),
        ("Owner", ctx.guild.owner, True),
        ("Region", ctx.guild.region, True),
        ("Created at", ctx.guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), True),
        ("Members", len(ctx.guild.members), True),
        ("Humans", len(list(filter(lambda m: not m.bot, ctx.guild.members))), True),
        ("Bots", len(list(filter(lambda m: m.bot, ctx.guild.members))), True),
        ("Banned members", len(await ctx.guild.bans()), True),
        ("Statuses", f"🟢 {statuses[0]} 🟠 {statuses[1]} 🔴 {statuses[2]} ⚪ {statuses[3]}", True),
        ("Text channels", len(ctx.guild.text_channels), True),
        ("Voice channels", len(ctx.guild.voice_channels), True),
        ("Categories", len(ctx.guild.categories), True),
        ("Roles", len(ctx.guild.roles), True),
        ("Invites", len(await ctx.guild.invites()), True),
        ("\u200b", "\u200b", True)]
  for name, value, inline in f:
    embed.add_field(name=name, value=value, inline=inline)

  await ctx.send(embed=embed)

@client.command()
async def dice(ctx):
  roll = random.choice([1, 2, 3, 4, 5, 6])
  await ctx.send(roll)

@client.command()
async def color(ctx, r: int, g: int, b: int):
  img = Image.open("whitedpy.jpg")

  font = ImageFont.truetype("RobotoSlab-ExtraBold.ttf", 80)

  draw = ImageDraw.Draw(img)

  draw.text((85, 290), f"({r}, {g}, {b})", (r, g, b), font=font)

  img.save("color.jpg")

  await ctx.send(file=discord.File("color.jpg"))

@client.command(aliases=['8ball'])
async def basically(ctx, que=None):
  if que != None:
    await ctx.send( random.choice(["It is certain :8ball:",
                                                                     "It is decidedly so :8ball:",
                                                                     "Without a doubt :8ball:",
                                                                     "Yes, definitely :8ball:",
                                                                     "You may rely on it :8ball:",
                                                                     "As I see it, yes :8ball:",
                                                                     "Most likely :8ball:",
                                                                     "Outlook good :8ball:",
                                                                     "Yes :8ball:",
                                                                     "Signs point to yes :8ball:",
                                                                     "Reply hazy try again :8ball:",
                                                                     "Ask again later :8ball:",
                                                                     "Better not tell you now :8ball:",
                                                                     "Cannot predict now :8ball:",
                                                                     "Concentrate and ask again :8ball:",
                                                                     "Don't count on it :8ball:",
                                                                     "My reply is no :8ball:",
                                                                     "My sources say no :8ball:",
                                                                     "Outlook not so good :8ball:",
                                                                     "Very doubtful :8ball:"]))

  else:
    await ctx.send("Please enter the question")

@client.command()
async def rainbow(ctx): 
    
  cols = [0x32a852, 0x3296a8, 0xb700ff, 0x9232a8, 0xa8326f, 0xf25207, 0x3efa00, 0xfa0000, 0xf28fe0, 0x8fd9f2, 0x122eff, 0x05ff4c, 0xfff129, 0xffffff]
  embed = discord.Embed(
      title = "RAINBOW",
      color = random.choice(cols)
  )

  msg = await ctx.send(embed=embed)

  for i in range(1000):
    embed2 = discord.Embed(
      title = "RAINBOW",
      color = random.choice(cols)
    )
    await asyncio.sleep(0.1)
    await msg.edit(embed=embed2)

@client.command()
async def yt(ctx, *, search=None):
  
  if search != None:
    search = search.replace(' ', '')
    try:
      html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={search}")

      vid_id = re.findall(r"watch\?v=(\S{11})", html.read().decode())

      await ctx.send("https://www.youtube.com/watch?v=" + vid_id[0])

    except:
      await ctx.send(f"Sorry I cannot find {search} youtube video")

  else:
    await ctx.send("Please enter the name of the youtube video")

@client.command()
async def create_invite(ctx):
  """Create instant invite"""
  link = await ctx.channel.create_invite(max_age = 300)
  await ctx.send(link)

@client.command()
async def roles(ctx):
    await ctx.send(", ".join([str(r) for r in ctx.guild.roles]))

@client.command()
async def tts(ctx, msg=None):
  if msg == None:
    await ctx.send("Please enter the message")
  else:
    await ctx.send(msg, tts=True)
     
@client.command()
async def rip(ctx, user: discord.Member = None):
  if user == None:
    user = ctx.author

  rip = Image.open("rip.jpg")

  asset = user.avatar_url_as(size=128)
  data = BytesIO(await asset.read())
  pfp = Image.open(data)

  pfp = pfp.resize((79, 74))

  rip.paste(pfp, (60, 129))
  rip.save("prip.jpg")

  await ctx.send(file=discord.File("prip.jpg"))

@client.command()
async def kill(ctx, user: discord.Member, user1: discord.Member):
  kill = Image.open("kill.jpg")

  asset = user.avatar_url_as(size=128)
  data = BytesIO(await asset.read())
  pfp = Image.open(data)

  asset1 = user1.avatar_url_as(size=128)
  data1 = BytesIO(await asset1.read())
  pfp1 = Image.open(data1)

  pfp1 = pfp1.resize((81, 81))

  pfp = pfp.resize((79, 74))
  kill.paste(pfp, (529, 589))
  kill.paste(pfp1, (169, 73))

  kill.save("pkill.jpg")
  await ctx.send(file=discord.File("pkill.jpg"))
  await ctx.send(f"`{user1}` killed `{user}`")

@client.command()
async def internetrules(ctx):
  """The rules of the internet"""
  await ctx.channel.trigger_typing()
  await ctx.send(file=discord.File("internetrules.txt"))

@client.command()
async def md5(ctx, *, msg:str=None):
  """Convert something to MD5"""
  if msg == None:
    await ctx.send("Please enter the text to convert into md5")
  else:
    await ctx.send("`{}`".format(hashlib.md5(bytes(msg.encode("utf-8"))).hexdigest()))\

@client.group(invoke_without_command=True)
async def help(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  t = "Help"
  em = discord.Embed(title=t, description=f"Use {pre}help <command> for extended information on a command", colour=discord.Colour.purple())

  em.add_field(name="Moderation", value="createtextchannel, createvoicechannel,   deletetextchannel, deletevoicechannel, addrole, removerole, kick, ban, unban, mute, unmute, createrole, deleterole, warn, warnings, lockdown, unlock")

  em.add_field(name="Miscellaneous", value="stats, si, changeprefix, announce, vote, poll, wiki, userinfo, changenickname, clear, ping, avatar, members, covid, perms, toprole, snipe, dm, tts",  inline=False)

  em.add_field(name="Fun", value="meme, quote, gif, createemoji, wanted, dog, cat, fox, eval, fact, slap, lol, joke, ei, color, 8ball, yt, rainbow, kill, rip, md5, internetrules", inline=False)

  em.add_field(name="Game", value="coin, tictactoe, trivia, guess, rps, dice")

  await ctx.send(embed=em)

@help.command()
async def createtextchannel(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="createtextchannel", description="creates a text channel")
  em.add_field(name="**Syntax**", value=f'{pre}createtextchannel <Name of the text channel>')
  await ctx.send(embed=em)

@help.command()
async def createvoicechannel(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="createvoicechannel", description="creates a voice channel")
  em.add_field(name="**Syntax**", value=f'{pre}createvoicechannel <Name of the voice channel>')
  await ctx.send(embed=em)

@help.command()
async def deletetextchannel(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="deletetextchannel", description="deletes a text channel")
  em.add_field(name="**Syntax**", value=f'{pre}deletetextchannel <Name of the text channel>')
  await ctx.send(embed=em)

@help.command()
async def deletevoicechannel(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="deletevoicechannel", description="deletes a voice channel")
  em.add_field(name="**Syntax**", value=f'{pre}deletevoicechannel <Name of the voice channel>')
  await ctx.send(embed=em)

@help.command()
async def addrole(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="addrole", description="gives a specific role to specific user")
  em.add_field(name="**Syntax**", value=f'{pre}addrole <Name of the role> <Name of the user>')
  await ctx.send(embed=em)

@help.command()
async def removerole(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="removerole", description="removes a specific role to specific user")
  em.add_field(name="**Syntax**", value=f'{pre}removerole <Name of the role> <Name of the user>')
  await ctx.send(embed=em)

@help.command()
async def announce(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="announce", description="announces a particular thing in a particular channel")
  em.add_field(name="**Syntax**", value=f'{pre}announce <Content of the announcement> <Name of the text channel>')
  await ctx.send(embed=em)

@help.command()
async def vote(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="vote", description="Opens a voting system")
  em.add_field(name="**Syntax**", value=f'{pre}vote <Content of the vote>')
  await ctx.send(embed=em)

@help.command()
async def wiki(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="wiki", description="searches a particular thing on wikipedia")
  em.add_field(name="**Syntax**", value=f'{pre}wiki <thing to search>')
  await ctx.send(embed=em)

# @help.command()
# async def alarm(ctx):
#   em = discord.Embed(title="alarm", description="sets an alarm")
#   em.add_field(name="**Syntax**", value='a?alarm <Hour> <Minute> <Am or pm>')
#   await ctx.send(embed=em)

@help.command()
async def userinfo(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="userinfo", description="displays user info")
  em.add_field(name="**Syntax**", value=f'{pre}userinfo <Name of the user>')
  await ctx.send(embed=em)

@help.command()
async def changenickname(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="changenickname", description="changes anyones nickname")
  em.add_field(name="**Syntax**", value=f'{pre}changenickname <Name of the user> <nickname>')
  await ctx.send(embed=em)

@help.command()
async def meme(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="meme", description="displays reddit memes")
  em.add_field(name="**Syntax**", value=f'{pre}meme')
  await ctx.send(embed=em)

# @help.command()
# async def spam(ctx):
#   with open("prefixes.json", "r") as f:
#     prefixes = json.load(f)

#   pre = prefixes[str(ctx.guild.id)]
#   em = discord.Embed(title="spam", description="repeates a particular thing a particular times")
#   em.add_field(name="**Syntax**", value=f'{pre}spam <times to repeat> <content to repeate>')
#   await ctx.send(embed=em)

@help.command()
async def quote(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="quote", description="displays zinquotes quotes")
  em.add_field(name="**Syntax**", value=f'{pre}quote')
  await ctx.send(embed=em)

@help.command()
async def gif(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="gif", description="displays giphy gifs")
  em.add_field(name="**Syntax**", value=f'{pre}gif <gif name>')
  await ctx.send(embed=em)

@help.command()
async def createemoji(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="createemoji", description="creates an emoji")
  em.add_field(name="**Syntax**", value=f'{pre}createemoji <url of the image> <name of the emoji>')
  await ctx.send(embed=em)

@help.command()
async def coin(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="coin", description="toss")
  em.add_field(name="**Syntax**", value=f'{pre}coin')
  await ctx.send(embed=em)

@help.command()
async def tictactoe(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="tictactoe", description="starts tictactoe game")
  em.add_field(name="**Syntax**", value=f'{pre}tictactoe <player 1 username> <player 2 username>, use a?place <num> to place X or 0 on the board')
  await ctx.send(embed=em)

@help.command()
async def kick(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="kick", description="kicks any member")
  em.add_field(name="**Syntax**", value=f'{pre}kick <Name of the user> <reason>')
  await ctx.send(embed=em)

@help.command()
async def ban(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="ban", description="bans any member")
  em.add_field(name="**Syntax**", value=f'{pre}ban <Name of the user> <reason>')
  await ctx.send(embed=em)

@help.command()
async def unban(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="unban", description="unbans any member")
  em.add_field(name="**Syntax**", value=f'{pre}unban <<Name of the user>#<discrminator>>')
  await ctx.send(embed=em)

@help.command()
async def mute(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="mute", description="mutes any member")
  em.add_field(name="**Syntax**", value=f'{pre}mute <Name of the user> <reason>')
  await ctx.send(embed=em)

@help.command()
async def unmute(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="unmute", description="unmutes any member")
  em.add_field(name="**Syntax**", value=f'{pre}unmute <Name of the user>')
  await ctx.send(embed=em)

@help.command()
async def clear(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="clear", description="deletes sepcific amount of messages")
  em.add_field(name="**Syntax**", value=f'{pre}clear <Number of messages>')
  await ctx.send(embed=em)

@help.command()
async def ping(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="ping", description="displays the ping of the bot")
  em.add_field(name="**Syntax**", value=f'{pre}ping')
  await ctx.send(embed=em)

@help.command()
async def avatar(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="avatar", description="displays the avatar of the user")
  em.add_field(name="**Syntax**", value=f'{pre}avatar <user>')
  await ctx.send(embed=em)

@help.command()
async def createrole(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="createrole", description="creates a role")
  em.add_field(name="**Syntax**", value=f'{pre}createrole <name> <r> <g> <b>')
  await ctx.send(embed=em)

@help.command()
async def deleterole(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="deleterole", description="deletes a role")
  em.add_field(name="**Syntax**", value=f'{pre}deleterole <name>')
  await ctx.send(embed=em)
  

@help.command()
async def wanted(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="wanted", description="creates wanted image")
  em.add_field(name="**Syntax**", value=f'{pre}wanted <user>')
  await ctx.send(embed=em)

@help.command()
async def changeprefix(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="changeprefix", description="changes prefix")
  em.add_field(name="**Syntax**", value=f'{pre}changeprefix <prefix>')
  await ctx.send(embed=em)

@help.command()
async def members(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="members", description="displays number of members in a server")
  em.add_field(name="**Syntax**", value=f'{pre}members')
  await ctx.send(embed=em)

@help.command()
async def covid(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="covid", description="displays live status of covid-19")
  em.add_field(name="**Syntax**", value=f'{pre}covid <country name>')
  await ctx.send(embed=em)


@help.command()
async def trivia(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="trivia", description="starts trivia")
  em.add_field(name="**Syntax**", value=f'{pre}trivia')
  await ctx.send(embed=em)


@help.command()
async def guess(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="guess", description="starts guess game")
  em.add_field(name="**Syntax**", value=f'{pre}guess <number>')
  await ctx.send(embed=em)

@help.command()
async def rps(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="rps", description="starts rock paper sissor game")
  em.add_field(name="**Syntax**", value=f'{pre}rps')
  await ctx.send(embed=em)

@help.command()
async def dog(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="dog", description="displays images of dogs")
  em.add_field(name="**Syntax**", value=f'{pre}dog')
  await ctx.send(embed=em)

@help.command()
async def cat(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="cat", description="displays images of cats")
  em.add_field(name="**Syntax**", value=f'{pre}cat')
  await ctx.send(embed=em)

@help.command()
async def fox(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="fox", description="displays images of foxes")
  em.add_field(name="**Syntax**", value=f'{pre}fox')
  await ctx.send(embed=em)

@help.command()
async def eval(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="eval", description="execute arguments as a shell command")
  em.add_field(name="**Syntax**", value=f'{pre}eval')
  await ctx.send(embed=em)

@help.command()
async def fact(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="fact", description="animal facts")
  em.add_field(name="**Syntax**", value=f'{pre}fact <Animal name>')
  await ctx.send(embed=em)

@help.command()
async def slap(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="slap", description="slaps any user")
  em.add_field(name="**Syntax**", value=f'{pre}slap <user> <reason>')
  await ctx.send(embed=em)

@help.command()
async def poll(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="poll", description="creats a poll")
  em.add_field(name="**Syntax**", value=f'{pre}poll <question> <option1(optional)> <option2(optional)> <option3(optional)> <option4(optional)>')
  await ctx.send(embed=em)

@help.command()
async def lockdown(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="lockdown", description="sets a channel in lockdown mode")
  em.add_field(name="**Syntax**", value=f'{pre}lockdown')
  await ctx.send(embed=em)

@help.command()
async def unlock(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="unlock", description="sets a channel in unlock mode")
  em.add_field(name="**Syntax**", value=f'{pre}unlock')
  await ctx.send(embed=em)

@help.command()
async def dm(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="dm", description="sends private messages")
  em.add_field(name="**Syntax**", value=f'{pre}dm <user id> <message>')
  await ctx.send(embed=em)

@help.command()
async def snipe(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="snipe", description="displays deleted message")
  em.add_field(name="**Syntax**", value=f'{pre}snipe')
  await ctx.send(embed=em)

@help.command()
async def warn(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="warn", description="warns any user")
  em.add_field(name="**Syntax**", value=f'{pre}warn <user> <reason>')
  await ctx.send(embed=em)

@help.command()
async def warnings(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="warnings", description="displays user warnings")
  em.add_field(name="**Syntax**", value=f'{pre}warnings <user>')
  await ctx.send(embed=em)

@help.command()
async def joke(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="joke", description="displays jokes")
  em.add_field(name="**Syntax**", value=f'{pre}joke <joke type>')
  await ctx.send(embed=em)

@help.command()
async def lol(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="lol", description="diplays funny images/gifs/videos")
  em.add_field(name="**Syntax**", value=f'{pre}lol <type>')
  await ctx.send(embed=em)

@help.command()
async def perms(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="perms", description="displays anyones permissions")
  em.add_field(name="**Syntax**", value=f'{pre}perms <user>')
  await ctx.send(embed=em)

@help.command()
async def toprole(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="toprole", description="displays anyones toprole")
  em.add_field(name="**Syntax**", value=f'{pre}toprole <user>')
  await ctx.send(embed=em)

@help.command()
async def stats(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="stats", description="bot stats")
  em.add_field(name="**Syntax**", value=f'{pre}stats')
  await ctx.send(embed=em)

@help.command()
async def si(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="si", description="server info")
  em.add_field(name="**Syntax**", value=f'{pre}si')
  await ctx.send(embed=em)

@help.command()
async def dice(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="dice", description="rolls a dice")
  em.add_field(name="**Syntax**", value=f'{pre}dice')
  await ctx.send(embed=em)

@help.command()
async def color(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="color", description="displays image with that color")
  em.add_field(name="**Syntax**", value=f'{pre}color <r> <g> <b>')
  await ctx.send(embed=em)

@help.command(aliases=['8ball'])
async def magicball(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="8ball", description="8ball")
  em.add_field(name="**Syntax**", value=f'{pre}8ball <question>')
  await ctx.send(embed=em)

@help.command()
async def rainbow(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="rainbow", description="rainbow embed")
  em.add_field(name="**Syntax**", value=f'{pre}rainbow')
  await ctx.send(embed=em)

@help.command()
async def yt(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="yt", description="searches a thing on yt")
  em.add_field(name="**Syntax**", value=f'{pre}yt <thing to search>')
  await ctx.send(embed=em)

@help.command()
async def tts(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="tts", description="sends tts messages")
  em.add_field(name="**Syntax**", value=f'{pre}tts <message>')
  await ctx.send(embed=em)

@help.command()
async def kill(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="kill", description="creates kill image")
  em.add_field(name="**Syntax**", value=f'{pre}kill <user to be killed> <user to be the killer>')
  await ctx.send(embed=em)

@help.command()
async def rip(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="rip", description="creates rip image")
  em.add_field(name="**Syntax**", value=f'{pre}rip <user>')
  await ctx.send(embed=em)

@help.command()
async def md5(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="md5", description="converts some text to md5")
  em.add_field(name="**Syntax**", value=f'{pre}md5 <text to convert>')
  await ctx.send(embed=em)

@help.command()
async def internetrules(ctx):
  with open("prefixes.json", "r") as f:
    prefixes = json.load(f)

  pre = prefixes[str(ctx.guild.id)]
  em = discord.Embed(title="internetrules", description="internetrules")
  em.add_field(name="**Syntax**", value=f'{pre}internetrules')
  await ctx.send(embed=em)

# keep_alive()

client.run('BOT-TOKEN')
