import os
from dotenv import load_dotenv
from discord.ext import commands
import discord
from src import dice, game
import ruamel.yaml
import re


class KattoBotException(discord.ext.commands.errors.CommandError):
    """ General Exception to be caught and send to guild channel"""

    def __init__(self, msg):
        super().__init__(f"**KattoBotException:** {msg}")


class KattoBot(commands.Bot):
    """ Main bot """

    def __init__(self, d={}):
        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")
        self.guild_name = os.getenv("DISCORD_GUILD")

        intents = discord.Intents.default()
        intents.typing = False
        intents.presences = True
        intents.members = True
        intents.reactions = False

        super().__init__(intents=intents, command_prefix="!")

        self.game = game.Game()
        self.load_game()

    @staticmethod
    def _split_args_kwargs(l):
        d = {}
        for i in l:
            if re.match("\w+:\w+", i):
                k, v = i.split(":")
                d[k] = v

        return [i for i in l if not re.match("\w+:\w+", i)], d

    def _game_file_path(self, filepath):
        return f"{self.guild_name}_game.yaml" if not filepath else filepath

    def load_game(self, filepath=None):
        filepath = self._game_file_path(filepath)

        try:
            with open(filepath, "r") as f:
                self.game = yaml.load(f)
        except IOError:
            pass

    def save_game(self, filepath=None):
        filepath = self._game_file_path(filepath)
        print(filepath)
        with open(filepath, "w") as f:
            yaml.dump(self.game, f)

    def run(self):
        """ Run the bot and connect using the token in .env """
        super().run(self.token)

    def get_guild(self):
        """ Get the guild you are logged into """
        return discord.utils.get(self.guilds, name=self.guild_name)

    def get_online_members(self):
        """ Get online members that are not bots """
        guild = self.get_guild()
        return [
            i for i in guild.members if i.status == discord.Status.online and not i.bot
        ]

    def get_member(self, name):
        """ Get user from its name """
        guild = self.get_guild()

        members = [i for i in guild.members if name == i.display_name]
        if len(members) == 0:
            members = [i for i in guild.members if name in i.display_name]
        if len(members) == 0:
            name = name.lower()
            members = [i for i in guild.members if name == i.display_name.lower()]
        if len(members) == 0:
            members = [i for i in guild.members if name in i.display_name.lower()]

        if len(members) == 0:
            raise KattoBotException(f"No matches for member: `{name}`")
        if len(members) == 1:
            return members[0]
        else:
            names = ", ".join([f"`{i.name}` (`{i.nick}`)" for i in members])
            raise KattoBotException(
                f"Member name: `{name}` matches too many members: {names}"
            )

    async def on_ready(self):
        """ Report some data to show that it is really connected """
        guild = self.get_guild()
        print(
            f"{self.user} is connected to the following guild:\n"
            f"{guild.name}(id: {guild.id})"
        )

    async def send_to_member(self, ctx, msg, to0):
        """ Send private message to user """
        to0 = self.get_member(to0)
        await to0.send(
            f"`{ctx.author.display_name}` told me to send you this message:\n{msg}"
        )
        await ctx.send(f"I sent to `{to0.display_name}` this message:\n{msg}")


# Required for the following decorated functions
yaml = ruamel.yaml.YAML()
yaml.register_class(game.Game)
bot = KattoBot()


@bot.event
async def on_command_error(ctx, error):
    """ We catch the errors and print them in the chat """
    print(error)
    return await ctx.send(str(error))


@bot.command(name="r")
async def roll(ctx, *args):
    """Roll and sum results

    Args:
          ctx: context manager
          args: it is split in cmd, and to
            cmd: the command you want to compute
            to: send response privately to this user

    Example:
          Message in general chat:
              cmd: "2d5 + 3 [space for comments]"
              to: katta

          Answer:
              private message to katta:
                  [2d5: 2, 3] 5 + 3 [space for comments]
                  Result: 8
    """
    args, kwargs = KattoBot._split_args_kwargs(args)
    cmd = " ".join(args)
    to = kwargs.get("to", None)

    res = dice.roll(cmd, successes=False)
    if not to:
        await ctx.send(res)
    else:
        await ctx.bot.send_to_member(ctx, res, to)


@bot.command(name="rs")
async def roll_successes(ctx, *args):

    """Roll and sum results

    Args:
          ctx: context manager
          args: it is split in cmd, and to
            cmd: the command you want to compute
            to: send response privately to this user
    Example:
          Message in general chat:
              cmd: "2d5 + 3 [space for comments]"
              to: katta

          Answer:
              private message to katta:
                  [2d5: 2, 3] 5 + 3 [space for comments]
                  Result: 8
    """
    args, kwargs = KattoBot._split_args_kwargs(args)
    cmd = " ".join(args)
    to = kwargs.get("to", None)

    res = dice.roll(cmd, successes=True)
    if not to:
        await ctx.send(res)
    else:
        await ctx.bot.send_to_member(ctx, res, to)


@bot.command(name="members", aliases=["get_members"])
async def get_users(ctx):
    """ Get online members """

    s = [f"`{i.display_name}`" for i in ctx.bot.get_online_members()]
    s = "The online members are: " + ", ".join(s)
    await ctx.send(s)


# @bot.command("set_dm")
# async def set_dm(ctx, name):
#     ctx.bot.dm = ctx.bot.get_user(name)
#     await ctx.send(f"All heil to `{ctx.bot.dm.name}`, the new dungeon master!")

# @bot.command("get_dm")
# async def get_dm(ctx):
#     if ctx.bot.dm is None:
#         await ctx.send(f"Nobody is dungeon master")
#     else:
#         await ctx.send(f"`{ctx.bot.dm.name}` is the rightful dungeon master!")
#
# @bot.command("save")
# async def save(ctx):
#     filename = "kattoBot.pickle"
#
#     with open(filename, "w") as f:
#         pickle.dump(bot, f)
#
#     await ctx.send(f"KattoBot state was saved into `{filename}`")


if __name__ == "__main__":
    """ Run the bot """
    bot.run()
