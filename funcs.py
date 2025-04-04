import psycopg
from psycopg import sql
import bcrypt
from geopy.geocoders import Nominatim
import requests
from math import radians, sin, cos, sqrt, atan2
import json
import app
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv
import random, string, base64

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

alphabet = string.ascii_lowercase
enc_key = os.getenv("ENC_KEY")

api_key = os.getenv("MAIL")
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key["api-key"] = api_key
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

def encode(clear):
    key = enc_key
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        if clear[i] in alphabet and key_c in alphabet:
            enc_c = alphabet[(alphabet.index(clear[i]) + alphabet.index(key_c)) % 26]
        else:
            enc_c = clear[i]
        enc.append(enc_c)
    return "".join(enc)

def decode(enc):
    key = enc_key
    dec = []
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        if enc[i] in alphabet and key_c in alphabet:
            dec_c = alphabet[(alphabet.index(enc[i]) - alphabet.index(key_c)) % 26]
        else:
            dec_c = enc[i]
        dec.append(dec_c)
    return "".join(dec)

def generate_auth_code():
    first_digit = str(random.randint(1, 9))
    remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(5)])
    return first_digit + remaining_digits

def generate_password_reset_code():
    return "".join(random.choices(string.ascii_lowercase, k=16))

def send_verification_email(recipient_email, auth_code):
    sender = {"name": "go2klo", "email": "noreply@go2klo.com"}
    to = [{"email": recipient_email, "name": recipient_email}]
    
    email_data = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        sender=sender,
        template_id=1,
        params={"auth_code": auth_code}
    )
    
    try:
        api_instance.send_transac_email(email_data)
        return True, f"Verification email sent to {recipient_email}"
    except ApiException as e:
        return False, f"Error sending email: {e}"
    
def send_password_reset_email(recipient_email, pwlink):
    sender = {"name": "go2klo", "email": "noreply@go2klo.com"}
    to = [{"email": recipient_email, "name": recipient_email}]
    
    email_data = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        sender=sender,
        template_id=2,
        params={"pwlink": f"https://go2klo.com/r/{pwlink}"}
    )
    
    try:
        api_instance.send_transac_email(email_data)
    except ApiException as e:
        print(f"Error sending email: {e}")

def reset_password(username, new_password):
    hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET password = %s WHERE username = %s",
                    (hashed_password.decode(), username)
                )
        return True, "Password reset successfully"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

def get_db_connection():
    return psycopg.connect(**DB_CONFIG)

def register(username: str, password: str, email: str):
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    email = encode(email)
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                    (username, hashed_password.decode(), email),
                )
        return True, "Success"
    except psycopg.errors.UniqueViolation:
        return False, "Username or email already exists"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

def check_username_or_email_exists(username: str, email: str):
    conn = get_db_connection()
    email = encode(email)

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE username = %s OR email = %s", (username, email))
            user = cur.fetchone()
            if user:
                return True, "Username or email already exists"
            else:
                return False, "Username and email are available"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

def get_username_by_email(email: str):
    conn = get_db_connection()
    email = encode(email)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username FROM users WHERE email = %s", (email,))
            result = cur.fetchone()
            if result:
                return result[0]
            else:
                return None
    except Exception as e:
        return None
    finally:
        conn.close()

def login(identifier: str, password: str):
    identifier = identifier.replace(" ", "")
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username, password, email FROM users WHERE username = %s OR email = %s", (identifier, encode(identifier)))
            user = cur.fetchone()
            if user and bcrypt.checkpw(password.encode(), user[1].encode()):
                return True, "Success"
            return False, "Wrong username/email or password. Remove spaces if entered!"
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

# def create_rating(cleanliness: int, supplies: int, privacy: int, comment: str, coords: tuple, user: str):
#     latitude, longitude = coords
#     conn = get_db_connection()

#     try:
#         with conn:
#             with conn.cursor() as cur:
#                 cur.execute(
#                     """
#                     SELECT 1 FROM ratings
#                     WHERE toilet_id IN (
#                         SELECT toilet_id FROM toilets
#                         WHERE latitude = %s AND longitude = %s
#                     ) AND username = %s
#                     """,
#                     (latitude, longitude, user)
#                 )
#                 if cur.fetchone():
#                     return False, "You have already rated this toilet."

#                 cur.execute(
#                     """
#                     SELECT toilet_id FROM toilets
#                     WHERE latitude = %s AND longitude = %s
#                     """,
#                     (latitude, longitude)
#                 )
#                 result = cur.fetchone()

#                 if result:
#                     toilet_id = result[0]
#                 else:
#                     cur.execute(
#                         """
#                         INSERT INTO toilets (latitude, longitude)
#                         VALUES (%s, %s)
#                         RETURNING toilet_id
#                         """,
#                         (latitude, longitude)
#                     )
#                     toilet_id = cur.fetchone()[0]

#                 cur.execute(
#                     """
#                     INSERT INTO ratings (toilet_id, cleanliness, supplies, privacy, comment, username)
#                     VALUES (%s, %s, %s, %s, %s, %s)
#                     RETURNING rating_id
#                     """,
#                     (toilet_id, cleanliness, supplies, privacy, comment, user)
#                 )
#                 rating_id = cur.fetchone()[0]

#                 cur.execute("SELECT achievements FROM users WHERE username = %s", (user,))
#                 result = cur.fetchone()
#                 if result is None:
#                     return False, "User not found."

#                 current_achievements = result[0] or []
#                 new_achievements = []

#                 cur.execute("SELECT COUNT(*) FROM ratings WHERE username = %s", (user,))
#                 rating_count = cur.fetchone()[0]
#                 if rating_count == 1 and "first_flush" not in current_achievements:
#                     new_achievements.append("first_flush")
#                     app.add_notification({"title": "New achievement earned!", "text": "Congrats, you earned 'First Flush'!"})

#                 cur.execute(
#                     """
#                     SELECT latitude, longitude 
#                     FROM toilets t
#                     JOIN ratings r ON t.toilet_id = r.toilet_id
#                     WHERE r.username = %s
#                     """,
#                     (user,)
#                 )
#                 user_ratings = cur.fetchall()
#                 if len(user_ratings) > 1:
#                     for prev_coords in user_ratings:
#                         if distance_between_coords(prev_coords, coords) >= 50 and "globetrotter" not in current_achievements:
#                             new_achievements.append("globetrotter")
#                             app.add_notification({"title": "New achievement earned!", "text": "Congrats, you earned 'Globetrotter'!"})
#                             break

#                 if cleanliness == 5 and supplies == 5 and privacy == 5 and "clean_sweep" not in current_achievements:
#                     new_achievements.append("clean_sweep")
#                     app.add_notification({"title": "New achievement earned!", "text": "Congrats, you earned 'Clean Sweep'!"})

#                 if rating_count >= 10 and "toilet_master" not in current_achievements:
#                     new_achievements.append("toilet_master")
#                     app.add_notification({"title": "New achievement earned!", "text": "Congrats, you earned 'Toilet Master'!"})

#                 if new_achievements:
#                     updated_achievements = list(set(current_achievements + new_achievements))
#                     cur.execute(
#                         "UPDATE users SET achievements = %s WHERE username = %s",
#                         (json.dumps(updated_achievements), user)
#                     )

#         return True, f"Rating added successfully with ID {rating_id} for toilet {toilet_id}"
#     except Exception as e:
#         return False, f"Error: {e}"
#     finally:
#         conn.close()

def create_rating(cleanliness: int, supplies: int, privacy: int, comment: str, coords: tuple, user_id: int):
    latitude, longitude = coords
    conn = get_db_connection()

    try:
        with conn:
            with conn.cursor() as cur:
                # Check if the user has already rated this toilet based on user_id
                cur.execute(
                    """
                    SELECT 1 FROM ratings
                    WHERE toilet_id IN (
                        SELECT toilet_id FROM toilets
                        WHERE latitude = %s AND longitude = %s
                    ) AND rated_user_id = %s
                    """,
                    (latitude, longitude, user_id)
                )
                if cur.fetchone():
                    return False, "You have already rated this toilet."

                # Get toilet_id based on latitude and longitude
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

                # Insert rating and associate it with user_id (now rated_user_id)
                cur.execute(
                    """
                    INSERT INTO ratings (toilet_id, cleanliness, supplies, privacy, comment, rated_user_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING rating_id
                    """,
                    (toilet_id, cleanliness, supplies, privacy, comment, user_id)
                )
                rating_id = cur.fetchone()[0]

                # Fetch the achievements of the user based on user_id
                cur.execute("SELECT achievements FROM users WHERE user_id = %s", (user_id,))
                result = cur.fetchone()
                if result is None:
                    return False, "User not found."

                current_achievements = result[0] or []
                new_achievements = []

                # Check how many ratings the user has made
                cur.execute("SELECT COUNT(*) FROM ratings WHERE rated_user_id = %s", (user_id,))
                rating_count = cur.fetchone()[0]
                if rating_count == 1 and "first_flush" not in current_achievements:
                    new_achievements.append("first_flush")
                    app.add_notification({"title": "New achievement earned!", "text": "Congrats, you earned 'First Flush'!"})

                # Check if the user qualifies for the "Globetrotter" achievement
                cur.execute(
                    """
                    SELECT latitude, longitude 
                    FROM toilets t
                    JOIN ratings r ON t.toilet_id = r.toilet_id
                    WHERE r.rated_user_id = %s
                    """,
                    (user_id,)
                )
                user_ratings = cur.fetchall()
                if len(user_ratings) > 1:
                    for prev_coords in user_ratings:
                        if distance_between_coords(prev_coords, coords) >= 50 and "globetrotter" not in current_achievements:
                            new_achievements.append("globetrotter")
                            app.add_notification({"title": "New achievement earned!", "text": "Congrats, you earned 'Globetrotter'!"})
                            break

                # Check if the user qualifies for the "Clean Sweep" achievement
                if cleanliness == 5 and supplies == 5 and privacy == 5 and "clean_sweep" not in current_achievements:
                    new_achievements.append("clean_sweep")
                    app.add_notification({"title": "New achievement earned!", "text": "Congrats, you earned 'Clean Sweep'!"})

                # Check if the user qualifies for the "Toilet Master" achievement
                if rating_count >= 10 and "toilet_master" not in current_achievements:
                    new_achievements.append("toilet_master")
                    app.add_notification({"title": "New achievement earned!", "text": "Congrats, you earned 'Toilet Master'!"})

                # Update the user's achievements if needed
                if new_achievements:
                    updated_achievements = list(set(current_achievements + new_achievements))
                    cur.execute(
                        "UPDATE users SET achievements = %s WHERE user_id = %s",
                        (json.dumps(updated_achievements), user_id)
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
                # Get toilet coordinates
                cur.execute("""
                    SELECT latitude, longitude
                    FROM toilets
                    WHERE toilet_id = %s
                """, (toilet_id,))
                toilet = cur.fetchone()
                if not toilet:
                    return None

                latitude, longitude = toilet

                # Get ratings for this toilet based on rated_user_id
                cur.execute("""
                    SELECT cleanliness, supplies, privacy, comment, rated_user_id
                    FROM ratings
                    WHERE toilet_id = %s
                """, (toilet_id,))
                ratings = cur.fetchall()

                # Calculate average ratings
                avg_cleanliness = sum(r[0] for r in ratings) / len(ratings) if ratings else 0
                avg_supplies = sum(r[1] for r in ratings) / len(ratings) if ratings else 0
                avg_privacy = sum(r[2] for r in ratings) / len(ratings) if ratings else 0

                # Fetch the username associated with each rating using user_id
                rated_users = []
                for r in ratings:
                    user_id = r[4]
                    cur.execute("""
                        SELECT username FROM users WHERE user_id = %s
                    """, (user_id,))
                    user = cur.fetchone()
                    rated_users.append({
                        "username": user[0] if user else "Unknown",
                        "cleanliness": r[0],
                        "supplies": r[1],
                        "privacy": r[2],
                        "comment": r[3]
                    })

                return {
                    "toilet_id": toilet_id,
                    "latitude": latitude,
                    "longitude": longitude,
                    "ratings": rated_users,
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
                # Get the username associated with the user_id
                cur.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
                user = cur.fetchone()

                if not user:
                    return {"message": "User not found."}

                username = user[0]

                # Fetch ratings based on the user_id (now using rated_user_id)
                cur.execute("""
                    SELECT 
                        r.toilet_id,
                        t.latitude,
                        t.longitude,
                        r.cleanliness,
                        r.supplies,
                        r.privacy,
                        r.comment,
                        r.rated_user_id
                    FROM ratings r
                    JOIN toilets t ON r.toilet_id = t.toilet_id
                    WHERE r.rated_user_id = %s
                """, (user_id,))

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
                        "username": username  # Returning the username here as it was fetched earlier
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
        # print(f"Error: {e}")
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
        # print(f"Error: {e}")
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
                    LEFT JOIN ratings r ON u.user_id = r.rated_user_id  -- Changed to use user_id
                    GROUP BY u.user_id  -- Group by user_id instead of username
                    HAVING COUNT(r.rating_id) > 0
                    ORDER BY rating_count DESC
                    LIMIT 50
                """)
                users = cur.fetchall()

                return [{"username": user[0], "rating_count": user[1]} for user in users]
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

def get_reviewed_countries(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT t.country 
                FROM toilets t
                JOIN ratings r ON t.toilet_id = r.toilet_id
                WHERE r.rated_user_id = %s AND t.country IS NOT NULL
                """,
                (user_id,)
            )
            countries = [row[0] for row in cur.fetchall()]
            return countries
    except Exception as e:
        # print(f"Error fetching countries: {e}")
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
        # print(f"Error fetching achievements: {e}")
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
        # print(f"Error fetching country: {e}")
        pass
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

# def convert_ratings_usernames_to_lowercase():
#     conn = get_db_connection()
#     try:
#         with conn:
#             with conn.cursor() as cur:
#                 cur.execute("SELECT rating_id, username FROM ratings")
#                 ratings = cur.fetchall()
                
#                 for rating_id, username in ratings:
#                     lower_username = username.lower()
#                     cur.execute(
#                         "UPDATE ratings SET username = %s WHERE rating_id = %s",
#                         (lower_username, rating_id)
#                     )
#         return True, "Ratings usernames converted to lowercase successfully."
#     except Exception as e:
#         return False, f"Error: {e}"
#     finally:
#         conn.close()

def encode_all_emails(): # yeah i didnt figure this out too quickly damn
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, email FROM users")
                users = cur.fetchall()
                
                for user_id, email in users:
                    if email:  # Check if email exists
                        encoded_email = encode(email)
                        cur.execute(
                            "UPDATE users SET email = %s WHERE user_id = %s",
                            (encoded_email, user_id)
                        )
        return True, "Emails encoded successfully."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()