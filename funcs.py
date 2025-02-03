import psycopg
from psycopg import sql
import bcrypt
from geopy.geocoders import Nominatim
import requests
from math import radians, sin, cos, sqrt, atan2
import json
import app
import os
from dotenv import load_dotenv

try:
    load_dotenv()
except:
    pass # :) great code, right?

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def get_db_connection():
    return psycopg.connect(**DB_CONFIG)

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
    except psycopg.errors.UniqueViolation:
        return False, "Username already exists"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

def login(username: str, password: str):
    username = username.replace(" ", "")
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if user and bcrypt.checkpw(password.encode(), user[0].encode()):
                return True, "Success"
            else:
                return False, "Wrong username or password. Remove spaces if entered!"
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
    latitude, longitude = coords
    conn = get_db_connection()

    try:
        with conn:
            with conn.cursor() as cur:
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

                cur.execute(
                    """
                    SELECT toilet_id FROM toilets
                    WHERE latitude = %s AND longitude = %s
                    """,
                    (latitude, longitude)
                )
                result = cur.fetchone()

                if result:
                    toilet_id = result[0]
                else:
                    cur.execute(
                        """
                        INSERT INTO toilets (latitude, longitude)
                        VALUES (%s, %s)
                        RETURNING toilet_id
                        """,
                        (latitude, longitude)
                    )
                    toilet_id = cur.fetchone()[0]

                cur.execute(
                    """
                    INSERT INTO ratings (toilet_id, cleanliness, supplies, privacy, comment, username)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING rating_id
                    """,
                    (toilet_id, cleanliness, supplies, privacy, comment, user)
                )
                rating_id = cur.fetchone()[0]

                cur.execute("SELECT achievements FROM users WHERE username = %s", (user,))
                result = cur.fetchone()
                if result is None:
                    return False, "User not found."

                current_achievements = result[0] or []
                new_achievements = []

                cur.execute("SELECT COUNT(*) FROM ratings WHERE username = %s", (user,))
                rating_count = cur.fetchone()[0]
                if rating_count == 1 and "first_flush" not in current_achievements:
                    new_achievements.append("first_flush")
                    app.add_notification({"title": "New achievement earned!", "text": "Congrats, you earned 'First Flush'!"})

                cur.execute(
                    """
                    SELECT latitude, longitude 
                    FROM toilets t
                    JOIN ratings r ON t.toilet_id = r.toilet_id
                    WHERE r.username = %s
                    """,
                    (user,)
                )
                user_ratings = cur.fetchall()
                if len(user_ratings) > 1:
                    for prev_coords in user_ratings:
                        if distance_between_coords(prev_coords, coords) >= 50 and "globetrotter" not in current_achievements:
                            new_achievements.append("globetrotter")
                            app.add_notification({"title": "New achievement earned!", "text": "Congrats, you earned 'Globetrotter'!"})
                            break

                if cleanliness == 5 and supplies == 5 and privacy == 5 and "clean_sweep" not in current_achievements:
                    new_achievements.append("clean_sweep")
                    app.add_notification({"title": "New achievement earned!", "text": "Congrats, you earned 'Clean Sweep'!"})

                if rating_count >= 10 and "toilet_master" not in current_achievements:
                    new_achievements.append("toilet_master")
                    app.add_notification({"title": "New achievement earned!", "text": "Congrats, you earned 'Toilet Master'!"})

                if new_achievements:
                    updated_achievements = list(set(current_achievements + new_achievements))
                    cur.execute(
                        "UPDATE users SET achievements = %s WHERE username = %s",
                        (json.dumps(updated_achievements), user)
                    )

        return True, f"Rating added successfully with ID {rating_id} for toilet {toilet_id}"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

def get_all_toilets(): # just for inital clicl on explore, to be concise the cards below map. gotta fix actually-..
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
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

                return [{"toilet_id": toilet[0], "latitude": toilet[1], "longitude": toilet[2], "rating_count": toilet[3]} for toilet in toilets]
    except Exception as e:
        return f"Error: {e}"
    
def get_toilets_chunk(start_id, limit):
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        t.toilet_id, 
                        t.latitude, 
                        t.longitude,
                        COUNT(r.rating_id) AS rating_count
                    FROM toilets t
                    LEFT JOIN ratings r ON t.toilet_id = r.toilet_id
                    WHERE t.toilet_id > %s
                    GROUP BY t.toilet_id
                    ORDER BY t.toilet_id
                    LIMIT %s
                """, (start_id, limit))
                toilets = cur.fetchall()

                return [{"toilet_id": toilet[0], "latitude": toilet[1], "longitude": toilet[2], "rating_count": toilet[3]} for toilet in toilets]
    except Exception as e:
        return {"error": str(e)}


def get_toilet_details(toilet_id):
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT latitude, longitude
                    FROM toilets
                    WHERE toilet_id = %s
                """, (toilet_id,))
                toilet = cur.fetchone()
                if not toilet:
                    return None

                latitude, longitude = toilet

                cur.execute("""
                    SELECT cleanliness, supplies, privacy, comment, username
                    FROM ratings
                    WHERE toilet_id = %s
                """, (toilet_id,))
                ratings = cur.fetchall()

                avg_cleanliness = sum(r[0] for r in ratings) / len(ratings) if ratings else 0
                avg_supplies = sum(r[1] for r in ratings) / len(ratings) if ratings else 0
                avg_privacy = sum(r[2] for r in ratings) / len(ratings) if ratings else 0

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

def get_user_ratings(user_id: int):
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
                username = cur.fetchone()
                
                if not username:
                    return {"message": "User not found."}

                username = username[0]

                cur.execute("""
                    SELECT 
                        r.toilet_id,
                        t.latitude,
                        t.longitude,
                        r.cleanliness,
                        r.supplies,
                        r.privacy,
                        r.comment,
                        r.username
                    FROM ratings r
                    JOIN toilets t ON r.toilet_id = t.toilet_id
                    WHERE r.username = %s
                """, (username,))

                ratings = cur.fetchall()

                if not ratings:
                    return []

                return [
                    {
                        "toilet_id": r[0],
                        "latitude": r[1],
                        "longitude": r[2],
                        "cleanliness": r[3],
                        "supplies": r[4],
                        "privacy": r[5],
                        "comment": r[6],
                        "username": r[7]
                    }
                    for r in ratings
                ]
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def check_user_exists(user_id: str):
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users WHERE username = %s", (user_id,))
                user = cur.fetchone()

                if user:
                    return True
                else:
                    return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

def get_username_by_user_id(user_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
            username = cur.fetchone()
            if username:
                return username[0]
            else:
                return None
    except Exception as e:
        return None

def get_user_id_by_username(username):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            user = cur.fetchone()

            if user:
                return user[0]
            else:
                return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        conn.close()

def coords_to_address(latitude, longitude):
    geolocator = Nominatim(user_agent="go2klo_app")
    location = geolocator.reverse((latitude, longitude))
    if location:
        return location.address
    else:
        return "Address not found"
    
def get_achievements_by_user_id(user_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT achievements FROM users WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            if result:
                return True, result[0]
            else:
                return False, "User not found."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

def distance_between_coords(coord1, coord2):
    R = 6371  # Radius of the Earth in kilometers
    lat1, lon1 = map(radians, coord1)
    lat2, lon2 = map(radians, coord2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

def get_users_sorted_by_ratings():
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        u.username, 
                        COUNT(r.rating_id) AS rating_count
                    FROM users u
                    LEFT JOIN ratings r ON u.username = r.username
                    GROUP BY u.username
                    ORDER BY rating_count DESC
                    LIMIT 50
                """)
                users = cur.fetchall()

                return [{"username": user[0], "rating_count": user[1]} for user in users]
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def get_reviewed_countries(user):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT t.country 
                FROM toilets t
                JOIN ratings r ON t.toilet_id = r.toilet_id
                WHERE r.username = %s AND t.country IS NOT NULL
                """,
                (user,)
            )
            countries = [row[0] for row in cur.fetchall()]
            return countries
    except Exception as e:
        print(f"Error fetching countries: {e}")
        return []
    finally:
        conn.close()

def get_achievements(user):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT achievements FROM users WHERE username = %s", (user,))
            result = cur.fetchone()
            if result:
                return json.loads(result[0]) if result[0] else []
            else:
                return []
    except Exception as e:
        print(f"Error fetching achievements: {e}")
        return []
    finally:
        conn.close()

def get_country_from_coordinates(lat, lon):
    geolocator = Nominatim(user_agent="go2klo_app")
    try:
        location = geolocator.reverse((lat, lon))
        if location and "address" in location.raw:
            return location.raw["address"].get("country", "unknown")
    except Exception as e:
        print(f"Error fetching country: {e}")
    return "unknown"

def convert_usernames_to_lowercase():
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, username FROM users")
                users = cur.fetchall()
                
                for user_id, username in users:
                    lower_username = username.lower()
                    cur.execute(
                        "UPDATE users SET username = %s WHERE user_id = %s",
                        (lower_username, user_id)
                    )
        return True, "Usernames converted to lowercase successfully."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

def get_top_10_toilets():
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        t.toilet_id, 
                        t.latitude, 
                        t.longitude,
                        COUNT(r.rating_id) AS rating_count
                    FROM toilets t
                    LEFT JOIN ratings r ON t.toilet_id = r.toilet_id
                    GROUP BY t.toilet_id
                    ORDER BY rating_count DESC
                    LIMIT 10
                """)
                toilets = cur.fetchall()

                return [{"toilet_id": toilet[0], "latitude": toilet[1], "longitude": toilet[2], "rating_count": toilet[3]} for toilet in toilets]
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def convert_ratings_usernames_to_lowercase():
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT rating_id, username FROM ratings")
                ratings = cur.fetchall()
                
                for rating_id, username in ratings:
                    lower_username = username.lower()
                    cur.execute(
                        "UPDATE ratings SET username = %s WHERE rating_id = %s",
                        (lower_username, rating_id)
                    )
        return True, "Ratings usernames converted to lowercase successfully."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()