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