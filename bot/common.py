import os
import random
import discord
from discord.ext import commands
import mysql.connector

TOKEN = os.getenv("TOKEN")
CHANNEL = int(os.getenv("CHANNEL"))
