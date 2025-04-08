import React, { useEffect, useState } from "react";
import { useUser } from "./UserContext";
import { db, doc, getDoc, collection, query, where, getDocs } from "../firebaseConfig";
import "./styles.css";

function Home() {
  const user = useUser();
  const [level, setLevel] = useState(1);
  const [xp, setXp] = useState(0);
  const [streak, setStreak] = useState(0);
  const [badges, setBadges] = useState([]);


  const xpToNextLevel = 500;

  const handleDownloadData = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:5000/export_profile?name=${user.displayName.toLowerCase()}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${user.displayName.toLowerCase()}_data.json`;
      a.click();
    } catch (err) {
      alert("⚠️ Failed to download data");
    }
  };
  
  
  const handleDeleteProfile = async () => {
    const confirmed = window.confirm("Are you sure you want to permanently delete your profile?");
    if (!confirmed) return;
  
    try {
      const res = await fetch("http://127.0.0.1:5000/delete_profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: user.displayName.toLowerCase() }),
      });
      const data = await res.json();
      alert(data.message || "Profile deleted.");
      window.location.reload();
    } catch (err) {
      alert("❌ Error deleting profile");
    }
  };
  

  useEffect(() => {
    if (!user) return;

    const playerId = user.displayName.toLowerCase();

    const fetchPlayerStats = async () => {
      const playerRef = doc(db, "players", playerId);
      const playerSnap = await getDoc(playerRef);

      if (playerSnap.exists()) {
        const data = playerSnap.data();
        const totalXP = data.xp || 0;
        const playerLevel = Math.floor(totalXP / xpToNextLevel) + 1;
        const xpInCurrentLevel = totalXP % xpToNextLevel;

        setXp(xpInCurrentLevel);
        setLevel(playerLevel);
        setBadges(generateBadges(data));
      }
    };

    const fetchDailyStreak = async () => {
      const ref = collection(db, "dailyResults");
      const q = query(ref, where("email", "==", user.email));
      const snap = await getDocs(q);
      const days = new Set();
      snap.forEach(doc => days.add(doc.data().day));
      setStreak(days.size);
    };

    fetchPlayerStats();
    fetchDailyStreak();
  }, [user]);

  const generateBadges = (data) => {
    const b = [];
    if ((data.results || []).length >= 10) b.push("🏅 10 Drills");
    if ((data.skill_level || "") === "Advanced") b.push("🥇 Advanced Level");
    return b;
  };

  const progressPercent = Math.min((xp / xpToNextLevel) * 100 || 0, 100);

  if (!user) {
    return (
      <div className="container">
        <h2>🏀 Welcome to the Basketball Training App!</h2>
        <p>Please log in to access your dashboard.</p>
      </div>
    );
  }

  return (
    <div className="container">
      <h2>🏀 Welcome Back, {user.displayName}!</h2>

      
      <div className="card xp-container">
        <h3>🎯 Level {level}</h3>
        <div className="xp-bar">
          <div className="xp-fill" style={{ width: `${progressPercent}%` }}></div>
          <span className="xp-text">{xp}/{xpToNextLevel} XP</span>
        </div>
      </div>

   
      <div className="card">
        <h3>🔥 Daily Streak</h3>
        <p>{streak} days in a row</p>
      </div>

      {/* Badges */}
      <div className="card">
        <h3>🏆 Badges Earned</h3>
        {badges.length > 0 ? (
          <ul style={{ listStyleType: "none", paddingLeft: 0 }}>
            {badges.map((badge, i) => (
              <li key={i}>{badge}</li>
            ))}
          </ul>
        ) : (
          <p>No badges yet</p>
        )}
      </div>
      <div className="card">
  <h3>🔐 Privacy Controls</h3>
  <button
    className="danger-button"
    onClick={handleDownloadData}
    style={{ backgroundColor: "#007bff", marginBottom: "10px" }}
  >
    📥 Download My Data
  </button>
  <button
    className="danger-button"
    onClick={handleDeleteProfile}
    style={{ backgroundColor: "#dc3545" }}
  >
    ❌ Delete My Profile
  </button>
</div>
    </div>
  );
}

export default Home;
