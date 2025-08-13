# import周り
import discord
from discord.ext import commands
import mysql.connector
import os
import random

# 環境変数の読み込み、クライアントの準備
TOKEN = os.getenv("TOKEN")
CHANNEL = int(os.getenv("CHANNEL"))
intent = discord.Intents.default()
intent.message_content = True
client = commands.Bot(command_prefix="/", intents=intent)

# MySQLの接続設定
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    username=os.getenv("DB_USERNAME"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
)
cursor = conn.cursor(buffered=True)

# ビンゴの状態を管理するグローバル変数
# Preparing: 待機中
# Adding: 参加者追加中
# Running: ビンゴ中
# Choosing: 受賞者選択中
current_mode = "Preparing"


async def is_correct_message(ctx):
    return ctx.author.bot and ctx.channel.id == CHANNEL


async def is_tutor(ctx):
    role = discord.utils.get(ctx.author.roles, name="チューター")
    if role not in ctx.author.roles:
        await ctx.channel.send("チューター以外はコマンドを実行できません。")
        return False
    return True


async def add_mention(lst):
    for i in range(len(lst)):
        lst[i] = lst[i].mention
    return lst


@client.command()
async def test(ctx):
    if not await is_tutor(ctx):
        return
    await ctx.send("Bot is working!")


@client.command()
async def change_mode(ctx, mode: str):
    global current_mode
    if not await is_tutor(ctx):
        return
    if mode in ["Preparing", "Adding", "Running", "Choosing"]:
        current_mode = mode
        await ctx.channel.send(f"モードを {mode} に変更しました。")
    else:
        await ctx.channel.send("無効なモードです。")


@client.command()
async def link(ctx):
    if not await is_tutor(ctx):
        return
    info = "BINGO CARD:\nhttps://www.oh-benri-tools.com/tools/game/bingo-card"
    await ctx.channel.send(info)


@client.command()
async def reset(ctx):
    global current_mode
    if not await is_tutor(ctx):
        return
    current_mode = "Preparing"
    cursor.execute("UPDATE bingo_members SET is_active = FALSE WHERE is_active = TRUE")
    conn.commit()
    await ctx.channel.send("初期状態にリセットしました。")


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
            await ctx.channel.send("参加者の追加を開始しました。")
        elif current_mode == "Adding":
            await ctx.channel.send("参加者の追加はすでに開始されています。")
        elif current_mode == "Running":
            await ctx.channel.send("現在ビンゴ中です。")
        elif current_mode == "Choosing":
            await ctx.channel.send("現在受賞者の選択中です。")
    elif arg[0] == "bingo":
        if current_mode == "Preparing":
            cursor.execute("SELECT COUNT(*) FROM bingo_members WHERE is_active = TRUE")
            count = cursor.fetchone()[0]
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
        cursor.execute("SELECT name FROM bingo_members WHERE is_active = TRUE")
        members = cursor.fetchall()
        if members == []:
            await ctx.channel.send("現在参加者はいません。")
            return
        member_list = "\n".join([m[0] for m in members])
        await ctx.channel.send(f"現在の参加者:\n\n{member_list}")
    elif args[0] == "bingo":
        cursor.execute(
            "SELECT name FROM bingo_members WHERE is_bingo = TRUE AND is_active = TRUE"
        )
        bingo_members = cursor.fetchall()
        if bingo_members == []:
            await ctx.channel.send("現在ビンゴした人はいません。")
            return
        bingo_list = "\n".join([b[0] for b in bingo_members])
        await ctx.channel.send(f"現在ビンゴしている人:\n\n{bingo_list}")


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
    cursor.execute(
        "SELECT name FROM bingo_members WHERE is_tutor = FALSE AND is_bingo = TRUE AND is_numberone = TRUE AND is_active = TRUE"
    )
    numberone_members = cursor.fetchall()
    reply = ""
    if len(numberone_members) != 0:
        speed_winners = await add_mention([n[0] for n in numberone_members])
        reply += "最速賞:\n" + "\n".join(speed_winners)
    cursor.execute(
        "SELECT name FROM bingo_members WHERE is_tutor = FALSE AND is_bingo = TRUE AND is_numberone = FALSE AND is_active = TRUE"
    )
    bingo_members = cursor.fetchall()
    if len(bingo_members) != 0:
        if len(bingo_members) < num:
            await ctx.channel.send("ビンゴした人が指定した数より少ないです。")
            return
        winners = await add_mention(random.sample([b[0] for b in bingo_members], num))
        reply += "\n飛び賞:\n" + "\n".join(winners)
    if reply != "":
        await ctx.channel.send("おめでとうございます！\n\n" + reply)


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
    cursor.execute(
        "SELECT name FROM bingo_members WHERE is_tutor = FALSE AND is_bingo = FALSE AND is_active = TRUE"
    )
    non_bingo_members = cursor.fetchall()
    if len(non_bingo_members) < num:
        await ctx.channel.send("ビンゴしていない人が指定した数より少ないです。")
        return
    winners = await add_mention(random.sample([n[0] for n in non_bingo_members], num))
    await ctx.send("おめでとうございます！\n\n逆ビンゴ賞:" + "\n".join(winners))


@client.command()
async def cancel(ctx):
    global current_mode
    if current_mode == "Adding":
        cursor.execute(
            "SELECT name FROM bingo_members WHERE is_active = TRUE AND name = %s",
            (ctx.author.display_name,),
        )
        if cursor.fetchone() is None:
            await ctx.channel.send(
                f"{ctx.author.display_name.mention}さんは参加していません。"
            )
            return
        else:
            cursor.execute(
                "UPDATE bingo_members SET is_active = FALSE WHERE name = %s",
                (ctx.author.display_name,),
            )
            conn.commit()
            await ctx.channel.send(
                f"{ctx.author.display_name}さんの参加を取り消しました。"
            )
    elif current_mode == "Running":
        cursor.execute(
            "SELECT name, is_bingo FROM bingo_members WHERE is_active = TRUE AND name = %s",
            (ctx.author.display_name,),
        )
        member = cursor.fetchone()
        if member == []:
            await ctx.channel.send(
                f"{ctx.author.display_name.mention}さんは参加していません。"
            )
            return
        else:
            if member[1] != True:
                await ctx.channel.send(
                    f"{ctx.author.display_name.mention}さんはビンゴしていません。"
                )
                return
            cursor.execute(
                "UPDATE bingo_members SET is_bingo = FALSE WHERE name = %s",
                (ctx.author.display_name,),
            )
            conn.commit()
            await ctx.channel.send(
                f"{ctx.author.display_name.mention}さんのビンゴを取り消しました。"
            )


@client.event
async def on_message(message):
    global current_mode
    if await is_correct_message(message):
        return
    if message.attachments == []:
        await message.channel.send("画像の添付をしてください。")
        return
    if current_mode == "Adding":
        cursor.execute(
            "SELECT is_active FROM bingo_members WHERE name = %s",
            (message.author.display_name,),
        )
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO bingo_members (name) VALUES (%s)",
                (message.author.display_name,),
            )
            conn.commit()
            await message.channel.send(
                f"{message.author.display_name.mention}さんが参加しました！"
            )
            if is_tutor(message):
                cursor.execute(
                    "UPDATE bingo_members SET is_tutor = TRUE WHERE name = %s",
                    (message.author.display_name,),
                )
                conn.commit()
        else:
            is_active = cursor.fetchone()[0]
            if not is_active:
                cursor.execute(
                    "UPDATE bingo_members SET is_bingo = FALSE, is_numberone = FALSE, is_active = TRUE WHERE name = %s",
                    (message.author.display_name,),
                )
                conn.commit()
                await message.channel.send(
                    f"{message.author.display_name.mention}さんが参加しました！"
                )
                if is_tutor(message):
                    cursor.execute(
                        "UPDATE bingo_members SET is_tutor = TRUE WHERE name = %s",
                        (message.author.display_name,),
                    )
                    conn.commit()
            else:
                await message.channel.send(
                    f"{message.author.display_name.mention}さんはすでに参加しています。"
                )
    elif current_mode == "Running":
        cursor.execute(
            "SELECT name FROM bingo_members WHERE is_active = TRUE AND name = %s",
            (message.author.display_name,),
        )
        if cursor.fetchone() is None:
            await message.channel.send(
                f"{message.author.display_name.mention}さんは参加していません。"
            )
            return
        cursor.execute(
            "SELECT is_bingo FROM bingo_members WHERE name = %s",
            (message.author.display_name,),
        )
        is_bingo = cursor.fetchone()[0]
        if not is_bingo:
            cursor.execute(
                "UPDATE bingo_members SET is_bingo = TRUE WHERE name = %s",
                (message.author.display_name,),
            )
            conn.commit()
            cursor.execute(
                "SELECT COUNT(*) FROM bingo_members WHERE is_tutor = FALSE AND  is_bingo = TRUE AND is_active = TRUE"
            )
            bingo_count = cursor.fetchone()[0]
            if bingo_count == 1:
                cursor.execute(
                    "UPDATE bingo_members SET is_numberone = TRUE WHERE name = %s",
                    (message.author.display_name,),
                )
                conn.commit()
            cursor.execute(
                "SELECT is_tutor FROM bingo_members WHERE is_bingo = TRUE AND is_active = TRUE"
            )
            is_tutor = cursor.fetchone()[0]
            if is_tutor:
                await message.channel.send(
                    f"{message.author.display_name.mention}さん(チューター)がビンゴしました！"
                )
            else:
                await message.channel.send(
                    f"{message.author.display_name.mention}さんがビンゴしました！({bingo_count}番目)"
                )
        else:
            await message.channel.send(
                f"{message.author.display_name.mention}さんはすでにビンゴしています。"
            )
    else:
        await message.channel.send("現在参加者の操作を受け付けていません。")


client.run(TOKEN)
