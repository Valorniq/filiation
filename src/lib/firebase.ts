import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

// Configuration prioritized for portability (Vite env vars > Provisioned Defaults)
// Note: Hardcoded defaults are the ones provisioned for this AI Studio project.
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyATSQRy7y8SnAG7Czdoj5ptMyonr6SsHNI",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "gen-lang-client-0020339804.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "gen-lang-client-0020339804",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "gen-lang-client-0020339804.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "811182296123",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:811182296123:web:02c725558608b28599a01e",
  firestoreDatabaseId: import.meta.env.VITE_FIREBASE_DATABASE_ID || "(default)"
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app, firebaseConfig.firestoreDatabaseId);
export const auth = getAuth(app);
