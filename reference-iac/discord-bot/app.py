import os
import random
import boto3
import httpx
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = "1458485887896649759"
ddb = boto3.resource('dynamodb', region_name='us-east-1')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)  # commands.when_mentioned_or("!") is used to make the bot respond to !ping and @bot ping

REGISTER_URL = "https://x5gjqnvpo8.execute-api.us-east-1.amazonaws.com/api/register"

async def setup_hook() -> None:  # This function is automatically called before the bot starts
    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)  # Guild-scoped sync is instant — good for dev iteration.
    else:
        await bot.tree.sync()  # Global sync — can take up to 1 hour to propagate.

bot.setup_hook = setup_hook  # Not the best way to sync slash commands, but it will have to do for now. A better way is to create a command that calls the sync function.

@bot.event
async def on_ready() -> None:  # This event is called when the bot is ready
    print(f"Logged in as {bot.user}")

# ping the bot
@bot.tree.command()
async def ping(inter: discord.Interaction) -> None:
    await inter.response.send_message(f"> Pong! {round(bot.latency * 1000)}ms")

# allow users to register their projects
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
        table = ddb.Table('cloud-bots')
        table.put_item(Item={'botname': project_id, 'user': username, 'boturl': url})
        await inter.followup.send(f"Project **{project_id}** registered successfully for `{username}`.")
    except Exception as e:
        await inter.followup.send(f"Error registering project: {e}")

# list all projects
@bot.tree.command(name="list", description="Get a list of student projects from this bot.")
async def list_projects(inter: discord.Interaction) -> None:
    await inter.response.defer()
    try:
        table = ddb.Table('cloud-bots')
        response = table.scan()
    except Exception as e:
        await inter.followup.send(f"Error fetching projects: {e}")
        return

    projects_list = sorted(response.get('Items', []), key=lambda p: p['botname'].lower())
    if not projects_list:
        await inter.followup.send("No projects registered yet. Use `/register` to add one.")
        return

    header = "Please select a student to get the sub-commands for.\nThen call a project and view its resources with `/project <project-id>`.\n\n"
    lines = [f"**{p['botname']}** (Owner: {p['user']})" for p in projects_list]

    chunk, first = header, True
    for line in lines:
        if len(chunk) + len(line) + 1 > 1900:
            await inter.followup.send(chunk)
            chunk = ""
        chunk += line + "\n"
    if chunk.strip():
        await inter.followup.send(chunk)

# get the resources for a project
@bot.tree.command(description="Get the resources for a project by PROJECT-ID, or call a specific resource.")
async def project(inter: discord.Interaction, project_id: str, resource: str = None) -> None:
    project_id = project_id.strip()
    resource = resource.strip() if resource else None
    await inter.response.defer()

    try:
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

    if resource:
        target_url = f"{boturl.rstrip('/')}/{resource}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                http_response = await client.get(target_url)
                http_response.raise_for_status()
                try:
                    payload = http_response.json()
                    body = payload.get('response', payload) if isinstance(payload, dict) else payload
                except Exception:
                    body = http_response.text
        except Exception as e:
            await inter.followup.send(f"Error calling `{target_url}`: {e}")
            return

        await inter.followup.send(f"{body}")
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            http_response = await client.get(boturl)
            http_response.raise_for_status()
            data = http_response.json()
    except Exception as e:
        await inter.followup.send(f"Error fetching resources from `{boturl}`: {e}")
        return

    about = (data.get('about') or '').strip()
    resources = data.get('resources', [])
    if not resources or len(resources) < 2:
        await inter.followup.send(f"Expected more than 1 resource from `{boturl}`, got {len(resources)}.")
        return

    resources_response = "\n".join(f"- {r}" for r in resources)
    await inter.followup.send(
        f"**{project_id}** (Owner: {user})\n**About:** {about}\n\n**API**: `{boturl}` > [Link]({boturl})\n\n**Available resources:**\n{resources_response}"
    )

bot.run(TOKEN)
