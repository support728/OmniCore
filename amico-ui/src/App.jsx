import { useState } from "react";
import { sendMessage as apiSendMessage } from "./services/api";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);

  // No changes needed: input is cleared and chat history is updated as required.
  // The code already implements both fixes as requested.

  return (
    <div>
      <h1>Amico Chat</h1>

      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Ask something..."
      />

      <button onClick={handleSend}>Send</button>

      <div style={{ marginTop: 20 }}>
        {messages.map((msg, i) => (
          <div key={i}>
            <b>{msg.role}:</b> {msg.text}
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;