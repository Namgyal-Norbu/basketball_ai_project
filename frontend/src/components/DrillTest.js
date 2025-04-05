import React, { useState, useEffect } from "react";
import { db, doc, getDoc, setDoc } from "../firebaseConfig";
import "./styles.css";

function DrillTest({ user }) {
  const [todayDrills, setTodayDrills] = useState([]);
  const [results, setResults] = useState({});
  const [message, setMessage] = useState("");

  const name = user?.displayName?.toLowerCase();
  const todayName = new Date().toLocaleDateString("en-US", { weekday: "long" });

  useEffect(() => {
    const fetchTodaysDrills = async () => {
      if (!name) return;

      try {
        const ref = doc(db, "players", name);
        const snap = await getDoc(ref);

        if (snap.exists()) {
          const data = snap.data();
          const routine = data.routine || {};

          // 🔍 Find the routine key that contains today (e.g. "Day 3 - Wednesday")
          const matchedKey = Object.keys(routine).find((key) =>
            key.includes(todayName)
          );

          const todayRoutine = matchedKey ? routine[matchedKey] : [];

          setTodayDrills(todayRoutine);

          // Initialize results input
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
      }
    };

    fetchTodaysDrills();
  }, [name, todayName]);

  const handleResultSubmit = async () => {
    const formattedResults = {};
    Object.entries(results).forEach(([drillName, value]) => {
      formattedResults[drillName] = parseInt(value || "0");
    });
  
    try {
      const res = await fetch("http://127.0.0.1:5000/submit_daily_results", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
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

          {todayDrills.length > 0 ? (
            <>
              <div className="form-section">
                {todayDrills.map((drill, idx) => (
                  <div key={idx}>
                    <label>{drill}</label>
                    <input
                      type="text"
                      placeholder="Enter result"
                      value={results[drill] || ""}
                      onChange={(e) =>
                        setResults({ ...results, [drill]: e.target.value })
                      }
                    />
                  </div>
                ))}
              </div>
              <button onClick={handleResultSubmit}>Submit Results</button>
            </>
          ) : (
            <p>No drills assigned for today.</p>
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
