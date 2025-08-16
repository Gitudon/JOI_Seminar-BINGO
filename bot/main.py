# import周り
import discord
from discord.ext import commands
import mysql.connector
import os
import random

# 環境変数の読み込み、クライアントの準備
TOKEN = os.getenv("TOKEN")
CHANNEL = int(os.getenv("CHANNEL"))
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="/", intents=intents)

# ビンゴの状態を管理するグローバル変数
# Preparing: 待機中
# Adding: 参加者追加中
# Running: ビンゴ中
# Choosing: 受賞者選択中
current_mode = "Preparing"


# MySQLの接続設定
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


async def run_select_sql(sql: str, params: tuple, is_all: bool):
    conn = get_connection()
    cursor = conn.cursor(buffered=True)
    if params != ():
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    if is_all:
        result = cursor.fetchall()
    else:
        result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


async def run_insert_or_update_sql(sql: str, params: tuple):
    conn = get_connection()
    cursor = conn.cursor(buffered=True)
    if params != ():
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()


async def is_correct_message(ctx):
    return not (ctx.author.bot) and ctx.channel.id == CHANNEL


async def is_tutor(ctx):
    if not await is_correct_message(ctx):
        return False
    role = discord.utils.get(ctx.author.roles, name="チューター")
    if role not in ctx.author.roles:
        return False
    return True


async def file_exists(ctx):
    if ctx.attachments == []:
        await ctx.channel.send(f"{ctx.author.mention}さん、画像の添付をお願いします。")
        return False
    return True


async def add_line_break(text):
    if text != "":
        text += "\n"
    return text


async def add_mention(lst):
    mentions = []
    for member_name in lst:
        member = await run_select_sql(
            "SELECT mention FROM bingo_participants WHERE name = %s AND is_active = TRUE",
            (member_name,),
            False,
        )
        mention = member_name + "さん"
        if member is not None:
            if member[0] is not None:
                mention = member[0] + "さん"
        mentions.append(mention)
    return mentions


@client.command()
async def test(ctx):
    if not await is_tutor(ctx):
        return
    await ctx.send("Bot is working!")


@client.command()
async def change_mode(ctx, *args):
    global current_mode
    if not await is_tutor(ctx):
        return
    if len(args) != 1:
        await ctx.channel.send("正しい個数の引数が必要です。")
        return
    mode = args[0]
    if mode in ["Preparing", "Adding", "Running", "Choosing"]:
        current_mode = mode
        await ctx.channel.send(f'モードを"{mode}"に変更しました。')
    else:
        await ctx.channel.send("無効なモードです。")


@client.command()
async def link(ctx):
    if not await is_tutor(ctx):
        return
    info = "BINGO CARD:\nhttps://www.oh-benri-tools.com/tools/game/bingo-card"
    await ctx.channel.send(info)


@client.command()
async def show(ctx, *args):
    if not await is_tutor(ctx):
        return
    if len(args) != 1:
        await ctx.channel.send("正しい個数の引数が必要です。")
        return
    if args[0] not in ["mode", "members", "bingo"]:
        await ctx.channel.send("無効な引数です。")
        return
    if args[0] == "mode":
        await ctx.channel.send(f"現在のモード: {current_mode}")
    elif args[0] == "members":
        members = await run_select_sql(
            "SELECT name FROM bingo_participants WHERE is_tutor = FALSE AND is_active = TRUE",
            (),
            True,
        )
        tutor_members = await run_select_sql(
            "SELECT name FROM bingo_participants WHERE is_tutor = TRUE AND is_active = TRUE",
            (),
            True,
        )
        members_list = "\n".join([m[0] for m in members])
        if members_list != "":
            members_list += "\n"
        members_list += "\n".join([(t[0] + "(チューター)") for t in tutor_members])
        if members_list == "":
            await ctx.channel.send("現在参加者はいません。")
            return
        await ctx.channel.send(f"現在の参加者(敬称略):\n\n{members_list}")
    elif args[0] == "bingo":
        numberone_members = await run_select_sql(
            "SELECT name FROM bingo_participants WHERE is_tutor = FALSE AND got_bingo = TRUE AND is_numberone = TRUE AND is_active = TRUE",
            (),
            True,
        )
        bingo_members = await run_select_sql(
            "SELECT name FROM bingo_participants WHERE is_tutor = FALSE AND got_bingo = TRUE AND is_numberone = FALSE AND is_active = TRUE",
            (),
            True,
        )
        tutor_bingo_members = await run_select_sql(
            "SELECT name FROM bingo_participants WHERE is_tutor = TRUE AND got_bingo = TRUE AND is_active = TRUE",
            (),
            True,
        )
        bingo_members_list = "\n".join([(n[0] + "(最速)") for n in numberone_members])
        if bingo_members_list != "":
            bingo_members_list += "\n"
        bingo_members_list += "\n".join([b[0] for b in bingo_members])
        if bingo_members_list != "":
            bingo_members_list += "\n"
        bingo_members_list += "\n".join(
            [(t[0] + "(チューター)") for t in tutor_bingo_members]
        )
        if bingo_members_list == "":
            await ctx.channel.send("現在ビンゴしている人はいません。")
            return
        await ctx.channel.send(f"現在ビンゴしている人(敬称略):\n\n{bingo_members_list}")


@client.command()
async def start(ctx, *arg):
    global current_mode
    if not await is_tutor(ctx):
        return
    if len(arg) != 1:
        await ctx.channel.send("正しい個数の引数が必要です。")
        return
    if arg[0] not in ["add", "bingo"]:
        await ctx.channel.send("正しい引数が必要です。")
        return
    if arg[0] == "add":
        if current_mode == "Preparing":
            current_mode = "Adding"
            await run_insert_or_update_sql(
                "UPDATE bingo_participants SET is_active = FALSE WHERE is_active = TRUE",
                (),
            )
            await ctx.channel.send("参加者の追加を開始しました。")
        elif current_mode == "Adding":
            await ctx.channel.send("参加者の追加はすでに開始されています。")
        elif current_mode == "Running":
            await ctx.channel.send("現在ビンゴ中です。")
        elif current_mode == "Choosing":
            await ctx.channel.send("現在受賞者の選択中です。")
    elif arg[0] == "bingo":
        if current_mode == "Preparing":
            count = await run_select_sql(
                "SELECT COUNT(*) FROM bingo_participants WHERE is_active = TRUE",
                (),
                False,
            )
            count = count[0]
            if count == 0:
                await ctx.channel.send("参加者がいません！")
                return
            current_mode = "Running"
            await ctx.channel.send("ビンゴスタート！")
        elif current_mode == "Adding":
            await ctx.channel.send("現在参加者追加中です。")
        elif current_mode == "Running":
            await ctx.channel.send("ビンゴはすでに開始されています。")
        elif current_mode == "Choosing":
            await ctx.channel.send("現在受賞者の選択中です。")


@client.command()
async def end(ctx, *arg):
    global current_mode
    if not await is_tutor(ctx):
        return
    if len(arg) != 1:
        await ctx.channel.send("正しい個数の引数が必要です。")
        return
    if arg[0] not in ["add", "bingo"]:
        await ctx.channel.send("正しい引数が必要です。")
        return
    if arg[0] == "add":
        if current_mode == "Adding":
            current_mode = "Preparing"
            await ctx.channel.send("参加者の追加を終了しました。")
        elif current_mode == "Preparing":
            await ctx.channel.send("参加者の追加はまだ開始されていません。")
        elif current_mode == "Running":
            await ctx.channel.send("現在ビンゴ中です。")
        elif current_mode == "Choosing":
            await ctx.channel.send("現在受賞者の選択中です。")
    elif arg[0] == "bingo":
        if current_mode == "Preparing":
            await ctx.channel.send("ビンゴはまだ開始されていません。")
        elif current_mode == "Adding":
            await ctx.channel.send("現在参加者追加中です。")
        elif current_mode == "Running":
            current_mode = "Choosing"
            await ctx.channel.send("ビンゴ終了！\n受賞者の選択を開始します。")
        elif current_mode == "Choosing":
            await ctx.channel.send("現在受賞者の選択中です。")


@client.command()
async def cancel(ctx):
    global current_mode
    if not await is_correct_message(ctx):
        return
    if current_mode == "Adding":
        participate = await run_select_sql(
            "SELECT name FROM bingo_participants WHERE is_active = TRUE AND name = %s",
            (ctx.author.display_name,),
            False,
        )
        if participate is None:
            await ctx.channel.send(f"{ctx.author.mention}さんは参加していません。")
            return
        else:
            await run_insert_or_update_sql(
                "UPDATE bingo_participants SET is_active = FALSE WHERE name = %s",
                (ctx.author.display_name,),
            )
            await ctx.channel.send(f"{ctx.author.mention}さんの参加を取り消しました。")
    elif current_mode == "Running":
        member = await run_select_sql(
            "SELECT got_bingo FROM bingo_participants WHERE is_active = TRUE AND name = %s",
            (ctx.author.display_name,),
            False,
        )
        if member is None:
            await ctx.channel.send(f"{ctx.author.mention}さんは参加していません。")
            return
        else:
            got_bingo = member[0]
            if got_bingo != True:
                await ctx.channel.send(
                    f"{ctx.author.mention}さんはビンゴしていません。"
                )
                return
            await run_insert_or_update_sql(
                "UPDATE bingo_participants SET got_bingo = FALSE, is_numberone = FALSE WHERE name = %s",
                (ctx.author.display_name,),
            )
            await ctx.channel.send(
                f"{ctx.author.mention}さんのビンゴを取り消しました。"
            )
    else:
        await ctx.channel.send("現在参加者の操作を受け付けていません。")


@client.command()
async def choice(ctx, *args):
    global current_mode
    if not await is_tutor(ctx):
        return
    if current_mode != "Choosing":
        await ctx.channel.send("現在受賞者の選択中ではありません。")
        return
    if len(args) != 1:
        await ctx.channel.send("正しい個数の引数が必要です。")
        return
    if not args[0].isdigit():
        await ctx.channel.send("引数は数字でなければなりません。")
        return
    num = int(args[0])
    numberone_members = await run_select_sql(
        "SELECT name FROM bingo_participants WHERE is_tutor = FALSE AND got_bingo = TRUE AND is_numberone = TRUE AND is_active = TRUE",
        (),
        True,
    )
    reply = ""
    if len(numberone_members) != 0:
        speed_winners = [n[0] for n in numberone_members]
        mentioned_speed_winners = await add_mention(speed_winners)
        reply += "**最速賞**\n" + "\n".join(mentioned_speed_winners)
    bingo_members = await run_select_sql(
        "SELECT name FROM bingo_participants WHERE is_tutor = FALSE AND got_bingo = TRUE AND is_numberone = FALSE AND is_active = TRUE",
        (),
        True,
    )
    if len(bingo_members) != 0:
        if len(bingo_members) < num:
            await ctx.channel.send("ビンゴした人が指定した数より少ないです。")
            return
        winners = random.sample([b[0] for b in bingo_members], num)
        mentioned_winners = await add_mention(winners)
        reply = await add_line_break(reply)
        reply = await add_line_break(reply)
        reply += "**飛び賞**\n" + "\n".join(mentioned_winners)
    if reply != "":
        await ctx.channel.send("おめでとうございます！\n\n" + reply)
    else:
        await ctx.channel.send("ビンゴした人がいません。")


@client.command()
async def gyakuchoice(ctx, *args):
    global current_mode
    if not await is_tutor(ctx):
        return
    if current_mode != "Choosing":
        await ctx.channel.send("現在受賞者の選択中ではありません。")
        return
    if len(args) != 1:
        await ctx.channel.send("正しい個数の引数が必要です。")
        return
    if not args[0].isdigit():
        await ctx.channel.send("引数は数字でなければなりません。")
        return
    num = int(args[0])
    not_bingo_members = await run_select_sql(
        "SELECT name FROM bingo_participants WHERE is_tutor = FALSE AND got_bingo = FALSE AND is_active = TRUE",
        (),
        True,
    )
    if len(not_bingo_members) != 0:
        if len(not_bingo_members) < num:
            await ctx.channel.send("ビンゴしていない人が指定した数より少ないです。")
            return
        gyaku_winners = random.sample([n[0] for n in not_bingo_members], num)
        mentioned_gyaku_winners = await add_mention(gyaku_winners)
        if mentioned_gyaku_winners != []:
            await ctx.send(
                "おめでとうございます！\n\n**逆ビンゴ賞**\n"
                + "\n".join(mentioned_gyaku_winners)
            )
    else:
        await ctx.send("ビンゴしていない人がいません。")


@client.event
async def on_message(message):
    global current_mode
    if message.content.startswith("/"):
        await client.process_commands(message)
        return
    if not await is_correct_message(message):
        return
    if current_mode == "Adding":
        if not await file_exists(message):
            return
        person = await run_select_sql(
            "SELECT is_active FROM bingo_participants WHERE name = %s",
            (message.author.display_name,),
            False,
        )
        if person is None:
            await run_insert_or_update_sql(
                "INSERT INTO bingo_participants (name, mention) VALUES (%s, %s)",
                (message.author.display_name, message.author.mention),
            )
            if await is_tutor(message):
                await run_insert_or_update_sql(
                    "UPDATE bingo_participants SET is_tutor = TRUE WHERE name = %s",
                    (message.author.display_name,),
                )
                await message.channel.send(
                    f"{message.author.mention}さん(チューター)が参加しました！"
                )
            else:
                await message.channel.send(
                    f"{message.author.mention}さんが参加しました！"
                )
        else:
            is_active = person[0]
            if not is_active:
                await run_insert_or_update_sql(
                    "UPDATE bingo_participants SET mention = %s, is_tutor = FALSE, got_bingo = FALSE, is_numberone = FALSE, is_active = TRUE WHERE name = %s",
                    (
                        message.author.mention,
                        message.author.display_name,
                    ),
                )
                if await is_tutor(message):
                    await run_insert_or_update_sql(
                        "UPDATE bingo_participants SET is_tutor = TRUE WHERE name = %s",
                        (message.author.display_name,),
                    )
                    await message.channel.send(
                        f"{message.author.mention}さん(チューター)が参加しました！"
                    )
                else:
                    await message.channel.send(
                        f"{message.author.mention}さんが参加しました！"
                    )
            else:
                await message.channel.send(
                    f"{message.author.mention}さんはすでに参加しています。"
                )
        return
    elif current_mode == "Running":
        if not await file_exists(message):
            return
        person = await run_select_sql(
            "SELECT got_bingo FROM bingo_participants WHERE is_active = TRUE AND name = %s",
            (message.author.display_name,),
            False,
        )
        if person is None:
            await message.channel.send(
                f"{message.author.mention}さんは参加していません。"
            )
            return
        if not person[0]:
            await run_insert_or_update_sql(
                "UPDATE bingo_participants SET got_bingo = TRUE WHERE name = %s",
                (message.author.display_name,),
            )
            bingo_count = await run_select_sql(
                "SELECT COUNT(*) FROM bingo_participants WHERE is_tutor = FALSE AND got_bingo = TRUE AND is_active = TRUE",
                (),
                False,
            )
            bingo_count = bingo_count[0]
            if bingo_count == 1:
                await run_insert_or_update_sql(
                    "UPDATE bingo_participants SET is_numberone = TRUE WHERE name = %s",
                    (message.author.display_name,),
                )
            tutor = await run_select_sql(
                "SELECT is_tutor FROM bingo_participants WHERE got_bingo = TRUE AND is_active = TRUE AND name = %s",
                (message.author.display_name,),
                False,
            )
            if tutor[0]:
                await message.channel.send(
                    f"{message.author.mention}さん(チューター)がビンゴしました！"
                )
            else:
                await message.channel.send(
                    f"{message.author.mention}さんがビンゴしました！({bingo_count}番目)"
                )
        else:
            await message.channel.send(
                f"{message.author.mention}さんはすでにビンゴしています。"
            )
        return
    else:
        await message.channel.send("現在参加者の操作を受け付けていません。")
        return


client.run(TOKEN)
