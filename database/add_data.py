import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database connection parameters from environment variables
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def get_db_connection():
    """Establishes a connection to the PostgreSQL database.

    Returns:
        psycopg2.extensions.connection: A connection object or None if connection fails.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print("Successfully connected to the PostgreSQL database!")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        print("Please check your .env file and PostgreSQL server status.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def example_usage(conn):
    """
    Demonstrates basic usage: inserting a user and selecting users.
    """
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            # Example: Insert a new user (ensure to handle potential conflicts with UNIQUE email)
            # For a real app, you'd hash passwords. This is just a demo.
            try:
                cur.execute(
                    sql.SQL("""
                        INSERT INTO users (name, email, password, timezone)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (email) DO NOTHING;
                    """),
                    ("Test User", "test@example.com", "securepassword123", "America/New_York")
                )
                conn.commit()
                if cur.rowcount > 0:
                    print("Test user inserted (or already existed).")
                else:
                    print("Test user with email test@example.com already exists.")

            except psycopg2.Error as e:
                print(f"Error inserting user: {e}")
                conn.rollback()


            # Example: Select all users
            cur.execute(sql.SQL("SELECT id, name, email, timezone FROM users;"))
            users = cur.fetchall()
            if users:
                print("\n--- Users ---")
                for user_row in users:
                    print(f"ID: {user_row[0]}, Name: {user_row[1]}, Email: {user_row[2]}, Timezone: {user_row[3]}")
            else:
                print("\nNo users found in the database.")

    except psycopg2.Error as e:
        print(f"Error during example usage: {e}")
        conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred during example usage: {e}")
        conn.rollback()

def main():
    """Main function to connect to the database and perform operations."""
    db_conn = None
    try:
        db_conn = get_db_connection()
        if db_conn:

            # Perform some example operations
            example_usage(db_conn)

    finally:
        if db_conn:
            db_conn.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("Error: .env file not found.")
        print("Please create a .env file with your database credentials.")
        print("Example .env content:")
        print("DB_NAME=your_db_name")
        print("DB_USER=your_db_user")
        print("DB_PASSWORD=your_db_password")
        print("DB_HOST=localhost")
        print("DB_PORT=5432")
    else:
        # Validate that all required environment variables are set
        required_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
            print("Please ensure all database credentials are set in your .env file.")
        else:
            main()
