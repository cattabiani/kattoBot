import os
from dotenv import load_dotenv
from discord.ext import commands
import discord
from src import utils

class KattoBotException(discord.ext.commands.errors.CommandError):
    def __init__(self, msg):
        super().__init__(f"**KattoBotException:** {msg}")


class KattoBot(commands.Bot):
    def __init__(self):
        load_dotenv("kattobotsandbox.env")
        self.token = os.getenv('DISCORD_TOKEN')
        self.guild_name = os.getenv('DISCORD_GUILD')

        intents = discord.Intents.default()
        intents.typing = False
        intents.presences = False
        intents.members = True
        intents.reactions = False

        super().__init__(intents=intents, command_prefix='!')

    async def on_ready(self):
        guild = discord.utils.get(self.guilds, name=self.guild_name)
        print(
            f'{self.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})'
        )

    def run(self):
        super().run(self.token)

    def get_user(self, name):
        users = [i for i in self.users if name == i.name]
        if len(users) == 0:
            users = [i for i in self.users if name in i.name]

        if len(users) == 0:
            raise KattoBotException(f"No matches for user: `{name}`")
        if len(users) == 1:
            return users[0]
        else:
            names = ", ".join([i.name for i in users])
            raise KattoBotException(f"User name: `{name}` matches too many users: `{names}`")

    async def send_to_user(self, msg, from0, to0):
        user = self.get_user(to0)
        msg = f"`{from0}` told me to send you this message:\n\n" + msg
        await user.send(msg)


bot = KattoBot()

@bot.event
async def on_command_error(ctx, error):
    print(type(error))
    print(error)
    if isinstance(error, KattoBotException):
        return await ctx.send(str(error))


@bot.command(name='r')
async def roll(ctx, cmd, reply_to=None):
    res = utils.roll(cmd)
    if not reply_to:
        await ctx.send(res)
    else:
        await ctx.bot.send_to_user(res, ctx.author.name, reply_to)

@bot.command(name='rs')
async def roll(ctx, cmd, reply_to=None):
    n, m = cmd.split('d')
    n = int(n)
    m = int(m)
    res = utils.format_roll_ndm_successes(n, m)
    if not reply_to:
        await ctx.send(res)
    else:
        await ctx.bot.send_to_user(res, ctx.author.name, reply_to)

if __name__ == "__main__":
    bot.run()
