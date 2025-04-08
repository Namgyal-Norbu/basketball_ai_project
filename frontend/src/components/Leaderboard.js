import React, { useEffect, useState } from "react";
import "./styles.css";

function Leaderboard() {
  const [leaders, setLeaders] = useState([]);
  const [topToday, setTopToday] = useState(null);
  const [topWeek, setTopWeek] = useState(null);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("xp"); // default: sort by XP

  useEffect(() => {
    fetch("http://127.0.0.1:5000/leaderboard")
      .then((res) => res.json())
      .then((data) => {
        setLeaders(data.players || []);
        setTopToday(data.top_performer_today || null);
        setTopWeek(data.top_performer_week || null);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching leaderboard:", err);
        setLoading(false);
      });
  }, []);

  const sortedLeaders = [...leaders].sort((a, b) => {
    switch (category) {
      case "xp":
        return b.xp - a.xp;
      case "level":
        return b.level - a.level;
      case "average":
        return b.average_score - a.average_score;
      case "days":
        return b.days_active - a.days_active;
      default:
        return b.xp - a.xp;
    }
  });

  return (
    <div className="leaderboard-container">
      <h2 className="leaderboard-header">🏆 Leaderboard</h2>
  
      <div className="filter-bar">
        <label htmlFor="category">Sort: </label>
        <select
          id="category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="xp">Total XP</option>
          <option value="level">Level</option>
          <option value="average">Average Score</option>
          <option value="days">Days Active</option>
        </select>
      </div>
  
      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          {sortedLeaders.length > 0 ? (
            <table className="leaderboard-table">
              <thead>
                <tr>
                  <th>Player</th>
                  {category === "level" && <th>Level</th>}
                  {category === "xp" && <th>Total XP</th>}
                  {category === "average" && <th>Avg Score</th>}
                  {category === "days" && <th>Days Active</th>}
                </tr>
              </thead>
              <tbody>
                {sortedLeaders.map((player, idx) => (
                  <tr key={idx}>
                    <td>{player.name}</td>
                    {category === "level" && <td>{player.level}</td>}
                    {category === "xp" && <td>{player.xp}</td>}
                    {category === "average" && <td>{player.average_score.toFixed(1)}</td>}
                    {category === "days" && <td>{player.days_active}</td>}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No data available yet.</p>
          )}
  
          {/* Top Performers */}
          <div className="top-performers" style={{ marginTop: "30px" }}>
            {topToday && (
              <div className="card">
                <h3>🔥 Top Performer Today</h3>
                <p>
                  <strong>{topToday.name}</strong> with <strong>{topToday.xp}</strong> XP
                </p>
              </div>
            )}
            {topWeek && (
              <div className="card">
                <h3>📈 Top Performer This Week</h3>
                <p>
                  <strong>{topWeek.name}</strong> with <strong>{topWeek.xp}</strong> XP
                </p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
export default Leaderboard;
