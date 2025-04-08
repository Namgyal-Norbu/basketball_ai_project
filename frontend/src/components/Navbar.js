

import React from "react";
import { useUser } from "./UserContext";
import { signInWithPopup, GoogleAuthProvider, signOut } from "firebase/auth";
import { auth } from "../firebaseConfig";
import "./styles.css";

const provider = new GoogleAuthProvider();

function Navbar() {
  const user = useUser();

  const handleLogin = async () => {
    try {
      await signInWithPopup(auth, provider);
    } catch (err) {
      console.error("Login failed:", err);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  return (
    <nav className="navbar">
      <div className="logo">🏀 Basketball AI Routine Creator</div>
      <div className="nav-links">
      <a href="/">Home</a>
        <a href="/drill-test">Daily Drills</a>
        <a href="/submit-drills">Submit Drills</a>
        <a href="/leaderboard">Leaderboard</a>
        <a href="/progress">Progress</a>
        <a href ="/how-to-use">How to Use</a>
        
      </div>

      <div className="auth-section">
        {user ? (
          <>
            <img
              src={user.photoURL}
              alt="Profile"
              className="profile-pic"
              title={user.displayName}
              onClick={handleLogout}
            />
          </>
        ) : (
          <button onClick={handleLogin} className="login-btn">Login</button>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
