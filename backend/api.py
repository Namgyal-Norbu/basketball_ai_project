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
        "Beginner": ["Form Shooting Without Jumping", "Bank Shots"],
        "Intermediate": ["Free Throws", "Shooting Of A Pass"],
        "Advanced": ["Two Hand Shooting From Hop", "Curl Screens"],
        "Professional": ["Step Back", "Deep Range Shooting"]
    },
    "ball_handling": {
        "Beginner": ["Cone Dribble", "Cross Over Dribble and Finish"],
        "Intermediate": ["Hesistation Dribble And Finish", "Rhythm Dribbling and Finish" ],
        "Advanced": ["Crossover With Resistance and Finish", "Retreat Crossover Dribble and Finish", ],
        "Professional": ["Zigzag One-on-One and Finish", "Half Spin Hesistation vs Screen and Finish"]
    },
    "defense": {
        "Beginner": ["Wall Closeouts", "Slide & Recover", "Closeouts"],
        "Intermediate": ["Mirror Slides", "Recovery Sprint Challenge"],
        "Advanced": ["Defensive Lane Denial", "Ball Screen Navigation"],
        "Professional": ["1v1 Containment Drill", "Defensive Read & React"]
    },
    "footwork": {
        "Beginner": ["Jump Stop & Pivot", "Line Hops", "Jump Stops"],
        "Intermediate": ["Figure 8 Footwork", "Crossover Drop Steps"],
        "Advanced": ["Box Drills", "Stallcup Sweep Drill"],
        "Professional": ["Reverse Pivot Jab Rip", "Closeout to Slide Combo"]
    },
    "finishing": {
        "Beginner": ["Right Side Layup", "Left Side Layup"],
        "Intermediate": ["Floaters", "Inside Hand Finish"],
        "Advanced": ["Mikan Drill", "Contested Layups"],
        "Professional": ["Attack From Pick And Roll", "Basket Cut To Wing"]
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
    
    skill_categories = list(skill_drill_bank.keys())

    for i in range(days):
        day_key = f"Day {i+1}"
        drills_for_day = []

        for skill in skill_categories:
            drills_by_level = skill_drill_bank[skill].get(skill_level, [])
            if drills_by_level:
                selected_drill = random.choice(drills_by_level)
                drills_for_day.append(selected_drill)

        routine[day_key] = drills_for_day

    return routine


def send_email_reminder(to_email, subject, player_name):
    from_email = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_PASS")

    today_day = datetime.utcnow().strftime("%A")
    player_doc = db.collection("players").document(to_email).get()
    if not player_doc.exists:
        return False

    routine = player_doc.to_dict().get("routine", {})
    progress = player_doc.to_dict().get("routine_progress", 1)
    matching_day_key = f"Day {progress}"

    drills_today = routine.get(matching_day_key, ["No drills assigned."])   

    drills_list_html = "".join(
    f"<li>{drill['name'] if isinstance(drill, dict) else drill}</li>" for drill in drills_today
)


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
CORS(app) 




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

drill_details = {
    "Free Throws": {
        "reps": "10 shots",
        "description": "Score 10 point for each made free throw."
    },
    "Cross Over Dribble and Finish": {
        "reps": "10 reps",
        "description": "Score 10 point per successful dribble + finish without losing control."
    },
    "Closeouts": {
        "reps": "10 reps",
        "description": "Score 10 point per correct closeout (sprint > chop steps > high hands)."
    },
    "Contested Layups": {
        "reps": "10 reps",
        "description": "Score 10 point for each made layup under contact or distraction."
    },
    "Jump Stops": {
        "reps": "10 stops",
        "description": "Score 10 point for each controlled jump stop with balance."
    },
    "Form Shooting Without Jumping": {
        "reps": "10 makes from 5 spots",
        "description": (
            "10 point per clean make:\n"
            "- Focus on shooting mechanics (elbow, wrist, follow-through)\n"
            "- Stay balanced and consistent\n"
            "- No jumping allowed"
        )
    },

    "Bank Shots": {
        "reps": "10 makes from each side of the lane",
        "description": (
            "10 point per successful bank shot:\n"
            "- Use the backboard from proper angles\n"
            "- Consistent foot placement\n"
            "- Focus on soft touch off glass"
        )
    },

    "Free Throws": {
        "reps": "10 shots",
        "description": (
            "10 point per made free throw:\n"
            "- Use proper shooting routine\n"
            "- Hold follow-through\n"
            "- Stay focused under pressure"
        )
    },
    "Shooting Of A Pass": {
        "reps": "10 catch-and-shoot reps",
        "description": (
            "10 point per make:\n"
            "- Catch ball in rhythm\n"
            "- Quick release\n"
            "- Maintain shooting form"
        )
    },

    "Two Hand Shooting From Hop": {
        "reps": "10 makes off hop",
        "description": (
            "10 point per clean make:\n"
            "- Hop into shooting stance\n"
            "- Square shoulders on catch\n"
            "- Explode upward with balanced base"
        )
    },
    "Curl Screens": {
        "reps": "10 reps off screen",
        "description": (
            "10 point per made shot:\n"
            "- Simulate curling off a screen\n"
            "- Square up quickly\n"
            "- Control footwork and shot speed"
        )
    },

    "Step Back": {
        "reps": "10 reps per side",
        "description": (
            "10 point per made step-back:\n"
            "- Create space with quick step back\n"
            "- Maintain balance\n"
            "- Use sharp footwork and full extension"
        )
    },
    "Deep Range Shooting": {
        "reps": "10 deep shots",
        "description": (
            "10 point per make beyond the 3-point line:\n"
            "- Maintain proper shooting mechanics\n"
            "- Stay balanced with legs under shot\n"
            "- No forced throws or breakdown in form"
        )
    },

    "Cone Dribble": {
        "reps": "3 sets of 5 cones",
        "description": (
            "10 point per clean run:\n"
            "- Navigate through cones without losing control\n"
            "- Use both hands\n"
            "- Stay low and tight with the ball"
        )
    },
    "Cross Over Dribble and Finish": {
        "reps": "10 reps",
        "description": (
            "10 point per successful rep:\n"
            "- Execute crossover smoothly\n"
            "- Maintain control while finishing at the rim\n"
            "- Use both hands equally"
        )
    },

    "Hesistation Dribble And Finish": {
        "reps": "10 reps",
        "description": (
            "10 point per complete rep:\n"
            "- Sell hesitation with body & eyes\n"
            "- Burst past defender and finish\n"
            "- Alternate hands each rep"
        )
    },
    "Rhythm Dribbling and Finish": {
        "reps": "10 reps",
        "description": (
            "10 point per successful rep:\n"
            "- Perform rhythm dribble sequence (cross, behind, etc.)\n"
            "- Finish strong at the basket\n"
            "- Focus on timing and control"
        )
    },

    "Crossover With Resistance and Finish": {
        "reps": "10 reps against a partner or resistance band",
        "description": (
            "10 point per powerful crossover:\n"
            "- Stay low with tight handle\n"
            "- Use explosive move to beat defender\n"
            "- Finish with control"
        )
    },
    "Retreat Crossover Dribble and Finish": {
        "reps": "10 reps",
        "description": (
            "10 point per smooth retreat-to-attack:\n"
            "- Retreat dribble to create space\n"
            "- Quick crossover and aggressive finish\n"
            "- Maintain balance and poise"
        )
    },

    "Zigzag One-on-One and Finish": {
        "reps": "10 full-court zigzags",
        "description": (
            "10 point per clean sequence:\n"
            "- Alternate between sharp direction changes\n"
            "- Simulate defender pressure\n"
            "- Explode to finish after last cut"
        )
    },
    "Half Spin Hesistation vs Screen and Finish": {
        "reps": "10 reps",
        "description": (
            "10 point per well-executed rep:\n"
            "- Use half spin to freeze defender\n"
            "- Navigate screen with control\n"
            "- Finish strong at basket"
        )
    },
    "Right Side Layup": {
        "reps": "10 reps",
        "description": (
            "10 point per clean make:\n"
            "- Use right hand and right foot timing\n"
            "- Aim for the top corner of the backboard\n"
            "- Smooth finish, no dribble bobble"
        )
    },
    "Left Side Layup": {
        "reps": "10 reps",
        "description": (
            "10 point per clean make:\n"
            "- Use left hand and left foot timing\n"
            "- Hit the correct angle on the backboard\n"
            "- Controlled approach and finish"
        )
    },

    # 🟠 Intermediate Finishing
    "Floaters": {
        "reps": "10 reps",
        "description": (
            "10 point per successful floater:\n"
            "- Soft high-arching release over a defender\n"
            "- Keep body under control\n"
            "- Land on balance"
        )
    },
    "Inside Hand Finish": {
        "reps": "10 reps per side",
        "description": (
            "10 point per deceptive finish:\n"
            "- Finish with opposite hand on same side\n"
            "- Avoid shot blockers\n"
            "- Shield with body"
        )
    },

    "Mikan Drill": {
        "reps": "20 alternating finishes",
        "description": (
            "10 point per successful make:\n"
            "- Quick footwork around rim\n"
            "- No dribble, alternate hands\n"
            "- Keep ball high, no pauses"
        )
    },
    "Contested Layups": {
        "reps": "10 reps with contact",
        "description": (
            "10 point per strong finish:\n"
            "- Simulate defender contact\n"
            "- Absorb bump and still convert\n"
            "- Controlled body and focused finish"
        )
    },

    "Attack From Pick And Roll": {
        "reps": "10 reps",
        "description": (
            "10 point per efficient attack:\n"
            "- Use screen correctly (reject or use)\n"
            "- Read help and finish with best option\n"
            "- Stay low and decisive"
        )
    },
    "Basket Cut To Wing": {
        "reps": "10 reps",
        "description": (
            "10 point per successful execution:\n"
            "- Make a sharp cut from corner to wing\n"
            "- Catch and finish in one motion\n"
            "- Focus on timing and footwork"
        )
    },

    "Wall Closeouts": {
        "reps": "10 reps",
        "description": (
            "10 point per proper closeout:\n"
            "- Sprint to wall, breakdown with choppy steps\n"
            "- Hands up, balanced, no lunging"
        )
    },
    "Slide & Recover": {
        "reps": "10 slide-sprint cycles",
        "description": (
            "10 point per correct sequence:\n"
            "- Slide left/right to cone\n"
            "- Sprint to recover cone\n"
            "- Maintain defensive stance"
        )
    },
    "Mirror Slides": {
        "reps": "10 rounds with a partner or reflection",
        "description": (
            "10 point per successful mirror:\n"
            "- Match movement without crossing feet\n"
            "- Stay low, maintain distance"
        )
    },
    "Recovery Sprint Challenge": {
        "reps": "10 reps",
        "description": (
            "10 point per sprint-slide combo:\n"
            "- Sprint to touch cone\n"
            "- Slide back in stance to baseline"
        )
    },
    "Defensive Lane Denial": {
        "reps": "10 reps against imaginary cutter",
        "description": (
            "10 point per correct denial:\n"
            "- Arm bar + inside foot positioning\n"
            "- No backpedaling or spinning"
        )
    },
    "Ball Screen Navigation": {
        "reps": "10 on-screen reps",
        "description": (
            "10 point per successful navigation:\n"
            "- Go over/under correctly\n"
            "- Maintain contact with screener"
        )
    },
    "1v1 Containment Drill": {
        "reps": "10 reps vs partner or shadow",
        "description": (
            "10 point for successful containment:\n"
            "- No blow-bys for 3 seconds\n"
            "- Stay square and on balance"
        )
    },
    "Defensive Read & React": {
        "reps": "10 reps from coach command",
        "description": (
            "10 point per correct reaction:\n"
            "- React to cue (help, rotate, closeout)\n"
            "- Decision speed under 1.5 seconds"
        )
    },

    "Jump Stop & Pivot": {
        "reps": "10 reps per foot",
        "description": (
            "10 point per clean sequence:\n"
            "- Controlled jump stop\n"
            "- Legal pivot without travel"
        )
    },
    "Line Hops": {
        "reps": "30 seconds x 3 rounds",
        "description": (
            "10 point per 10 hops:\n"
            "- Quick feet\n"
            "- Both feet clear line"
        )
    },
    "Figure 8 Footwork": {
        "reps": "10 continuous loops",
        "description": (
            "10 point per loop:\n"
            "- Stay low, sharp cuts\n"
            "- Don’t step outside cones"
        )
    },
    "Crossover Drop Steps": {
        "reps": "10 reps each direction",
        "description": (
            "10 point per fluid rep:\n"
            "- Low stance, controlled crossover\n"
            "- Explosive drop step"
        )
    },
    "Box Drills": {
        "reps": "5 clockwise + 5 counter-clockwise laps",
        "description": (
            "10 point per lap:\n"
            "- Hit all four corners\n"
            "- Quick first step, sharp cuts"
        )
    },
    "Stallcup Sweep Drill": {
        "reps": "10 sweeps",
        "description": (
            "10 point per sweep:\n"
            "- Stay low with wide stance\n"
            "- Clean foot replacement\n"
            "- Don’t travel"
        )
    },
    "Reverse Pivot Jab Rip": {
        "reps": "10 reps each side",
        "description": (
            "10 point per rep:\n"
            "- Reverse pivot cleanly\n"
            "- Jab + rip low and sharp"
        )
    },
    "Closeout to Slide Combo": {
        "reps": "10 reps",
        "description": (
            "10 point per sequence:\n"
            "- Closeout with control\n"
            "- Immediate slide left or right\n"
            "- Hands up entire time"
        )
    },
}


@app.route("/generate_drill_test", methods=["POST", "OPTIONS"])
@cross_origin(origins="http://localhost:3000")
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

    # Basic test drills
    test_drills = {
        "shooting": ["Free Throws"],
        "ball_handling": ["Cross Over Dribble and Finish"],
        "defense": ["Closeouts"],
        "finishing": ["Contested Layups"],
        "footwork": ["Jump Stops"]
    }

    # Return enriched drill data
    enriched = {}
    for skill, drills in test_drills.items():
        enriched[skill] = [{
            "name": drill,
            "reps": drill_details.get(drill, {}).get("reps", ""),
            "description": drill_details.get(drill, {}).get("description", "")
        } for drill in drills]

    return jsonify({
        "message": f"Test drills generated for {name}.",
        "drills": enriched
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

@app.route("/assess_skill_weighted", methods=["POST"])
@cross_origin()
def assess_skill_weighted():
    print("🎯 POST request received for /assess_skill_weighted")
    data = request.get_json()
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

def check_skill_change_recent_submissions(email):
    player_ref = db.collection("players").document(email)
    player_data = player_ref.get().to_dict()

    if not player_data:
        return "Player not found for skill check."

    current_level = player_data.get("skill_level", "Beginner")
    levels = ["Beginner", "Intermediate", "Advanced", "Professional"]
    current_index = levels.index(current_level)

    # Get the last 3 submission entries by timestamp
    recent_entries = (
        db.collection("dailyResults")
        .where("email", "==", email)
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(3)
        .stream()
    )

    recent_averages = []
    for doc in recent_entries:
        data = doc.to_dict()
        scores = data.get("results", {}).values()
        numeric_scores = [int(s) for s in scores if str(s).isdigit()]
        if numeric_scores:
            avg = sum(numeric_scores) / len(numeric_scores)
            recent_averages.append(avg)

    if len(recent_averages) < 3:
        return "✅ Waiting for 3 valid training submissions."

    high_days = sum(1 for avg in recent_averages if avg > 85)
    low_days = sum(1 for avg in recent_averages if avg < 40)

    def update_remaining_routine(new_level):
        existing_routine = player_data.get("routine", {})
        new_full_routine = enrich_routine(generate_skill_based_routine_by_level(new_level))
        updated_routine = {}

        # Only keep drills that have already been submitted
        submitted_days = set()
        result_docs = db.collection("dailyResults").where("email", "==", email).stream()
        for doc in result_docs:
            day_key = doc.to_dict().get("day")
            if day_key:
                for key in existing_routine:
                    if day_key in key:
                        submitted_days.add(key)

        for key in existing_routine:
            if key in submitted_days:
                updated_routine[key] = existing_routine[key]
            else:
                updated_routine[key] = new_full_routine.get(key, existing_routine.get(key))

        player_ref.update({
            "skill_level": new_level,
            "routine": updated_routine
        })

    if high_days == 3 and current_index < len(levels) - 1:
        new_level = levels[current_index + 1]
        update_remaining_routine(new_level)
        return f"⬆️ Promoted to {new_level} after 3 great training days!"

    if low_days == 3 and current_index > 0:
        new_level = levels[current_index - 1]
        update_remaining_routine(new_level)
        return f"⏬ Regressed to {new_level} after 3 poor training days."

    return "✅ No skill level change needed."





def enrich_routine(routine):
    enriched = {}
    for day, drills in routine.items():
        enriched[day] = [
            {
                "name": drill,
                "reps": drill_details.get(drill, {}).get("reps", "N/A"),
                "description": drill_details.get(drill, {}).get("description", "No description available.")
            }
            for drill in drills
        ]
    return enriched

@app.route("/get_routine", methods=["GET"])
def get_routine():
    email = request.args.get("email")
    mock_day = request.args.get("mock_day")  # Optional for testing

    if not email:
        return jsonify({"error": "Missing email"}), 400

    player_doc = db.collection("players").document(email).get()
    if not player_doc.exists:
        return jsonify({"error": "Player not found"}), 404

    player = player_doc.to_dict()
    routine = player.get("routine", {})
    progress = int(player.get("routine_progress", 1))

    # Check if they already submitted today
    today_str = mock_day if mock_day else date.today().isoformat()
    if player.get("last_submission_date") == today_str:
        # Block access to the next day
        progress -= 1

    full_key = f"Day {progress}"
    drills = routine.get(full_key)

    if not drills:
        return jsonify({
            "routine": {},
            "message": "🎉 You’ve completed your full routine!"
        })

    enriched_drills = []
    for drill in drills:
        if isinstance(drill, dict):
            enriched_drills.append(drill)
        else:
            enriched_drills.append({
                "name": drill,
                "reps": drill_details.get(drill, {}).get("reps", "N/A"),
                "description": drill_details.get(drill, {}).get("description", "No description available.")
            })

    return jsonify({
        "day": full_key,
        "drills": enriched_drills
    })

@app.route("/submit_test_results", methods=["POST"])
def submit_test_results():
    data = request.json
    email = data.get("email")
    name = data.get("name")
    results = data.get("results")  
    show_on_leaderboard = data.get("show_on_leaderboard", False)
    wants_email_reminders = data.get("wants_email_reminders", False)
    days_per_week = int(data.get("days_per_week", 7))  

    if not name or not results or not email:
        return jsonify({"error": "Missing name, email, or results"}), 400

    player_ref = db.collection("players").document(email)
    doc = player_ref.get()
    if not doc.exists:
        return jsonify({"error": "Player not found"}), 404

    if doc.to_dict().get("test_completed"):
        return jsonify({"error": "Test already submitted. You can't take it again."}), 403

    weighted_score = round(calculate_weighted_score(results), 2)
    print(f"🎯 Final Weighted Score: {weighted_score}")
   
    if weighted_score >= 90:
        skill_level = "Professional"
    elif weighted_score >= 70:
        skill_level = "Advanced"
    elif weighted_score >= 50:
        skill_level = "Intermediate"
    else:
        skill_level = "Beginner"

    total_days = days_per_week * 2  # e.g. 3 days/week → 6 training days
    raw_routine = generate_skill_based_routine_by_level(skill_level, days=total_days)

    full_routine = enrich_routine(raw_routine)


    badges = determine_badges({
        "results": list(results.values()),
        "badges": []
    }, new_xp=0, streak_count=1)

    player_ref.update({
    "name": name,
    "email": email,
    "results": results,
    "skill_level": skill_level,
    "routine": full_routine,
    "test_completed": True,
    "show_on_leaderboard": show_on_leaderboard,
    "wants_email_reminders": wants_email_reminders,
    "badges": badges,  
    "days_per_week": days_per_week,
    "routine_progress": 1,

})

    print("Raw submitted results:", results)
    return jsonify({
        "message": f"🎯 Results submitted. {name} is classified as {skill_level}.",
        "skill_level": skill_level,
        "routine": full_routine,
        "weighted_score": round(weighted_score, 2)
    })

def determine_badges(player_data, new_xp, streak_count):
    badges = set(player_data.get("badges", []))  
    total_drills = len(player_data.get("results", []))

    if total_drills >=5:
        badges.add("🏅 5 drills")

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


def calculate_weighted_score(results):
    weights = {
        "shooting": 0.274,
        "ball_handling": 0.267,
        "defense": 0.219,
        "finishing": 0.137,
        "footwork": 0.104
    }

    skill_scores = {skill: [] for skill in weights}

    for drill, score in results.items():
        skill = drill_to_skill.get(drill)
        if skill:
            try:
                skill_scores[skill].append(round(float(score)))
            except:
                continue


    weighted_score = 0
    for skill, scores in skill_scores.items():
            print(f"{skill}: {scores}")
            if scores:
                avg = sum(scores) / len(scores)
                weighted_score += avg * weights[skill]

    return round(weighted_score, 2)


@app.route("/submit_daily_results", methods=["POST"])
def submit_daily_results():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    results = data.get("results")  
    mock_day = data.get("mock_day")  # Optional for testing

    if not all([name, email, results]):
        return jsonify({"error": "Missing fields"}), 400

    # Use current date or mock date
    today_str = mock_day if mock_day else date.today().isoformat()

    # Get player document
    player_ref = db.collection("players").document(email)
    player_doc = player_ref.get()
    if not player_doc.exists:
        return jsonify({"error": "Player not found"}), 404

    player_data = player_doc.to_dict()
    routine = player_data.get("routine", {})
    routine_progress = int(player_data.get("routine_progress", 1))

    # ❌ Already submitted today
    if player_data.get("last_submission_date") == today_str:
        return jsonify({
            "error": "🚫 You’ve already submitted drills for today. Come back tomorrow!"
        }), 403

    today_key = next((k for k in routine if k.startswith(f"Day {routine_progress}")), None)
    if not today_key:
        return jsonify({"error": "Routine day not found."}), 404

    doc_id = f"{email}_{today_key.replace(' ', '_')}"
    result_ref = db.collection("dailyResults").document(doc_id)

    # XP and Badge Calculation
    weighted_score = calculate_weighted_score(results)
    xp_gained = int(weighted_score * 5)

    existing_results = player_data.get("results", [])
    if isinstance(existing_results, dict):
        existing_results = list(existing_results.values())

    new_results = existing_results + [str(score) for score in results.values()]
    current_xp = int(player_data.get("xp", 0))

    temp_player_data = {**player_data, "results": new_results}
    updated_badge_list = determine_badges(temp_player_data, current_xp + xp_gained, streak_count=1)

    # Save result
    result_ref.set({
        "name": name,
        "email": email,
        "day": today_key,
        "results": results,
        "xp_gained": xp_gained,
        "timestamp": datetime.now(UTC).isoformat(),
        "badges": updated_badge_list
    })

    # Only move to next day if one exists
    next_progress = routine_progress + 1 if any(k.startswith(f"Day {routine_progress + 1}") for k in routine) else routine_progress

    # Update player
    player_ref.update({
        "xp": current_xp + xp_gained,
        "results": new_results,
        "badges": updated_badge_list,
        "routine_progress": next_progress,
        "last_submission_date": today_str
    })

    # Skill check
    skill_msg = check_skill_change_recent_submissions(email)

    return jsonify({
        "message": f"✅ Results submitted successfully for {today_key}. You earned {xp_gained} XP!",
        "xp_gained": xp_gained,
        "weighted_score": weighted_score,
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

    normalized_sub = (
    "".join(c for c in subcategory.lower() if c.isalnum()) if subcategory else ""
)

    
    if email:
        player_ref = db.collection("players").document(email)
        doc = player_ref.get()
        if not doc.exists:
            return jsonify({"response": "❌ Player not found."}), 404

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
            progress = player.get("routine_progress", 1)
            drills = routine.get(f"Day {progress}", [])
            drill_names = [d["name"] if isinstance(d, dict) else str(d) for d in drills]

            return jsonify({
                "response": f"📋 Your drills for today (Day {progress}) are: {', '.join(drill_names) if drill_names else 'No drills found.'}"
})

    
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
    week_start = today - timedelta(days=today.weekday())  

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

       
        numeric_results = []
        for x in raw_results:
            try:
                numeric_results.append(float(x))
            except ValueError:
                continue

        average_score = sum(numeric_results) / len(numeric_results) if numeric_results else 0

       
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
        name = name.lower()  
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

    daily_results = db.collection("dailyResults").where("email", "==", data.get("email")).stream()
    data["daily_results"] = [doc.to_dict() for doc in daily_results]

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

   
    if "xp" in question:
        return jsonify({"response": f"💪 You currently have {player.get('xp', 0)} XP."})

    if "level" in question or "skill" in question:
        return jsonify({"response": f"🧠 Your current skill level is {player.get('skill_level', 'Unknown')}."})

    if "badge" in question:
        badges = player.get("badges", [])
        return jsonify({"response": f"🏅 You’ve earned: {', '.join(badges) if badges else 'no badges yet.'}"})

    if "drill" in question and "today" in question:
        routine_dict = player.get("routine", {})
        progress = player.get("routine_progress", 1)
        matching_day = f"Day {progress}"

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

schedule.every().day.at("08:00").do(send_daily_reminders)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True, port=5050)


