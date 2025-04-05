import { initializeApp } from "firebase/app";
import { getFirestore, doc, getDoc, setDoc, collection, query, where, getDocs } from "firebase/firestore";
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from "firebase/auth";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAuWr_xVANGzz5utLwC7mhZAb18EzZDPR4",
  authDomain: "basketball-c918a.firebaseapp.com",
  projectId: "basketball-c918a",
  storageBucket: "basketball-c918a.firebasestorage.app",
  messagingSenderId: "625147903198",
  appId: "1:625147903198:web:001857ce5cbe6e4647d64f",
  measurementId: "G-G4HMYV8QEG"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

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