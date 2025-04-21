import React, { useState } from "react";
import { useUser } from "./UserContext";
import { signInWithPopup, GoogleAuthProvider, signOut } from "firebase/auth";
import { db, doc, getDoc, setDoc, auth } from "../firebaseConfig";
import "./styles.css";

const provider = new GoogleAuthProvider();

function Navbar() {
  const user = useUser();
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (loading) return;
    setLoading(true);

    try {
      const result = await signInWithPopup(auth, provider);
      const firebaseUser = result.user;

      const playerRef = doc(db, "players", firebaseUser.email);
      const playerSnap = await getDoc(playerRef);

      if (!playerSnap.exists()) {
        await setDoc(playerRef, {
          name: firebaseUser.displayName,
          email: firebaseUser.email,
          uid: firebaseUser.uid,
          xp: 0,
          skill_level: "Beginner",
          show_on_leaderboard: true,
          test_completed: false,
          last_login: new Date().toISOString()
        });
        console.log("✅ Created new player profile");
      } else {
       
        await setDoc(playerRef, {
          last_login: new Date().toISOString()
        }, { merge: true });

        console.log("👋 Welcome back!", playerSnap.data());
      }

    } catch (err) {
      console.error("Login failed:", err);
    } finally {
      setLoading(false);
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
    <a href="/" className="logo">🏀 Basketball Routine Creator</a>
  
    <div className="nav-links">
      <a href="/">Home</a>
      <a href="/drill-test">Daily Drills</a>
      <a href="/submit-drills">Take Assesment Drills</a>
      <a href="/leaderboard">Leaderboard</a>
      <a href="/progress">Progress</a>
      <a href="/how-to-use">How to Use</a>
    </div>
  
    <div className="auth-section">
      {user ? (
        <img
          src={user.photoURL}
          alt="Profile"
          className="profile-pic"
          title="Click to log out"
          onClick={handleLogout}
        />
      ) : (
        <button
          onClick={handleLogin}
          className="login-btn"
          disabled={loading}
        >
          {loading ? "Logging in..." : "Login"}
        </button>
      )}
    </div>
  </nav>
  
  );
}

export default Navbar;
