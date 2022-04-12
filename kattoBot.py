import os
import random
import re

import discord
import ruamel.yaml
from discord.ext import commands, tasks
from dotenv import load_dotenv

from src import dice, game, character


class KattoBotException(discord.ext.commands.errors.CommandError):
    """ General Exception to be caught and send to guild channel"""

    def __init__(self, msg):
        super().__init__(f"**KattoBotException:** {msg}")


class ItemNotFound(KattoBotException):
    pass


class FoundTooManyItems(KattoBotException):
    pass


class KattoBot(commands.Bot):
    """ Main bot """

    def __init__(self, d={}):
        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")
        self.guild_name = os.getenv("DISCORD_GUILD")
        self.thread = None
        self.thread_continue = False

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
            members = [
                i for i in guild.members if name.lower() == i.display_name.lower()
            ]
        if len(members) == 0:
            members = [
                i for i in guild.members if name.lower() in i.display_name.lower()
            ]

        if len(members) == 0:
            raise ItemNotFound(f"No matches for member: `{name}`")
        if len(members) == 1:
            return members[0]
        else:
            names = ", ".join([f"`{i.name}` (`{i.nick}`)" for i in members])
            raise FoundTooManyItems(
                f"Member name: `{name}` matches too many members: {names}"
            )

    def get_channel(self, name):
        """ Get channel from its name """
        all_channels = self.get_guild().channels

        channels = [i for i in all_channels if name == i.name]
        if len(channels) == 0:
            channels = [i for i in all_channels if name in i.name]
        if len(channels) == 0:
            channels = [i for i in all_channels if name.lower() == i.name.lower()]
        if len(channels) == 0:
            channels = [i for i in all_channels if name.lower() in i.name.lower()]

        if len(channels) == 0:
            raise ItemNotFound(f"No matches for channel: `{name}`")
        if len(channels) == 1:
            return channels[0]
        else:
            names = ", ".join([f"`{i.name}`" for i in channels])
            raise FoundTooManyItems(
                f"Channel name: `{name}` matches too many channels: {names}"
            )

    def get_receiver(self, name):
        try:
            return self.get_member(name)
        except ItemNotFound:
            return self.get_channel(name)

    async def on_ready(self):
        """ Report some data to show that it is really connected """
        guild = self.get_guild()
        print(
            f"{self.user} is connected to the following guild:\n"
            f"{guild.name}(id: {guild.id})"
        )

    async def send_to(self, ctx, msg, to0, secret_sender):
        """ Send private message to user """

        if not to0:
            await ctx.send(msg)
            return

        to0 = self.get_receiver(to0)
        try:
            to0_name = to0.display_name
        except:
            to0_name = to0.name

        if not secret_sender:
            await to0.send(
                f"`{ctx.author.display_name}` told me to send you this message:\n{msg}"
            )
        else:
            await to0.send(msg)

        await ctx.send(f"I sent to `{to0_name}` this message:\n{msg}")

    @tasks.loop(seconds=3)
    async def loop_msg(self, ctx, msg, to0, range, secret_sender):
        """Send the same message over and over. Intervals can be random"""

        if range[0] < 0:
            range[0] = 3
        if range[1] < 0:
            range[1] = 3

        if range[1] < range[0]:
            raise KattoBotException("The range is malformed")

        v = random.uniform(range[0], range[1])

        self.loop_msg.change_interval(seconds=v)
        await self.send_to(ctx, msg, to0, secret_sender)


# Required for the following decorated functions
yaml = ruamel.yaml.YAML()
yaml.register_class(game.Game)
yaml.register_class(character.Character)
bot = KattoBot()


@bot.event
async def on_command_error(ctx, error):
    """ We catch the errors and print them in the chat """
    print(error)
    return await ctx.send(str(error))


@bot.command(name="load")
async def load_game(ctx):
    ctx.bot.load_game()
    await ctx.send("Game loaded successfully")


@bot.command(name="save")
async def save_game(ctx):
    ctx.bot.save_game()
    await ctx.send("Game saved successfully")


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
        await ctx.send(f"`{ctx.author.display_name}` rolls:{res}")
    else:
        await ctx.bot.send_to(ctx, res, to, secret_sender=False)


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
        await ctx.send(f"`{ctx.author.display_name}` rolls:\n{res}")
    else:
        await ctx.bot.send_to(ctx, res, to, secret_sender=False)


@bot.command(name="members", aliases=["get_members"])
async def get_members(ctx):
    """ Get online members """

    s = [f"`{i.display_name}`" for i in ctx.bot.get_online_members()]
    s = "The online members are: " + ", ".join(s)
    await ctx.send(s)


@bot.command(name="characters", aliases=["get_characters", "chars"])
async def get_characters(ctx):
    await ctx.send(ctx.bot.game.get_characters())


@bot.command(name="create_character", aliases=["create_char"])
async def create_character(ctx, name):
    ctx.bot.game.create_character(ctx.author.display_name, name)
    await ctx.send(f"Now `{ctx.author.display_name}` controls the character `{name}`")


@bot.command(name="set_stats")
async def set_stats(ctx, *args):
    _, kwargs = KattoBot._split_args_kwargs(args)
    c = ctx.bot.game.characters[ctx.author.display_name]
    c.set_stats(kwargs)

    await ctx.send(f"Now `{c.name}` has the following stats: \n{c.get_stats()}")


@bot.command(name="tell")
async def tell(ctx, *args):
    args, kwargs = KattoBot._split_args_kwargs(args)
    msg = " ".join(args)
    to = kwargs.get("to", None)
    secret = bool(kwargs.get("secret", False))

    await ctx.bot.send_to(ctx, msg, to, secret_sender=secret)


@bot.command(name="start_loop")
async def start_loop(ctx, *args):
    args, kwargs = KattoBot._split_args_kwargs(args)
    msg = " ".join(args)
    range = [float(kwargs.get("mint", -1)), float(kwargs.get("maxt", -1))]

    if len(msg) == 0:
        raise KattoBotException("Cannot loop an empty message")

    await ctx.bot.loop_msg.start(ctx, msg, None, range, secret_sender=False)


@bot.command(name="stop_loop")
async def stop_loop(ctx):
    ctx.bot.loop_msg.stop()


if __name__ == "__main__":
    """ Run the bot """
    bot.run()
