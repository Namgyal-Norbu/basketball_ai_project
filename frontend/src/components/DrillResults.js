import React, { useState } from "react";
import { db, doc, getDoc } from "../firebaseConfig";
import "./styles.css";

function DailyDrill() {
  const [name, setName] = useState("");
  const [day] = useState(new Date().toLocaleDateString("en-US", { weekday: "long" }));
  const [dailyDrills, setDailyDrills] = useState([]);
  const [message, setMessage] = useState("");

  const searchDailyDrills = async () => {
    if (!name) {
      setMessage("Please enter a player name.");
      return;
    }

    try {
      const ref = doc(db, "players", name);
      const snap = await getDoc(ref);

      if (snap.exists()) {
        const data = snap.data();
        const routine = data.routine || {};
        const todayDrills = routine[day] || routine[`Day 1 (${day})`] || [];

        setDailyDrills(todayDrills);
        setMessage(todayDrills.length > 0 ? "" : "No drills assigned for today.");
      } else {
        setDailyDrills([]);
        setMessage("Player not found.");
      }
    } catch (err) {
      console.error("Error fetching daily drills:", err);
      setMessage("Failed to fetch daily drills.");
    }
  };

  return (
    <div className="container">
      <h2>📅 Daily Drill (Today: {day})</h2>

      <label>Player Name:</label>
      <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
      <button onClick={searchDailyDrills}>Get Today's Routine</button>

      {dailyDrills.length > 0 && (
        <ul>
          {dailyDrills.map((drill, index) => (
            <li key={index}>{drill}</li>
          ))}
        </ul>
      )}

      {message && <p>{message}</p>}
    </div>
  );
}

export default DailyDrill;
