import { useState } from "react";

export default function App() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");

  const sendMessage = async () => {
    const res = await fetch("https://omnicore-backend.onrender.com/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ message })
    });

    const data = await res.json();
    setResponse(data.response || JSON.stringify(data));
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>TEST RENDER</h1>
      <h1>OmniCore AI</h1>

      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type a message"
      />

      <button onClick={sendMessage}>Send</button>

      <p>{response}</p>
    </div>
  );
}