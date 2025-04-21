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

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend);

function ProgressChart() {
  const user = useUser();
  const [charts, setCharts] = useState({});
  const [drillToSkill, setDrillToSkill] = useState({});
  const [selectedSkill, setSelectedSkill] = useState("general");

  //fetch skill drill bank from backend and map drills to skill categories 
  useEffect(() => {
    const fetchSkillDrillBank = async () => {
      try {
        const res = await fetch("http://127.0.0.1:5050/skill_drill_bank");
        const data = await res.json();
        const mapping = {};

        for (const skill in data) {
          for (const level in data[skill]) {
            data[skill][level].forEach((drill) => {
              mapping[drill] = skill;
            });
          }
        }

        setDrillToSkill(mapping);
      } catch (err) {
        console.error("Failed to load skill drill bank:", err);
      }
    };

    fetchSkillDrillBank();
  }, []);

// fetch drill results for player then group by skill and date 
  useEffect(() => {
    const fetchResults = async () => {
      if (!user || Object.keys(drillToSkill).length === 0) return;

      const ref = collection(db, "dailyResults");
      const q = query(ref, where("email", "==", user.email));
      const snapshot = await getDocs(q);

      const skillData = {};
      const generalData = {};

      snapshot.forEach(doc => {
        const data = doc.data();
        const timestamp = data.timestamp;
        if (!timestamp || !data.results) return;

        const dateObj = new Date(timestamp);
        const formattedDate = dateObj.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric"
        });

        let total = 0;
        let count = 0;

        for (const [drill, score] of Object.entries(data.results)) {
          const skill = drillToSkill[drill] || "unknown";
          if (!skillData[skill]) skillData[skill] = {};
          if (!skillData[skill][formattedDate]) skillData[skill][formattedDate] = [];

          const numericScore = Number(score);
          skillData[skill][formattedDate].push(numericScore);

      
          total += numericScore;
          count += 1;
        }

        if (count > 0) {
          if (!generalData[formattedDate]) generalData[formattedDate] = [];
          generalData[formattedDate].push(total / count);
        }
      });

      const chartsData = {};
    
  // got help from AI on this part  
      const generalDates = Object.keys(generalData).sort((a, b) => new Date(a) - new Date(b));
      const generalAverages = generalDates.map(date => {
        const values = generalData[date];
        return values.reduce((a, b) => a + b, 0) / values.length;
      });

      chartsData["general"] = {
        labels: generalDates,
        datasets: [
          {
            label: "General Average Score",
            data: generalAverages,
            borderColor: "black",
            backgroundColor: "rgba(0,0,0,0.1)",
            fill: true,
            tension: 0.3,
          },
        ],
      };

      for (const [skill, dateMap] of Object.entries(skillData)) {
        const dates = Object.keys(dateMap).sort((a, b) => new Date(a) - new Date(b));
        const averages = dates.map(date => {
          const scores = dateMap[date];
          return scores.reduce((a, b) => a + b, 0) / scores.length;
        });

        chartsData[skill] = {
          labels: dates,
          datasets: [
            {
              label: `${skill[0].toUpperCase() + skill.slice(1)} Score`,
              data: averages,
              borderColor: "blue",
              backgroundColor: "rgba(0, 123, 255, 0.2)",
              fill: true,
              tension: 0.3,
            },
          ],
        };
      }

      setCharts(chartsData);
    };

    fetchResults();
  }, [user, drillToSkill]);

  const skillOptions = Object.keys(charts);

  return (
    <div className="chart-wrapper">
      <h2 className = "title">📊 Your Progress</h2>

      {skillOptions.length > 0 ? (
        <>
          <label htmlFor="skillSelect">View By:</label>
          <select
            id="skillSelect"
            value={selectedSkill}
            onChange={(e) => setSelectedSkill(e.target.value)}
            style={{ marginBottom: "20px", padding: "8px" }}
          >
            {skillOptions.map((skill) => (
              <option key={skill} value={skill}>
                {skill === "general"
                  ? "📊 General Progress"
                  : `📈 ${skill[0].toUpperCase() + skill.slice(1)} Progress`}
              </option>
            ))}
          </select>

          <Line data={charts[selectedSkill]} />
        </>
      ) : (
        <p>Loading progress...</p>
      )}
    </div>
  );
}

export default ProgressChart;
