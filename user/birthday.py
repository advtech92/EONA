import discord
from discord.ext import tasks
from discord import app_commands
import sqlite3
import os
from logger import logger
from user_data.consent import ConsentManager
from user_data.data_access import DataAccessManager
import datetime
import config


class Birthday:
    def __init__(self, client):
        self.client = client
        self.db_path = "data/elysia.db"
        self.logger = logger
        self.consent_manager = ConsentManager(self.db_path)
        self.data_access_manager = DataAccessManager(self.db_path)
        self.birthday_channel_id = None  # Initially unset

        # Ensure that the database and tables are set up
        self.ensure_db()

    def ensure_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS birthdays (
                user_id INTEGER,
                guild_id INTEGER,
                user_name TEXT,
                birthday TEXT,
                PRIMARY KEY (user_id, guild_id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                guild_id INTEGER PRIMARY KEY,
                birthday_channel_id INTEGER
            );
        """)
        conn.commit()
        conn.close()

    def set_birthday_channel(self, guild_id, channel_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO settings (guild_id, birthday_channel_id) 
            VALUES (?, ?)
            ON CONFLICT(guild_id) 
            DO UPDATE SET birthday_channel_id = excluded.birthday_channel_id;
        """, (guild_id, channel_id))
        conn.commit()
        conn.close()
        self.birthday_channel_id = channel_id  # Store in the instance

    def get_birthday_channel(self, guild_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT birthday_channel_id FROM settings WHERE guild_id = ?", (guild_id,))
        row = cursor.fetchone()
        conn.close()

        if row and row[0]:
            return row[0]  # Return the set channel ID
        else:
            return config.DEFAULT_CHANNEL_ID  # Fall back to default from config

    async def send_birthday_alert(self, guild, message):
        channel_id = self.get_birthday_channel(guild.id)
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(message)
        else:
            self.logger.error(f"Channel with ID {channel_id} not found in guild {guild.name}")

    async def delete_birthday(self, user_id, guild_id):
        self.data_access_manager.delete_data(user_id, guild_id)

    async def get_birthday(self, user_id, guild_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT birthday FROM birthdays WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    @tasks.loop(hours=24)
    async def check_birthdays(self):
        today = datetime.date.today().strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, guild_id FROM birthdays WHERE birthday = ?", (today,))
        rows = cursor.fetchall()
        conn.close()

        for user_id, guild_id in rows:
            guild = self.client.get_guild(int(guild_id))
            if guild:
                user = guild.get_member(int(user_id))
                if user:
                    message = f"Happy birthday {user.mention}! 🎉🎂"
                    await self.send_birthday_alert(guild, message)

    async def setup_hook(self):
        self.check_birthdays.start()
        self.logger.info("Birthday module loaded")

    def setup(self, tree: discord.app_commands.CommandTree):
        @tree.command(name="set_birthday_channel", description="Set the channel for birthday alerts")
        @app_commands.checks.has_permissions(administrator=True)
        async def set_birthday_channel(interaction: discord.Interaction, channel: discord.TextChannel):
            guild_id = interaction.guild.id
            self.set_birthday_channel(guild_id, channel.id)
            await interaction.response.send_message(f"Birthday alerts will now be sent to {channel.mention}.", ephemeral=True)


        @tree.command(name="consent", description="Give consent for data storage.")
        async def consent_command(interaction: discord.Interaction):
            self.consent_manager.give_consent(interaction.user.id, interaction.guild.id)
            await interaction.response.send_message(f"{interaction.user.mention}, your consent has been recorded.", ephemeral=True)

        @tree.command(name="view_data", description="View your stored data.")
        async def view_data_command(interaction: discord.Interaction):
            data = self.data_access_manager.view_user_data(interaction.user.id, interaction.guild.id)
            if data:
                await interaction.response.send_message(f"{interaction.user.mention}, your stored data: {data}", ephemeral=True)
            else:
                await interaction.response.send_message(f"{interaction.user.mention}, no data found.", ephemeral=True)

        @tree.command(name="delete_data", description="Delete your stored data.")
        async def delete_data_command(interaction: discord.Interaction):
            self.data_access_manager.delete_user_data(interaction.user.id, interaction.guild.id)
            await interaction.response.send_message(f"{interaction.user.mention}, your data has been deleted.", ephemeral=True)

        @tree.command(name="set_birthday", description="Set your birthday (YYYY-MM-DD)")
        async def set_birthday_command(interaction: discord.Interaction):
            await interaction.response.send_modal(BirthdayModal(self))

        @tree.command(name="get_birthday", description="Check your birthday")
        async def get_birthday_command(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            guild_id = str(interaction.guild.id)
            birthday = await self.get_birthday(user_id, guild_id)
            if birthday:
                await interaction.response.send_message(f"Your birthday has been set to {birthday}", ephemeral=True)
            else:
                await interaction.response.send_message("Your birthday has not been set. Please use `/set_birthday` to set your birthday.", ephemeral=True)

        if not tree.get_command("consent"):
            tree.add_command(consent_command)
        if not tree.get_command("view_data"):
            tree.add_command(view_data_command)
        if not tree.get_command("delete_data"):
            tree.add_command(delete_data_command)
        if not tree.get_command("set_birthday"):
            tree.add_command(set_birthday_command)
        if not tree.get_command("get_birthday"):
            tree.add_command(get_birthday_command)
        if not tree.get_command("set_birthday_channel"):
            tree.add_command(set_birthday_channel)


class BirthdayModal(discord.ui.Modal, title="Set your birthday"):
    birthday = discord.ui.TextInput(label="Your birthday", placeholder="YYYY-MM-DD", style=discord.TextStyle.short, required=True)

    def __init__(self, birthday_module):
        super().__init__()
        self.birthday_module = birthday_module

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        try:
            # Validate the date format
            birthday_str = self.birthday.value
            birthday = datetime.strptime(birthday_str, "%Y-%m-%d").date()

            # Proceed to set the birthday if valid
            await self.birthday_module.set_birthday(interaction, user_id, guild_id, birthday_str)
        except ValueError:
            await interaction.response.send_message("Invalid date format. Please enter the date in YYYY-MM-DD format.", ephemeral=True)


def setup(client):
    birthday_module = Birthday(client)
    client.add_cog(birthday_module)
    client.birthday_module = birthday_module