# faq_bot.py
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_faq_bot(user_question):
    context = """
    You are a helpful FAQ assistant for a basketball training app.

    Some key info:
    - Players get XP by submitting daily drills.
    - Players can be promoted or demoted between Beginner, Intermediate, and Advanced.
    - Leaderboard shows top players by XP and weekly performance.
    - Email reminders are optional and can be turned on during drill test.
    - Users must log in with Google to access their routine.
    - A 14-day personalized routine is created based on skill and position.
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": user_question}
        ],
        max_tokens=300,
        temperature=0.5
    )

    return response.choices[0].message["content"]
