from dotenv import load_dotenv
import os

load_dotenv()

config = {
    "TOKEN": os.getenv("DISCORD_TOKEN"),
    "modules": {
        'birthday': {'enabled': True},
    }
}
