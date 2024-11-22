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

def acquire(username: str, achievement: str):
    if not achievement in achievements:
        return "Error, achievement not available"
    
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Fetch the current achievements of the user
                cur.execute("SELECT achievements FROM users WHERE username = %s", (username,))
                user_achievements = cur.fetchone()
                
                if user_achievements:
                    current_achievements = user_achievements[0]  # this should be a list (array)
                else:
                    current_achievements = []

                # Ensure no duplicates by checking if the achievement is already in the list
                if achievement not in current_achievements:
                    # Append the new achievement to the list
                    current_achievements.append(achievement)

                    # Update the user's achievements in the database
                    cur.execute("""
                        UPDATE users 
                        SET achievements = %s
                        WHERE username = %s
                    """, (current_achievements, username))
                    return True, "Achievement added successfully!"
                else:
                    return False, "Achievement already unlocked!"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()