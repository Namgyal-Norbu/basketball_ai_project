import React, { useState, useEffect } from "react";
import "./styles.css";

function DrillTest({ user }) {
  const [todayDrills, setTodayDrills] = useState([]);
  const [results, setResults] = useState({});
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [routineDayLabel, setRoutineDayLabel] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [xpGained, setXpGained] = useState(0);
  const [mockDay, setMockDay] = useState("");

  const email = user?.email;

  const checkSubmissionStatus = async () => {
    if (!email) return;
    try {
      const res = await fetch(`http://localhost:5050/check_today_submission?email=${email}`);
      const data = await res.json();
      setSubmitted(data.submitted);
      setXpGained(data.xp_gained || 0);
    } catch (err) {
      console.error("Failed to check submission:", err);
    }
  };

  const loadTodayDrills = async () => {
    if (!email) return;
  
    try {
      setLoading(true);
      setMessage("");
  
      const res = await fetch(`http://localhost:5050/get_routine?email=${email}&mock_day=${mockDay}`);
      const data = await res.json();
  
      if (data.error || data.message) {
        setMessage(data.error || data.message);
        setTodayDrills([]);
        setRoutineDayLabel("");
        return;
      }
  
      const todayRoutine = data.drills || [];
      setTodayDrills(todayRoutine);
      setRoutineDayLabel(`Day ${data.day.split(" ")[1]} (from ${mockDay})`);

  
      const initialResults = {};
      todayRoutine.forEach((drill) => {
        initialResults[drill.name] = "";
      });
      setResults(initialResults);
    } catch (err) {
      console.error("Error loading drills:", err);
      setMessage("⚠️ Error fetching today's drills.");
    } finally {
      setLoading(false);
    }
  };
  

  useEffect(() => {
    if (email) {
      loadTodayDrills();
      checkSubmissionStatus();
    }
  }, [email, mockDay]);

  const handleResultSubmit = async () => {
    const allFilled = Object.values(results).every(val => val !== "" && !isNaN(val));
    if (!allFilled) {
      setMessage("🚫 Please enter a score for each drill.");
      return;
    }

    const formattedResults = {};
    Object.entries(results).forEach(([drillName, value]) => {
      formattedResults[drillName] = Number(value);
    });

    try {
      const res = await fetch("http://localhost:5050/submit_daily_results", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: user.displayName,
          email: user.email,
          results: formattedResults,
          mock_day: mockDay || undefined
        }),
      });

      const data = await res.json();
      if (res.status === 200) {
        setMessage(data.message || "✅ Drill results submitted!");
        setSubmitted(true);
        setXpGained(data.xp_gained || 0);
      } else {
        setMessage(data.error || "⚠️ Failed to submit results.");
      }
    } catch (err) {
      console.error("Error submitting results:", err);
      setMessage("⚠️ Failed to submit results.");
    }
  };

  return (
    <div className="container">
      <h2>📅 Today's Routine {routineDayLabel && `(${routineDayLabel})`}</h2>

      {user ? (
        <>
          <p><strong>Welcome,</strong> {user.displayName}</p>
          <input
            type="text"
            placeholder="🛠 Enter mock day (e.g. 2025-04-14)"
            value={mockDay}
            onChange={(e) => setMockDay(e.target.value)}
            style={{ marginBottom: "12px", padding: "8px", width: "100%", maxWidth: "400px" }}
          />

          {loading ? (
            <p>⏳ Loading drills...</p>
          ) : todayDrills.length > 0 ? (
            <>
              <div className="form-section">
                {todayDrills.map((drill, idx) => (
                  <div key={idx} className="drill-card enhanced-drill-card">
                    <h3 className="drill-title">{drill.name}</h3>
                    <p className="drill-reps"><em>📌 {drill.reps}</em></p>
                    <p className="drill-description">{drill.description}</p>
                    {submitted ? (
                      <p className="submitted-text">✅ Already submitted</p>
                    ) : (
                      <select
                  className="drill-input"
                  value={results[drill.name] || ""}
                  onChange={(e) =>
                    setResults({ ...results, [drill.name]: e.target.value })
                  }
                >
                  <option value="">🏀 Select Score</option>
                  {[...Array(11)].map((_, i) => {
                    const score = i * 10;
                    return (
                      <option key={score} value={score}>
                        {score}
                      </option>
                    );
                  })}
                </select>

                    )}
                  </div>
                ))}
              </div>

              <button
                onClick={handleResultSubmit}
                disabled={submitted}
                className={submitted ? "disabled" : ""}
              >
                {submitted ? "✅ Already Submitted" : "✅ Submit Results"}
              </button>

              {submitted && xpGained > 0 && (
                <p className="xp-gained-text">🌟 You gained {xpGained} XP today!</p>
              )}
            </>
          ) : (
            <p>📭 No drills assigned for today.</p>
          )}
        </>
      ) : (
        <p>🔒 Please log in to view your drills.</p>
      )}

      {message && <p>{message}</p>}
    </div>
  );
}

export default DrillTest;
