import psycopg2
from psycopg2 import sql
import bcrypt

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

def register(username: str, password: str) -> str:
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username, hashed_password.decode()),
                )
        return "User registered successfully."
    except psycopg2.errors.UniqueViolation:
        return "Error: Username already exists."
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()

def login(username: str, password: str) -> str:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if user and bcrypt.checkpw(password.encode(), user[0].encode()):
                return "Login successful!"
            else:
                return "Invalid username or password."
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()