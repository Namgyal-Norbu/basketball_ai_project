import React, { useState, useEffect } from "react";
import { db, doc, getDoc } from "../firebaseConfig";
import "./styles.css";

function DrillTest({ user }) {
  const [todayDrills, setTodayDrills] = useState([]);
  const [results, setResults] = useState({});
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const email = user?.email;
  const todayName = new Date().toLocaleDateString("en-US", { weekday: "long" });

  useEffect(() => {
    const fetchTodaysDrills = async () => {
      if (!email) return;

      try {
        setLoading(true);
        const ref = doc(db, "players", email);
        const snap = await getDoc(ref);

        if (snap.exists()) {
          const data = snap.data();
          const routine = data.routine || {};
          const matchedKey = Object.keys(routine).find((key) =>
            key.includes(todayName)
          );
          const todayRoutine = matchedKey ? routine[matchedKey] : [];

          setTodayDrills(todayRoutine);

          const initialResults = {};
          todayRoutine.forEach((drill) => {
            initialResults[drill] = "";
          });
          setResults(initialResults);
        } else {
          setMessage("❌ Player not found in database.");
        }
      } catch (err) {
        console.error("Error loading drills:", err);
        setMessage("⚠️ Error fetching today's drills.");
      } finally {
        setLoading(false);
      }
    };

    fetchTodaysDrills();
  }, [email, todayName]);

  const handleResultSubmit = async () => {
    // Validate all inputs are filled
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
      const res = await fetch("http://127.0.0.1:5000/submit_daily_results", {
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
      <h2>📅 Today's Routine ({todayName})</h2>

      {user ? (
        <>
          <p><strong>Welcome,</strong> {user.displayName}</p>

          {loading ? (
            <p>⏳ Loading drills...</p>
          ) : todayDrills.length > 0 ? (
            <>
              <div className="form-section">
                {todayDrills.map((drill, idx) => (
                  <div key={idx}>
                    <label>{drill}</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      placeholder="Enter score (0–100)"
                      value={results[drill] || ""}
                      onChange={(e) =>
                        setResults({ ...results, [drill]: e.target.value })
                      }
                    />
                  </div>
                ))}
              </div>
              <button onClick={handleResultSubmit} disabled={todayDrills.length === 0}>
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
