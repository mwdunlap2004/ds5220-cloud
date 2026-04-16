import os
import random
import boto3
import httpx
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)  # commands.when_mentioned_or("!") is used to make the bot respond to !ping and @bot ping

REGISTER_URL = "https://x5gjqnvpo8.execute-api.us-east-1.amazonaws.com/api/register"

async def setup_hook() -> None:  # This function is automatically called before the bot starts
    await bot.tree.sync()   # This function is used to sync the slash commands with Discord it is mandatory if you want to use slash commands

bot.setup_hook = setup_hook  # Not the best way to sync slash commands, but it will have to do for now. A better way is to create a command that calls the sync function.

@bot.event
async def on_ready() -> None:  # This event is called when the bot is ready
    print(f"Logged in as {bot.user}")

@bot.tree.command()
async def ping(inter: discord.Interaction) -> None:
    await inter.response.send_message(f"> Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="register", description="Add your project to this bot. Send as PROJECT-ID, USERNAME, and URL.")
async def register(inter: discord.Interaction, project_id: str, username: str, url: str) -> None:
    project_id = project_id.strip()
    username = username.strip()
    url = url.strip()

    if not project_id or not username or not url:
        await inter.response.send_message(
            "Missing values. Usage: `/register <project_id> <username> <url>` "
            "— example: `/register mybot nem2p https://myapi.com/`"
        )

    if " " in project_id or " " in username:
        await inter.response.send_message("`project_id` and `username` cannot contain spaces.")
    if not (url.startswith("http://") or url.startswith("https://")):
        await inter.response.send_message(f"`{url}` is not a valid URL — it must start with http:// or https://.")

    await inter.response.defer()
    try:
        ddb = boto3.resource('dynamodb')
        table = ddb.Table('cloud-bots')
        table.put_item(Item={'botname': project_id, 'user': username, 'boturl': url})
        await inter.followup.send(f"Project **{project_id}** registered successfully for `{username}`.")
    except Exception as e:
        await inter.followup.send(f"Error registering project: {e}")

@bot.tree.command(description="Get the methods for a project by PROJECT-ID.")
async def projects(inter: discord.Interaction, project_id: str) -> None:
    project_id = project_id.strip()
    await inter.response.defer()

    try:
        ddb = boto3.resource('dynamodb')
        table = ddb.Table('cloud-bots')
        response = table.get_item(Key={'botname': project_id})
    except Exception as e:
        await inter.followup.send(f"Error fetching project from DynamoDB: {e}")
        return

    item = response.get('Item')
    if not item:
        await inter.followup.send(f"No project found with PROJECT-ID `{project_id}`.")
        return

    boturl = (item.get('boturl') or '').strip()
    user = item.get('user')
    if not boturl:
        await inter.followup.send(f"Project `{project_id}` has no `boturl` configured.")
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            http_response = await client.get(boturl)
            http_response.raise_for_status()
            data = http_response.json()
    except Exception as e:
        await inter.followup.send(f"Error fetching methods from `{boturl}`: {e}")
        return

    methods = data.get('methods', [])
    if not methods or len(methods) < 2:
        await inter.followup.send(f"Expected more than 1 method from `{boturl}`, got {len(methods)}.")
        return

    methods_response = "\n".join(f"- {m}" for m in methods)
    await inter.followup.send(
        f"**{project_id}** (Owner: {user})\nAvailable methods:\n{methods_response}"
    )

@bot.command(name="projects")
async def projects_prefix(ctx: commands.Context, *, name: str = "nem2p") -> None:
    await ctx.send("Output for the nem2p project.")

bot.run(TOKEN)
