import discord
import pymongo
from pymongo import MongoClient
from redbot.core import Config, checks, commands

class Logging(commands.Cog):
    """Second Interation of the Logging Command (Now for Public Use)"""

    def __init__(self, bot):
        self.config = Config.get_conf(self, identifier=1072001)
        default_guild = {
            "MongoDB_URL" : "[None]",
            "Cluster" : "[None]",
            "WarnCollection" : "[None]",
            "LogProfileColor" : "FF0000",
            "ShowPrevOffences": False
        }
        self.config.register_guild(**default_guild)
        self.bot = bot

    @commands.group(name="log")
    async def log(self, ctx):
        """Log, and Lookup a User in the database"""
        pass

    @log.command(name="profile", aliases=["lookup"])
    async def log_profile(self, ctx : commands.Context, ID : int):
        """Lookup a Player inside the Database"""
        MongoURL = await self.config.guild(ctx.guild).MongoDB_URL()
        Cluster = await self.config.guild(ctx.guild).Cluster()
        Collection = await self.config.guild(ctx.guild).WarnCollection()
        ShowPrevOffences = await self.config.guild(ctx.guild).ShowPrevOffences()

        cluster = MongoClient(MongoURL)
        db = cluster[Cluster]
        WarnCollection = db[Collection]

        result = WarnCollection.find({"_id" : ID})


        try:
            embed = discord.Embed(title="Player Profile", color=0x4AE019)
            for results in result:
                Reason = (results['LatestReason'])
                TimesWarnedBefore = (results['TimesWarnedBefore'])
                PrevOffences = (results['PrevWarnings'])

                embed.add_field(name="ID", value=ID, inline=True)
                embed.add_field(name="Timed Warned Before", value=TimesWarnedBefore, inline=True)
                embed.add_field(name="Latest Warning Reason", value=Reason, inline=False)
                if ShowPrevOffences:
                    embed.add_field(name="Previous Reasons", value=PrevOffences, inline=False)
                else:
                    pass

            await ctx.send(embed=embed)
        except:
            await ctx.send("Player doesn't have a profile")
            return

    @log.command(name="warn")
    @checks.mod_or_permissions(manage_messages=True)
    async def log_warn(self, ctx : commands.Context, ID : int, * , Reason : str):
        """Warn a user, and store it inside the database"""
        MongoURL = await self.config.guild(ctx.guild).MongoDB_URL()
        Cluster = await self.config.guild(ctx.guild).Cluster()
        Collection = await self.config.guild(ctx.guild).WarnCollection()

        cluster = MongoClient(MongoURL)
        db = cluster[Cluster]
        WarnCollection = db[Collection]

        if len(str(ID)) > 18:
            await ctx.send("A ID Cannot be that long")
            return
        if len(str(ID)) < 16:
            await ctx.send("An ID cannot be that short!")
            return

        try:
            addWarning = {"_id" : ID, "LatestReason" : Reason, "TimesWarnedBefore" : 1, "PrevWarnings" : [Reason], "LatestModerator" : ctx.author.id}
            WarnCollection.insert_one(addWarning)
            embed=discord.Embed(title="Warning Added", color=0xC24949)
            embed.add_field(name="ID", value=ID, inline=False)
            embed.add_field(name="Reason", value=Reason)
            embed.set_footer(text=ctx.author.name)
            await ctx.send(embed=embed)
            return
        except pymongo.errors.DuplicateKeyError:

            updateReason = WarnCollection.update_one({"_id" : ID}, {"$set":{"LatestReason" : Reason, "LatestModerator" : ctx.author.id}})
            pushReasons = WarnCollection.update_one({"_id" : ID}, {"$push" : {"PrevWarnings" : [Reason]}})
            updateAmount = WarnCollection.update_one({"_id" : ID}, {"$inc" : {"TimesWarnedBefore" : 1}})
            embed = discord.Embed(title="Warning Added", description="**User had a previous warning**", color=0xC24949)
            embed.add_field(name="ID", value=ID, inline=False)
            embed.add_field(name="Reason", value=Reason)
            embed.set_footer(text=ctx.author.name)
            await ctx.send(embed=embed)
            return

    @log.command(name="amount")
    @checks.mod_or_permissions(manage_messages=True)
    async def log_amount(self, ctx : commands.Context, User : discord.Member = None):
        """Find the amount of warnings, optionally, mention a user to find how many warning they have"""
        MongoURL = await self.config.guild(ctx.guild).MongoDB_URL()
        Cluster = await self.config.guild(ctx.guild).Cluster()
        Collection = await self.config.guild(ctx.guild).WarnCollection()

        cluster = MongoClient(MongoURL)
        db = cluster[Cluster]
        WarnCollection = db[Collection]

        if User is None:
            logAmount = WarnCollection.find().count()
            embed = discord.Embed(title="Total Entries", color=0x46A9D2)
            embed.add_field(name="__Warnings__", value=logAmount)
            await ctx.send(embed=embed)
        else:
            moderatorAmount = WarnCollection.find({"LatestModerator" : User.id}).count()
            embed = discord.Embed(title=f"{User.name}'s Warnings", color=0x46A9D2)
            embed.add_field(name="__Warnings__", value=moderatorAmount)
            await ctx.send(embed=embed)
        return


    @log.group(name="settings")
    @checks.admin()
    async def logsettings(self, ctx):
        """Settings for Logs"""
        pass

    
    @logsettings.group(name="database")
    @checks.admin()
    async def logsettings_database(self, ctx):
        """Set the Database"""
        pass
    
    @logsettings_database.command(name="url")
    @checks.admin()
    async def ls_db_url(self, ctx : commands.Context, URL : str):
        """Set the MongoURL"""
        try:
            await self.config.guild(ctx.guild).MongoDB_URL.set(URL)
            await ctx.send(f"URL has been set : {URL}")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the URL")

    @logsettings_database.command(name="cluster")
    @checks.admin()
    async def ls_db_cluster(self, ctx : commands.Context, Cluster : str):
        """Set the Cluster"""
        try:
            await self.config.guild(ctx.guild).Cluster.set(Cluster)
            await ctx.send(f"Cluster has been set : {Cluster}")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the Cluster")

    @logsettings_database.command(name="collection")
    @checks.admin()
    async def ls_db_coll(self, ctx : commands.Context, Collection : str):
        """Set the Collection"""
        try:
            await self.config.guild(ctx.guild).WarnCollection.set(Collection)
            await ctx.send(f"Collection has been set : {Collection}")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the Collection")

    @logsettings.group(name="customization")
    @checks.admin()
    async def ls_cust(self, ctx):
        """Customize how the commands look"""
        pass

    @ls_cust.group(name="profile")
    @checks.admin()
    async def ls_cust_profile(self, ctx):
        """Customize ?log profile"""
        pass

    @ls_cust_profile.command(name="showpreviousoffences")
    @checks.admin()
    async def showpreviousoffences(self, ctx : commands.Context, Bool : bool):
        """To Enable, type True"""
        try:
            await self.config.guild(ctx.guild).ShowPrevOffences.set(Bool)
            await ctx.send(f"Settings has been set : {Bool}")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the value")






