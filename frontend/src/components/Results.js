import React, { useState, useEffect } from "react";
import { db, doc, getDoc, setDoc } from "../firebaseConfig";
import "./styles.css";

function Results() {
  const [name, setName] = useState("");
  const [drills, setDrills] = useState([]);
  const [results, setResults] = useState({});

  useEffect(() => {
    const fetchDrills = async () => {
      if (!name) return;
      const docRef = doc(db, "players", name);
      const docSnap = await getDoc(docRef);
      if (docSnap.exists()) {
        setDrills(docSnap.data().drills);
      }
    };
    fetchDrills();
  }, [name]);

  const handleResultChange = (index, value) => {
    setResults((prev) => ({ ...prev, [index]: value }));
  };

  const handleSubmitResults = async () => {
    await setDoc(doc(db, "players", name), {
      drills,
      results,
    }, { merge: true });

    alert("Results Saved!");
  };

  return (
    <div className="container">
      <h2>📊 Enter Drill Results</h2>
      <input type="text" placeholder="Enter Name" value={name} onChange={(e) => setName(e.target.value)} required />
      {drills.length > 0 ? (
        <div className="results">
          <h3>Your Drills:</h3>
          <ul>
            {drills.map((drill, index) => (
              <li key={index}>
                {drill} - 
                <input type="number" placeholder="Score" onChange={(e) => handleResultChange(index, e.target.value)} />
              </li>
            ))}
          </ul>
          <button onClick={handleSubmitResults}>Submit Results</button>
        </div>
      ) : (
        <p>No drills found. Enter your name to fetch drills.</p>
      )}
    </div>
  );
}

export default Results;
