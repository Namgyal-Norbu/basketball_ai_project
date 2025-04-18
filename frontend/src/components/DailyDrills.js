import React, { useState, useEffect } from "react";
import "./styles.css";

function DrillTest({ user }) {
  const [todayDrills, setTodayDrills] = useState([]);
  const [results, setResults] = useState({});
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [routineDayLabel, setRoutineDayLabel] = useState("");

  const email = user?.email;

  const loadTodayDrills = async () => {
    if (!email) return;

    try {
      setLoading(true);
      setMessage("");

      const res = await fetch(`http://localhost:5050/get_routine?email=${email}`);
      const data = await res.json();

      // ✅ Handle error or message returned from the backend
      if (data.error || data.message) {
        setMessage(data.error || data.message);
        setTodayDrills([]);
        setRoutineDayLabel("");
        return;
      }

      const todayRoutine = data.drills || [];
      setTodayDrills(todayRoutine);
      setRoutineDayLabel(data.day || "");

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
    loadTodayDrills();
  }, [email]);

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
        }),
      });

      const data = await res.json();
      if (res.status === 200) {
        setMessage(data.message || "✅ Drill results submitted!");
        loadTodayDrills(); // Refresh drills in case it completes a day
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
                    <input
                      type="number"
                      className="drill-input"
                      min="0"
                      max="100"
                      placeholder="🏀 Enter score (0–100)"
                      value={results[drill.name] || ""}
                      onChange={(e) =>
                        setResults({ ...results, [drill.name]: e.target.value })
                      }
                    />
                  </div>
                ))}
              </div>

              <button onClick={handleResultSubmit}>
                ✅ Submit Results
              </button>
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
