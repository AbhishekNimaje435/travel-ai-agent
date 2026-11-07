// ---------- Chat with AI (Groq, no tools, uses /api/chat) ----------
const chatButton = document.getElementById("chat-button");
const chatPanel = document.getElementById("chat-panel");
const chatCloseButton = document.getElementById("chat-close");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatSendButton = document.getElementById("chat-send");
const chatMessages = document.getElementById("chat-messages");

// Only user and assistant messages go here, so the API always gets a valid history
const chatHistory = [];
const CHAT_HISTORY_SENT_LIMIT = 10;

function openChat() {
  chatPanel.hidden = false;
  chatInput.focus();
  if (chatMessages.children.length === 0) {
    addChatBubble("assistant", "Hi! Ask me about destinations, things to do, or packing tips.");
  }
}

function closeChat() {
  chatPanel.hidden = true;
}

function addChatBubble(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble chat-bubble-${role}`;
  bubble.textContent = text; // textContent keeps the reply safe from HTML injection
  chatMessages.appendChild(bubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return bubble;
}

async function sendChatMessage(text) {
  chatHistory.push({ role: "user", content: text });
  addChatBubble("user", text);

  const typingBubble = addChatBubble("assistant", "Typing...");
  typingBubble.classList.add("chat-typing");
  chatSendButton.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: chatHistory.slice(-CHAT_HISTORY_SENT_LIMIT),
        model_name: "openai/gpt-oss-20b",
      }),
    });
    const data = await response.json();

    typingBubble.remove();

    if (!response.ok) {
      // Remove the unanswered user message so the history stays valid for the next try
      chatHistory.pop();
      addChatBubble("assistant", data.detail || "Sorry, I could not reply right now.");
      return;
    }

    chatHistory.push({ role: "assistant", content: data.reply });
    addChatBubble("assistant", data.reply);
  } catch (networkError) {
    typingBubble.remove();
    chatHistory.pop();
    addChatBubble("assistant", "Could not connect to the server. Please try again.");
  } finally {
    chatSendButton.disabled = false;
    chatInput.focus();
  }
}

chatButton.addEventListener("click", openChat);
chatCloseButton.addEventListener("click", closeChat);

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = "";
  sendChatMessage(text);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !chatPanel.hidden) {
    closeChat();
  }
});