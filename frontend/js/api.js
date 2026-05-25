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
 *
 * TODO: Replace the stub below with a real fetch() call.
 * Example:
 *   const response = await fetch('/api/chat', {
 *       method: 'POST',
 *       headers: { 'Content-Type': 'application/json' },
 *       body: JSON.stringify({ message }),
 *   });
 *   const data = await response.json();
 *   return data.reply;
 */
async function sendToServer(message) {
    // --- STUB: simulates a network delay + placeholder response ---
    // Delete this block when wiring up the real backend.
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve(`I received your message: "${message}". Backend integration pending.`);
        }, 1200);
    });
}
