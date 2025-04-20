import React from "react";
import "./styles.css";

function HowToUse() {
  return (
    <div className="container how-to-use-page">
      <h2>📘 How to Use Basketball AI</h2>

      <section className="card">
        <h3>👤 1. Sign In</h3>
        <p>Log in using your Google account to access your personalized dashboard.</p>
      </section>

      <section className="card">
        <h3>🧪 2. Take the Drill Test</h3>
        <p>Complete an initial 3-drill test based on your position (Guard, Forward, Center). Your performance will determine your starting skill level.</p>
      </section>

      <section className="card">
        <h3>📅 3. Follow Your 14-Day Routine</h3>
        <p>A daily training plan will be generated for you. Each day includes skill-appropriate drills tailored to your role and ability.</p>
      </section>

      <section className="card">
        <h3>📈 4. Submit Daily Results</h3>
        <p>After completing your drills, enter your results to earn XP and track your progress. The system adapts your level based on performance trends.</p>
      </section>

      <section className="card">
        <h3>🏆 5. Earn Badges & Climb the Leaderboard</h3>
        <p>Gain XP and unlock badges based on consistency, volume, and surprise achievements. Top performers can appear on the leaderboard if opted in.</p>
      </section>

      <section className="card">
        <h3>🔐 6. Privacy & Control</h3>
        <p>From the homepage, you can download all your data or permanently delete your profile at any time.</p>
      </section>
    </div>
  );
}

export default HowToUse;
