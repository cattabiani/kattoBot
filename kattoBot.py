import os
from dotenv import load_dotenv
from discord.ext import commands
import discord
from src import dice
import re


class KattoBotException(discord.ext.commands.errors.CommandError):
    """ General Exception to be caught and send to guild channel"""

    def __init__(self, msg):
        super().__init__(f"**KattoBotException:** {msg}")


class KattoBot(commands.Bot):
    """ Main bot """

    def __init__(self):
        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")
        self.guild_name = os.getenv("DISCORD_GUILD")

        intents = discord.Intents.default()
        intents.typing = False
        intents.presences = False
        intents.members = True
        intents.reactions = False

        super().__init__(intents=intents, command_prefix="!")

    async def on_ready(self):
        """ Report some data to show that it is really connected """
        guild = discord.utils.get(self.guilds, name=self.guild_name)
        print(
            f"{self.user} is connected to the following guild:\n"
            f"{guild.name}(id: {guild.id})"
        )

    def run(self):
        """ Run the bot and connect using the token in .env """
        super().run(self.token)

    def get_user(self, name):
        """ Get user from its name """
        users = [i for i in self.users if name == i.name]
        if len(users) == 0:
            users = [i for i in self.users if name in i.name]

        if len(users) == 0:
            raise KattoBotException(f"No matches for user: `{name}`")
        if len(users) == 1:
            return users[0]
        else:
            names = ", ".join([i.name for i in users])
            raise KattoBotException(
                f"User name: `{name}` matches too many users: `{names}`"
            )

    async def send_to_user(self, msg, from0, to0):
        """ Send private message to user """
        user = self.get_user(to0)
        msg = f"`{from0}` told me to send you this message:\n\n" + msg
        await user.send(msg)


# Required for the following decorated functions
bot = KattoBot()


@bot.event
async def on_command_error(ctx, error):
    """ We catch the errors and print them in the chat """
    print(error)
    return await ctx.send(str(error))


@bot.command(name="r")
async def roll(ctx, cmd, reply_to=None):
    """Roll and sum results

    Args:
          ctx: context manager
          cmd: command to be rolled
          reply_to: send response privately to this user

    Example:
          Message in general chat:
              cmd: "2d5 + 3 [space for comments]"
              reply_to: katta

          Answer:
              private message to katta:
                  [2d5: 2, 3] 5 + 3 [space for comments]
                  Result: 8
    """
    res = dice.roll(cmd)
    if not reply_to:
        await ctx.send(res)
    else:
        await ctx.bot.send_to_user(res, ctx.author.name, reply_to)


@bot.command(name="rs")
async def roll_successes(ctx, cmd, reply_to=None):
    """Roll and sum results

    Same as for the roll command but for rolling successes. Used in vampires for example. Check roll_ndm for more
    information on this rolling method

    Args:
          ctx: context manager
          cmd: command to be rolled
          reply_to: send response privately to this user
    """
    cmd = cmd.strip()
    ms = re.match("\d+d\d+", cmd)
    if ms == None or ms.span()[0] != 0 or ms.span()[1] != len(cmd):
        raise KattoBotException(f"command {cmd} is not in the form: `int`d`int`")

    n, m = cmd.split("d")
    n = int(n)
    m = int(m)
    res = dice.format_roll_ndm_successes(n, m)
    if not reply_to:
        await ctx.send(res)
    else:
        await ctx.bot.send_to_user(res, ctx.author.name, reply_to)


if __name__ == "__main__":
    """ Run the bot """
    bot.run()
