import psycopg2
from psycopg2 import sql
import json

with open("credentials.yml", "r") as creds:
    pw = creds.readlines()[0]

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres.barioakzubwwtootaupm",
    "password": pw,
    "host": "aws-0-eu-west-3.pooler.supabase.com",
    "port": 6543,
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

achievements = {"first_flush": {"_id": "first_flush", "name": "First Flush", "rarity": "common", "icon": "first_flush.png", "desc": "Awarded after submitting the first toilet rating."},
                "globetrotter": {"_id": "globetrotter", "name": "Globetrotter", "rarity": "rare", "icon": "globetrotter.png", "desc": "Awarded when a user rates toilets in multiple cities or countries."},
                "toilet_master": {"_id": "toilet_master", "name": "Toilet Connoisseur", "rarity": "epic", "icon": "toilet_connoisseur.png", "desc": "Awarded after rating 10 toilets."},
                "clean_sweep": {"_id": "clean_sweep", "name": "Clean Sweep", "rarity": "epic", "icon": "clean_sweep.png", "desc": "Awarded when a user rates cleanliness with a perfect score (5/5) on 10+ toilets."}}

def acquire(username: str, trophy_name: str):
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Fetch current achievements
                cur.execute("SELECT achievements FROM users WHERE username = %s", (username,))
                existing = cur.fetchone()
                
                current_achievements = existing[0] or []  # Default to empty list if null

                # Prevent duplicates
                if trophy_name in current_achievements:
                    print(f"Trophy '{trophy_name}' already acquired for user {username}")
                    return False, "Achievement already acquired"

                # Add the new achievement
                current_achievements.append(trophy_name)

                # Update the achievements column
                cur.execute(
                    "UPDATE users SET achievements = %s WHERE username = %s",
                    (json.dumps(current_achievements), username),
                )
                print(f"Added trophy '{trophy_name}' for user {username}")
                return True, "Achievement added successfully"
    except Exception as e:
        print(f"Error in acquire: {e}")
        return False, f"Error: {e}"
    finally:
        conn.close()
