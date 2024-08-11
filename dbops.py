import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve database connection details from environment variables
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def create_connection():
    """
    Establish a connection to the PostgreSQL database.
    Returns the connection object.
    """
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"An error occurred while connecting to the database: {e}")
        return None

def get_all_plants(conn):
    """
    Fetch all plant records from the 'plants' table.
    Returns a list of tuples where each tuple represents a plant.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM plants;")
            plants = cur.fetchall()
            return plants
    except Exception as e:
        print(f"An error occurred while fetching plants: {e}")
        return []

def get_all_zombies(conn):
    """
    Fetch all zombie records from the 'zombies' table.
    Returns a list of tuples where each tuple represents a zombie.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM zombies;")
            zombies = cur.fetchall()
            return zombies
    except Exception as e:
        print(f"An error occurred while fetching zombies: {e}")
        return []

def close_connection(conn):
    """
    Close the connection to the PostgreSQL database.
    """
    try:
        conn.close()
        print("Database connection closed.")
    except Exception as e:
        print(f"An error occurred while closing the database connection: {e}")
