from flask import Flask, jsonify, request
from flask_cors import CORS
from database import get_players, add_new_player, log_workout
from ai_engine import get_ai_recommendations
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, date
from dateutil import parser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
import threading


# Only initialize Firebase once
if not firebase_admin._apps:
    cred = credentials.Certificate("basketball-c918a-firebase-adminsdk-fbsvc-f831bd2577.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def send_email_reminder(to_email, subject, player_name):
    from_email = "tenzinnamgyalnorbu@gmail.com"
    password = "fujx qbvt ppya nmsd"

    # 🔍 Fetch today's drills
    today_day = datetime.utcnow().strftime("%A")
    player_doc = db.collection("players").document(to_email).get()
    if not player_doc.exists:
        return False

    routine = player_doc.to_dict().get("routine", {})
    drills_today = routine.get(today_day, ["No drills assigned."])

    drills_list_html = "".join(f"<li>{drill}</li>" for drill in drills_today)

    msg = MIMEMultipart("alternative")
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 10px;">
        <h2 style="color: #4CAF50;">🏀 Hey {player_name.title()}, ready to train?</h2>
        <p>Here's your drill lineup for <strong>{today_day}</strong>:</p>
        <ul>
          {drills_list_html}
        </ul>
        <p>Don't forget to log your scores in the app so you can keep leveling up! 💪</p>
        <p style="margin-top: 20px;">– Your Basketball AI Coach</p>
      </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print(f"📬 Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False
    
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
def get_drills_map():
    return {
        "Guard": {
            "Beginner": ["Form Shooting", "Stationary Dribbling", "Layups"],
            "Intermediate": ["Catch & Shoot", "Speed Dribbling", "Floaters"],
            "Advanced": ["3-Point Shooting", "Pick-and-Roll", "Fast Break Offense"]
        },
        "Forward": {
            "Beginner": ["Post Entries", "Jump Stops", "Backboard Layups"],
            "Intermediate": ["Spin Move Finishes", "Baseline Cuts", "Help Defense"],
            "Advanced": ["Isolation Scoring", "Mid-Post Fadeaways", "Transition Defense"]
        },
        "Center": {
            "Beginner": ["Drop Steps", "Rebounding Form", "Close-Range Shots"],
            "Intermediate": ["Hook Shots", "Outlet Passes", "Post Defense"],
            "Advanced": ["Advanced Post Moves", "Shot Blocking", "Pick & Roll Defense"]
        }
    }

def generate_14_day_routine(drills):
    routine = {}
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i in range(14):
        routine[f"Day {i+1} - {weekdays[i % 7]}"] = drills
    return routine

def check_skill_change(email, today_day_name):
    player_ref = db.collection("players").document(email)
    player_data = player_ref.get().to_dict()

    if not player_data:
        return "Player not found for skill check."

    current_level = player_data.get("skill_level", "Beginner")
    position = player_data.get("position")
    levels = ["Beginner", "Intermediate", "Advanced"]
    current_index = levels.index(current_level)

    # simulate relative days from mocked day
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today_index = weekdays.index(today_day_name)

    low_days = 0
    high_days = 0

    for i in range(3):
        check_day = weekdays[(today_index - i) % 7]
        doc_id = f"{email}_{check_day}"
        result_doc = db.collection("dailyResults").document(doc_id).get()
        if result_doc.exists:
            try:
                scores = result_doc.to_dict().get("results", {}).values()
                numeric_scores = list(map(int, scores))
                avg = sum(numeric_scores) / len(numeric_scores)
                if avg < 40:
                    low_days += 1
                elif avg > 85:
                    high_days += 1
            except:
                continue

    # Regression check
    if low_days >= 3 and current_index > 0:
        new_level = levels[current_index - 1]
        drills_map = get_drills_map()
        new_routine = generate_14_day_routine(drills_map[position][new_level])
        player_ref.update({
            "skill_level": new_level,
            "routine": new_routine
        })
        return f"⏬ Regressed to {new_level} after 3 poor days."

    # Promotion check
    if high_days >= 3 and current_index < 2:
        new_level = levels[current_index + 1]
        drills_map = get_drills_map()
        new_routine = generate_14_day_routine(drills_map[position][new_level])
        player_ref.update({
            "skill_level": new_level,
            "routine": new_routine
        })
        return f"⬆️ Promoted to {new_level} after 3 great days!"

    return "✅ No skill level change needed."

@app.route("/send_reminder", methods=["POST"])
def send_reminder():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"error": "Missing email"}), 400

    subject = "⏰ Time for your daily basketball drills!"
    body = "Don't forget to log into Basketball AI and complete today's drills. 💪🏀"

    success = send_email_reminder(email, subject, body)

    if success:
        return jsonify({"message": "Reminder email sent."}), 200
    else:
        return jsonify({"error": "Failed to send reminder"}), 500


@app.route("/generate_drill_test", methods=["POST"])
def generate_drill_test():
    
    data = request.json
    name = data.get("name")
    position = data.get("position")
    email = data.get("email")  # ✅ Get email from request

    if not name or not position or not email:
        return jsonify({"error": "Missing name, position, or email"}), 400

    player_ref = db.collection("players").document(email)
    player_doc = player_ref.get()

    drills_by_position = {
        "Guard": ["Dribble Course", "Free Throws", "Speed Layups"],
        "Forward": ["Post Moves", "Mid-Range Shooting", "Box Out Drills"],
        "Center": ["Rebounding", "Hook Shots", "Defensive Positioning"]
    }

    test_drills = drills_by_position.get(position, ["General Drills"])

    # 🔄 Create or update player entry with email, position & drills
    player_ref.set({
        "name": name,
        "position": position,
        "email": email,  # ✅ Save email to Firestore
        "drills": test_drills,
        "show_on_leaderboard": True,
        "test_completed": False
    }, merge=True)

    return jsonify({
        "message": f"Drill test created for {name} ({position})",
        "drills": test_drills
    })



@app.route("/player_status")
def player_status():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Missing name"}), 400

    doc = db.collection("players").document(email).get()
    if not doc.exists:
        return jsonify({"test_completed": False})

    return jsonify({
        "test_completed": doc.to_dict().get("test_completed", False)
    })




@app.route("/submit_test_results", methods=["POST"])
def submit_test_results():
    data = request.json
    email = data.get("email")
    name = data.get("name")
    results = data.get("results")  
    show_on_leaderboard = data.get("show_on_leaderboard", False)

    if not name or not results:
        return jsonify({"error": "Missing name or results"}), 400

    player_ref = db.collection("players").document(email)
    doc = player_ref.get()
    if not doc.exists:
        return jsonify({"error": "Player not found"}), 404

    if doc.to_dict().get("test_completed"):
        return jsonify({"error": "Test already submitted. You can't take it again."}), 403

    player = doc.to_dict()
    position = player.get("position", "Unknown")

    try:
        scores = list(map(int, results.values()))
        avg_score = sum(scores) / len(scores)
    except:
        return jsonify({"error": "Invalid score values"}), 400

    if avg_score >= 70:
        skill = "Advanced"
    elif avg_score >= 40:
        skill = "Intermediate"
    else:
        skill = "Beginner"

    # Generate 14-day routine
    routines = {
        "Guard": {
            "Beginner": ["Form Shooting", "Basic Dribbling", "Layup Lines"],
            "Intermediate": ["Speed Dribbling", "Catch & Shoot", "Pull-Up Jumpers"],
            "Advanced": ["3-Point Shooting", "Pick & Roll Reads", "Iso Moves"]
        },
        "Forward": {
            "Beginner": ["Post Entry Passing", "Rebounding Basics", "Close Shots"],
            "Intermediate": ["Spin Moves", "Elbow Jumpers", "Help Defense"],
            "Advanced": ["Mid-Post Isolation", "Transition Defense", "Step-back Shooting"]
        },
        "Center": {
            "Beginner": ["Post Footwork", "Layups", "Outlet Passing"],
            "Intermediate": ["Post Hooks", "Rim Protection", "Drop Step Moves"],
            "Advanced": ["Pick & Roll Defense", "Advanced Post Work", "Shot Contesting"]
        }
    }

    routine = routines.get(position, {}).get(skill, ["General Drills"])
    full_routine = {}
    start_date = datetime.today().date()
    for i in range(14):
        day = start_date + timedelta(days=i)
        weekday = day.strftime("%A")
        full_routine[weekday] = routine

    # Save player info
    player_ref.update({
        "results": results,
        "skill_level": skill,
        "routine": full_routine,
        "test_completed": True,
        "show_on_leaderboard": show_on_leaderboard
    })

    return jsonify({
        "message": f"Results submitted. {name} is classified as {skill}.",
        "skill_level": skill,
        "routine": full_routine
    })


@app.route("/submit_drill_results", methods=["POST"])
def submit_drill_results():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    position = data.get("position")
    results = data.get("results")  # list of scores

    if not all([name, email, position, results]):
        return jsonify({"error": "Missing fields"}), 400

    # 1. Determine skill level
    scores = list(map(int, results))
    avg_score = sum(scores) // len(scores)

    if avg_score >= 70:
        skill_level = "Advanced"
    elif avg_score >= 40:
        skill_level = "Intermediate"
    else:
        skill_level = "Beginner"

    # 2. Define drills
    drills = {
        "Guard": {
            "Beginner": ["Form Shooting", "Stationary Dribbling", "Layups"],
            "Intermediate": ["Catch & Shoot", "Speed Dribbling", "Floaters"],
            "Advanced": ["3-Point Shooting", "Pick-and-Roll", "Fast Break Offense"]
        },
        "Forward": {
            "Beginner": ["Post Entries", "Jump Stops", "Backboard Layups"],
            "Intermediate": ["Spin Move Finishes", "Baseline Cuts", "Help Defense"],
            "Advanced": ["Isolation Scoring", "Mid-Post Fadeaways", "Transition Defense"]
        },
        "Center": {
            "Beginner": ["Drop Steps", "Rebounding Form", "Close-Range Shots"],
            "Intermediate": ["Hook Shots", "Outlet Passes", "Post Defense"],
            "Advanced": ["Advanced Post Moves", "Shot Blocking", "Pick & Roll Defense"]
        }
    }

    # 3. Generate 14-day routine
    base_drills = drills.get(position, {}).get(skill_level, ["General Drills"])
    routine = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i in range(14):
        day_name = days[i % 7]
        routine[f"Day {i+1} - {day_name}"] = base_drills

    # 4. Save player profile + routine
    player_ref = db.collection("players").document(email)
    player_ref.set({
        "name": name,
        "email": email,
        "position": position,
        "results": results,
        "skill_level": skill_level,
        "routine": routine,
         "show_on_leaderboard": show_on_leaderboard
    }, merge=True)

    # 5. Save today's results
    today = data.get("mock_day") or datetime.today().strftime("%A")
    db.collection("dailyResults").document(f"{name}_{today}").set({
        "name": name,
        "email": email,
        "day": today,
        "results": {f"Drill {i+1}": score for i, score in enumerate(results)},
        "timestamp": datetime.utcnow().isoformat()
    })

    # 6. Adaptive check: skill regression
    regression_msg = check_regression_and_update_skill(email)

    return jsonify({
        "message": "Drill results submitted and routine generated.",
        "skill_level": skill_level,
        "routine": routine,
        "regression_check": regression_msg
    }), 200


# ✅ Regression Logic
def check_regression_and_update_skill(email):
    player_ref = db.collection("players").document(email)
    player_data = player_ref.get().to_dict()

    if not player_data:
        return "Player not found for regression check."

    current_level = player_data.get("skill_level", "Beginner")
    position = player_data.get("position")
    drills_map = {
        "Guard": {
            "Beginner": ["Form Shooting", "Stationary Dribbling", "Layups"],
            "Intermediate": ["Catch & Shoot", "Speed Dribbling", "Floaters"],
            "Advanced": ["3-Point Shooting", "Pick-and-Roll", "Fast Break Offense"]
        },
        "Forward": {
            "Beginner": ["Post Entries", "Jump Stops", "Backboard Layups"],
            "Intermediate": ["Spin Move Finishes", "Baseline Cuts", "Help Defense"],
            "Advanced": ["Isolation Scoring", "Mid-Post Fadeaways", "Transition Defense"]
        },
        "Center": {
            "Beginner": ["Drop Steps", "Rebounding Form", "Close-Range Shots"],
            "Intermediate": ["Hook Shots", "Outlet Passes", "Post Defense"],
            "Advanced": ["Advanced Post Moves", "Shot Blocking", "Pick & Roll Defense"]
        }
    }

    today = datetime.utcnow().date()
    low_days = 0

    for i in range(3):
        check_day = (today - timedelta(days=i)).strftime("%A")
        doc_id = f"{name}_{check_day}"
        result_doc = db.collection("dailyResults").document(doc_id).get()
        if result_doc.exists:
            try:
                scores = result_doc.to_dict().get("results", {}).values()
                numeric_scores = list(map(int, scores))
                avg = sum(numeric_scores) / len(numeric_scores)
                if avg < 40:
                    low_days += 1
            except:
                continue

    if low_days >= 3:
        if current_level == "Advanced":
            new_level = "Intermediate"
        elif current_level == "Intermediate":
            new_level = "Beginner"
        else:
            return "Player already at Beginner level."

        new_drills = drills_map.get(position, {}).get(new_level, ["General Drills"])
        new_routine = {}
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i in range(14):
            new_routine[f"Day {i+1} - {weekdays[i % 7]}"] = new_drills

        player_ref.update({
            "skill_level": new_level,
            "routine": new_routine
        })

        return f"⏬ Player regressed to {new_level} after 3 consecutive low-score days."

    return "✅ No regression needed."

def determine_badges(player_data, new_xp, streak_count):
    badges = set(player_data.get("badges", []))  # Ensure unique badges
    total_drills = len(player_data.get("results", []))

    # Volume-based
    if total_drills >= 10:
        badges.add("🏅 10 Drills")
    if total_drills >= 25:
        badges.add("🥈 25 Drills")
    if total_drills >= 50:
        badges.add("🥇 50 Drills")

    # XP Milestones
    if new_xp >= 500:
        badges.add("🌟 Rising Star")
    if new_xp >= 1000:
        badges.add("🚀 Prodigy")

    # Streak-based
    if streak_count >= 3:
        badges.add("🔥 3-Day Streak")
    if streak_count >= 7:
        badges.add("🔥🔥 7-Day Streak")

    # Surprise badge logic (example)
    if total_drills == 13:
        badges.add("🎁 Lucky 13")

    return list(badges)


@app.route("/submit_daily_results", methods=["POST"])
def submit_daily_results():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    results = data.get("results")  # {"Drill 1": 30, ...}
    mock_day = data.get("mock_day")

    if not all([name, email, results]):
        return jsonify({"error": "Missing fields"}), 400

    today = mock_day if mock_day else datetime.today().strftime("%A")
    doc_id = f"{email}_{today}"
    result_ref = db.collection("dailyResults").document(doc_id)

    # 🚫 Prevent duplicate submission
    if result_ref.get().exists:
        return jsonify({
            "error": f"🚫 You've already submitted results for {today}."
        }), 409  # 409 Conflict

    # ✅ XP calculation
    total_score = sum(int(score) for score in results.values() if str(score).isdigit())
    xp_gained = total_score * 5

    # 🔄 Save daily result
    result_ref.set({
        "name": name,
        "email": email,
        "day": today,
        "results": results,
        "xp_gained": xp_gained,
        "timestamp": datetime.utcnow().isoformat()
    })

    # 🔄 Update player profile
    player_ref = db.collection("players").document(email)
    player_doc = player_ref.get()

    # 🛡️ Default message
    skill_msg = "✅ No skill level check (new player)."

    if player_doc.exists:
        player_data = player_doc.to_dict()
        existing_results = player_data.get("results", [])

        if isinstance(existing_results, dict):
            existing_results = list(existing_results.values())

        new_results = existing_results + [str(score) for score in results.values()]
        current_xp = int(player_data.get("xp", 0))
        position = player_data.get("position", "Unknown")
        skill_level = player_data.get("skill_level", "Beginner")

        drills_map = {
            "Guard": {
                "Beginner": ["Form Shooting", "Stationary Dribbling", "Layups"],
                "Intermediate": ["Catch & Shoot", "Speed Dribbling", "Floaters"],
                "Advanced": ["3-Point Shooting", "Pick-and-Roll", "Fast Break Offense"]
            },
            "Forward": {
                "Beginner": ["Post Entries", "Jump Stops", "Backboard Layups"],
                "Intermediate": ["Spin Move Finishes", "Baseline Cuts", "Help Defense"],
                "Advanced": ["Isolation Scoring", "Mid-Post Fadeaways", "Transition Defense"]
            },
            "Center": {
                "Beginner": ["Drop Steps", "Rebounding Form", "Close-Range Shots"],
                "Intermediate": ["Hook Shots", "Outlet Passes", "Post Defense"],
                "Advanced": ["Advanced Post Moves", "Shot Blocking", "Pick & Roll Defense"]
            }
        }

        base_drills = drills_map.get(position, {}).get(skill_level, ["General Drills"])
        routine = {f"Day {i+1} - {['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][i % 7]}": base_drills for i in range(14)}

        # 🔄 Save updates
        player_ref.update({
            "xp": current_xp + xp_gained,
            "results": new_results,
            "routine": routine
        })

        # ✅ Skill check
        skill_msg = check_skill_change(name, today)

    else:
        # First-time player
        player_ref.set({
            "name": name,
            "email": email,
            "results": [str(score) for score in results.values()],
            "xp": xp_gained
        })

    return jsonify({
        "message": f"✅ Results submitted successfully. You earned {xp_gained} XP!",
        "xp_gained": xp_gained,
        "skill_update": skill_msg
    }), 200



# --- GET ALL PLAYERS ---
@app.route("/players", methods=["GET"])
def fetch_players():
    players = get_players()
    return jsonify([
        {
            "id": p[0],
            "name": p[1],
            "position": p[2],
            "skill_level": p[3],
            "shooting_accuracy": p[4],
            "dribbling_skill": p[5],
            "finishing_skill": p[6]
        } for p in players
    ])

# --- GET AI TRAINING ROUTINE FROM ai_engine.py ---
@app.route("/training/<int:player_id>", methods=["GET"])
def fetch_training_routine(player_id):
    routine = get_ai_recommendations(player_id)
    return jsonify(routine)

# --- LOG DAILY WORKOUT ---
@app.route("/log_training", methods=["POST"])
def log_training():
    data = request.json
    player_id = data.get("player_id")
    shooting = data.get("shooting_accuracy")
    dribbling = data.get("dribbling_skill")
    finishing = data.get("finishing_skill")

    if None in [player_id, shooting, dribbling, finishing]:
        return jsonify({"error": "Missing required fields"}), 400

    log_workout(player_id, shooting, dribbling, finishing)
    return jsonify({"message": "Training log added"}), 201

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    players_ref = db.collection("players")
    results_ref = db.collection("dailyResults")

    players = []
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday

    top_today = None
    top_today_xp = 0

    top_week = None
    top_week_score = 0

    for doc in players_ref.stream():
        data = doc.to_dict()
        if not data.get("show_on_leaderboard", False):
            continue

        name = data.get("name", "Unknown")
        xp = data.get("xp", 0)
        level = (xp // 500) + 1
        results = data.get("results", [])
        average_score = sum(map(float, results)) / len(results) if results else 0

        # Count unique days active
        day_query = results_ref.where("email", "==", data.get("email"))
        day_docs = day_query.stream()
        day_set = set()
        weekly_scores = []

        for d in day_docs:
            result_data = d.to_dict()
            day_set.add(result_data.get("day"))

            # Parse timestamp safely
            submitted_date = result_data.get("timestamp")
            if submitted_date:
                ts_date = parser.isoparse(submitted_date).date()
                if week_start <= ts_date <= today:
                    drill_scores = result_data.get("results", {}).values()
                    numeric_scores = list(map(int, drill_scores))
                    avg = sum(numeric_scores) / len(numeric_scores)
                    weekly_scores.append(avg)

                    # Top performer today
                    if ts_date == today:
                        if xp > top_today_xp:
                            top_today = {"name": name, "xp": xp}
                            top_today_xp = xp

        max_week_score = max(weekly_scores) if weekly_scores else 0
        if max_week_score > top_week_score:
            top_week = {"name": name, "xp": xp}
            top_week_score = max_week_score

        players.append({
            "name": name,
            "average_score": average_score,
            "days_active": len(day_set),
            "xp": xp,
            "level": level,
            "top_week_score": max_week_score
        })

    # Sort leaderboard
    players.sort(key=lambda x: (-x["top_week_score"], -x["xp"]))

    return jsonify({
        "players": players,
        "top_performer_today": top_today,
        "top_performer_week": top_week
    })

@app.route("/delete_profile", methods=["POST"])
def delete_profile():
    data = request.json
    name = data.get("name")
    email = data.get("email")

    if not email:
        return jsonify({"error": "Missing player name"}), 400

    try:
        name = name.lower()  # 💥 Normalize casing
        print(f"🔍 Deleting player: {name}")

        email = data.get("email")
        db.collection("players").document(email).delete()

        results = db.collection("dailyResults").where("email", "==", email).stream()
        for doc in results:
            print(f"🗑️ Deleting result doc: {doc.id}")
            doc.reference.delete()

        return jsonify({"message": f"✅ Profile for '{name}' deleted successfully."}), 200

    except Exception as e:
        print(f"❌ Error during deletion: {e}")
        return jsonify({"error": f"Failed to delete profile: {str(e)}"}), 500


@app.route("/export_profile", methods=["GET"])
def export_profile():
    
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Missing player name"}), 400

    try:
        doc = db.collection("players").document(email).get()
        profile = doc.to_dict()
        results = db.collection("dailyResults").where("email", "==", email).stream()
        result_data = [doc.to_dict() for doc in results]

        return jsonify({
            "profile": profile,
            "daily_results": result_data
        }), 200
    except Exception as e:
        return jsonify({"error": f"Export failed: {str(e)}"}), 500
    
@app.route('/export_player_data')
def export_player_data():
    name = request.args.get('name')
    email = request.args.get("email")
    
    if not name:
        return jsonify({"error": "Missing player name"}), 400

    player_ref = db.collection("players").document(email)
    player_doc = player_ref.get()

    if not player_doc.exists:
        return jsonify({"error": "Player not found"}), 404

    data = player_doc.to_dict()

    # Include daily results
    daily_results = db.collection("dailyResults").where("email", "==", data.get("email")).stream()
    data["daily_results"] = [doc.to_dict() for doc in daily_results]

    # Serve as a downloadable JSON file
    json_data = json.dumps(data, indent=2)
    return Response(
        json_data,
        mimetype='application/json',
        headers={"Content-Disposition": f"attachment;filename={name}_data.json"}
    )


# --- ASSESS NEW PLAYER & SAVE TO DB ---
@app.route("/assess_player", methods=["POST"])
def assess_and_add_player():
    data = request.json
    name = data.get("name")
    position = data.get("position")
    shooting = data.get("shooting_accuracy")
    dribbling = data.get("dribbling_skill")
    finishing = data.get("finishing_skill")

    if None in [name, position, shooting, dribbling, finishing]:
        return jsonify({"error": "Missing required fields"}), 400

    result = add_new_player(name, position, shooting, dribbling, finishing)
    return jsonify(result), 201

def send_daily_reminders():
    players_ref = db.collection("players").stream()
    for player in players_ref:
        data = player.to_dict()
        email = data.get("email")
        name = data.get("name")
        if email and name:
            subject = "📬 Your Daily Basketball Drill Routine"
            send_email_reminder(email, subject, name)

# 🔁 Schedule to run at 8 AM daily
schedule.every().day.at("08:00").do(send_daily_reminders)

# 🧵 Background thread to keep schedule running
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True)


