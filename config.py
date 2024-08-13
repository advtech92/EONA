from dotenv import load_dotenv
import os

load_dotenv()

config = {
    "TOKEN": os.getenv("DISCORD_TOKEN"),
    "DEFAULT_CHANNEL_ID": os.getenv("DEFAULT_BIRTHDAY_CHANNEL_ID"),
    "modules": {
        'birthday': {'enabled': True},
    }
}
