import React, { useState, useEffect } from "react";
import { useUser } from "./UserContext";
import "./styles.css";

function SubmitDrill() {
  const user = useUser();
  const [position, setPosition] = useState("Guard");
  const [daysPerWeek, setDaysPerWeek] = useState(3);
  const [testDrills, setTestDrills] = useState([]);
  const [results, setResults] = useState({});
  const [message, setMessage] = useState("");
  const [hasCompletedTest, setHasCompletedTest] = useState(false); 
  const [showOnLeaderboard, setShowOnLeaderboard] = useState(true);

  const name = user?.displayName?.toLowerCase();

  useEffect(() => {
    if (!user) {
      setMessage("Please log in to continue.");
      return;
    }

    // 🔍 Check if test already completed
    const checkTestStatus = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:5000/player_status?name=${name}`);
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
  }, [user, name]);

  const fetchTestDrills = async () => {
    if (!name || !position) {
      setMessage("Missing name or position.");
      return;
    }

    try {
      const res = await fetch("http://127.0.0.1:5000/generate_drill_test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          name, 
          position,
          email: user.email 
        }),
        
      });

      const data = await res.json();

      if (res.status === 403) {
        setMessage("🚫 You've already completed the drill test.");
        setHasCompletedTest(true);
        setTestDrills([]);
        return;
      }

      if (data.drills) {
        const initial = {};
        data.drills.forEach((drill) => (initial[drill] = ""));
        setTestDrills(data.drills);
        setResults(initial);
        setMessage(data.message || "");
      } else {
        setMessage(data.error || "Error getting test drills.");
      }
    } catch (err) {
      console.error("Fetch error:", err);
      setMessage("Could not load test drills.");
    }
  };

  const handleSubmit = async () => {
    const formattedResults = {};
    testDrills.forEach((drill, idx) => {
      formattedResults[`Drill ${idx + 1}`] = parseInt(results[drill] || "0");
    });

    try {
      const res = await fetch("http://127.0.0.1:5000/submit_test_results", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          email: user.email,
          position,
          results: formattedResults,
          show_on_leaderboard: showOnLeaderboard,
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

      setTestDrills([]);
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
              <label>Position:</label>
              <select value={position} onChange={(e) => setPosition(e.target.value)}>
                <option value="Guard">Guard</option>
                <option value="Forward">Forward</option>
                <option value="Center">Center</option>
              </select>

              <label>Days per Week:</label>
              <select value={daysPerWeek} onChange={(e) => setDaysPerWeek(Number(e.target.value))}>
                <option value={3}>3</option>
                <option value={5}>5</option>
                <option value={7}>7</option>
              </select>

              <button onClick={fetchTestDrills} disabled={hasCompletedTest}>
                🧪 Get Test Drills
              </button>

              {testDrills.length > 0 && (
                <div className="form-section">
                  <h3>Test Drills</h3>
                  {testDrills.map((drill, idx) => (
                    <div key={idx}>
                      <label>{drill}</label>
                      <input
                        type="text"
                        value={results[drill] || ""}
                        onChange={(e) =>
                          setResults({ ...results, [drill]: e.target.value })
                        }
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
