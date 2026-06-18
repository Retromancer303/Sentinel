/**
 * chat.js — Chat UI logic
 *
 * Responsibilities:
 * - Rendering messages to the DOM
 * - Handling user input (form submit, Enter key)
 * - Managing input state (enabled/disabled during bot typing)
 * - Auto-scrolling to the latest message
 * - Calling api.js sendToServer() for bot responses
 *
 * Architecture:
 * - All DOM references are cached once in init() for performance
 * - UI helpers (render, scroll, toggle) are separate from business logic
 * - sendMessage() orchestrates the full send/receive cycle
 */

// ============================================================
// 1. DOM references — cached once on page load
// ============================================================
// Caching avoids repeated getElementById calls, which is a
// common frontend performance practice.

let messagesEl;      // The container where message bubbles are appended
let formEl;          // The <form> element
let inputEl;         // The text input field
let typingIndicator; // The "bot is typing" animated dots

/**
 * init() — runs once after DOM is ready.
 * Caches DOM elements and binds event listeners.
 */
function init() {
    messagesEl = document.getElementById("messages");
    formEl = document.getElementById("chat-form");
    inputEl = document.getElementById("message-input");
    typingIndicator = document.getElementById("typing-indicator");

    // Listen for form submission (covers both button click and Enter key)
    formEl.addEventListener("submit", handleSubmit);

    // Focus the input on page load so the user can start typing immediately
    inputEl.focus();
}

// ============================================================
// 2. Event handlers
// ============================================================

/**
 * handleSubmit — called when the user submits the form.
 * Prevents the default page reload, validates input, and sends.
 */
function handleSubmit(event) {
    event.preventDefault(); // Stop the form from reloading the page

    const text = inputEl.value.trim(); // .trim() prevents whitespace-only messages
    if (!text) return;

    sendMessage(text);
}

// ============================================================
// 3. Core chat flow
// ============================================================

/**
 * sendMessage — orchestrates the full send/receive cycle:
 * 1. Render the user's message
 * 2. Clear and disable input
 * 3. Show typing indicator
 * 4. Call the backend (via api.js)
 * 5. Render the bot's response
 * 6. Re-enable input
 *
 * @param {string} text - The user's message (already validated, non-empty)
 */
async function sendMessage(text) {
    // Step 1: Show the user's message immediately
    addMessage(text, "user");

    // Step 2: Clear input and lock the UI while bot "thinks"
    inputEl.value = "";
    setInputEnabled(false);

    // Step 3: Show typing indicator
    showTypingIndicator(true);

    try {
        // Step 4: Call the backend (api.js handles the actual request)
        const reply = await sendToServer(text);

        // Step 5: Render the bot's reply
        addMessage(reply, "bot");
    } catch (error) {
        // If the backend fails, show a user-friendly error message
        console.error("Failed to get bot response:", error);
        addMessage("Sorry, something went wrong. Please try again.", "bot");
    } finally {
        // Step 6: Always re-enable input, even if the request failed
        showTypingIndicator(false);
        setInputEnabled(true);
        inputEl.focus(); // Return focus so the user can type again
    }
}

// ============================================================
// 4. UI helper functions
// ============================================================
// These are pure DOM manipulation helpers. They don't know about
// API calls or business logic — they just update what's on screen.

/**
 * addMessage — creates a message bubble and appends it to the chat.
 *
 * @param {string} text - The message text
 * @param {"user"|"bot"} sender - Who sent it (determines styling)
 */
function addMessage(text, sender) {
    const bubble = document.createElement("div");
    bubble.classList.add("message", `message-${sender}`);
    bubble.textContent = text; // textContent is safer than innerHTML (prevents XSS)

    messagesEl.appendChild(bubble);
    scrollToBottom();
}

/**
 * scrollToBottom — scrolls the chat window to show the newest message.
 * Called after every new message so the user always sees the latest.
 */
function scrollToBottom() {
    const chatWindow = messagesEl.closest(".chat-window");
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

/**
 * setInputEnabled — toggles the input field and button on/off.
 * Disabled while waiting for the bot to respond, so the user
 * doesn't send duplicate messages.
 *
 * @param {boolean} enabled
 */
function setInputEnabled(enabled) {
    inputEl.disabled = !enabled;
    const sendButton = formEl.querySelector(".send-button");
    sendButton.disabled = !enabled;
}

/**
 * showTypingIndicator — shows or hides the animated dots.
 *
 * @param {boolean} show
 */
function showTypingIndicator(show) {
    typingIndicator.classList.toggle("hidden", !show);
    if (show) {
        scrollToBottom(); // Scroll down so the user sees the indicator
    }
}

// ============================================================
// 5. Bootstrap
// ============================================================
// DOMContentLoaded fires when the HTML is fully parsed.
// This ensures all elements exist before we try to reference them.

document.addEventListener("DOMContentLoaded", init);
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
