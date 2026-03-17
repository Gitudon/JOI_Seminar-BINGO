from common import *
from use_mysql import UseMySQL


class Logic:
    @staticmethod
    async def is_correct_message(ctx):
        return not (ctx.author.bot) and ctx.channel.id == CHANNEL

    @classmethod
    async def is_tutor(cls, ctx):
        if not await cls.is_correct_message(ctx):
            return False
        role = discord.utils.get(ctx.author.roles, name="チューター")
        if role not in ctx.author.roles:
            return False
        return True

    @staticmethod
    async def file_exists(ctx):
        if ctx.attachments == []:
            return False
        return True

    @staticmethod
    async def add_line_break(text):
        if text != "":
            text += "\n"
        return text

    @staticmethod
    async def add_mention(lst):
        mentions = []
        for member_name in lst:
            member = await UseMySQL.run_sql(
                "SELECT mention FROM bingo_participants WHERE name = %s AND is_active = TRUE",
                (member_name,),
            )
            mention = member_name + "さん"
            if member != []:
                if member[0][0]:
                    mention = member[0][0] + "さん"
            mentions.append(mention)
        return mentions
