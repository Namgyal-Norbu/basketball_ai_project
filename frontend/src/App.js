import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./components/Home";
import DrillTest from "./components/DrillTest";
import Results from "./components/Results";
import DrillResults from "./components/DrillResults";
import SubmitDrill from "./components/SubmitDrill.js";
import DailyRoutine from "./components/DailyRoutine";
import { useUser } from "./components/UserContext"; 
import Leaderboard from "./components/Leaderboard";
import ProgressChart from "./components/ProgressChart";

import "./components/styles.css";

function App() {
  const user = useUser(); // ✅ Access logged-in user

  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/drill-test" element={<DrillTest user={user} />} />
        <Route path="/results" element={<Results />} />
        <Route path="/drill-results" element={<DrillResults />} />
        <Route path="/submit-drills" element={<SubmitDrill user={user} />} /> 
        <Route path="/routine" element={<DailyRoutine user={user} />} />     
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/progress" element={<ProgressChart />} /> 
      </Routes>
    </Router>
  );
}

export default App;
