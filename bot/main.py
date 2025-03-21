import discord
from discord.ext import commands
import os
import random

TOKEN =  os.getenv("TOKEN")
CHANNEL =  int(os.getenv("CHANNEL"))
intent = discord.Intents.default()
intent.message_content= True

client = commands.Bot(
    command_prefix='/',
    intents=intent
)

members=[]
bingo=[]
running=[False,False]

@client.event
async def on_message(message):
    global members,bingo,running
    if message.author.bot:
        return
    if message.channel.id!=CHANNEL:
        return
    if message.content==('/test'):
        await message.channel.send("Bot is working!")
        return
    if message.content==('/init'):
        info="BINGO CARD:\nhttps://www.oh-benri-tools.com/tools/game/bingo-card"
        await message.channel.send(info)
        return
    if message.content==('/reset'):
        members=[]
        bingo=[]
        running=[False,False]
        await message.channel.send("リセットしました。")
        return
    if message.content==('/bingo start'):
        if members==[]:
            await message.channel.send("参加者がいません！")
            return
        running=[True,False]
        await message.channel.send("ビンゴスタート！")
        return
    if message.content==('/bingo end'):
        if bingo==[]:
            await message.channel.send("ビンゴはスタートしていません！")
            return
        running=[False,False]
        await message.channel.send("ビンゴ終了！")
        return
    if message.content==('/add start'):
        running=[False,True]
        await message.channel.send("参加者の追加を開始しました。")
        return
    if message.content==('/add end'):
        running=[False,False]
        await message.channel.send("参加者の追加を終了しました。")
        return
    if message.content.startswith('/show'):
        if message.content[6:]=="members":
            if members==[]:
                await message.channel.send("参加者がいません！")
                return
            reply="Members:\n\n"
            for i in range(len(members)):
                reply+=members[i].mention
                if i!=len(members)-1:
                    reply+="\n"
            await message.channel.send(reply)
            return
        elif message.content[6:]=="bingo":
            if bingo==[]:
                await message.channel.send("ビンゴの人はいません！")
                return
            reply="Bingo:\n\n"
            for i in range(len(bingo)):
                reply+=f'{i+1}: {bingo[i].mention}'
                if i!=len(bingo)-1:
                    reply+="\n"
            await message.channel.send(reply)
            return
    if message.content.startswith('/choice'):
        if running==[False,False]:
            num=message.content[8:]
            if num.isdigit():
                num=int(num)
                if num>len(bingo)-1:
                    await message.channel.send("入力が大きすぎます。")
                else:
                    choice=[]
                    choice+=[bingo[0]]
                    bingo=bingo[1:]
                    choiced=random.sample(bingo,num)
                    choice+=choiced
                    reply="Congratulations!\n\n"
                    for i in range(len(choice)):
                        if i==0:
                            reply+="Number-1: "
                        reply+=choice[i].mention
                        if i!=len(choice)-1:
                            reply+="\n"
                    await message.channel.send(reply)
            else:
                await message.channel.send("不正な入力です。")
        else:
            await message.channel.send("ゲームが終了していません！")
        return
    if message.content.startswith('/gyakuchoice'):
        if running==[False,False]:
            num=message.content[13:]
            gyakubingo=[]
            for m in members:
                if m not in bingo:
                    gyakubingo.append(m)
            if num.isdigit():
                if num>len(bingo):
                    await message.channel.send("入力が大きすぎます。")
                else:
                    gyakuchoice=random.sample(gyakubingo,num)
                    reply="Congratulations!\n\n"
                    for i in range(len(gyakuchoice)):
                        reply+=gyakuchoice[i].mention
                        if i!=len(gyakuchoice)-1:
                            reply+="\n"
                    await message.channel.send(reply)
            else:
                await message.channel.send("不正な入力です。")
        else:
            await message.channel.send("ゲームが終了していません！")
        return
    if running[1]:
        if message.attachments!=[]:
            if message.author not in members:
                members.append(message.author)
                await message.channel.send(f'{message.author.mention} が参加しました！')
        if message.content==('/del'):
            if message.author in members:
                members.remove(message.author)
                await message.channel.send(f'{message.author.mention} が参加を取り消しました。')
    elif running[0]:
        if message.attachments!=[]:
            if message.author in members:
                bingo.append(message.author)
                reply=f'{message.author.mention} がビンゴしました！ ('+str(len(bingo))+'番目)'
                await message.channel.send(reply)
    return

client.run(TOKEN)