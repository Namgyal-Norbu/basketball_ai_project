
from flask import Flask, jsonify, request
from flask_cors import CORS
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
import os
from dotenv import load_dotenv
from datetime import datetime, UTC
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from flask import send_file
from flask_cors import cross_origin
import random


load_dotenv()

skill_drill_bank = {
    "shooting": {
        "Amateur": ["Form Shooting", "Spot Shots"],
        "Beginner": ["Catch & Shoot", "Bank Shots"],
        "Intermediate": ["Pull-Up Jumpers", "Off-Dribble 3s"],
        "Advanced": ["Step-back 3s", "Curl Screens"],
        "Professional": ["Shooting Under Pressure", "Deep Range Shooting"]
    },
    "ball_handling": {
        "Amateur": ["Cone Dribbles", "Stationary Crossovers"],
        "Beginner": ["Zig-Zag Dribble", "Two-Ball Dribble"],
        "Intermediate": ["Change-of-Pace Moves", "Speed Dribbling"],
        "Advanced": ["Behind-the-Back Sequences", "Crossover & Finish"],
        "Professional": ["Elite Combo Moves", "Game Speed Dribbling"]
    },
    "defense": {
        "Amateur": ["Defensive Slides", "Hands Up Drill"],
        "Beginner": ["Closeouts", "Shuffle Slides"],
        "Intermediate": ["1v1 Defense", "Help Defense Rotations"],
        "Advanced": ["Switch Defense", "Trap Rotations"],
        "Professional": ["Elite Recovery", "Defensive Read & React"]
    },
    "finishing": {
        "Amateur": ["Basic Layups", "Mikan Drill"],
        "Beginner": ["Contested Layups", "Reverse Layups"],
        "Intermediate": ["Floaters", "Inside Hand Finish"],
        "Advanced": ["Euro Step", "Spin Finish"],
        "Professional": ["Body Contact Finishing", "And-1 Simulation"]
    },
    "footwork": {
        "Amateur": ["Jump Stops", "Triple Threat Position"],
        "Beginner": ["Pivot Series", "Footwork Squares"],
        "Intermediate": ["Ladder Drills", "Shot Preparation"],
        "Advanced": ["Up-and-Under Footwork", "Turnarounds"],
        "Professional": ["Pro Jab Sequences", "Advanced Footwork Counters"]
    }
}

faq_knowledge_base = {
    "how do I improve my shooting?": "Practice form shooting daily and focus on footwork.",
    "what's a good drill for dribbling?": "Try the cone dribble weave or 2-ball dribble drill.",
    "how often should I train?": "Ideally, train 5 days a week for 45-60 minutes per session.",
    "how is my skill level calculated?": "It's based on your average score during the test drills."
}
chatbot_knowledge_base = {
    "📋 Daily Drills": {
        "todaysdrills": "Here are your drills for today! 💪 Check your dashboard or ask for details.",
        "howmanydrillsshouldidodaily": "Aim for 3 drills a day for steady progress."
    },
    "📈 Player Progress": {
        "xp": "You earn XP for each drill based on performance.",
        "skilllevel": "Your skill level updates automatically based on your recent performance.",
        "progressgraph": "You can view your drill progress in a weekly chart on your dashboard."
    },
    "🎖️ Achievements & Badges": {
        "mybadges": "Badges are earned by completing drills, XP milestones, or special achievements!"
    },
    "🎯 Leveling & XP": {
        "howdoiearnxp": "You gain 5 XP per point scored in a drill."
    },
    "📅 Training Schedule": {
        "recommendedweeklyroutine": "Train 5–6 days a week for best improvement. Rest is important too!"
    },
    "🏆 Leaderboard Info": {
        "topplayers": "Top players are ranked by XP and consistency. Visit the leaderboard page to see the rankings."
    },
    "🛠️ Account & Settings": {
        "deletemyprofile": "You can delete your profile from the settings page. This will erase all your data.",
        "exportmydata": "Use the Export button in your settings to download your full training history."
    }
}

# Only initialize Firebase once
if not firebase_admin._apps:
    cred = credentials.Certificate("basketball-c918a-firebase-adminsdk-fbsvc-f831bd2577.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def build_drill_to_skill_map():
    mapping = {}
    for skill, levels in skill_drill_bank.items():
        for drill_list in levels.values():
            for drill in drill_list:
                mapping[drill] = skill
    return mapping
drill_to_skill = build_drill_to_skill_map()


def generate_skill_based_routine_by_level(skill_level, days=14):
    routine = {}
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    skill_categories = list(skill_drill_bank.keys())

    for i in range(days):
        day_name = weekdays[i % 7]
        drills_for_day = []

        for skill in skill_categories:
            drills_by_level = skill_drill_bank[skill].get(skill_level, [])
            if drills_by_level:
                selected_drill = random.choice(drills_by_level)
                drills_for_day.append(selected_drill)

        routine[f"Day {i+1} - {day_name}"] = drills_for_day

    return routine

def send_email_reminder(to_email, subject, player_name):
    from_email = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_PASS")

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


@app.route("/faq_manual", methods=["POST"])
def faq_manual_bot():
    data = request.json
    user_msg = data.get("message", "").lower()

    faq_map = {
      "shooting accuracy": "Try focusing on form shooting daily, and track your consistency.",
    "beginner drills": "Form shooting, stationary dribbling, and layup lines are great for beginners.",
    "daily drills": "We recommend 3 drills per day for consistent progress.",
    "xp system": "You earn XP based on the total score of your drills. More effort = more XP!",
    "level up": "Your routine adjusts based on your new skill level to keep things challenging.",
    "dribbling drill": "Try the cone dribble weave or 2-ball dribble drill.",
    "drill for dribbling": "Try the Figure 8 Dribbling Drill or Stationary Crossovers."
}
    

    for keyword, answer in faq_map.items():
        if keyword in user_msg:
            return jsonify({"response": answer})
    
    return jsonify({"response": "🤔 I'm not sure about that. Try asking about drills, XP, or leveling up."})

def check_skill_change(email, today_day_name):
    player_ref = db.collection("players").document(email)
    player_data = player_ref.get().to_dict()

    if not player_data:
        return "Player not found for skill check."

    current_level = player_data.get("skill_level", "Beginner")
   
    levels = ["Amateur", "Beginner", "Intermediate", "Advanced", "Professional"]
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

  
    if low_days >= 3 and current_index > 0:
        new_level = levels[current_index - 1]
        
        new_routine = generate_skill_based_routine_by_level(new_level)
        player_ref.update({
            "skill_level": new_level,
            "routine": new_routine
        })
        return f"⏬ Regressed to {new_level} after 3 poor days."

   
    if high_days >= 3 and current_index < len(levels) - 1:
        new_level = levels[current_index + 1]
        
        new_routine = generate_skill_based_routine_by_level(new_level)
        player_ref.update({
            "skill_level": new_level,
            "routine": new_routine
        })
        return f"⬆️ Promoted to {new_level} after 3 great days!"

    return "✅ No skill level change needed."


@app.route("/skill_drill_bank", methods=["GET"])
def get_skill_drill_bank():
    return jsonify(skill_drill_bank)

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
    email = data.get("email")

    if not name or not email:
        return jsonify({"error": "Missing name or email"}), 400

    player_ref = db.collection("players").document(email)
    player_ref.set({
        "name": name,
        "email": email,
        "test_completed": False
    }, merge=True)

    # Categorized test drills
    test_drills = {
        "shooting": ["Free Throws"],
        "ball_handling": ["Zig-Zag Dribble"],
        "defense": ["Closeouts",],
        "finishing": ["Contested Layups",],
        "footwork": ["Jump Stops", ]
    }

    return jsonify({
        "message": f"Test drills generated for {name}.",
        "drills": test_drills
    })


@app.route("/player_status")
def player_status():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Missing name"}), 400

    doc = db.collection("players").document(email).get()
    if not doc.exists:
        return jsonify({"test_completed": False})  # <— still safe if missing

    return jsonify({
        "test_completed": doc.to_dict().get("test_completed", False)
    })

@app.route("/assess_skill_weighted", methods=["POST"])
@cross_origin()
def assess_skill_weighted():
    print("🎯 POST request received for /assess_skill_weighted")
    data = request.get_json()

    # Normalized weights excluding "passing"
    weights = {
        "shooting": 0.274,
        "ball_handling": 0.267,
        "defense": 0.219,
        "finishing": 0.137,
        "footwork": 0.104
    }

    weighted_score = 0
    missing_keys = []

    for skill, weight in weights.items():
        if skill not in data:
            missing_keys.append(skill)
            continue
        weighted_score += data[skill] * weight

    if missing_keys:
        return jsonify({
            "error": f"Missing required fields: {', '.join(missing_keys)}"
        }), 400

    return jsonify({
        "weighted_score": round(weighted_score, 2),
        "message": f"🎯 Weighted performance score: {round(weighted_score, 2)}"
    })


@app.route("/submit_test_results", methods=["POST"])
def submit_test_results():
    data = request.json
    email = data.get("email")
    name = data.get("name")
    results = data.get("results")  # expects drill name -> score
    show_on_leaderboard = data.get("show_on_leaderboard", False)
    wants_email_reminders = data.get("wants_email_reminders", False)
    days_per_week = int(data.get("days_per_week", 7))  # Default to 7

    if not name or not results or not email:
        return jsonify({"error": "Missing name, email, or results"}), 400

    player_ref = db.collection("players").document(email)
    doc = player_ref.get()
    if not doc.exists:
        return jsonify({"error": "Player not found"}), 404

    if doc.to_dict().get("test_completed"):
        return jsonify({"error": "Test already submitted. You can't take it again."}), 403

    # 🔁 Map drills to skills
    drill_to_skill = {
        "Zig-Zag Dribble": "ball_handling",
        "Closeouts": "defense",
        "Contested Layups": "finishing",
        "Jump Stops": "footwork",
        "Free Throws": "shooting"
    }

    # 🎯 Use weighted scoring
    weights = {
        "shooting": 0.274,
        "ball_handling": 0.267,
        "defense": 0.219,
        "finishing": 0.137,
        "footwork": 0.104
    }

    # Aggregate drill scores into skill scores
    skill_scores = {k: 0 for k in weights.keys()}
    try:
        for drill_name, score in results.items():
            skill = drill_to_skill.get(drill_name)
            if skill:
                skill_scores[skill] = int(score)
    except Exception as e:
        return jsonify({"error": f"Failed to parse results: {e}"}), 400

    weighted_score = sum(skill_scores[skill] * weights[skill] for skill in weights)

    # 🧠 Skill classification
    if weighted_score >= 90:
        skill_level = "Professional"
    elif weighted_score >= 70:
        skill_level = "Advanced"
    elif weighted_score >= 50:
        skill_level = "Intermediate"
    elif weighted_score >= 30:
        skill_level = "Beginner"
    else:
        skill_level = "Amateur"

    # ✅ Generate routine using skill-based drill bank (not "General Drills")
    full_routine = generate_skill_based_routine_by_level(skill_level, days=14)

    # 💾 Save player profile to Firestore
    player_ref.update({
        "name": name,
        "email": email,
        "results": results,  # original test results
        "skill_level": skill_level,
        "routine": full_routine,
        "test_completed": True,
        "show_on_leaderboard": show_on_leaderboard,
        "wants_email_reminders": wants_email_reminders,
        "badges": [],
        "days_per_week": days_per_week
    })

    return jsonify({
        "message": f"🎯 Results submitted. {name} is classified as {skill_level}.",
        "skill_level": skill_level,
        "routine": full_routine,
        "weighted_score": round(weighted_score, 2)
    })

def determine_badges(player_data, new_xp, streak_count):
    badges = set(player_data.get("badges", []))  # Ensure unique badges
    total_drills = len(player_data.get("results", []))

    if total_drills >= 10:
        badges.add("🏅 10 Drills")
    if total_drills >= 25:
        badges.add("🥈 25 Drills")
    if total_drills >= 50:
        badges.add("🥇 50 Drills")

    if new_xp >= 500:
        badges.add("🌟 Rising Star")
    if new_xp >= 1000:
        badges.add("🚀 Prodigy")

    if streak_count >= 3:
        badges.add("🔥 3-Day Streak")
    if streak_count >= 7:
        badges.add("🔥🔥 7-Day Streak")

    if total_drills == 13:
        badges.add("🎁 Lucky 13")

    return list(badges)


@app.route("/submit_daily_results", methods=["POST"])
def submit_daily_results():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    results = data.get("results")  
    mock_day = data.get("mock_day")

    if not all([name, email, results]):
        return jsonify({"error": "Missing fields"}), 400

    today = mock_day if mock_day else datetime.today().strftime("%A")
    doc_id = f"{email}_{today}"
    result_ref = db.collection("dailyResults").document(doc_id)

    # Prevent duplicate submission
    if result_ref.get().exists:
        return jsonify({
            "error": f"🚫 You've already submitted results for {today}."
        }), 409  # 409 Conflict

    # XP calculation
    total_score = sum(int(score) for score in results.values() if str(score).isdigit())
    xp_gained = total_score * 5

    # Update player profile
    player_ref = db.collection("players").document(email)
    player_doc = player_ref.get()

    # Default response
    skill_msg = "✅ No skill level check (new player)."
    updated_badge_list = []
    
    if player_doc.exists:
        player_data = player_doc.to_dict()
        existing_results = player_data.get("results", [])

        if isinstance(existing_results, dict):
            existing_results = list(existing_results.values())

        new_results = existing_results + [str(score) for score in results.values()]
        current_xp = int(player_data.get("xp", 0))
        
        skill_level = player_data.get("skill_level", "Beginner")

        # 🏅 Calculate new badges
        updated_badge_list = determine_badges(player_data, current_xp + xp_gained, streak_count=1)

        # 🎯 Update 14-day routine
        routine = generate_skill_based_routine_by_level(skill_level, days=14)

        player_ref.update({
            "xp": current_xp + xp_gained,
            "results": new_results,
            "routine": routine,
            "badges": updated_badge_list
        })

        # 🔁 Check if skill should change
        skill_msg = check_skill_change(email, today)

    else:
        # First-time player
        player_ref.set({
            "name": name,
            "email": email,
            "results": [str(score) for score in results.values()],
            "xp": xp_gained,
            "badges": [],
        })

    # Save daily result
    result_ref.set({
        "name": name,
        "email": email,
        "day": today,
        "results": results,
        "xp_gained": xp_gained,
        "timestamp": datetime.now(UTC).isoformat(),
        "badges": updated_badge_list
    })

    return jsonify({
        "message": f"✅ Results submitted successfully. You earned {xp_gained} XP!",
        "xp_gained": xp_gained,
        "skill_update": skill_msg
    }), 200

@app.route("/chatbot_category", methods=["POST"])
def chatbot_category():
    data = request.json
    email = data.get("email")
    category = data.get("category")
    question = data.get("question", "").lower()

    if not email or not category:
        return jsonify({"response": "❌ Missing email or category"}), 400

    if category == "📋 Daily Drills":
        return handle_daily_drills(email)
    elif category == "📈 Player Progress":
        return handle_progress(email)
    elif category == "🎖️ Achievements & Badges":
        return handle_badges(email)
    elif category == "🎯 Leveling & XP":
        return jsonify({"response": "🏀 You earn XP from drills. Every 500 XP = 1 level."})
    elif category == "📅 Training Schedule":
        return jsonify({"response": "🗓️ Try to train 5–6 days a week for best results."})
    elif category == "🏆 Leaderboard Info":
        return jsonify({"response": "💡 The leaderboard ranks players based on XP and performance consistency."})
    elif category == "🛠️ Account & Settings":
        return jsonify({"response": "You can export or delete your profile in the settings section."})
    else:
        return jsonify({"response": "🤔 I'm not sure how to help with that category."})
    

@app.route("/chatbot_query", methods=["POST"])
def chatbot_query():
    data = request.json
    category = data.get("category")
    subcategory = data.get("subcategory")
    email = data.get("email", None)

    normalized_sub = "".join(c for c in subcategory.lower() if c.isalnum())

    
    if email:
        player_ref = db.collection("players").document(email)
        doc = player_ref.get()
        if doc.exists:
            player = doc.to_dict()
            today = datetime.utcnow().strftime("%A")

        if normalized_sub in ["xp"]:
            return jsonify({"response": f"💪 You currently have {player.get('xp', 0)} XP."})

        if normalized_sub in ["skilllevel", "level"]:
            return jsonify({"response": f"🧠 Your current skill level is {player.get('skill_level', 'Unknown')}."})

        if normalized_sub in ["badges", "mybadges"]:
            badges = player.get("badges", [])
            return jsonify({"response": f"🏅 You’ve earned: {', '.join(badges) if badges else 'no badges yet.'}"})

        if normalized_sub in ["todaysdrills"]:
            routine = player.get("routine", {})
            matching_day = next((k for k in routine if today in k), None)
            drills = routine.get(matching_day, [])
            return jsonify({"response": f"📋 Your drills for today ({today}) are: {', '.join(drills) if drills else 'No drills found.'}"})

    # 2. General FAQ lookup
    category_map = chatbot_knowledge_base.get(category)
    if not category_map:
        return jsonify({"response": "❌ Unknown category."}), 404

    response = category_map.get(normalized_sub)
    if not response:
        return jsonify({"response": "❓ Sorry, I don’t have information on that yet."}), 404

    return jsonify({"response": response})

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
        raw_results = data.get("results", [])

        # ✅ Filter out non-numeric results
        numeric_results = []
        for x in raw_results:
            try:
                numeric_results.append(float(x))
            except ValueError:
                continue

        average_score = sum(numeric_results) / len(numeric_results) if numeric_results else 0

        # Count unique days active
        day_query = results_ref.where("email", "==", data.get("email"))
        day_docs = day_query.stream()
        day_set = set()
        weekly_scores = []

        for d in day_docs:
            result_data = d.to_dict()
            day_set.add(result_data.get("day"))

            submitted_date = result_data.get("timestamp")
            if submitted_date:
                ts_date = parser.isoparse(submitted_date).date()
                if week_start <= ts_date <= today:
                    drill_scores = result_data.get("results", {}).values()

                    # ✅ Safely convert scores to int, skip if not valid
                    valid_scores = []
                    for val in drill_scores:
                        try:
                            valid_scores.append(int(val))
                        except:
                            continue

                    if valid_scores:
                        avg = sum(valid_scores) / len(valid_scores)
                        weekly_scores.append(avg)

                        if ts_date == today and xp > top_today_xp:
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
        name = name.lower()  # Normalize casing
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
        return jsonify({"error": "Missing player email"}), 400

    try:
        doc = db.collection("players").document(email).get()
        profile = doc.to_dict()
        results = db.collection("dailyResults").where("email", "==", email).stream()
        result_data = [doc.to_dict() for doc in results]

        # Create a PDF in memory
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica", 12)

        y = 750
        c.drawString(30, y, f"Player Profile Export for {profile.get('name', 'Unknown')}")
        y -= 20
        c.drawString(30, y, f"Email: {email}")
        y -= 20
        c.drawString(30, y, f"Skill Level: {profile.get('skill_level', '')}")
        y -= 20
        c.drawString(30, y, f"XP: {profile.get('xp', 0)}")
        y -= 40
        c.drawString(30, y, "Drill Results:")
        y -= 20

        for entry in result_data:
            if y < 60:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 750

            day = entry.get("day", "Unknown Day")
            c.drawString(40, y, f"{day} - {entry.get('timestamp', '')}")
            y -= 20
            for drill, score in entry.get("results", {}).items():
                c.drawString(60, y, f"{drill}: {score}")
                y -= 15
            y -= 10

        c.save()
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{profile.get('name', 'player')}_data.pdf",
            mimetype="application/pdf"
        )

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

@app.route("/player_question", methods=["POST"])
def player_question():
    data = request.json
    email = data.get("email")
    question = data.get("question", "").lower()

    if not email or not question:
        return jsonify({"response": "❌ Email and question are required."}), 400

    player_ref = db.collection("players").document(email)
    player_doc = player_ref.get()

    if not player_doc.exists:
        return jsonify({"response": "❌ Player not found."}), 404

    player = player_doc.to_dict()
    today = datetime.utcnow().strftime("%A")
    result_id = f"{email}_{today}"
    result_doc = db.collection("dailyResults").document(result_id).get()

    # 🌟 Match question patterns
    if "xp" in question:
        return jsonify({"response": f"💪 You currently have {player.get('xp', 0)} XP."})

    if "level" in question or "skill" in question:
        return jsonify({"response": f"🧠 Your current skill level is {player.get('skill_level', 'Unknown')}."})

    if "badge" in question:
        badges = player.get("badges", [])
        return jsonify({"response": f"🏅 You’ve earned: {', '.join(badges) if badges else 'no badges yet.'}"})

    if "drill" in question and "today" in question:
        routine_dict = player.get("routine", {})
        # Look for the key that contains today's day
        matching_day = next((key for key in routine_dict if today in key), None)
        if matching_day:
            drills = routine_dict[matching_day]
            return jsonify({"response": f"📋 Your drills for today ({today}) are: {', '.join(drills)}"})
        else:
            return jsonify({"response": f"😕 No drills found for {today}."})

    if "result" in question or "logged" in question:
        if result_doc.exists:
            scores = result_doc.to_dict().get("results", {})
            response = "\n".join([f"• {k}: {v}" for k, v in scores.items()])
            return jsonify({"response": f"📈 Your logged results for {today}:\n{response}"})
        else:
            return jsonify({"response": f"🕐 You haven’t submitted any results for today ({today})."})

    return jsonify({"response": "🤔 I didn’t understand that. Try asking about XP, level, badges, drills, or results."})

@app.route("/assess_player", methods=["POST"])
def assess_and_add_player():
    data = request.json
    name = data.get("name")
    shooting = data.get("shooting_accuracy")
    dribbling = data.get("dribbling_skill")
    finishing = data.get("finishing_skill")

    if None in [name, shooting, dribbling, finishing]:
        return jsonify({"error": "Missing required fields"}), 400

    result = add_new_player(name,shooting, dribbling, finishing)
    return jsonify(result), 201

def send_daily_reminders():
    players_ref = db.collection("players").stream()
    for player in players_ref:
        data = player.to_dict()
        email = data.get("email")
        name = data.get("name")
        if email and name and data.get("wants_email_reminders", False):
            subject = "📬 Your Daily Basketball Drill Routine"
            send_email_reminder(email, subject, name)

# Schedule to run at 8 AM daily
schedule.every().day.at("08:00").do(send_daily_reminders)

# Background thread to keep schedule running
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True)


