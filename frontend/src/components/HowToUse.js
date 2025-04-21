import React from "react";
import "./styles.css";

function HowToUse() {
  return (
    <div className="container how-to-use-page">
      <h2>📘 How to Use Basketball AI</h2>

      <section className="card">
        <h3>👤 1. Sign In</h3>
        <p>Sign in with your Google account to access your personalized basketball training dashboard.</p>
      </section>

      <section className="card">
        <h3>🧪 2. Take the Skill Test</h3>
        <p>Complete an initial 5-drill skill assessment covering shooting, ball handling, defense, finishing, and footwork. Your performance will determine your starting skill level and unlock your 14-day routine.</p>
      </section>

      <section className="card">
        <h3>📅 3. Start Your 14-Day Routine</h3>
        <p>Each day, you'll receive a customized drill based on your skill level and different skill categories. Your routine is tracked using your start date, and cycles every 14 days.</p>
      </section>

      <section className="card">
        <h3>📤 4. Submit Daily Results</h3>
        <p>Log your performance after completing each drill. You'll earn XP, and your skill level may change based on trends across your most recent submissions.</p>
      </section>

      <section className="card">
        <h3>🏅 5. Earn Badges & XP</h3>
        <p>Badges are awarded based on your consistency, drill volume, and XP milestones. Earn XP with every valid submission and track your growth visually.</p>
      </section>

      <section className="card">
        <h3>📊 6. View Progress & Leaderboards</h3>
        <p>Track your skill-specific performance over time. If you choose to opt in, your XP and stats can appear on the leaderboard with top performers.</p>
      </section>

      <section className="card">
        <h3>🔐 7. Control Your Data</h3>
        <p>You can download your data or permanently delete your profile from the homepage at any time. Your privacy and control are a priority.</p>
      </section>
    </div>
  );
}

export default HowToUse;
