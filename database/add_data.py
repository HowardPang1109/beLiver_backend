import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
import bcrypt

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
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            # 原始明文密碼
            plain_password = "pass1234"

            # bcrypt hash
            hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # 插入使用者
            cur.execute("""
                INSERT INTO users (name, email, hashed_password)
                VALUES (%s, %s, %s)
                ON CONFLICT (email) DO NOTHING;
            """, ("Alice", "alice@example.com", hashed_password))
            conn.commit()

            # 取得 user_id
            cur.execute("SELECT id FROM users WHERE email = %s;", ("alice@example.com",))
            user_id = cur.fetchone()[0]

            # 插入專案（先不設定 current_milestone）
            cur.execute("""
                INSERT INTO projects (name, summary, start_time, end_time, estimated_loading, due_date, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                "Productivity App", "A web app to manage tasks", 
                datetime.now() - timedelta(days=10),
                datetime.now() + timedelta(days=20),
                12.5, (datetime.now() + timedelta(days=25)).date(), user_id
            ))
            project_id = cur.fetchone()[0]
            conn.commit()

            # 插入里程碑
            milestone_name = "Initial Setup"
            cur.execute("""
                INSERT INTO milestones (name, summary, start_time, end_time, estimated_loading, project_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                milestone_name, "Setup DB, auth, and backend",
                datetime.now() - timedelta(days=5),
                datetime.now() + timedelta(days=5),
                6.5, project_id
            ))
            milestone_id = cur.fetchone()[0]
            conn.commit()

            # 更新 project.current_milestone 為里程碑名稱
            cur.execute("""
                UPDATE projects SET current_milestone = %s WHERE id = %s;
            """, (milestone_name, project_id))
            conn.commit()

            # 插入任務
            for i in range(3):
                cur.execute("""
                    INSERT INTO tasks (title, description, due_date, estimated_loading, milestone_id, is_completed)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (
                    f"Task {i+1}",
                    f"Description for task {i+1}",
                    (datetime.now() + timedelta(days=random.randint(3, 10))).date(),
                    round(random.uniform(1.0, 3.5), 1),
                    milestone_id,
                    random.choice([True, False])
                ))
            conn.commit()

            # 插入檔案
            cur.execute("""
                INSERT INTO files (name, url, project_id)
                VALUES (%s, %s, %s);
            """, ("design-doc.pdf", "https://example.com/files/design-doc.pdf", project_id))
            conn.commit()

            # 插入 AI 助理訊息
            messages = [
                ("user", "Hey, what's the next deadline?"),
                ("assistant", "The next task is due in 5 days."),
                ("user", "Add that to my calendar please."),
            ]
            for sender, msg in messages:
                cur.execute("""
                    INSERT INTO chat_histories (user_id, project_id, message, sender)
                    VALUES (%s, %s, %s, %s);
                """, (user_id, project_id, msg, sender))
            conn.commit()

            print("✅ 假資料成功插入所有表格！")

    except Exception as e:
        print(f"Error inserting mock data: {e}")
        conn.rollback()


def main():
    """Main function to connect to the database and perform operations."""
    db_conn = None
    try:
        db_conn = get_db_connection()
        # if db_conn:

        #     # Perform some example operations
        #     example_usage(db_conn)

    finally:
        if db_conn:
            db_conn.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("Error: .env file not found.")
    else:
        # Validate that all required environment variables are set
        required_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
            print("Please ensure all database credentials are set in your .env file.")
        else:
            main()
