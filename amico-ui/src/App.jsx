import React, { useState } from "react";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);

  async function handleSend() {
    if (!message.trim()) return;

    const userMessage = message;

    setMessages((prev) => [
      ...prev,
      { role: "user", text: userMessage }
    ]);

    setMessage("");

    try {
      const res = await fetch("https://omnicore-backend.onrender.com/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: userMessage })
      });

      const data = await res.json();

      const reply =
        data?.response ||
        data?.reply ||
        data?.text ||
        "No response from server.";

      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: reply }
      ]);
    } catch (error) {
      console.error("Send error:", error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Error: Could not send message."
        }
      ]);
    }
  }

  return (
    <div>
      <div>
        {messages.map((msg, i) => (
          <div key={i}>
            <b>{msg.role}:</b> {msg.text}
          </div>
        ))}
      </div>

      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />

      <button onClick={handleSend}>Send</button>
    </div>
  );
}

export default App;