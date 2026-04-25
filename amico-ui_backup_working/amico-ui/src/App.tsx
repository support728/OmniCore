import { useState } from "react";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

function App() {
  const [message, setMessage] = useState<string>("");
  const [chat, setChat] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "You can call me Amico. How can I assist you today?",
    },
  ]);

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = message;

    setChat((prev) => [
      ...prev,
      { role: "user", content: userMessage },
    ]);

    setMessage("");

    try {
      const response = await fetch("http://127.0.0.1:8011/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userMessage,
        }),
      });

      const data = await response.json();

      setChat((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response ?? "No response from server.",
        },
      ]);
    } catch (error) {
      setChat((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Error connecting to server.",
        },
      ]);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>Amico AI</h1>

      <div>
        {chat.map((msg, index) => (
          <p key={index}>
            <strong>{msg.role}:</strong> {msg.content}
          </p>
        ))}
      </div>

      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your message..."
      />

      <button onClick={sendMessage}>Send</button>
    </div>
  );
}

export default App;