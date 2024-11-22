import psycopg2
from psycopg2 import sql
import bcrypt
from geopy.geocoders import Nominatim
import requests
from math import radians, sin, cos, sqrt, atan2

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

def register(username: str, password: str):
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username, hashed_password.decode()),
                )
        return True, "Success"
    except psycopg2.errors.UniqueViolation:
        return False, "Username already exists"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

def login(username: str, password: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if user and bcrypt.checkpw(password.encode(), user[0].encode()):
                return True, "Success"
            else:
                return False, "Wrong username or password"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

def get_coordinates(location_name):
    geolocator = Nominatim(user_agent="go2klo_app")

    location = geolocator.geocode(location_name)

    if location:
        return location.latitude, location.longitude
    else:
        return None, None
    
def create_rating(cleanliness: int, supplies: int, privacy: int, comment: str, coords: tuple, user: str):
    """
    Adds a rating for a toilet at the specified coordinates.
    
    Args:
        cleanliness (int): Rating for cleanliness (1-5).
        supplies (int): Rating for supplies (1-5).
        privacy (int): Rating for privacy (1-5).
        comment (str): Optional comment.
        coords (tuple): Tuple of (latitude, longitude) for the toilet.
        user (str): username from login/registering

    Returns:
        tuple: (bool, str) indicating success and a message.
    """
    latitude, longitude = coords
    conn = get_db_connection()

    try:
        with conn:
            with conn.cursor() as cur:
                # Check if the user has already rated this toilet
                cur.execute(
                    """
                    SELECT 1 FROM ratings
                    WHERE toilet_id IN (
                        SELECT toilet_id FROM toilets
                        WHERE latitude = %s AND longitude = %s
                    ) AND username = %s
                    """,
                    (latitude, longitude, user)
                )
                if cur.fetchone():
                    return False, "You have already rated this toilet."

                # Check if the toilet already exists
                cur.execute(
                    """
                    SELECT toilet_id FROM toilets
                    WHERE latitude = %s AND longitude = %s
                    """,
                    (latitude, longitude),
                )
                result = cur.fetchone()

                if result:
                    toilet_id = result[0]  # Get existing toilet_id
                else:
                    # Insert a new toilet entry
                    cur.execute(
                        """
                        INSERT INTO toilets (latitude, longitude)
                        VALUES (%s, %s)
                        RETURNING toilet_id
                        """,
                        (latitude, longitude),
                    )
                    toilet_id = cur.fetchone()[0]  # Get the new toilet_id

                # Insert the rating along with the username (user)
                cur.execute(
                    """
                    INSERT INTO ratings (toilet_id, cleanliness, supplies, privacy, comment, username)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING rating_id
                    """,
                    (toilet_id, cleanliness, supplies, privacy, comment, user)  # username will now be passed here
                )

                rating_id = cur.fetchone()[0]  # Fetch the auto-generated rating_id

        return True, f"Rating added successfully with ID {rating_id} for toilet {toilet_id}"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

def get_all_toilets():
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                # SQL query that joins the toilets table with the ratings table
                # and counts the number of ratings for each toilet
                cur.execute("""
                    SELECT 
                        t.toilet_id, 
                        t.latitude, 
                        t.longitude,
                        COUNT(r.rating_id) AS rating_count
                    FROM toilets t
                    LEFT JOIN ratings r ON t.toilet_id = r.toilet_id
                    GROUP BY t.toilet_id
                """)
                toilets = cur.fetchall()

                # Return list of dictionaries for each toilet with its coordinates and rating count
                return [{"toilet_id": toilet[0], "latitude": toilet[1], "longitude": toilet[2], "rating_count": toilet[3]} for toilet in toilets]
    except Exception as e:
        return f"Error: {e}"
    
def get_toilet_details(toilet_id):
    """
    Fetches the details of a specific toilet, including its ratings and average scores.
    
    Args:
        toilet_id (int): The ID of the toilet.

    Returns:
        dict: A dictionary containing toilet details, including ratings and average scores.
    """
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                # Fetch the toilet's basic information and ratings
                cur.execute("""
                    SELECT latitude, longitude
                    FROM toilets
                    WHERE toilet_id = %s
                """, (toilet_id,))
                toilet = cur.fetchone()
                if not toilet:
                    return None  # Toilet not found

                latitude, longitude = toilet

                # Fetch the ratings for this toilet
                cur.execute("""
                    SELECT cleanliness, supplies, privacy, comment, username
                    FROM ratings
                    WHERE toilet_id = %s
                """, (toilet_id,))
                ratings = cur.fetchall()

                # Calculate averages for cleanliness, supplies, and privacy
                avg_cleanliness = sum(r[0] for r in ratings) / len(ratings) if ratings else 0
                avg_supplies = sum(r[1] for r in ratings) / len(ratings) if ratings else 0
                avg_privacy = sum(r[2] for r in ratings) / len(ratings) if ratings else 0

                # Return the toilet details along with the ratings and averages
                return {
                    "toilet_id": toilet_id,
                    "latitude": latitude,
                    "longitude": longitude,
                    "ratings": [
                        {
                            "username": r[4],
                            "cleanliness": r[0],
                            "supplies": r[1],
                            "privacy": r[2],
                            "comment": r[3]
                        }
                        for r in ratings
                    ],
                    "avg_cleanliness": avg_cleanliness,
                    "avg_supplies": avg_supplies,
                    "avg_privacy": avg_privacy
                }
    except Exception as e:
        return {"error": str(e)}