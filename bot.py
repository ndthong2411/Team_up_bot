import discord
from discord.ext import commands
import nest_asyncio
import asyncio
import os
from server import keep_alive
from random import shuffle


nest_asyncio.apply()

intents = discord.Intents.default()
intents.message_content = True  # For newer versions of discord.py

bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to store queues for each server (guild)
server_queues = {}

# Initialize queue for a guild if not present
def init_guild_queue(guild_id):
    if guild_id not in server_queues:
        server_queues[guild_id] = {'queue': [], 'high_priority': []}

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')

@bot.command()
async def join(ctx):
    """Add a user to the queue."""
    guild_id = ctx.guild.id
    init_guild_queue(guild_id)
    queue = server_queues[guild_id]['queue']
    high_priority = server_queues[guild_id]['high_priority']
    
    if ctx.author not in queue and ctx.author not in high_priority:
        queue.append(ctx.author)
        await ctx.send(f'{ctx.author.mention} has joined the queue. Total in queue: {len(queue)}')
        if len(queue) + len(high_priority) >= 12:
            await create_matchup(ctx)
    else:
        await ctx.send(f'{ctx.author.mention}, you are already in the queue or high-priority list.')

@bot.command()
async def leave(ctx):
    """Remove a user from the queue."""
    guild_id = ctx.guild.id
    init_guild_queue(guild_id)
    queue = server_queues[guild_id]['queue']
    high_priority = server_queues[guild_id]['high_priority']
    
    if ctx.author in queue:
        queue.remove(ctx.author)
        await ctx.send(f'{ctx.author.mention} has left the queue. Total in queue: {len(queue)}')
    elif ctx.author in high_priority:
        high_priority.remove(ctx.author)
        await ctx.send(f'{ctx.author.mention} has left the high-priority list. Total in queue: {len(queue)}')
    else:
        await ctx.send(f'{ctx.author.mention}, you are not in the queue or high-priority list.')

@bot.command()
async def status(ctx):
    """Show the current queue status."""
    guild_id = ctx.guild.id
    init_guild_queue(guild_id)
    queue = server_queues[guild_id]['queue']
    high_priority = server_queues[guild_id]['high_priority']
    
    if queue or high_priority:
        queue_status = ', '.join([user.mention for user in queue])
        high_priority_status = ', '.join([user.mention for user in high_priority])
        await ctx.send(f'Queue ({len(queue)}): {queue_status}')
        if high_priority:
            await ctx.send(f'High-Priority List ({len(high_priority)}): {high_priority_status}')
    else:
        await ctx.send('The queue is currently empty.')

async def create_matchup(ctx):
    """Create and announce the teams when at least 12 members are available."""
    guild_id = ctx.guild.id
    queue = server_queues[guild_id]['queue']
    high_priority = server_queues[guild_id]['high_priority']
    
    # Consolidate the high-priority and queue for selection
    combined_queue = high_priority + queue
    shuffle(combined_queue)  # Shuffle the combined list to make random teams

    # Select the first 12 people for the match
    selected_players = combined_queue[:12]
    leftover_players = combined_queue[12:]

    # Divide into two teams of 6
    team1 = selected_players[:6]
    team2 = selected_players[6:12]

    # Clear current queue and set leftover players as high-priority
    server_queues[guild_id]['queue'] = []
    server_queues[guild_id]['high_priority'] = leftover_players

    # Send the team composition to the channel
    await ctx.send('Teams are ready!')
    await ctx.send('**Team 1:**\n' + '\n'.join([user.mention for user in team1]))
    await ctx.send('**Team 2:**\n' + '\n'.join([user.mention for user in team2]))
    
    # Inform users about the new high-priority list
    if leftover_players:
        await ctx.send('The following users are on the high-priority list for the next match:\n' +
                       ', '.join([user.mention for user in leftover_players]))

@bot.command()
async def clear_queue(ctx):
    """Clear the current queue and high-priority list."""
    guild_id = ctx.guild.id
    init_guild_queue(guild_id)
    server_queues[guild_id]['queue'] = []
    server_queues[guild_id]['high_priority'] = []
    await ctx.send('The queue and high-priority list have been cleared.')

# Keep the web server alive
keep_alive()

# Run the bot using the token from environment variable
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
