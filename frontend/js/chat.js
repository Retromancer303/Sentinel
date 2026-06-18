const API_URL = "http://localhost:8000/chat";

function addMessage(text, type) {
    const msg = document.createElement("div");
    msg.classList.add("message", type);
    msg.innerText = text;

    const messages = document.getElementById("messages");
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById("input");
    const text = input.value.trim();

    if (!text) return;

    addMessage(text, "user");
    input.value = "";

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: text })
        });

        if (!response.ok) {
            throw new Error("Chat request failed");
        }

        const data = await response.json();
        addMessage(data.reply, "bot");
    } catch (error) {
        addMessage("Unable to reach the Sentinel chatbot backend. Make sure the FastAPI server is running.", "bot");
    }
}

document.getElementById("input").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        sendMessage();
    }
});
