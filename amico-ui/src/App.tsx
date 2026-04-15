import { useState } from "react";
import { sendMessage } from "./services/api";

type Message = {
  role: string;
  content: string;
};

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "Amico", content: "Amico is ready." },
  ]);
  const [input, setInput] = useState("");

  const handleSend = async () => {
    const userMessage = input.trim();
    if (!userMessage) return;

    setMessages((prev) => [
      ...prev,
      { role: "You", content: userMessage },
    ]);

    setInput("");

    const reply = await sendMessage(userMessage);

    setMessages((prev) => [
      ...prev,
      { role: "Amico", content: reply || "No response" },
    ]);
  };

  return (
    <div style={styles.app}>
      <div style={styles.header}>Amico AI 🎤</div>

      <div style={styles.chat}>
        {messages.map((msg, index) => (
          <div key={index} style={styles.message}>
            <strong>{msg.role}:</strong> {msg.content}
          </div>
        ))}
      </div>

      <div style={styles.inputBar}>
        <input
          style={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
          placeholder="Type your command..."
        />
        <button style={styles.button} onClick={handleSend}>
          Send
        </button>
      </div>
    </div>
  );
}

const styles = {
  app: {
    height: "100vh",
    display: "flex",
    flexDirection: "column" as const,
    fontFamily: "Arial, sans-serif",
    background: "#fff",
  },
  header: {
    padding: "16px",
    fontSize: "24px",
    fontWeight: "bold",
    borderBottom: "1px solid #ddd",
  },
  chat: {
    flex: 1,
    overflowY: "auto" as const,
    padding: "16px",
  },
  message: {
    marginBottom: "14px",
    fontSize: "16px",
    lineHeight: 1.4,
  },
  inputBar: {
    display: "flex",
    gap: "10px",
    padding: "12px 16px",
    borderTop: "1px solid #ddd",
    background: "#fff",
  },
  input: {
    flex: 1,
    padding: "10px",
    fontSize: "16px",
  },
  button: {
    padding: "10px 18px",
    fontSize: "16px",
    cursor: "pointer",
  },
};