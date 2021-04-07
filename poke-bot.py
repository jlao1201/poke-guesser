"""
    PokeGuesser Discord Bot. Given an image of a Pokemon, guess the name!
"""

import discord
from discord.ext import commands
from pymongo import MongoClient
import random
from fuzzywuzzy import fuzz
import config


client = commands.Bot(command_prefix='!', help_command=None)

cluster = MongoClient(f"mongodb+srv://{config.DB_USER}:{config.DB_PASS}@cluster0.pvvk0.mongodb.net/myFirstDatabase"
                      f"?retryWrites=true&w=majority")
db = cluster['poke-guesser']
collection = db['pokemon']
count = collection.count_documents({})
gens = {0: (0, count), 1: (0, 151), 2: (151, 251), 3: (251, 386), 4: (386, 493),
        5: (494, 649), 6: (649, 721), 7: (722, 809), 8: (809, count)}


@client.event
async def on_ready():
    print('Bot is ready.')


@client.group(invoke_without_command=True)
async def help(ctx):
    """ Help command; lists all available commands. """
    help_embed = discord.Embed(title='Help',
                               description='Use !help <command> for extended information on a specific command.',
                               color=ctx.author.color)
    help_embed.add_field(name='Pokemon', value='pokeguesser')
    help_embed.add_field(name='General', value='purge')
    await ctx.send(embed=help_embed)


@help.command()
async def pokeguesser(ctx):
    """ Help description for pokeguesser command. """
    embed = discord.Embed(title='pokeguesser',
                          description='Initiates a round of PokeGuesser',
                          color=ctx.author.color)
    embed.add_field(name='Syntax', value='!pokeguesser [generation number]')
    await ctx.send(embed=embed)


@client.command()
async def pokeguesser(ctx, gen=0, difficulty='normal'):
    """ Command for PokeGuesser game; guess the Pokemon given an image. """
    game_on = True
    score = 0
    # Main game loop
    while game_on:
        # Get random Pokemon from database given a generation
        temp = collection.find()[random.randrange(gens[int(gen)][0], gens[int(gen)][1])]
        img_url = temp['img-src-large']
        name = temp['name']

        # Create Embed for Pokemon image
        poke_embed = discord.Embed(title="Who's that Pokemon?",
                                   color=discord.Color.red())
        poke_embed.set_image(url=img_url)
        poke_embed.set_footer(text='Image from https://pokemondb.net')
        # print(img_url)
        await ctx.send(embed=poke_embed)

        # Check that response is from user who started game
        def check(m):
            return m.author == ctx.author and m.author.id == ctx.author.id

        # Determine if user got the correct answer or not
        msg = await client.wait_for('message', check=check)
        acc_ratio = fuzz.ratio(msg.content.lower(), name.lower())
        if difficulty == 'normal':
            if msg.content.lower() == name.lower():
                await ctx.send(f":white_check_mark:Correct! It's {name}!")
                score += 1
            else:
                game_on = False
                user_id = msg.author.id
                user_name = msg.author.name
                high_score = update_score(user_id, score)
                await ctx.send(f":x:Wrong! It's {name}!")
                # Display the user's score and high score after game ends
                stats_embed = discord.Embed(title=f'Pokeguesser stats for {user_name}',
                                            color=discord.Color.red(),
                                            description=f'Score for this round: {score}\nHigh Score: {high_score}')
                stats_embed.set_thumbnail(url=ctx.author.avatar_url)
                await ctx.send(embed=stats_embed)
        elif difficulty == 'easy':
            if msg.content.lower() == name.lower():
                await ctx.send(f":white_check_mark:Correct! It's {name}!")
                score += 1
            elif acc_ratio > 80:
                await ctx.send(f":white_check_mark:Close enough! It's {name}!")
                score += 1
            else:
                game_on = False
                user_id = msg.author.id
                user_name = msg.author.name
                high_score = update_score(user_id, score)
                await ctx.send(f":x:Wrong! It's {name}!")
                # Display the user's score and high score after game ends
                stats_embed = discord.Embed(title=f'Pokeguesser stats for {user_name}',
                                            color=discord.Color.red(),
                                            description=f'Score for this round: {score}\nHigh Score: {high_score}')
                stats_embed.set_thumbnail(url=ctx.author.avatar_url)
                await ctx.send(embed=stats_embed)


def update_score(user_id, user_score):
    """ Get the high score of a given user. """
    user_collection = db['players']
    docs = user_collection.find({'id': user_id})
    num_docs = docs.count()
    if num_docs != 0:
        # If user is already in the database
        for doc in docs:
            # Check and update high score
            if doc['high_score'] < user_score:
                user_collection.update_one({'id': user_id}, {'$set': {'high_score': user_score}})
                return user_score
            else:
                return doc['high_score']
    else:
        # If user is not yet in the database
        user_collection.insert_one({'id': user_id, 'high_score': user_score})
        return user_score


client.run(config.BOT_TOKEN)
