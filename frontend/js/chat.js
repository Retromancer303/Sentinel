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
let clearChatBtn;    // The clear chat button
let exportChatBtn;   // The export chat button

/**
 * init() — runs once after DOM is ready.
 * Caches DOM elements and binds event listeners.
 */
function init() {
    messagesEl = document.getElementById("messages");
    formEl = document.getElementById("chat-form");
    inputEl = document.getElementById("message-input");
    typingIndicator = document.getElementById("typing-indicator");
    clearChatBtn = document.getElementById("clear-chat-btn");
    exportChatBtn = document.getElementById("export-chat-btn");

    // Listen for form submission (covers both button click and Enter key)
    formEl.addEventListener("submit", handleSubmit);
    clearChatBtn.addEventListener("click", clearChat);
    exportChatBtn.addEventListener("click", exportChat);

    // Escape key: clear input if it has text, otherwise clear chat
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            if (inputEl.value.trim()) {
                inputEl.value = "";
            } else {
                clearChat();
            }
        }
    });

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
 * addMessage — creates a message bubble with a timestamp and appends it to the chat.
 *
 * @param {string} text - The message text
 * @param {"user"|"bot"} sender - Who sent it (determines styling)
 */
// SVG icons for copy button states
const CLIPBOARD_ICON = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`;
const CHECK_ICON = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`;

function addMessage(text, sender) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message-wrapper", `message-wrapper-${sender}`);

    const bubble = document.createElement("div");
    bubble.classList.add("message", `message-${sender}`);
    bubble.textContent = text; // textContent is safer than innerHTML (prevents XSS)

    const timestamp = document.createElement("div");
    timestamp.classList.add("message-timestamp");
    timestamp.textContent = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
    });

    wrapper.appendChild(bubble);
    wrapper.appendChild(timestamp);

    // Add copy button for bot messages
    if (sender === "bot") {
        const copyBtn = document.createElement("button");
        copyBtn.classList.add("copy-button");
        copyBtn.title = "Copy message";
        copyBtn.innerHTML = CLIPBOARD_ICON;

        copyBtn.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(text);
                copyBtn.classList.add("copied");
                copyBtn.innerHTML = CHECK_ICON;
                setTimeout(() => {
                    copyBtn.classList.remove("copied");
                    copyBtn.innerHTML = CLIPBOARD_ICON;
                }, 1500);
            } catch {
                // Clipboard API may fail in non-secure contexts
            }
        });

        wrapper.appendChild(copyBtn);
    }

    messagesEl.appendChild(wrapper);
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

/**
 * clearChat — removes all messages and resets the session.
 * The backend will get a fresh session ID on the next message.
 */
function clearChat() {
    messagesEl.innerHTML = "";
    sessionStorage.removeItem("sentinel-session-id");
    inputEl.focus();
}

/**
 * exportChat — downloads the conversation as a .txt file.
 * Iterates over message wrappers, collects sender labels and text,
 * then triggers a browser download via a temporary anchor element.
 */
function exportChat() {
    const wrappers = messagesEl.querySelectorAll(".message-wrapper");
    if (wrappers.length === 0) return;

    const lines = [];
    wrappers.forEach((wrapper) => {
        const bubble = wrapper.querySelector(".message");
        const timestamp = wrapper.querySelector(".message-timestamp");
        const sender = wrapper.classList.contains("message-wrapper-user") ? "You" : "Sentinel";
        const time = timestamp ? timestamp.textContent : "";
        lines.push(`[${time}] ${sender}: ${bubble.textContent}`);
    });

    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sentinel-chat-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}

// ============================================================
// 5. Bootstrap
// ============================================================
// DOMContentLoaded fires when the HTML is fully parsed.
// This ensures all elements exist before we try to reference them.

document.addEventListener("DOMContentLoaded", init);
