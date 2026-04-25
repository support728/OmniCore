import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyC4uScEu7HwsLxL_HmqXOIB19p8npVCxmY",
  authDomain: "amico-app-7648e.firebaseapp.com",
  projectId: "amico-app-7648e",
  storageBucket: "amico-app-7648e.firebasestorage.app",
  messagingSenderId: "423216365848",
  appId: "1:423216365848:web:2d01d6466d2cc3ed13de6d",
  measurementId: "G-QVNSEK2PY7"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);