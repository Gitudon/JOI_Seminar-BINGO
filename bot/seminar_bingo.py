from common import *
from logic import Logic
from use_mysql import UseMySQL

# クライアントの準備
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="/", intents=intents)
# ビンゴの状態を管理するグローバル変数
# Preparing: 待機中
# Adding   : 参加者追加中
# Running  : ビンゴ中
# Choosing : 受賞者選択中
current_mode = "Preparing"


@client.command()
async def test(ctx):
    if not await Logic.is_tutor(ctx):
        return
    await ctx.send("JOI Seminar Bingo Bot is working!")


# 現在のモードを変更する
@client.command()
async def change_mode(ctx, *args):
    global current_mode
    if not await Logic.is_tutor(ctx):
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
    if not await Logic.is_tutor(ctx):
        return
    info = "BINGO CARD:\nhttps://www.oh-benri-tools.com/tools/game/bingo-card"
    await ctx.channel.send(info)


@client.command()
async def show(ctx, *args):
    if not await Logic.is_tutor(ctx):
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
        members = await UseMySQL.run_sql(
            "SELECT name FROM bingo_participants WHERE is_tutor = FALSE AND is_active = TRUE ORDER BY name",
            (),
        )
        tutor_members = await UseMySQL.run_sql(
            "SELECT name FROM bingo_participants WHERE is_tutor = TRUE AND is_active = TRUE ORDER BY name",
            (),
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
        numberone_members = await UseMySQL.run_sql(
            "SELECT name FROM bingo_participants WHERE is_tutor = FALSE AND got_bingo = TRUE AND is_numberone = TRUE AND is_active = TRUE ORDER BY name",
            (),
        )
        bingo_members = await UseMySQL.run_sql(
            "SELECT name FROM bingo_participants WHERE is_tutor = FALSE AND got_bingo = TRUE AND is_numberone = FALSE AND is_active = TRUE ORDER BY name",
            (),
        )
        tutor_bingo_members = await UseMySQL.run_sql(
            "SELECT name FROM bingo_participants WHERE is_tutor = TRUE AND got_bingo = TRUE AND is_active = TRUE ORDER BY name",
            (),
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
    if not await Logic.is_tutor(ctx):
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
            await UseMySQL.run_sql(
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
            count = await UseMySQL.run_sql(
                "SELECT COUNT(*) FROM bingo_participants WHERE is_active = TRUE",
                (),
            )
            count = count[0][0]
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
    if not await Logic.is_tutor(ctx):
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
    if not await Logic.is_correct_message(ctx):
        return
    if current_mode == "Adding":
        participate = await UseMySQL.run_sql(
            "SELECT name FROM bingo_participants WHERE is_active = TRUE AND name = %s",
            (ctx.author.display_name,),
        )
        if participate == []:
            await ctx.channel.send(f"{ctx.author.mention}さんは参加していません。")
            return
        else:
            await UseMySQL.run_sql(
                "UPDATE bingo_participants SET is_active = FALSE WHERE name = %s",
                (ctx.author.display_name,),
            )
            await ctx.channel.send(f"{ctx.author.mention}さんの参加を取り消しました。")
    elif current_mode == "Running":
        member = await UseMySQL.run_sql(
            "SELECT got_bingo FROM bingo_participants WHERE is_active = TRUE AND name = %s",
            (ctx.author.display_name,),
        )
        if member == []:
            await ctx.channel.send(f"{ctx.author.mention}さんは参加していません。")
            return
        else:
            got_bingo = member[0][0]
            if got_bingo != True:
                await ctx.channel.send(
                    f"{ctx.author.mention}さんはビンゴしていません。"
                )
                return
            await UseMySQL.run_sql(
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
    if not await Logic.is_tutor(ctx):
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
    if num <= 0:
        await ctx.channel.send("正の整数を指定してください。")
        return
    numberone_members = await UseMySQL.run_sql(
        "SELECT name FROM bingo_participants WHERE is_tutor = FALSE AND got_bingo = TRUE AND is_numberone = TRUE AND is_active = TRUE ORDER BY name",
        (),
    )
    reply = ""
    if len(numberone_members) != 0:
        speed_winners = [n[0] for n in numberone_members]
        mentioned_speed_winners = await Logic.add_mention(speed_winners)
        reply += "**最速賞**\n" + "\n".join(mentioned_speed_winners)
    bingo_members = await UseMySQL.run_sql(
        "SELECT name FROM bingo_participants WHERE is_tutor = FALSE AND got_bingo = TRUE AND is_numberone = FALSE AND is_active = TRUE ORDER BY name",
        (),
    )
    if len(bingo_members) != 0:
        if len(bingo_members) < num:
            await ctx.channel.send("ビンゴした人が指定した数より少ないです。")
            return
        winners = random.sample([b[0] for b in bingo_members], num)
        mentioned_winners = await Logic.add_mention(winners)
        reply = await Logic.add_line_break(reply)
        reply = await Logic.add_line_break(reply)
        reply += "**飛び賞**\n" + "\n".join(mentioned_winners)
    if reply != "":
        await ctx.channel.send("おめでとうございます！\n\n" + reply)
        current_mode = "Preparing"
    else:
        await ctx.channel.send("ビンゴした人がいません。")


# 逆ビンゴを選ぶときChoosingにもどすのがダサい
# ビンゴ集計モード→逆ビンゴ集計モード
@client.command()
async def gyakuchoice(ctx, *args):
    global current_mode
    if not await Logic.is_tutor(ctx):
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
    if num <= 0:
        await ctx.channel.send("正の整数を指定してください。")
        return
    not_bingo_members = await UseMySQL.run_sql(
        "SELECT name FROM bingo_participants WHERE is_tutor = FALSE AND got_bingo = FALSE AND is_active = TRUE",
        (),
    )
    if len(not_bingo_members) != 0:
        if len(not_bingo_members) < num:
            await ctx.channel.send("ビンゴしていない人が指定した数より少ないです。")
            return
        gyaku_winners = random.sample([n[0] for n in not_bingo_members], num)
        mentioned_gyaku_winners = await Logic.add_mention(gyaku_winners)
        if mentioned_gyaku_winners != []:
            await ctx.send(
                "おめでとうございます！\n\n**逆ビンゴ賞**\n"
                + "\n".join(mentioned_gyaku_winners)
            )
            current_mode = "Preparing"
    else:
        await ctx.send("ビンゴしていない人がいません。")


@client.event
async def on_message(message):
    global current_mode
    if message.content.startswith("/"):
        await client.process_commands(message)
        return
    if not await Logic.is_correct_message(message):
        return
    if current_mode == "Adding":
        if not await Logic.file_exists(message):
            await message.channel.send(
                f"{message.author.mention}さん、画像の添付をお願いします。"
            )
            return
        person = await UseMySQL.run_sql(
            "SELECT is_active FROM bingo_participants WHERE name = %s",
            (message.author.display_name,),
        )
        if person == []:
            await UseMySQL.run_sql(
                "INSERT INTO bingo_participants (name, mention) VALUES (%s, %s)",
                (message.author.display_name, message.author.mention),
            )
            if await Logic.is_tutor(message):
                await UseMySQL.run_sql(
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
            is_active = person[0][0]
            if not is_active:
                await UseMySQL.run_sql(
                    "UPDATE bingo_participants SET mention = %s, is_tutor = FALSE, got_bingo = FALSE, is_numberone = FALSE, is_active = TRUE WHERE name = %s",
                    (
                        message.author.mention,
                        message.author.display_name,
                    ),
                )
                if await Logic.is_tutor(message):
                    await UseMySQL.run_sql(
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
        if not await Logic.file_exists(message):
            await message.channel.send(
                f"{message.author.mention}さん、画像の添付をお願いします。"
            )
            return
        person = await UseMySQL.run_sql(
            "SELECT got_bingo FROM bingo_participants WHERE is_active = TRUE AND name = %s",
            (message.author.display_name,),
        )
        if person == []:
            await message.channel.send(
                f"{message.author.mention}さんは参加していません。"
            )
            return
        if not person[0][0]:
            await UseMySQL.run_sql(
                "UPDATE bingo_participants SET got_bingo = TRUE WHERE name = %s",
                (message.author.display_name,),
            )
            bingo_count = await UseMySQL.run_sql(
                "SELECT COUNT(*) FROM bingo_participants WHERE is_tutor = FALSE AND got_bingo = TRUE AND is_active = TRUE",
                (),
            )
            bingo_count = bingo_count[0][0]
            tutor = await UseMySQL.run_sql(
                "SELECT is_tutor FROM bingo_participants WHERE got_bingo = TRUE AND is_active = TRUE AND name = %s",
                (message.author.display_name,),
            )
            is_tutor = tutor[0][0]
            if is_tutor:
                await message.channel.send(
                    f"{message.author.mention}さん(チューター)がビンゴしました！"
                )
            else:
                if bingo_count == 1:
                    await UseMySQL.run_sql(
                        "UPDATE bingo_participants SET is_numberone = TRUE WHERE name = %s",
                        (message.author.display_name,),
                    )
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
