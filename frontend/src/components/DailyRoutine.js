import React, { useState, useEffect } from "react";
import { useUser } from "./UserContext"; // ✅ import logged-in user
import { db, doc, getDoc } from "../firebaseConfig";

function DailyRoutine() {
  const user = useUser();
  const [routine, setRoutine] = useState(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const fetchRoutine = async () => {
      if (!user) return;

      try {
        const playerRef = doc(db, "players", user.email);
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

    fetchRoutine();
  }, [user]);

  if (!user) {
    return <p>🔒 Please log in to view your daily routine.</p>;
  }

  return (
    <div className="container">
      <h2>🏀 Your 14-Day Drill Routine</h2>
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
