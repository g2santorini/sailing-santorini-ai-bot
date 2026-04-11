(function () {
  const API_URL = "/chat";

  const style = document.createElement("style");
  style.innerHTML = `
    #ss-widget-bubble {
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 58px;
      height: 58px;
      border-radius: 50%;
      background: linear-gradient(135deg, #0b3b66, #145c94);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 22px;
      cursor: pointer;
      box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
      z-index: 999999;
    }

    #ss-widget-container {
      position: fixed;
      bottom: 90px;
      right: 20px;
      width: 360px;
      height: 560px;
      background: #f4f6f8;
      border-radius: 18px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.22);
      display: none;
      flex-direction: column;
      overflow: hidden;
      z-index: 999999;
      font-family: Arial, sans-serif;
    }

    #ss-header {
      background: #ffffff;
      border-bottom: 1px solid #e6e6e6;
      padding: 10px 14px;
      flex-shrink: 0;
    }

    #ss-header-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    #ss-logo {
      width: 42px;
      height: 42px;
      object-fit: contain;
    }

    #ss-close {
      border: none;
      background: transparent;
      font-size: 22px;
      cursor: pointer;
      color: #4b5563;
    }

    #ss-body {
      flex: 1;
      min-height: 0;
      padding: 16px;
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
      background: #eef2f5;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    #ss-welcome {
      background: white;
      border-radius: 16px;
      padding: 16px;
      color: #1f2937;
      font-size: 15px;
      line-height: 1.5;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
      max-width: 85%;
    }

    .ss-message {
      max-width: 85%;
      padding: 12px 14px;
      border-radius: 16px;
      font-size: 15px;
      line-height: 1.45;
      word-break: break-word;
    }

    .ss-message-user {
      background: #0b3b66;
      color: white;
      align-self: flex-end;
      white-space: pre-wrap;
    }

    .ss-message-assistant {
      background: white;
      color: #1f2937;
      align-self: flex-start;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }

    .ss-message-typing {
      background: white;
      color: #6b7280;
      align-self: flex-start;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
      font-style: italic;
    }

    .ss-message-assistant p,
    #ss-welcome p,
    .ss-message-typing p {
      margin: 0 0 10px 0;
    }

    .ss-message-assistant p:last-child,
    #ss-welcome p:last-child,
    .ss-message-typing p:last-child {
      margin-bottom: 0;
    }

    .ss-message-assistant a,
    #ss-welcome a {
      color: #0b3b66;
      text-decoration: underline;
      word-break: break-all;
    }

    #ss-footer {
      background: #ffffff;
      border-top: 1px solid #e6e6e6;
      padding: 12px 14px calc(12px + env(safe-area-inset-bottom));
      flex-shrink: 0;
    }

    #ss-input-row {
      display: flex;
      gap: 10px;
      align-items: center;
    }

    #ss-input {
      flex: 1;
      height: 44px;
      border: 1px solid #d1d5db;
      border-radius: 14px;
      padding: 0 14px;
      font-size: 15px;
      outline: none;
      min-width: 0;
    }

    #ss-send {
      height: 44px;
      border: none;
      border-radius: 14px;
      padding: 0 16px;
      background: #0b3b66;
      color: white;
      cursor: pointer;
      flex-shrink: 0;
    }

    #ss-send:disabled,
    #ss-input:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }

    #ss-bottom {
      margin-top: 8px;
      font-size: 11px;
      color: #6b7280;
      text-align: center;
    }

    @media (max-width: 640px) {
      #ss-widget-container {
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        width: 100%;
        height: 100dvh;
        border-radius: 0;
      }

      #ss-widget-bubble {
        bottom: 16px;
        right: 16px;
      }
    }
  `;
  document.head.appendChild(style);

  const bubble = document.createElement("div");
  bubble.id = "ss-widget-bubble";
  bubble.innerHTML = "💬";

  const container = document.createElement("div");
  container.id = "ss-widget-container";

  container.innerHTML = `
    <div id="ss-header">
      <div id="ss-header-top">
        <img id="ss-logo" src="/static/logo.png" alt="Sunset Oia logo" />
        <button id="ss-close" aria-label="Close">×</button>
      </div>
    </div>

    <div id="ss-body">
      <div id="ss-welcome">
        <p>Greetings from the beautiful Santorini!</p>
        <p>I’m here to help you with your cruise experience at Sunset Oia.</p>
        <p>Feel free to ask about availability, private options, or the differences between our tours.</p>
      </div>
    </div>

    <div id="ss-footer">
      <div id="ss-input-row">
        <input id="ss-input" placeholder="Write your message..." />
        <button id="ss-send">Send</button>
      </div>
      <div id="ss-bottom">
        Sunset Oia Online assistant • Instant reply
      </div>
    </div>
  `;

  document.body.appendChild(bubble);
  document.body.appendChild(container);

  const closeBtn = container.querySelector("#ss-close");
  const body = container.querySelector("#ss-body");
  const input = container.querySelector("#ss-input");
  const sendBtn = container.querySelector("#ss-send");

  let chatHistory = [];

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function formatMessageHtml(text) {
    const escaped = escapeHtml(text);

    const withLinks = escaped.replace(
      /(https?:\/\/[^\s<]+)/g,
      '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
    );

    const paragraphs = withLinks
      .split(/\n\s*\n/)
      .map(part => part.trim())
      .filter(Boolean)
      .map(part => `<p>${part.replace(/\n/g, "<br>")}</p>`)
      .join("");

    return paragraphs || `<p>${withLinks}</p>`;
  }

  function scrollToBottom() {
    body.scrollTop = body.scrollHeight;
  }

  function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.className = `ss-message ss-message-${sender}`;

    if (sender === "assistant") {
      msg.innerHTML = formatMessageHtml(text);
    } else {
      msg.textContent = text;
    }

    body.appendChild(msg);
    scrollToBottom();
  }

  function addTypingMessage() {
    const typing = document.createElement("div");
    typing.id = "ss-typing";
    typing.className = "ss-message ss-message-typing";
    typing.innerHTML = "<p>Typing...</p>";
    body.appendChild(typing);
    scrollToBottom();
  }

  function removeTypingMessage() {
    const typing = container.querySelector("#ss-typing");
    if (typing) {
      typing.remove();
    }
  }

  function adjustMobileViewport() {
    if (window.innerWidth > 640) {
      container.style.height = "560px";
      return;
    }

    if (window.visualViewport) {
      const vh = window.visualViewport.height;
      container.style.height = `${vh}px`;
    } else {
      container.style.height = `${window.innerHeight}px`;
    }

    scrollToBottom();
  }

  async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, "user");
    chatHistory.push({ role: "user", content: message });

    input.value = "";
    input.disabled = true;
    sendBtn.disabled = true;

    addTypingMessage();

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          history: chatHistory
        })
      });

      const data = await res.json();
      const replyText = data.reply || "Sorry, something went wrong.";

      removeTypingMessage();
      addMessage(replyText, "assistant");
      chatHistory.push({ role: "assistant", content: replyText });
    } catch (error) {
      removeTypingMessage();
      addMessage("Sorry, there was a connection error.", "assistant");
      console.error("Widget error:", error);
    } finally {
      input.disabled = false;
      sendBtn.disabled = false;
      adjustMobileViewport();
      input.focus();
    }
  }

  bubble.onclick = () => {
    container.style.display = "flex";
    bubble.style.display = "none";
    adjustMobileViewport();
    setTimeout(() => {
      input.focus();
      scrollToBottom();
    }, 50);
  };

  closeBtn.onclick = () => {
    container.style.display = "none";
    bubble.style.display = "flex";
  };

  sendBtn.onclick = sendMessage;

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  });

  input.addEventListener("focus", () => {
    setTimeout(() => {
      adjustMobileViewport();
      scrollToBottom();
    }, 250);
  });

  input.addEventListener("blur", () => {
    setTimeout(() => {
      adjustMobileViewport();
    }, 250);
  });

  window.addEventListener("resize", adjustMobileViewport);

  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", adjustMobileViewport);
    window.visualViewport.addEventListener("scroll", adjustMobileViewport);
  }
})();