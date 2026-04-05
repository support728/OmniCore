const API_URL = "http://127.0.0.1:8000/api/chat/dashboard-update";

const chatContainer = document.getElementById("chat-container");
const inputBox = document.getElementById("chat-input");
const sendButton = document.getElementById("send-button");

function addMessage(text, role) {
    const msg = document.createElement("div");
    msg.className = role;
    msg.innerText = text;
    chatContainer.appendChild(msg);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function sendMessage() {
    const text = inputBox.value.trim();
    if (!text) return;

    addMessage(text, "user");
    inputBox.value = "";

    try {
        const res = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ user_input: text })
        });

        const data = await res.json();
        addMessage(data.answer || "No response", "assistant");

    } catch (err) {
        addMessage("Connection error", "assistant");
    }
}

sendButton.onclick = sendMessage;

inputBox.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
});