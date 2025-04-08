import React, { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";

import { collection, query, where, getDocs } from "firebase/firestore";

import { db } from "../firebaseConfig";
import { useUser } from "./UserContext";


import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend
);

function ProgressChart() {
  const user = useUser();
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      if (!user) return;
      const ref = collection(db, "dailyResults");
      const q = query(ref, where("email", "==", user.email));
      const snapshot = await getDocs(q);

      const dates = [];
      const avgScores = [];

      snapshot.forEach(doc => {
        const data = doc.data();
        dates.push(data.day);
        const scores = Object.values(data.results).map(Number);
        const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
        avgScores.push(avg);
      });

      setChartData({
        labels: dates,
        datasets: [
          {
            label: "Average Drill Score",
            data: avgScores,
            borderColor: "blue",
            backgroundColor: "rgba(0, 123, 255, 0.2)",
            fill: true,
            tension: 0.3,
          },
        ],
      });
    };

    fetchResults();
  }, [user]);

  return (
    <div className="container">
      <h2>📈 Your Progress</h2>
      {chartData ? (
        <Line data={chartData} />
      ) : (
        <p>Loading progress...</p>
      )}
    </div>
  );
}

export default ProgressChart;
