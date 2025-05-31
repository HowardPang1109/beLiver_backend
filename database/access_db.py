import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
import bcrypt
import uuid

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


def select_all_data(conn):
    """Selects and prints all data from relevant tables."""
    try:
        with conn.cursor() as cur:
            tables = [
                "users",
                "projects",
                "milestones",
                "tasks",
                "files",
                "chat_histories",
            ]

            for table in tables:
                print(f"\n📄 {table.upper()} =========================")
                cur.execute(f"SELECT * FROM {table};")
                rows = cur.fetchall()

                if rows:
                    for row in rows:
                        print(row)
                else:
                    print("No data found.")

    except Exception as e:
        print(f"❌ Error reading data: {e}")
        
def main():
    """Main function to connect to the database and perform operations."""
    db_conn = None
    try:
        db_conn = get_db_connection()
        if db_conn:
            # example_usage(db_conn)
            select_all_data(db_conn)

    finally:
        if db_conn:
            db_conn.close()
            print("\nDatabase connection closed.")

def generate_mock_data():
    """Generate mock data in memory."""
    users = []
    projects = []
    milestones = []
    tasks = []
    files = []
    chat_histories = []

    for u in range(3):  # 3 users
        user_id = str(uuid.uuid4())
        plain_password = f"password{u+1}"
        hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = {
            "id": user_id,
            "name": f"User{u+1}",
            "email": f"user{u+1}@example.com",
            "hashed_password": hashed_password
        }
        users.append(user)

        for p in range(2):  # 2 projects per user
            project_id = str(uuid.uuid4())
            project = {
                "id": project_id,
                "name": f"Project {p+1} (User{u+1})",
                "summary": "Auto-generated project",
                "start_time": datetime.now() - timedelta(days=15),
                "end_time": datetime.now() + timedelta(days=30),
                "estimated_loading": round(random.uniform(8.0, 20.0), 1),
                "due_date": (datetime.now() + timedelta(days=40)).date(),
                "user_id": user_id,
                "current_milestone": None
            }
            projects.append(project)

            for m in range(2):  # 2 milestones per project
                milestone_id = str(uuid.uuid4())
                milestone_name = f"Milestone {m+1} (Proj{p+1}-User{u+1})"
                milestone = {
                    "id": milestone_id,
                    "name": milestone_name,
                    "summary": "Auto-generated milestone",
                    "start_time": datetime.now() - timedelta(days=5),
                    "end_time": datetime.now() + timedelta(days=10),
                    "estimated_loading": round(random.uniform(4.0, 10.0), 1),
                    "project_id": project_id
                }
                milestones.append(milestone)

                # For first milestone only, set as current in project
                if m == 0:
                    project["current_milestone"] = milestone_name

                for t in range(5):  # 5 tasks per milestone
                    task_id = str(uuid.uuid4())
                    task = {
                        "id": task_id,
                        "title": f"Task {t+1}",
                        "description": f"Auto-generated task {t+1}",
                        "due_date": (datetime.now() + timedelta(days=random.randint(2, 12))).date(),
                        "estimated_loading": round(random.uniform(1.0, 3.5), 1),
                        "milestone_id": milestone_id,
                        "is_completed": random.choice([True, False])
                    }
                    tasks.append(task)

            # 1 file per project
            file = {
                "id": str(uuid.uuid4()),
                "name": "file.pdf",
                "url": "https://example.com/file.pdf",
                "project_id": project_id
            }
            files.append(file)

            # 3 messages per project
            for sender, msg in [("user", "What's next?"), ("assistant", "Finish Task 2."), ("user", "Got it.")]:
                message = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "project_id": project_id,
                    "message": msg,
                    "sender": sender
                }
                chat_histories.append(message)

    return users, projects, milestones, tasks, files, chat_histories

def generate_mock_data_for_alice():
    """Generate mock data for Alice with 3 projects, 4 milestones each, 5 tasks per milestone."""
    users = []
    projects = []
    milestones = []
    tasks = []
    files = []
    chat_histories = []

    # Fixed Alice info
    alice_id = "4caaa385-3a04-4bbc-8fb4-773766f70f59"
    alice = {
        "id": alice_id,
        "name": "Alice",
        "email": "alice@example.com",
        "hashed_password": "$2b$12$YXTBScc7xBxw.m6XDQpdoud3K546XvG58p7ZNVlgWH0F/5Nay6OW2"
    }
    users.append(alice)

    for p in range(3):  # 3 projects
        project_id = str(uuid.uuid4())
        project = {
            "id": project_id,
            "name": f"Alice Project {p+1}",
            "summary": "Project for Alice",
            "start_time": datetime.now() - timedelta(days=10),
            "end_time": datetime.now() + timedelta(days=30),
            "estimated_loading": round(random.uniform(10.0, 25.0), 1),
            "due_date": (datetime.now() + timedelta(days=40)).date(),
            "user_id": alice_id,
            "current_milestone": None
        }
        projects.append(project)

        for m in range(4):  # 4 milestones
            milestone_id = str(uuid.uuid4())
            milestone_name = f"Alice Milestone {m+1} (Proj{p+1})"
            milestone = {
                "id": milestone_id,
                "name": milestone_name,
                "summary": "Milestone for Alice",
                "start_time": datetime.now() - timedelta(days=2),
                "end_time": datetime.now() + timedelta(days=15),
                "estimated_loading": round(random.uniform(3.0, 8.0), 1),
                "project_id": project_id
            }
            milestones.append(milestone)

            if m == 0:
                project["current_milestone"] = milestone_name

            for t in range(5):  # 5 tasks
                task = {
                    "id": str(uuid.uuid4()),
                    "title": f"Alice Task {t+1}",
                    "description": f"Task {t+1} for Alice milestone {m+1}",
                    "due_date": (datetime.now() + timedelta(days=random.randint(3, 10))).date(),
                    "estimated_loading": round(random.uniform(1.0, 3.0), 1),
                    "milestone_id": milestone_id,
                    "is_completed": random.choice([True, False])
                }
                tasks.append(task)

        # 1 file per project
        file = {
            "id": str(uuid.uuid4()),
            "name": f"AliceFile{p+1}.pdf",
            "url": "https://example.com/alice_file.pdf",
            "project_id": project_id
        }
        files.append(file)

        # 3 chat messages
        for sender, msg in [("user", "Any updates?"), ("assistant", "Please complete milestone 1."), ("user", "On it.")]:
            chat = {
                "id": str(uuid.uuid4()),
                "user_id": alice_id,
                "project_id": project_id,
                "message": msg,
                "sender": sender
            }
            chat_histories.append(chat)

    return users, projects, milestones, tasks, files, chat_histories

def insert_mock_data(conn, users, projects, milestones, tasks, files, chat_histories):
    try:
        with conn.cursor() as cur:
            for user in users:
                cur.execute("""
                    INSERT INTO users (id, name, email, hashed_password)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (email) DO NOTHING;
                """, (user["id"], user["name"], user["email"], user["hashed_password"]))

            for project in projects:
                cur.execute("""
                    INSERT INTO projects (id, name, summary, start_time, end_time, estimated_loading, due_date, user_id, current_milestone)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    project["id"], project["name"], project["summary"],
                    project["start_time"], project["end_time"],
                    project["estimated_loading"], project["due_date"],
                    project["user_id"], project["current_milestone"]
                ))

            for milestone in milestones:
                cur.execute("""
                    INSERT INTO milestones (id, name, summary, start_time, end_time, estimated_loading, project_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (
                    milestone["id"], milestone["name"], milestone["summary"],
                    milestone["start_time"], milestone["end_time"],
                    milestone["estimated_loading"], milestone["project_id"]
                ))

            for task in tasks:
                cur.execute("""
                    INSERT INTO tasks (id, title, description, due_date, estimated_loading, milestone_id, is_completed)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (
                    task["id"], task["title"], task["description"],
                    task["due_date"], task["estimated_loading"],
                    task["milestone_id"], task["is_completed"]
                ))

            for file in files:
                cur.execute("""
                    INSERT INTO files (id, name, url, project_id)
                    VALUES (%s, %s, %s, %s);
                """, (file["id"], file["name"], file["url"], file["project_id"]))

            for msg in chat_histories:
                cur.execute("""
                    INSERT INTO chat_histories (id, user_id, project_id, message, sender)
                    VALUES (%s, %s, %s, %s, %s);
                """, (msg["id"], msg["user_id"], msg["project_id"], msg["message"], msg["sender"]))

            conn.commit()
            print("✅ 全部假資料插入完成！")

    except Exception as e:
        print(f"❌ Error inserting mock data: {e}")
        conn.rollback()

def main():
    db_conn = None
    try:
        db_conn = get_db_connection()
        if db_conn:
            # users, projects, milestones, tasks, files, chat_histories = generate_mock_data()
            # users, projects, milestones, tasks, files, chat_histories = generate_mock_data_for_alice()
            # print(users, projects, milestones, tasks, files, chat_histories)
            # insert_mock_data(db_conn, users, projects, milestones, tasks, files, chat_histories)
            select_all_data(db_conn)

    finally:
        if db_conn:
            db_conn.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
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
