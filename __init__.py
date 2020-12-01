from .log import Logging

def setup(bot):
    cog = Logging(bot)
    bot.add_cog(cog)
