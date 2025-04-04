from experta import *
from database import get_players, get_latest_training

# Training routines based on position & skill level
training_routines = {
    "Guard": {
        "Amateur": ["Basic Dribbling", "Layups", "Short-range Shooting"],
        "Beginner": ["Dribbling under Pressure", "Free Throws", "Passing"],
        "Intermediate": ["Pick-and-Roll Offense", "3-Point Shooting", "Fast Break Drills"],
        "Advanced": ["Isolation Moves", "Step-Back Shooting", "Ball Handling under Pressure"],
        "Professional": ["Elite Shooting Drills", "Advanced Court Vision Training", "Quick Decision Making"]
    },
    "Forward": {
        "Amateur": ["Basic Post Moves", "Short-range Shots", "Rebounding Basics"],
        "Beginner": ["Post-up Game", "Mid-Range Shooting", "Boxing Out"],
        "Intermediate": ["Pick-and-Pop Offense", "3-Point Shooting", "Help Defense"],
        "Advanced": ["Spin Moves", "Jump Hook", "Defensive Switching"],
        "Professional": ["Elite Post Play", "Footwork & Agility", "Advanced Rebounding"]
    },
    "Center": {
        "Amateur": ["Basic Hook Shot", "Defensive Positioning", "Layups"],
        "Beginner": ["Shot Blocking", "Power Moves", "Defensive Rebounding"],
        "Intermediate": ["Drop Step", "Mid-range Shooting", "Screening"],
        "Advanced": ["Face-up Game", "Elite Rim Protection", "Footwork Drills"],
        "Professional": ["NBA-Level Post Play", "Dominant Defensive Strategies", "High-Post Shooting"]
    }
}

### **AI-BASED TRAINING RECOMMENDATIONS** ###
def get_ai_recommendations(player_id):
    """Generate AI-based training recommendations for a player"""
    training_data = get_latest_training(player_id)

    if not training_data:
        return {"error": "No training data found"}

    shooting, dribbling, finishing = training_data[:3]

    recommendations = {
        "shooting": "Advanced shot selection" if shooting > 70 else "Basic shooting drills",
        "dribbling": "Advanced ball-handling drills" if dribbling > 70 else "Fundamental dribbling drills",
        "finishing": "Aggressive finishing moves" if finishing > 70 else "Basic layup drills"
    }

    return recommendations

# AI Engine Constants
EASY_ADJUSTMENT = -10  # Reduce difficulty by 10% if player underperforms
HARD_ADJUSTMENT = 10   # Increase difficulty by 10% if player overperforms
THRESHOLD = 15         # % change needed to trigger an adjustment

class Player(Fact):
    """Defines a basketball player with training stats and expected values."""
    player_id = Field(int, mandatory=True)
    shooting_accuracy = Field(float, default=50.0)
    dribbling_skill = Field(float, default=50.0)
    finishing_skill = Field(float, default=50.0)
    expected_shooting = Field(float, default=50.0)
    expected_dribbling = Field(float, default=50.0)
    expected_finishing = Field(float, default=50.0)
    skill_level = Field(str, default="Amateur")
    position = Field(str, default="Guard")

class TrainingAI(KnowledgeEngine):
    
    @Rule(Player(player_id=MATCH.p_id, skill_level=MATCH.skill, position=MATCH.pos))
    def assign_training_routine(self, p_id, skill, pos):
        routine = training_routines.get(pos, {}).get(skill, ["No training available"])
        print(f"🏀 Player ID {p_id}: Assigned Training Routine for {pos} ({skill}): {routine}")

    @Rule(Player(shooting_accuracy=MATCH.s_acc, expected_shooting=MATCH.exp_s, player_id=MATCH.p_id))
    def adjust_shooting(self, s_acc, exp_s, p_id):
        """Adjust shooting drills if the player over or underperforms significantly."""
        diff = ((s_acc - exp_s) / exp_s) * 100  # Percentage change
        if diff < -THRESHOLD:
            print(f"⚠️ Player {p_id} underperformed in shooting (-{abs(diff):.1f}%). Assigning easier drills!")
        elif diff > THRESHOLD:
            print(f"🔥 Player {p_id} overperformed in shooting (+{diff:.1f}%). Assigning harder drills!")

    @Rule(Player(dribbling_skill=MATCH.d_skill, expected_dribbling=MATCH.exp_d, player_id=MATCH.p_id))
    def adjust_dribbling(self, d_skill, exp_d, p_id):
        diff = ((d_skill - exp_d) / exp_d) * 100
        if diff < -THRESHOLD:
            print(f"⚠️ Player {p_id} underperformed in dribbling (-{abs(diff):.1f}%). Assigning easier drills!")
        elif diff > THRESHOLD:
            print(f"🔥 Player {p_id} overperformed in dribbling (+{diff:.1f}%). Assigning harder drills!")

    @Rule(Player(finishing_skill=MATCH.f_skill, expected_finishing=MATCH.exp_f, player_id=MATCH.p_id))
    def adjust_finishing(self, f_skill, exp_f, p_id):
        diff = ((f_skill - exp_f) / exp_f) * 100
        if diff < -THRESHOLD:
            print(f"⚠️ Player {p_id} underperformed in finishing (-{abs(diff):.1f}%). Assigning easier drills!")
        elif diff > THRESHOLD:
            print(f"🔥 Player {p_id} overperformed in finishing (+{diff:.1f}%). Assigning harder drills!")

# Initialize AI Engine
ai = TrainingAI()
ai.reset()

# Fetch players and their latest training logs
players = get_players()
for player in players:
    player_id, name, skill_level, position, shooting_accuracy, dribbling_skill, finishing_skill = player
    shooting, dribbling, finishing = get_latest_training(player_id)
    
    # Expected values (assuming player's previous session is the expected level)
    expected_shooting = shooting - 5  
    expected_dribbling = dribbling - 5  
    expected_finishing = finishing - 5  

    print(f"📊 Loading Player ID {player_id}: {name} ({position}, {skill_level})")
    ai.declare(Player(
        player_id=player_id, 
        shooting_accuracy=shooting, 
        dribbling_skill=dribbling, 
        finishing_skill=finishing,
        expected_shooting=expected_shooting,
        expected_dribbling=expected_dribbling,
        expected_finishing=expected_finishing,
        skill_level=skill_level or "Amateur", 
        position=position
    ))

# Run AI engine
ai.run()
