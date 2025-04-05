import React, { useState } from "react";
import { db, doc, getDoc } from "../firebaseConfig";

function DailyRoutine() {
  const [name, setName] = useState("");
  const [routine, setRoutine] = useState(null);
  const [message, setMessage] = useState("");

  const fetchRoutine = async () => {
    if (!name) return setMessage("Enter a player name.");

    try {
      const playerRef = doc(db, "players", name);
      const playerSnap = await getDoc(playerRef);

      if (playerSnap.exists()) {
        const data = playerSnap.data();
        setRoutine(data.routine || {});
        setMessage("");
      } else {
        setMessage("Player not found.");
        setRoutine(null);
      }
    } catch (err) {
      console.error("Error fetching routine:", err);
      setMessage("Error fetching routine.");
    }
  };

  return (
    <div className="container">
      <h2>🏀 View 14-Day Drill Routine</h2>
      <input
        type="text"
        placeholder="Enter player name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <button onClick={fetchRoutine}>Fetch Routine</button>

      {message && <p>{message}</p>}

      {routine && (
        <div className="routine-box">
          {Object.entries(routine).map(([day, drills]) => (
            <div key={day} className="routine-day">
              <h4>{day}</h4>
              <ul>
                {drills.map((drill, i) => (
                  <li key={i}>{drill}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default DailyRoutine;
