import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./components/Home";
import DrillTest from "./components/DailyDrills.js";
import SubmitDrill from "./components/DrillTest.js";
import { useUser } from "./components/UserContext"; 
import Leaderboard from "./components/Leaderboard";
import ProgressChart from "./components/ProgressChart";
import HowToUse from "./components/HowToUse";
import ChatBotWidget from "./components/ChatBotWidget";
import backgroundImage from './components/Photos/Background.jpg';

import "./components/styles.css";

function App() {
  const user = useUser(); 

  return (
    <div
      style={{
        backgroundImage: `url(${backgroundImage})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundAttachment: "fixed",
        minHeight: "100vh",
      }}
    >
      <Router>
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/drill-test" element={<DrillTest user={user} />} />
          <Route path="/submit-drills" element={<SubmitDrill user={user} />} /> 
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/progress" element={<ProgressChart />} /> 
          <Route path="/how-to-use" element={<HowToUse />} />
        </Routes>
        <ChatBotWidget />
      </Router>
    </div>
  );
}

export default App;
