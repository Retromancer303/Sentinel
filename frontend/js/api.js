/**
 * api.js — Backend communication layer
 *
 * Purpose: Isolate all server communication into this single file.
 * When you connect to a real backend, only THIS file changes.
 * The rest of the app (chat.js) calls sendToServer() and doesn't
 * care how the request is made.
 *
 * Why separate this?
 * - Easy to swap fetch -> WebSocket -> SDK later
 * - Easy to mock for testing
 * - Keeps chat.js focused purely on UI
 */

/**
 * Send a message to the backend and return the bot's response.
 *
 * @param {string} message - The user's message text
 * @returns {Promise<string>} - The bot's reply text
 */
async function sendToServer(message) {
    const sessionId = sessionStorage.getItem("sentinel-session-id") || `session-${Date.now()}`;
    sessionStorage.setItem("sentinel-session-id", sessionId);

    const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message, session_id: sessionId })
    });

    if (!response.ok) {
        throw new Error(`Chat request failed with status ${response.status}`);
    }

    const data = await response.json();
    return data.reply || "";
}
