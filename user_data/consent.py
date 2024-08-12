import sqlite3
import os
from logger import logger


class ConsentManager:
    def __init__(self, db_path="data/EONA.db"):
        self.db_path = db_path
        self.ensure_db()

    def ensure_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS consents (
            user_id INTEGER,
            guild_id INTEGER,
            consent INTEGER,
            PRIMARY KEY (user_id, guild_id)
            );""")
        conn.commit()
        conn.close()
        logger.info("Consent table ensured")

    async def request_consent(self, interaction):
        await interaction.response.send_message(
            "To use this feature, please consent to our data policy. "
            "Type `/consent` to agree, or `/decline` to disagree.",
            ephemeral=True
        )

    def give_consent(self, user_id, guild_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO consents (user_id, guild_id, consent)
                       VALUES (?, ?, 1) ON CONFLICT(user_id, guild_id)
                       DO UPDATE SET consent = 1;""",
                       (user_id, guild_id))
        conn.commit()
        conn.close()
        logger.info(f"User {user_id} consented to data storage.")

    def has_consent(self, user_id, guild_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT consent FROM consents WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        row = cursor.fetchone()
        conn.close()
        return row and row[0] == 1  # Returns True if consent is given
