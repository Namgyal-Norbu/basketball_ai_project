import React, { useEffect, useState } from "react";
import "./styles.css";

function Leaderboard() {
  const [leaders, setLeaders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://127.0.0.1:5000/leaderboard")
      .then((res) => res.json())
      .then((data) => {
        setLeaders(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching leaderboard:", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="leaderboard-container">
      <h2 className="leaderboard-header">🏆 Leaderboard</h2>

      {loading ? (
        <p>Loading...</p>
      ) : leaders.length > 0 ? (
        <table className="leaderboard-table">
          <thead>
            <tr>
              <th>Player</th>
              <th>Average Score</th>
              <th>Days Active</th>
            </tr>
          </thead>
          <tbody>
            {leaders.map((player, idx) => (
              <tr key={idx}>
                <td>{player.name}</td>
                <td>{Number(player.average_score).toFixed(2)}</td>
                <td>{player.days_active}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No data available yet.</p>
      )}
    </div>
  );
}

export default Leaderboard;
