import discord
import time
import pymongo
import requests
from pymongo import MongoClient
from datetime import datetime
from redbot.core import Config, checks, commands
from redbot.core.commands.converter import TimedeltaConverter
import socket

DATABASE_URL_INCOMPLETE = "Database URL is Incorrect, do `[p]logsettings` to set and view the settings\n[p] is the prefix you have set"
WARNING_COLLECTION_INCOMPLETE = "Warning Collection is Incorrect, do `[p]logsettings` to set and view the settings\n[p] is the prefix you have set"
WARNLOGS_COLLECTION_INCOMPLETE = "Warning Logs Collection is Incorrect, do `[p]logsettings` to set and view the settings\n[p] is the prefix you have set"
MUTES_COLLECTION_INCOMPLETE = "Mutes Collection is Incorrect, do `[p]logsettings` to set and view the settings\n[p] is the prefix you have set"
MUTELOGS_COLLECTION_INCOMPLETE = "Mute Logs Collection is Incorrect, do `[p]logsettings` to set and view the settings\n[p] is the prefix you have set"
PLAYERLOGS_COLLECTION_INCOMPLETE = "Player Collection is Incorrect, do `[p]logsettings` to set and view the settings\n[p] is the prefix you have set"
DATABASE_CLUSTER_INCOMPLETE = "Database Cluster is Incorrect, do `[p]logsettings` to set and view the settings\n[p] is the prefix you have set"
STEAMAPIKEY_INCORRECT = "SteamAPI Key is incorrect, do `[p]logsettings` to set and view the settings\n[p] is the prefix you have set"


class Logging(commands.Cog):
    """Logs a players punishments"""

    def __init__(self, bot):
        self.config = Config.get_conf(self, identifier=1072001)
        default_guild = {
            "mongoDB_URL": "[None]",
            "Warning_Collection": "[None]",
            "WarnLog_Collection": "[None]",
            "Mute_Collection": "[None]",
            "MuteLog_Collection": "[None]",
            "PlayerLogs_Collection": "[None]",
            "doubledPoints": False,
            "Cluster": "[None]",
            "steamkey": "[None]",
            "storageServerIP" : "[None]",
            "externalStorageEnabled" : False,
            "ModRole": 0,
            "adminRole": 0}
        self.config.register_guild(**default_guild)
        self.bot = bot

    @commands.group()
    async def log(self, ctx):
        """Log your Warnings, and Mutes"""
        pass

    @log.command(name="profile", aliases=["p"])
    async def log_points(self, ctx: commands.Context, id: int, RAW: bool = False):
        """View a players points for both warnings and mutes

        Additonal Syntax: `$log profile <Steam64ID>`"""
        # Load the Mongo_URL Settings, if they are none, then display an error
        mongo_url = await self.config.guild(ctx.guild).mongoDB_URL()
        if "None" in mongo_url:
            await ctx.send(DATABASE_URL_INCOMPLETE)
            return
        #######################################################################
        getCluster = await self.config.guild(ctx.guild).Cluster()
        if "None" in getCluster:
            await ctx.send(DATABASE_CLUSTER_INCOMPLETE)
            return
        #######################################################################
        getWarnLog = await self.config.guild(ctx.guild).WarnLog_Collection()
        if "None" in getWarnLog:
            await ctx.send(WARNLOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getMuteLog = await self.config.guild(ctx.guild).MuteLog_Collection()
        if "None" in getMuteLog:
            await ctx.send(MUTELOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getPlayerLog = await self.config.guild(ctx.guild).PlayerLogs_Collection()
        if "None" in getPlayerLog:
            await ctx.send(PLAYERLOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        apiToken = await self.config.guild(ctx.guild).steamkey()
        if "None" in apiToken:
            await ctx.send(STEAMAPIKEY_INCORRECT)
            return
        #######################################################################

        cluster = MongoClient(mongo_url)
        db = cluster[getCluster]
        waCollection = db[getWarnLog]
        muCollection = db[getMuteLog]
        plCollection = db[getPlayerLog]

        startTimeCommand = time.strftime('%X')

        if len(str(id)) == 17:
            # This is a Steam64ID
            link = (f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={apiToken}&steamids={id}")
            r = requests.get(link)
            data = r.json()
            dataResponse = data['response']['players'][0]
            avatarURL = (dataResponse['avatarfull'])
            personaname = (dataResponse['personaname'])
            profileURL = (dataResponse['profileurl'])
            pass
        elif len(str(id)) == 18:
            # This is a DiscordID
            avatarURL = "https://www.shitpostbot.com/resize/585/400?img=%2Fimg%2Fsourceimages%2Fdefault-discord-icon-5b254285e1034.png";
            personaname = "Discord User"
            profileURL = "None"
            pass

        results = waCollection.find({"_id": id})
        muteResults = muCollection.find({"_id": id})
        playerResults = plCollection.find({"_id": id})

        try:
            embed = discord.Embed(
                title=(f"{personaname}'s Profile"),
                description='Here is the information about the user',
                colour=discord.Colour.green())
            for result in results:
                steamID = (result["_id"])
                warnPoints = (result["MasterWarnPoints"])
                warnReason = (result["FirstWarnReason"])

                embed.add_field(name='ID', value=steamID, inline=False)
                embed.add_field(name='Warning Points', value=warnPoints, inline=True)
                embed.add_field(name='Warning Reason', value=warnReason, inline=True)
            for muteResult in muteResults:
                mutePoints = (muteResult["MasterMutePoints"])
                muteReason = (muteResult["muteReason"])
                embed.add_field(name='Mute Points', value=mutePoints, inline=False)
                embed.add_field(name='Mute Reason', value=muteReason, inline=True)
            for plResult in playerResults:
                BanReason = (plResult["BanReason"])
                BanLength = (plResult["MostRecentBanLength"])

                embed.add_field(name='Ban Length:', value=BanLength, inline=False)
                embed.add_field(name='Ban Reason:', value=BanReason, inline=False)

            embed.set_thumbnail(url=avatarURL)
            endTimeCommand = time.strftime('%X')
            finalTimeString = (startTimeCommand + "-->" + endTimeCommand)
            embed.add_field(name="Steam Profile URL:", value=profileURL, inline=False)
            embed.set_footer(text=finalTimeString)
            await ctx.send(embed=embed)
        except pymongo.errors.PyMongoError:
            embed = discord.Embed(
                title='User Profile not found',
                description='User does not have any warnings!',
                colour=discord.Colour.green())
            await ctx.send(embed=embed)

    @log.command(name="warn", aliases=["warning"])
    @checks.mod_or_permissions(manage_messages=True)
    async def log_warn(self, ctx: commands.Context, id: int, warnPoints: int, *, warnReason: str):
        """Log your warnings"""
        mongo_url = await self.config.guild(ctx.guild).mongoDB_URL()
        if "None" in mongo_url:
            await ctx.send(DATABASE_URL_INCOMPLETE)
            return
        #######################################################################
        getCluster = await self.config.guild(ctx.guild).Cluster()
        if "None" in getCluster:
            await ctx.send(DATABASE_CLUSTER_INCOMPLETE)
            return
        #######################################################################
        getWarnLog = await self.config.guild(ctx.guild).WarnLog_Collection()
        if "None" in getWarnLog:
            await ctx.send(WARNLOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getWarnColl = await self.config.guild(ctx.guild).Warning_Collection()
        if "None" in getWarnLog:
            await ctx.send(WARNING_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getPlayerInfo = await self.config.guild(ctx.guild).PlayerLogs_Collection()
        if "None" in getPlayerInfo:
            await ctx.send(PLAYERLOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        apiToken = await self.config.guild(ctx.guild).steamkey()
        if "None" in apiToken:
            await ctx.send(STEAMAPIKEY_INCORRECT)
            return
        #######################################################################
        getStorageIP = await self.config.guild(ctx.guild).storageServerIP()
        getStorageEnabled = await self.config.guild(ctx.guild).externalStorageEnabled()

        cluster = MongoClient(mongo_url)
        db = cluster[getCluster]
        waCollection = db[getWarnLog]
        wCollection = db[getWarnColl]
        plCollection = db[getPlayerInfo]

        startTimeCommand = time.strftime('%X')

        if '|' in warnReason:
            await ctx.send("Cannot have '|' in your reason")
            return

        author = ctx.author
        author = ctx.author.id
        if len(str(id)) == 17:
            link = (f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={apiToken}&steamids={id}")
            r = requests.get(link)
            data = r.json()
            dataResponse = data['response']['players'][0]
            personaname = (dataResponse['personaname'])
            pass
        elif len(str(id)) == 18:
            personaname = "Unknown Discord User";
            pass

        try:
            createWarnLog = {"_id": id, "MasterWarnPoints": warnPoints, "FirstWarnReason": warnReason}
            createWarning = {"_id": id, "Moderator": author}
            waCollection.insert_one(createWarnLog)
            wCollection.insert_one(createWarning)
            embed = discord.Embed(
                title='Warning Success',
                description=f'You have warned {personaname}!',
                colour=discord.Colour.green())
            endTimeCommand = time.strftime('%X')
            finalTimeString = (startTimeCommand + "-->" + endTimeCommand)
            embed.set_footer(text=finalTimeString)
            await ctx.send(embed=embed)
            if getStorageEnabled:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_address = (getStorageIP, 7500)
                    sock.connect(server_address)
                    try:
                        tcpMessage = f"LOG_WARNING-{id}|{personaname}|{warnPoints}|{warnReason}|{datetime.today().strftime('%Y-%m-%d')}|{ctx.author}"
                        sock.sendall(tcpMessage.encode('utf-8'))
                    finally:
                        sock.close()
                except:
                    return
            else:
                pass
        except pymongo.errors.DuplicateKeyError:
            AddWarning = waCollection.update_one({"_id": id}, {"$inc": {"MasterWarnPoints": warnPoints}})
            UpdateReason = waCollection.update_one({"_id": id}, {"$set": {"FirstWarnReason": warnReason}})
            embed = discord.Embed(
                title='Warning Success',
                description=f'{personaname} had a previous warning, so the points have been updated!',
                colour=discord.Colour.green())

            warnResults = waCollection.find({"_id": id})
            for result in warnResults:
                warnPoints = (result["MasterWarnPoints"])
                if warnPoints >= 10:
                    embed.add_field(name='Warn Points Alert!', value="That user has over 10+ points", inline=False)
                elif warnPoints >= 9:
                    embed.add_field(name='Warn Points Alert!', value="That user has 9+ points", inline=False)
                elif warnPoints >= 8:
                    embed.add_field(name='Warn Points Alert!', value="That user has 8+ points", inline=False)
                elif warnPoints >= 6:
                    embed.add_field(name='Warn Points Alert!', value="That user has 6+ points", inline=False)
                elif warnPoints >= 3:
                    embed.add_field(name='Warn Points Alert!', value="That user has 3+ points", inline=False)
                else:
                    pass
            endTimeCommand = time.strftime('%X')
            finalTimeString = (startTimeCommand + "-->" + endTimeCommand)
            embed.set_footer(text=finalTimeString)
            await ctx.send(embed=embed)
            if getStorageEnabled:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_address = (getStorageIP, 7500)
                    sock.connect(server_address)
                    try:
                        tcpMessage = f"LOG_WARNING-{id}|{personaname}|{warnPoints}|{warnReason}|{datetime.today().strftime('%Y-%m-%d')}|{ctx.author}"
                        sock.sendall(tcpMessage.encode('utf-8'))
                    finally:
                        sock.close()
                except:
                    return
            else:
                pass

        except ValueError:
            await ctx.send("Are you forgetting the users warning points?")
            return

    @log.command(name="delete", aliases=["del"])
    @checks.mod_or_permissions(manage_messages=True)
    async def log_delete(self, ctx: commands.Context, Type: str, id: int):
        """Delete a user's information

        Additonal Syntax: `$log delete <(warn/mute/mic)> <Steam64ID>`"""
        mongo_url = await self.config.guild(ctx.guild).mongoDB_URL()
        if "None" in mongo_url:
            await ctx.send(DATABASE_URL_INCOMPLETE)
            return
        #######################################################################
        getCluster = await self.config.guild(ctx.guild).Cluster()
        if "None" in getCluster:
            await ctx.send(DATABASE_CLUSTER_INCOMPLETE)
            return
        #######################################################################
        getWarnLog = await self.config.guild(ctx.guild).WarnLog_Collection()
        if "None" in getWarnLog:
            await ctx.send(WARNLOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getMuteLog = await self.config.guild(ctx.guild).MuteLog_Collection()
        if "None" in getMuteLog:
            await ctx.send(MUTELOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getPlayerLog = await self.config.guild(ctx.guild).PlayerLogs_Collection()
        if "None" in getPlayerLog:
            await ctx.send(PLAYERLOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getWarnColl = await self.config.guild(ctx.guild).Warning_Collection()
        if "None" in getWarnLog:
            await ctx.send(WARNING_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getMuteColl = await self.config.guild(ctx.guild).Mute_Collection()
        if "None" in getMuteColl:
            await ctx.send(MUTELOGS_COLLECTION_INCOMPLETE)
            return

        cluster = MongoClient(mongo_url)
        db = cluster[getCluster]
        waCollection = db[getWarnLog]
        wCollection = db[getWarnColl]
        mCollection = db[getMuteColl]
        muCollection = db[getMuteLog]
        PLCollection = db[getPlayerLog]

        if Type == "mute" or Type == "mic":
            try:
                muteDelete = mCollection.delete_one({"_id": id})
                muteLogDelete = muCollection.delete_one({"_id": id})
                embed = discord.Embed(
                    title='Mute Deleted',
                    description='Players mute information has been deleted!',
                    colour=discord.Colour.green())
                await ctx.send(embed=embed)
            except pymongo.errors.PyMongoError:
                embed = discord.Embed(
                    title='Mute Deletion Failed',
                    description='Ask a developer for help!',
                    colour=discord.Colour.red())
                await ctx.send(embed=embed)
        elif Type == "warn":
            try:
                warnDelete = wCollection.delete_one({"_id": id})
                warningLogDelete = waCollection.delete_one({"_id": id})
                embed = discord.Embed(
                    title='Warning Deleted',
                    description='Players Warning information has been deleted!',
                    colour=discord.Colour.green())
                await ctx.send(embed=embed)
            except:
                embed = discord.Embed(
                    title='Warning Deletion Failed',
                    description='Ask a developer for help!',
                    colour=discord.Colour.red())
                await ctx.send(embed=embed)
        elif Type == "bans" or Type == "ban":
            try:
                banDelete = PLCollection.delete_one({"_id": id})
                embed = discord.Embed(
                    title='Ban Deleted',
                    description='Players Ban information has been deleted!',
                    colour=discord.Colour.green())
                await ctx.send(embed=embed)
            except:
                embed = discord.Embed(
                    title='Ban Deletion Failed',
                    description='Ask a developer for help!',
                    colour=discord.Colour.red())
                await ctx.send(embed=embed)
        else:
            await ctx.send("That doesn't exist!")
            return

    @log.command(name="mute", aliases=["mic"])
    @checks.mod_or_permissions(manage_messages=True)
    async def log_mute(self, ctx: commands.Context, id: int, mutePoints: int, *, muteReason: str):
        """Log your mutes"""
        mongo_url = await self.config.guild(ctx.guild).mongoDB_URL()
        if "None" in mongo_url:
            await ctx.send(DATABASE_URL_INCOMPLETE)
            return
        #######################################################################
        getCluster = await self.config.guild(ctx.guild).Cluster()
        if "None" in getCluster:
            await ctx.send(DATABASE_CLUSTER_INCOMPLETE)
            return
        #######################################################################
        getWarnLog = await self.config.guild(ctx.guild).WarnLog_Collection()
        if "None" in getWarnLog:
            await ctx.send(WARNLOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getMuteLog = await self.config.guild(ctx.guild).MuteLog_Collection()
        if "None" in getMuteLog:
            await ctx.send(MUTELOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getPlayerLog = await self.config.guild(ctx.guild).PlayerLogs_Collection()
        if "None" in getPlayerLog:
            await ctx.send(PLAYERLOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getWarnColl = await self.config.guild(ctx.guild).Warning_Collection()
        if "None" in getWarnLog:
            await ctx.send(WARNING_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getMuteColl = await self.config.guild(ctx.guild).Mute_Collection()
        if "None" in getMuteColl:
            await ctx.send(MUTELOGS_COLLECTION_INCOMPLETE)
            return
        doubledPoints = await self.config.guild(ctx.guild).doubledPoints()
        apiToken = await self.config.guild(ctx.guild).steamkey()
        if "None" in apiToken:
            await ctx.send(STEAMAPIKEY_INCORRECT)
            return
        #######################################################################
        getStorageIP = await self.config.guild(ctx.guild).storageServerIP()
        getStorageEnabled = await self.config.guild(ctx.guild).externalStorageEnabled()

        cluster = MongoClient(mongo_url)
        db = cluster[getCluster]
        mCollection = db[getMuteColl]
        muCollection = db[getMuteLog]
        plCollection = db[getPlayerLog]

        results = muCollection.find({"_id": id})
        for muResult in results:
            oldReason = (muResult['muteReason'])

        startTimeCommand = time.strftime('%X')

        if '|' in muteReason:
            await ctx.send("Cannot have '|' in your reason")
            return

        author = ctx.author.id
        if len(str(id)) == 17:
            link = (f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={apiToken}&steamids={id}")
            r = requests.get(link)
            data = r.json()
            dataResponse = data['response']['players'][0]
            personaname = (dataResponse['personaname'])
            pass
        elif len(str(id)) == 18:
            personaname = "Unknown Discord User";
            pass

        if mutePoints > 10:
            embed = discord.Embed(
                title='Mute Failure',
                description='You cannot enter more than 10 points at a time',
                colour=discord.Colour.red())
            await ctx.send(embed=embed)
            return

        try:
            createMuteLog = {"_id": id, "MasterMutePoints": mutePoints, "muteReason": muteReason}
            createMute = {"_id": id, "Moderator": author}
            MuteLog = muCollection.insert_one(createMuteLog)
            Muting = mCollection.insert_one(createMute)
            embed = discord.Embed(
                title='Mute Success',
                description=f'{personaname} has been logged',
                colour=discord.Colour.green())
            endTimeCommand = time.strftime('%X')
            finalTimeString = (startTimeCommand + "-->" + endTimeCommand)
            embed.set_footer(text=finalTimeString)
            await ctx.send(embed=embed)
            if getStorageEnabled:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_address = (getStorageIP, 7500)
                    sock.connect(server_address)
                    try:
                        tcpMessage = f"LOG_MUTE-{id}|{personaname}|{mutePoints}|{muteReason}|{datetime.today().strftime('%Y-%m-%d')}|{ctx.author}"
                        sock.sendall(tcpMessage.encode('utf-8'))
                    finally:
                        sock.close()
                except:
                    return
            else:
                pass
        except pymongo.errors.DuplicateKeyError:
            if 'micspam' in oldReason.lower() and doubledPoints is True:
                embed = discord.Embed(
                    title='Mute Success',
                    description=f'{personaname} had a previous mute, for the same reason. The Points have been Doubled!',
                    colour=discord.Colour.green()
                )
                mutePoints = mutePoints * 2
                AddMute = muCollection.update_one({"_id": id}, {"$inc": {"MasterMutePoints": mutePoints}})
            else:
                embed = discord.Embed(
                    title='Mute Success',
                    description=f'{personaname} had a previous mute, so they have been updated',
                    colour=discord.Colour.green()
                )
                AddMute = muCollection.update_one({"_id": id}, {"$inc": {"MasterMutePoints": mutePoints}})
            EditReason = muCollection.update_one({"_id": id}, {"$set": {"muteReason": muteReason}})

            muteResults = muCollection.find({"_id": id})
            for result in muteResults:
                mutePoints = (result["MasterMutePoints"])
                if mutePoints >= 10:
                    embed.add_field(name='Mute Points Alert!', value="That user has over 10+ points", inline=False)
                elif mutePoints >= 9:
                    embed.add_field(name='Mute Points Alert!', value="That user has 9+ points", inline=False)
                elif mutePoints >= 6:
                    embed.add_field(name='Mute Points Alert!', value="That user has 6+ points", inline=False)
                elif mutePoints >= 3:
                    embed.add_field(name='Mute Points Alert!', value="That user has 3+ points", inline=False)
                else:
                    pass
            endTimeCommand = time.strftime('%X')
            finalTimeString = (startTimeCommand + "-->" + endTimeCommand)
            embed.set_footer(text=finalTimeString)
            await ctx.send(embed=embed)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_address = (getStorageIP, 7500)
                sock.connect(server_address)
                try:
                    tcpMessage = f"LOG_MUTE-{id}|{personaname}|{mutePoints}|{muteReason}|{datetime.today().strftime('%Y-%m-%d')}|{ctx.author}"
                    sock.sendall(tcpMessage.encode('utf-8'))
                finally:
                    sock.close()
            except:
                return

    @log.command(name="ban")
    @checks.mod_or_permissions(manage_messages=True)
    async def log_ban(self, ctx: commands.Context, id: int, Duration: TimedeltaConverter, *, Ban_Reason: str = ""):
        """Give the player additional information"""
        mongo_url = await self.config.guild(ctx.guild).mongoDB_URL()
        if "None" in mongo_url:
            await ctx.send(DATABASE_URL_INCOMPLETE)
            return
        #######################################################################
        getCluster = await self.config.guild(ctx.guild).Cluster()
        if "None" in getCluster:
            await ctx.send(DATABASE_CLUSTER_INCOMPLETE)
            return
        #######################################################################
        getPlayerLog = await self.config.guild(ctx.guild).PlayerLogs_Collection()
        if "None" in getPlayerLog:
            await ctx.send(PLAYERLOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        apiToken = await self.config.guild(ctx.guild).steamkey()
        if "None" in apiToken:
            await ctx.send(STEAMAPIKEY_INCORRECT)
            return
        getStorageIP = await self.config.guild(ctx.guild).storageServerIP()
        getStorageEnabled = await self.config.guild(ctx.guild).externalStorageEnabled()

        cluster = MongoClient(mongo_url)
        db = cluster[getCluster]
        plCollection = db[getPlayerLog]

        authorID = ctx.author.id
        author = ctx.author

        if len(str(id)) == 17:
            link = (f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={apiToken}&steamids={id}")
            r = requests.get(link)
            data = r.json()
            dataResponse = data['response']['players'][0]
            personaname = (dataResponse['personaname'])
            pass
        elif len(str(id)) == 18:
            personaname = "Unknown Discord User";
            pass

        try:
            AddInformation = {"_id": id, "BanReason": Ban_Reason, "ModeratorID": authorID, "Moderator": str(author),
                              "TimesBanned": 1, "MostRecentBanLength": str(Duration)}
            PlayerInfo = plCollection.insert_one(AddInformation)
            embed = discord.Embed(
                title='Ban Logged!',
                description='Ban has been logged successfully!',
                colour=discord.Colour.green()
            )
            await ctx.send(embed=embed)
            if getStorageEnabled:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_address = (getStorageIP, 7500)
                    sock.connect(server_address)
                    try:
                        tcpMessage = f"LOG_BAN-{id}|{personaname}|{Duration}|{Ban_Reason}|{datetime.today().strftime('%Y-%m-%d')}|{ctx.author}"
                        sock.sendall(tcpMessage.encode('utf-8'))
                    finally:
                        sock.close()
                except:
                    return
            else:
                pass
        except pymongo.errors.DuplicateKeyError:
            UpdateReason = plCollection.update_one({"_id": id}, {
                "$set": {"BanReason": Ban_Reason, "ModeratorID": authorID, "Moderator": str(author),
                         "MostRecentBanLength": str(Duration)}})
            UpdateShit = plCollection.update_one({"_id": id}, {"$inc": {"TimesBanned": 1}})
            embed = discord.Embed(
                title='Ban Logged!',
                description='User had a previous ban before, updated reason',
                colour=discord.Colour.green()
            )
            await ctx.send(embed=embed)
            if getStorageEnabled:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    server_address = (getStorageIP, 7500)
                    sock.connect(server_address)
                    try:
                        tcpMessage = f"LOG_BAN-{id}|{personaname}|{Duration}|{Ban_Reason}|{datetime.today().strftime('%Y-%m-%d')}|{ctx.author}"
                        sock.sendall(tcpMessage.encode('utf-8'))
                    finally:
                        sock.close()
                except:
                    return
            else:
                pass

    @log.command(name="help")
    @checks.mod_or_permissions(manage_messages=True)
    async def log_help(self, ctx):
        """More In-depth look into the commands"""
        await ctx.send("**Logging Command Help**\n\n __**Logging a warning**__\n You can log a warning with the "
                       "command `$log warn <SteamID> <Points> <Reason>` Here is an example below: \n ```$log warn "
                       "76561198146812074 1 Killing Cuffed D-Class``` \n\n __**Logging a mute**__\nYou can log a mute "
                       "with the following command: `$log mute <SteamID> <Points> <Reason>` Here is an example "
                       "below:\n```$log mute 76561198146812074 2 Earrape in DeadChat```\n\n __**Deleting a Warning or "
                       "Mute**__\nIf you ever need to delete a user's Warning or Mute History: `$log delete "
                       "<mute/warn> <SteamID>` Here is an example of that:\n```$log delete mute "
                       "76561198146812074```\n\n __**Logging Bans**__\nWhen logging bans, you use this command: `$log "
                       "ban <SteamID> <Time> <Reason>` Here is an example below:\n```$log ban 76561198146812074 1d "
                       "Closing doors on teammates even after warning```\n\n __**Viewing a Players Profile**__\nTo "
                       "view a players previous Warning and Mute history use the following command: `$log profile "
                       "<SteamID>`Here is example below:\n```$log profile 76561198146812074```\n\n")

    @log.command(name="amount")
    @checks.mod_or_permissions(manage_messages=True)
    async def log_amount(self, ctx: commands.Context):
        """Find out how many warnings and mutes have been entered"""
        mongo_url = await self.config.guild(ctx.guild).mongoDB_URL()
        if "None" in mongo_url:
            await ctx.send(DATABASE_URL_INCOMPLETE)
            return
        #######################################################################
        getCluster = await self.config.guild(ctx.guild).Cluster()
        if "None" in getCluster:
            await ctx.send(DATABASE_CLUSTER_INCOMPLETE)
            return
        #######################################################################
        getWarnLog = await self.config.guild(ctx.guild).WarnLog_Collection()
        if "None" in getWarnLog:
            await ctx.send(WARNLOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getMuteLog = await self.config.guild(ctx.guild).MuteLog_Collection()
        if "None" in getMuteLog:
            await ctx.send(MUTELOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getPlayerLog = await self.config.guild(ctx.guild).PlayerLogs_Collection()
        if "None" in getPlayerLog:
            await ctx.send(PLAYERLOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################

        cluster = MongoClient(mongo_url)
        db = cluster[getCluster]
        WLCollection = db[getWarnLog]
        MLCollection = db[getMuteLog]
        plCollection = db[getPlayerLog]

        startTimeCommand = time.strftime('%X')

        author = ctx.author

        WLMod = WLCollection.find().count()
        MLMod = MLCollection.find().count()
        PLMod = plCollection.find().count()

        embed = discord.Embed(
            title='Amounts of Warns/Mutes/Bans!',
            description='Here it is',
            colour=discord.Colour.green()
        )
        embed.add_field(name='Warnings', value=WLMod, inline=False)
        embed.add_field(name='Mutes', value=MLMod, inline=False)
        embed.add_field(name='Bans', value=PLMod, inline=False)
        endTimeCommand = time.strftime('%X')
        finalTime = (startTimeCommand + " --> " + endTimeCommand)
        embed.set_footer(text=finalTime)
        await ctx.send(embed=embed)

    @log.command(name="mod")
    @checks.mod_or_permissions(manage_messages=True)
    async def log_mod(self, ctx: commands.Context, user: discord.Member):
        """How many warnings has a Moderator done?"""
        mongo_url = await self.config.guild(ctx.guild).mongoDB_URL()
        if "None" in mongo_url:
            await ctx.send(DATABASE_URL_INCOMPLETE)
            return
        #######################################################################
        getCluster = await self.config.guild(ctx.guild).Cluster()
        if "None" in getCluster:
            await ctx.send(DATABASE_CLUSTER_INCOMPLETE)
            return
        #######################################################################
        getWarnColl = await self.config.guild(ctx.guild).Warning_Collection()
        if "None" in getWarnColl:
            await ctx.send(WARNING_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getMuteColl = await self.config.guild(ctx.guild).Mute_Collection()
        if "None" in getMuteColl:
            await ctx.send(MUTELOGS_COLLECTION_INCOMPLETE)
            return
        #######################################################################
        getPlayerLog = await self.config.guild(ctx.guild).PlayerLogs_Collection()
        if "None" in getPlayerLog:
            await ctx.send(PLAYERLOGS_COLLECTION_INCOMPLETE)
            return
        ######################################################################



        cluster = MongoClient(mongo_url)
        db = cluster[getCluster]
        WLCollection = db[getWarnColl]
        MLCollection = db[getMuteColl]
        PLCollection = db[getPlayerLog]

        author = ctx.author

        DiscordID = user.id

        WLAmount = WLCollection.find({"Moderator": DiscordID}).count()
        MLAmount = MLCollection.find({"Moderator": DiscordID}).count()
        PLAmount = PLCollection.find({"ModeratorID": DiscordID}).count()

        try:
            embed = discord.Embed(
                title='Amount of Warnings',
                description='Here it is',
                colour=discord.Colour.green()
            )
            embed.add_field(name='Warnings', value=WLAmount, inline=False)
            embed.add_field(name='Mutes', value=MLAmount, inline=False)
            embed.add_field(name='Bans', value=PLAmount, inline=False)
            await ctx.send(embed=embed)
        except:
            await ctx.send("That user does not exist, or has not entered any warnings")

    @commands.group(name="logsettings")
    @checks.admin()
    async def logsettings(self, ctx):
        """Edit the Logging Commands for Roles and Users"""
        pass

    @logsettings.group(name="misc")
    @checks.admin()
    async def logsettings_misc(self, ctx):
        """Misc. Settings for Logging"""
        pass

    @logsettings.group(name="storage")
    @checks.admin()
    async def logsettings_storage(self, ctx):
        """Change the Storage Settings of Logs (Optional)"""
        pass

    @logsettings_storage.command(name="ip")
    @checks.admin()
    async def storage_ip(self, ctx, IP : str):
        """Set the IP of the TCP Server"""
        try:
            await self.config.guild(ctx.guild).storageServerIP.set(IP)
            await ctx.send(f"IP has been set to {IP}")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the IP, double check and try again!")

    @logsettings_storage.command(name="enabled")
    @checks.admin()
    async def storage_enabled(self, ctx : commands.Context, Enabled : bool):
        """Enable or Disable the Storage"""
        try:
            await self.config.guild(ctx.guild).externalStorageEnabled.set(Enabled)
            await ctx.send(f"The Storage Server has been set to {Enabled}\nBe sure to check the IP")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the IP, double check and try again!")

    @logsettings_misc.command(name="steamapikey")
    @checks.admin()
    async def steamapikey(self, ctx: commands.Context, APIKey: str):
        """Set the API Key for Steam
        You can get one here : https://steamcommunity.com/dev/apikey"""
        if len(APIKey) < 32:
            await ctx.send("That doesn't look like an API Key")
            return
        try:
            await self.config.guild(ctx.guild).steamkey.set(APIKey)
            await ctx.send(f"SteamAPI Key has been set")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the Key, double check and try again!")

    @logsettings_misc.command(name="doubledpoints")
    @checks.admin()
    async def doublepoints(self, ctx: commands.Context, Enabled: bool):
        """Double the Points if a offender has the same offence as the new reason"""
        try:
            await self.config.guild(ctx.guild).doubledPoints.set(Enabled)
            await ctx.send(f"Doubled Points has been set to {Enabled}")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the Key, double check and try again!")

    @logsettings.group(name="database")
    @checks.admin()
    async def logsettings_database(self, ctx):
        """Set the settings for Logs and Entering it into the Database"""
        pass

    @logsettings_database.command(name="url")
    @checks.admin()
    async def logsettings_database_url(self, ctx: commands.Context, URL: str):
        """Set the MongoDB URL"""
        try:
            await self.config.guild(ctx.guild).mongoDB_URL.set(URL)
            await ctx.send(f"MongoDB URL Set to : {URL}")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the URL, double check and try again!")

    @logsettings_database.command(name="warningcollection")
    @checks.admin()
    async def logsettings_database_warningcollection(self, ctx: commands.Context, Name: str):
        """Set the Warning Collection"""
        try:
            await self.config.guild(ctx.guild).Warning_Collection.set(Name)
            await ctx.send(f"Set Warning Collection to : {Name}")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the Collection, double check and try again!")

    @logsettings_database.command(name="warnlogcollection")
    @checks.admin()
    async def logsettings_database_warnlogcollection(self, ctx: commands.Context, Name: str):
        """Set the Warn Log Collection"""
        try:
            await self.config.guild(ctx.guild).WarnLog_Collection.set(Name)
            await ctx.send(f"Set Warn Log Collection to : {Name}")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the Collection, double check and try again!")

    @logsettings_database.command(name="mutecollection")
    @checks.admin()
    async def logsettings_database_mutecollection(self, ctx: commands.Context, Name: str):
        """Set the Mute Collection"""
        try:
            await self.config.guild(ctx.guild).Mute_Collection.set(Name)
            await ctx.send(f"Set Mute Collection to : {Name}")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the Collection, double check and try again!")

    @logsettings_database.command(name="mutelogcollection")
    @checks.admin()
    async def logsettings_database_mutelogcollection(self, ctx: commands.Context, Name: str):
        """Set the Mute Log Collection"""
        try:
            await self.config.guild(ctx.guild).MuteLog_Collection.set(Name)
            await ctx.send(f"Set Mute Log Collection to : {Name}")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the Collection, double check and try again!")

    @logsettings_database.command(name="cluster")
    @checks.admin()
    async def logsettings_database_cluster(self, ctx: commands.Context, ClusterName: str):
        """Set the Cluster"""
        try:
            await self.config.guild(ctx.guild).Cluster.set(ClusterName)
            await ctx.send(f"Set Cluster to : {ClusterName}")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the Cluster, double check and try again!")

    @logsettings_database.command(name="playerinfo")
    @checks.admin()
    async def logsettings_database_playerinfo(self, ctx: commands.Context, Collection: str):
        """Set the PlayerInfo Collection"""
        try:
            await self.config.guild(ctx.guild).PlayerLogs_Collection.set(Collection)
            await ctx.send(f"Set Cluster to : {Collection}")
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was an error setting the Cluster, double check and try again!")

    @logsettings.command(name="view", aliases=["show"])
    @checks.admin()
    async def logsettings_show(self, ctx):
        """Show the Settings of the Current Database"""
        mongo_url = await self.config.guild(ctx.guild).mongoDB_URL()
        getCluster = await self.config.guild(ctx.guild).Cluster()
        getWarnLog = await self.config.guild(ctx.guild).WarnLog_Collection()
        getMuteLog = await self.config.guild(ctx.guild).MuteLog_Collection()
        getPlayerLog = await self.config.guild(ctx.guild).PlayerLogs_Collection()
        getWarnColl = await self.config.guild(ctx.guild).Warning_Collection()
        getMuteColl = await self.config.guild(ctx.guild).Mute_Collection()
        apiToken = await self.config.guild(ctx.guild).steamkey()

        modRole = await self.config.guild(ctx.guild).ModRole()
        adminRole = await self.config.guild(ctx.guild).adminRole()

        await ctx.send(f"```MongoDB URL : {mongo_url}\n" +
                       f"Cluster Name : {getCluster}\n" +
                       f"Warn Log Collection: {getWarnLog}\n" +
                       f"Warnings Collection : {getWarnColl}\n" +
                       f"Mute Log Collection : {getMuteLog}\n" +
                       f"Mute Collection : {getMuteColl}\n" +
                       f"Player Info Collection : {getPlayerLog}\n\n" +
                       f"Moderator Role : {modRole}\n" +
                       f"Admin Role : {adminRole}\n\n" +
                       f"SteamAPI Key : {apiToken}```")

    @logsettings.group(name="roles")
    @checks.admin()
    async def logsettings_roles(self, ctx):
        """Set roles for the Logs"""
        pass

    @logsettings_roles.command(name="moderator")
    @checks.admin()
    async def logsettings_roles_moderator(self, ctx: commands.Context, Role: discord.Role):
        """Sets the Moderator Role"""

        try:
            await self.config.guild(ctx.guild).ModRole.set(Role.id)
            await ctx.send("The Moderator Role is now set to : {}".format(Role.name))
        except:
            await ctx.send("An error has occured, and cannot set the Mod Role")
            return
        return

    @logsettings_roles.command(name="admin")
    @checks.admin()
    async def logsettings_roles_admin(self, ctx: commands.Context, Role: discord.Role):
        """Sets the Admin Role"""

        try:
            await self.config.guild(ctx.guild).adminRole.set(Role.id)
            await ctx.send("The Admin Role is now set to : {}".format(Role.name))
        except:
            await ctx.send("An error has occured, and cannot set the Mod Role")
            return
        return
