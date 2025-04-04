import sqlite3
from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials, firestore

# Set the correct path to your service account JSON file
SERVICE_ACCOUNT_PATH = "/Users/namgyalnorbu/basketball_ai_project/backend/basketball-c918a-firebase-adminsdk-fbsvc-f831bd2577.json"

if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()


### USER MANAGEMENT (Google OAuth) ###
def initialize_user_table():
    """Create the users table for Google authentication."""
    conn = sqlite3.connect("basketball_ai.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

def get_user_by_google_id(google_id):
    """Fetch a user from the database by Google ID"""
    conn = sqlite3.connect("basketball_ai.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, email, name FROM users WHERE google_id = ?", (google_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return {"id": user[0], "email": user[1], "name": user[2]}
    return None

def create_user(google_id, email, name):
    """Insert a new user into the database"""
    conn = sqlite3.connect("basketball_ai.db")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO users (google_id, email, name) VALUES (?, ?, ?)",
                   (google_id, email, name))
    conn.commit()
    conn.close()

    return {"id": cursor.lastrowid, "email": email, "name": name}

### PLAYER & TRAINING DATABASE MANAGEMENT ###
def initialize_db():
    """Create the database and players table if they don't exist."""
    conn = sqlite3.connect("basketball_ai.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            skill_level TEXT CHECK(skill_level IN ('Beginner', 'Amateur', 'Intermediate', 'Advanced', 'Elite', 'Professional')),
            position TEXT CHECK(position IN ('Guard', 'Forward', 'Center')),
            shooting_accuracy FLOAT,
            dribbling_skill FLOAT DEFAULT 50.0,
            finishing_skill FLOAT DEFAULT 50.0
        )
    """)

    conn.commit()
    conn.close()

def player_exists(name, position):
    """Check if a player with the same name and position exists in the database."""
    conn = sqlite3.connect("basketball_ai.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM players WHERE name = ? AND position = ?", (name, position))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def add_player(name, skill_level, position, shooting_accuracy, dribbling_skill=50.0, finishing_skill=50.0):
    """Add a player only if they don't already exist in that position."""
    if player_exists(name, position):
        print(f"⚠️ Player '{name}' ({position}) already exists! Skipping...")
        return

    conn = sqlite3.connect("basketball_ai.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO players (name, skill_level, position, shooting_accuracy, dribbling_skill, finishing_skill)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, skill_level, position, shooting_accuracy, dribbling_skill, finishing_skill))
    conn.commit()
    conn.close()
    print(f"✅ Player '{name}' ({position}) added successfully!")

def get_players():
    """Fetch all players from the database with correct columns."""
    conn = sqlite3.connect("basketball_ai.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, skill_level, position, shooting_accuracy, dribbling_skill, finishing_skill
        FROM players
    """)  # Ensure all 7 fields are selected
    
    players = cursor.fetchall()
    conn.close()
    return players  # This should return exactly 7 values per player


### TRAINING LOG MANAGEMENT ###
def initialize_training_logs():
    """Create a table to track player workout history."""
    conn = sqlite3.connect("basketball_ai.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            shooting_accuracy FLOAT,
            dribbling_skill FLOAT,
            finishing_skill FLOAT,
            FOREIGN KEY (player_id) REFERENCES players (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()



def store_training_routine(name, training_data):
    """Save training routine to Firestore."""
    doc_ref = db.collection("training_routines").document(name)
    doc_ref.set(training_data)
    print(f"Training plan stored for {name}")

def log_workout(player_id, shooting_accuracy, dribbling_skill, finishing_skill):
    """Logs a player's training session."""
    conn = sqlite3.connect("basketball_ai.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO training_logs (player_id, shooting_accuracy, dribbling_skill, finishing_skill)
        VALUES (?, ?, ?, ?)
    """, (player_id, shooting_accuracy, dribbling_skill, finishing_skill))

    conn.commit()
    conn.close()
    print(f"✅ Training log added for Player ID {player_id}")

### PLAYER SKILL ASSESSMENT ###
def assess_player(shooting, dribbling, finishing):
    """Determine initial skill level based on performance."""
    try:
        # Convert inputs to float to ensure calculation works
        shooting = float(shooting)
        dribbling = float(dribbling)
        finishing = float(finishing)

        avg_score = (shooting + dribbling + finishing) / 3

        if avg_score <= 30:
            return "Beginner"
        elif avg_score < 50:
            return "Amateur"
        elif avg_score < 70:
            return "Intermediate"
        elif avg_score < 85:
            return "Advanced"
        elif avg_score <= 95:
            return "Elite"
        else:  
            return "Professional"  # Above 95 is Professional
    except ValueError:
        return None  # Handle non-numeric inputs safely

def add_new_player(name, position, shooting, dribbling, finishing):
    """Assess and add a new player to the database"""
    skill_level = assess_player(shooting, dribbling, finishing)
    
    conn = sqlite3.connect("basketball_ai.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO players (name, skill_level, position, shooting_accuracy, dribbling_skill, finishing_skill) VALUES (?, ?, ?, ?, ?, ?)",
                   (name, skill_level, position, shooting, dribbling, finishing))
    conn.commit()
    conn.close()
    
    return {"message": f"✅ Player '{name}' added as {skill_level}!"}

### FETCH TRAINING DATA ###
def get_latest_training(player_id):
    """Fetch the latest training stats for a player."""
    conn = sqlite3.connect("basketball_ai.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT shooting_accuracy, dribbling_skill, finishing_skill
        FROM training_logs
        WHERE player_id = ?
        ORDER BY date DESC
        LIMIT 1
    """, (player_id,))

    latest_training = cursor.fetchone()
    conn.close()

    return latest_training if latest_training else (50.0, 50.0, 50.0)  # Default values

def get_training_routine(player_id):
    """Fetch player's training logs and suggest a routine."""
    conn = sqlite3.connect("basketball_ai.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT shooting_accuracy, dribbling_skill, finishing_skill
        FROM training_logs
        WHERE player_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (player_id,))
    
    last_training = cursor.fetchone()
    conn.close()

    if last_training:
        shooting, dribbling, finishing = last_training
        return {"shooting": shooting, "dribbling": dribbling, "finishing": finishing}
    else:
        return {"error": "No training data available"}

# Initialize everything
if __name__ == "__main__":
    initialize_user_table()
    initialize_db()
    initialize_training_logs()
    print("✅ Database initialized with required tables!")
