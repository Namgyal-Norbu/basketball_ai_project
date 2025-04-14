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

  useEffect(() => {
    if (!user) return;

    const checkTestStatus = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:5000/player_status?email=${user.email}`);
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

  const fetchTestDrills = async () => {
    try {
      const res = await fetch("http://127.0.0.1:5000/generate_drill_test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email: user.email })
      });

      const data = await res.json();
      if (res.ok && data.drills) {
        setTestDrills(data.drills);

        const initial = {};
        for (const drills of Object.values(data.drills)) {
          drills.forEach(drill => {
            initial[drill] = "";
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

  const handleChange = (key, value) => {
    setResults({ ...results, [key]: value });
  };

  const handleSubmit = async () => {
    const allFilled = Object.values(results).every(val => val !== "" && !isNaN(val));
    if (!allFilled) {
      setMessage("🚫 Please complete all drill scores before submitting.");
      return;
    }

    const formattedResults = {};
    for (const drill in results) {
      formattedResults[drill] = Number(results[drill]) || 0;
    }

    try {
      const res = await fetch("http://127.0.0.1:5000/submit_test_results", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          email: user.email,
          results: formattedResults,
          show_on_leaderboard: showOnLeaderboard,
          wants_email_reminders: wantsEmailReminders,
          days_per_week: daysPerWeek
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
    <div className="container">
      <h2>🏀 Submit Drill Test</h2>

      {user ? (
        <>
          <p><strong>Logged in as:</strong> {user.displayName}</p>

          {hasCompletedTest ? (
            <p>✅ You have already completed your drill test. Great work!</p>
          ) : (
            <>
              <label>Days per Week:</label>
              <select value={daysPerWeek} onChange={(e) => setDaysPerWeek(Number(e.target.value))}>
                {[1, 2, 3, 4, 5, 6, 7].map((day) => (
                  <option key={day} value={day}>{day}</option>
                ))}
              </select>

              <button onClick={fetchTestDrills}>🧪 Load Test Drills</button>

              {Object.keys(testDrills).length > 0 && (
                <div className="form-section">
                  {Object.entries(testDrills)
                    .flatMap(([_, drills]) => drills)
                    .map((drill, idx) => (
                      <div key={idx}>
                        <label>{drill}</label>
                        <input
                          type="number"
                          value={results[drill] || ""}
                          onChange={(e) => handleChange(drill, e.target.value)}
                          min="0"
                          max="100"
                        />
                      </div>
                    ))}

                  <div className="checkbox-wrapper">
                    <input
                      type="checkbox"
                      id="showOnLeaderboard"
                      checked={showOnLeaderboard}
                      onChange={() => setShowOnLeaderboard(!showOnLeaderboard)}
                    />
                    <label htmlFor="showOnLeaderboard">Show my stats on the public leaderboard</label>
                  </div>

                  <div className="checkbox-wrapper">
                    <input
                      type="checkbox"
                      id="wantsEmailReminders"
                      checked={wantsEmailReminders}
                      onChange={() => setWantsEmailReminders(!wantsEmailReminders)}
                    />
                    <label htmlFor="wantsEmailReminders">Send me daily email reminders for drills</label>
                  </div>

                  <button onClick={handleSubmit}>✅ Submit Test Results</button>
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
