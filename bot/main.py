import discord
from discord.ext import commands
import os
import random

TOKEN =  os.getenv("TOKEN")
intent = discord.Intents.default()
intent.message_content= True

client = commands.Bot(
    command_prefix='/',
    intents=intent
)

channels=[]
members=[]
bingo=[]
running=[False,False]

@client.event
async def on_message(message):
    global members,bingo,running
    if message.author.bot:
        return
    if message.channel not in channels:
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
        await message.channel.send("Reset done!")
        return
    if message.content==('/bingo start'):
        if members==[]:
            await message.channel.send("No members!")
            return
        running=[True,False]
        await message.channel.send("BINGO START!")
        return
    if message.content==('/bingo end'):
        if bingo==[]:
            await message.channel.send("No BINGO!")
            return
        running=[False,False]
        await message.channel.send("BINGO END!")
        return
    if message.content==('/add start'):
        running=[False,True]
        await message.channel.send("MEMBER ADDING START!")
        return
    if message.content==('/add end'):
        running=[False,False]
        await message.channel.send("MEMBER ADDING END!")
        return
    if message.content==('/show members'):
        if members==[]:
            await message.channel.send("No members!")
            return
        reply="Members:\n\n"
        for i in range(len(members)):
            reply+=members[i].mention
            if i!=len(members)-1:
                reply+="\n"
        await message.channel.send(reply)
        return
    if message.content.startswith('/choice'):
        if running==[False,False]:
            num=message.content[8:]
            if num.isdigit():
                num=int(num)
                if num>len(bingo)-1:
                    await message.channel.send("Too many input!")
                else:
                    choice=[]
                    choice+=[bingo[0]]
                    bingo=bingo[1:]
                    random.sample(bingo,num)
                    reply="Congratulations!\n\n"
                    for i in range(len(choice)):
                        reply+=choice[i].mention
                        if i!=len(choice)-1:
                            reply+="\n"
                    await message.channel.send(reply)
            else:
                await message.channel.send("Invalid input!")
        else:
            await message.channel.send("The game has not ended!")
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
                    await message.channel.send("Too many input!")
                else:
                    random.sample(gyakubingo,num)
                    reply="Congratulations!\n\n"
                    for i in range(len(choice)):
                        reply+=choice[i].mention
                        if i!=len(choice)-1:
                            reply+="\n"
                    await message.channel.send(reply)
            else:
                await message.channel.send("Invalid input!")
        else:
            await message.channel.send("The game has not ended!")
        return
    if running[1]:
        if message.attachments!=[]:
            if message.author not in members:
                members.append(message.author)
                await message.channel.send(f'{message.author.mention} was added!')
        if message.content==('/del'):
            if message.author in members:
                members.remove(message.author)
                await message.channel.send(f'{message.author.mention} was removed!')
    elif running[0]:
        if message.attachments!=[]:
            if message.author in members:
                bingo.append(message.author)
                reply=f'{message.author.mention} got BINGO! ('+str(len(bingo))+')'
                await message.channel.send(reply)
    return

client.run(TOKEN)