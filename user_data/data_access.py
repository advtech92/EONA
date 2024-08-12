import sqlite3
import os
from logger import logger


class DataAccessManager:
    def __init__(self, db_path="data/EONA.db"):
        self.db_path = db_path

    def delete_user_data(self, user_id, guild_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM birthdays WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        cursor.execute("DELETE FROM consents WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        conn.commit()
        conn.close()
        logger.info(f"User {user_id} requested data deletion.")

    def view_user_data(self, user_id, guild_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM birthdays WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        birthday = cursor.fetchone()
        conn.close()
        return birthday
