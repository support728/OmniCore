import { useState, useRef } from "react";

export default function useMic() {
  const [listening, setListening] = useState(false);
  const [text, setText] = useState("");

  const recognitionRef = useRef(null);

  const initRecognition = () => {
    if (recognitionRef.current) return;

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech Recognition not supported in this browser");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      let transcript = "";

      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }

      setText(transcript);
    };

    recognition.onstart = () => {
      console.log("🎤 STARTED");
      setListening(true);
    };

    recognition.onend = () => {
      console.log("🛑 STOPPED");
      setListening(false);
    };

    recognition.onerror = (e) => {
      console.error("Mic error:", e);
    };

    recognitionRef.current = recognition;
  };

  const start = () => {
    initRecognition();
    recognitionRef.current?.start();
  };

  const stop = () => {
    recognitionRef.current?.stop();
  };

  return { listening, text, setText, start, stop };
}