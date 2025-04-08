import React, { useState, useEffect } from "react";
import { db, doc, getDoc } from "../firebaseConfig";
import { useUser } from "./UserContext";
import "./styles.css";

function DailyDrill() {
  const user = useUser();
  const [day] = useState(new Date().toLocaleDateString("en-US", { weekday: "long" }));
  const [dailyDrills, setDailyDrills] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const fetchDailyDrills = async () => {
      if (!user) return;

      try {
        const ref = doc(db, "players", user.email);
        const snap = await getDoc(ref);

        if (snap.exists()) {
          const data = snap.data();
          const routine = data.routine || {};
          const todayDrills = routine[day] || [];

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

    fetchDailyDrills();
  }, [user, day]);

  if (!user) {
    return <p>🔒 Please log in to view your daily drills.</p>;
  }

  return (
    <div className="container">
      <h2>📅 Your Drills for {day}</h2>

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
