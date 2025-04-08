import { initializeApp } from "firebase/app";
import { 
  getFirestore, 
  doc, getDoc, setDoc, 
  collection, query, where, getDocs 
} from "firebase/firestore";
import { 
  getAuth, 
  GoogleAuthProvider, 
  signInWithPopup, 
  signOut 
} from "firebase/auth";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAuWr_xVANGzz5utLwC7mhZAb18EzZDPR4",
  authDomain: "basketball-c918a.firebaseapp.com",
  projectId: "basketball-c918a",
  storageBucket: "basketball-c918a.appspot.com", // ✅ typo fix: was "firebasestorage.app"
  messagingSenderId: "625147903198",
  appId: "1:625147903198:web:001857ce5cbe6e4647d64f",
  measurementId: "G-G4HMYV8QEG"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// 🔐 Services
const auth = getAuth(app);
const db = getFirestore(app);
const provider = new GoogleAuthProvider();

export const login = async () => {
  try {
    const result = await signInWithPopup(auth, provider);
    const user = result.user;
    console.log("✅ Signed in:", user.displayName, user.email);
    return user;
  } catch (error) {
    console.error("❌ Login failed:", error.message);
    return null;
  }
};

export {
  db,
  auth,
  provider,
  signInWithPopup,
  signOut,
  doc,
  getDoc,
  setDoc,
  collection,
  query,       
  where,       
  getDocs      
};
