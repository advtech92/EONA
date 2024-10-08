from config import config
import discord
from logger import logger

logger.info("Starting Elysia...")

TOKEN = config["TOKEN"]

intents = discord.Intents.default()


class Elysia(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.load_modules()

    async def setup_hook(self):
        logger.info("Setting up...")
        await self.tree.sync()
        logger.info("Commands Synced")

    def load_modules(self):
        try:
            from config import config
        except ImportError:
            logger.error("config.py not found")
        try:
            if config["modules"]["birthday"]["enabled"]:
                from user.birthday import Birthday
                birthday = Birthday(self)
                birthday.setup(self.tree)
                logger.info("Birthday module loaded")
        except KeyError:
            logger.error("Birthday module not enabled")


client = Elysia()


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")

client.run(TOKEN)
