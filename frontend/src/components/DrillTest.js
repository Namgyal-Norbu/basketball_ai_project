import React, { useState, useEffect } from "react";
import { useUser } from "./UserContext";
import "./styles.css";

function SubmitDrill() {
  const user = useUser();
  const [daysPerWeek, setDaysPerWeek] = useState(3);
  const [testDrills, setTestDrills] = useState({});
  const [results, setResults] = useState({});
  const [message, setMessage] = useState("");
  const [hasCompletedTest, setHasCompletedTest] = useState(false);
  const [showOnLeaderboard, setShowOnLeaderboard] = useState(true);
  const [wantsEmailReminders, setWantsEmailReminders] = useState(true);
  const name = user?.displayName?.toLowerCase();

  //checks if player has already completed test by using email
  useEffect(() => {
    if (!user) return;
    const checkTestStatus = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:5050/player_status?email=${user.email}`);
        const data = await res.json();
        if (data.test_completed) {
          setHasCompletedTest(true);
          setMessage("🚫 You’ve already completed your drill test.");
        }
      } catch (err) {
        console.error("Error checking test status:", err);
      }
    };
    checkTestStatus();
  }, [user]);

  // calling the backend app.route generating the drill test 
  const fetchTestDrills = async () => {
    try {
      const res = await fetch("http://127.0.0.1:5050/generate_drill_test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email: user.email }),
      });

      const data = await res.json();
      if (res.ok && data.drills) {
        setTestDrills(data.drills);
        const initial = {};
        for (const drills of Object.values(data.drills)) {
          drills.forEach(drill => {
            initial[drill.name] = "";
          });
        }
        setResults(initial);
        setMessage(data.message || "");
      } else {
        setMessage(data.error || "Failed to fetch drills.");
      }
    } catch (error) {
      console.error("Fetch error:", error);
      setMessage("Unable to load drills.");
    }
  };

 // update drill score after user input 
  const handleChange = (key, value) => {
    setResults(prev => ({ ...prev, [key]: value }));
  };

//submit drill score and player preference 
  const handleSubmit = async () => {

// ensure all inputs are filled 
    const allFilled = Object.values(results).every(val => val !== "" && !isNaN(val));
    if (!allFilled) {
      setMessage("🚫 Please complete all drill scores before submitting.");
      return;
    }
    const formattedResults = {};
    for (const drill in results) {
      formattedResults[drill] = Number(results[drill]) || 0;
    }
// runs the app.route submit_test_results
    try {
      const res = await fetch("http://127.0.0.1:5050/submit_test_results", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          // collects the following information from the user
          name,
          email: user.email,
          results: formattedResults,
          show_on_leaderboard: showOnLeaderboard,
          wants_email_reminders: wantsEmailReminders,
          days_per_week: daysPerWeek,
        }),
      });

      const data = await res.json();
      if (res.status === 403) {
        setMessage("🚫 You have already submitted your drill test.");
        setHasCompletedTest(true);
      } else {
        setMessage(data.message || "✅ Drill results submitted!");
        setHasCompletedTest(true);
      }
    } catch (error) {
      console.error("Submit error:", error);
      setMessage("Failed to submit test results.");
    }
  };

  return (
    <div className="container test-form">
      <h2 className="test-header">🏀 Submit Drill Test</h2>

      {user ? (
        <>
          <p><strong>Logged in as:</strong> {user.displayName}</p>

          {hasCompletedTest ? (
            <p>✅ You have already completed your drill test. Great work!</p>
          ) : (
            <>
              <div className="form-section">
                <label style={{ fontWeight: "bold" }}>📅 Days per Week:</label>
                <select
                  value={daysPerWeek}
                  onChange={(e) => setDaysPerWeek(Number(e.target.value))}
                >
                  {[1, 2, 3, 4, 5, 6, 7].map(day => (
                    <option key={day} value={day}>{day}</option>
                  ))}
                </select>

                <button onClick={fetchTestDrills}>🧪 Load Test Drills</button>
              </div>

              {Object.keys(testDrills).length > 0 && (
                <div className="form-section">
                  {Object.entries(testDrills)
                    .flatMap(([_, drills]) => drills)
                    .map((drill, idx) => (
                      <div key={idx} className="drill-card">
                        <h4>{drill.name}</h4>
                        <p><em>{drill.reps}</em></p>
                        <p>{drill.description}</p>
                        <select
                className="drill-input"
                value={results[drill.name] || ""}
                onChange={(e) => handleChange(drill.name, e.target.value)}
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

                      </div>
                    ))}

                  <div className="checkbox-wrapper">
                    <input
                      type="checkbox"
                      id="showOnLeaderboard"
                      checked={showOnLeaderboard}
                      onChange={() => setShowOnLeaderboard(!showOnLeaderboard)}
                    />
                    <label htmlFor="showOnLeaderboard">
                      Show my stats on the public leaderboard
                    </label>
                  </div>

                  <div className="checkbox-wrapper">
                    <input
                      type="checkbox"
                      id="wantsEmailReminders"
                      checked={wantsEmailReminders}
                      onChange={() => setWantsEmailReminders(!wantsEmailReminders)}
                    />
                    <label htmlFor="wantsEmailReminders">
                      Send me daily email reminders for drills
                    </label>
                  </div>

                  <button className="submit-btn" onClick={handleSubmit}>
                    ✅ Submit Test Results
                  </button>
                </div>
              )}
            </>
          )}
        </>
      ) : (
        <p>🔒 Please log in to access your drill test.</p>
      )}

      {message && <p>{message}</p>}
    </div>
  );
}

export default SubmitDrill;
