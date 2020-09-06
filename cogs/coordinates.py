import discord
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice
import asyncio
from discord.ext import commands
import aiosqlite
from utils import pages, group_list, numbered


class coordinates(commands.Cog):
    """Commands to create and store coordinates for your Minecraft server"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['cs'])
    async def coordset(self, ctx, x: int, z: int, y=62):
        """Sets the coord of the user using format: (x) (z) (y defaults to 62 if not stated)
        e.g : $cs 50 50 62
        alias: 'cs'"""
        await ctx.message.delete()
        sql_create_coords_table = """CREATE TABLE IF NOT EXISTS coords (
                                        user_id integer,
                                        usernick text, 
                                        base_coords text,
                                        guild_id integer
                                        );"""
        ints = [x, z, y]
        if y > 256:
            await ctx.send('Y level cant be higher than 256 blocks :b')
        else:
            str_of_coords = "/".join([str(int) for int in ints])
            async with aiosqlite.connect("coorddata") as db:
                await db.execute(sql_create_coords_table)
                await db.execute(
                    """INSERT INTO coords(user_id, usernick, base_coords, guild_id) VALUES (?,?,?,?)""",
                    (ctx.author.id, ctx.author.display_name, str_of_coords, ctx.guild.id,))
                await db.commit()
            embed_set = discord.Embed(
                title=f'Coords set for {ctx.author.display_name} as {str_of_coords}', colour=0xFFAE00)
            await ctx.send(embed=embed_set)

    @commands.command()
    async def coords(self, ctx, user: discord.Member):
        """Returns the coords of the user mentioned
        e.g: $coords @tigersharkpr"""
        await ctx.message.delete()
        async with aiosqlite.connect("coorddata") as db:
            async with db.execute("SELECT * FROM coords WHERE guild_id=? and user_id=?",
                                  (ctx.guild.id, user.id,)) as cursor:
                rows = await cursor.fetchall()
        if not rows:
            embed_nocrds = discord.Embed(
                title=f'No coords set for {user.display_name}', colour=0xFF0000)
            await ctx.send(embed=embed_nocrds)
        else:
            coords_list = f"{user.display_name}'s coords:\n(x)/(z)/(y)\n"
            for i in rows:
                coords_list += f"{i[2]}\n"
            embed_coords = discord.Embed(title=f"{coords_list}", colour=0xFFAE00)
            embed_coords.set_thumbnail(url=user.avatar_url)
            await ctx.send(embed=embed_coords)

    @commands.command()
    async def coordel(self, ctx):
        """Deletes the coords of the author of the message from the database"""
        await ctx.message.delete()
        confirmation = BotConfirmation(ctx, 0xFFAE00)
        await confirmation.confirm("Are you sure?")
        if confirmation.confirmed:
            await confirmation.update("Confirmed", color=0xFFAE00)
            async with aiosqlite.connect("coorddata") as db:
                await db.execute("DELETE FROM coords WHERE guild_id=? and user_id=?", (
                    ctx.guild.id, ctx.author.id,))
                await db.commit()
            embed_delete = discord.Embed(
                title=f"{ctx.author.display_name}'s coords deleted", colour=0xFFAE00)
            await ctx.send(embed=embed_delete)
            await asyncio.sleep(1)
            await ctx.send('Now you live nowhere dummy :b')

        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xff5555)

    @commands.command(aliases=['allcds'])
    async def allcoords(self, ctx):
        """Returns a list of the coords from all users
         alias: 'allcds'"""
        await ctx.message.delete()
        embed_error = discord.Embed(title='No coords set', colour=0xFF0000)
        async with aiosqlite.connect("coorddata") as db:
            async with db.execute(
                    "SELECT user_id, base_coords FROM coords WHERE guild_id=?", (ctx.guild.id,)) as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    await ctx.send(embed=embed_error)
                else:
                    await (BotEmbedPaginator(ctx, pages(
                        numbered([f"{ctx.guild.get_member(r[0])}: {r[1]}" for r in rows]),
                        n=10, title=f'Coordinates for {ctx.guild}'))).run()

    @commands.command(aliases=['delucds'])
    @commands.has_permissions(administrator=True)
    async def delusercoords(self, ctx, user: discord.Member):
        """*ADMIN ONLY* Users with the administrator permission can delete all coords from the mentioned user
        e.g: $delucds @tigersharkpr
        alias: 'delcds'"""
        await ctx.message.delete()
        confirmation = BotConfirmation(ctx, 0xFFAE00)
        await confirmation.confirm("Are you sure?")
        if confirmation.confirmed:
            await confirmation.update("Confirmed", color=0xFFAE00)
            async with aiosqlite.connect("coorddata") as db:
                await db.execute("DELETE FROM coords WHERE guild_id=? and user_id=?", (
                    ctx.guild.id, user.id,))
                await db.commit()
            embed_delete = discord.Embed(
                title=f"{ctx.author.display_name}'s coords deleted",
                description=f'Coords deleted by {ctx.author} ', colour=0xFFAE00)
            await ctx.send(embed=embed_delete)
        else:
            await confirmation.update("Not confirmed", hide_author=True, color=0xff5555)

    @commands.command(aliases=['smisc'])
    @commands.has_permissions(administrator=True)
    async def setmisccoords(self, ctx, name: str, x: int, z: int, y=62):
        """*ADMIN ONLY* Sets a miscellaneous coordinate for the server, e.g: end portal coords, spawn, etc
        If the name has more than 1 word please wrap it in double quotes, e.g: "Mining District"
        e.g: '$setmisccoords "end portal" (x) (z) (y defaults to 62 if not stated)
        alias: smisc"""
        await ctx.message.delete()
        ints = [x, z, y]
        str_of_coords = "/".join([str(int) for int in ints])
        async with aiosqlite.connect("coorddata") as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS misc (
                                name text,
                                coordinates text,
                                creator integer,
                                guild_id integer
                                );""")
            await db.execute("""INSERT INTO misc(name, coordinates, creator, guild_id) VALUES(?,?,?,?)""",
                             (name, str_of_coords, ctx.author.id, ctx.guild.id))
            await db.commit()
        embed_set = discord.Embed(
            title=f'Misc coords for {name} set as {str_of_coords}',
            description=f'By {ctx.author}', colour=0xFFAE00)
        await ctx.send(embed=embed_set)

    @commands.command(aliases=['allmisc'])
    async def viewallmisccoords(self, ctx):
        """Returns all the misc coords of the current server
        alias: 'allmisc'"""
        await ctx.message.delete()
        embed_error = discord.Embed(title='No misc coords set', colour=0xFF0000)
        async with aiosqlite.connect("coorddata") as db:
            async with db.execute(
                    "SELECT name, coordinates FROM misc WHERE guild_id=?", (ctx.guild.id,)) as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    await ctx.send(embed=embed_error)
                else:
                    await (BotEmbedPaginator(ctx, pages(
                        numbered([f"{r[0]}: {r[1]}" for r in rows]),
                        n=10, title=f'Misc coordinates for {ctx.guild}'))).run()

    @commands.command(aliases=['delmisc'])
    @commands.has_permissions(administrator=True)
    async def deletemisccoords(self, ctx, name: str):
        """*ADMIN ONLY* Deletes the misc coord belonging to the name stated
        e.g : $delmisc "end portal"
        alias: 'delmisc'"""
        await ctx.message.delete()
        async with aiosqlite.connect("coorddata") as db:
            await db.execute("""DELETE FROM misc WHERE name=? AND guild_id=?""", (name, ctx.guild.id,))
            await db.commit()
        embed_del = discord.Embed(
            title=f'Misc coords for {name} deleted', description=f'Deleted by {ctx.author}', colour=0xFF0000)
        await ctx.send(embed=embed_del)


def setup(bot):
    bot.add_cog(coordinates(bot))
