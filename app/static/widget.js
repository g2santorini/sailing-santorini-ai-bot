(function () {
  const API_URL = "/chat";

  const AUTO_OPEN_ENABLED = true;
  const AUTO_OPEN_DELAY = 5000;
  const AUTO_OPEN_SESSION_KEY = "ss_widget_auto_opened";
  const AUTO_OPEN_CLOSED_KEY = "ss_widget_closed";

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

    #ss-body {
      flex: 1;
      min-height: 0;
      padding: 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 10px;
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
    }

    #ss-input {
      flex: 1;
      height: 44px;
      border: 1px solid #d1d5db;
      border-radius: 14px;
      padding: 0 14px;
      font-size: 15px;
    }

    #ss-send {
      height: 44px;
      border: none;
      border-radius: 14px;
      padding: 0 16px;
      background: #0b3b66;
      color: white;
    }

    .ss-message {
      max-width: 85%;
      padding: 12px 14px;
      border-radius: 16px;
      font-size: 15px;
    }

    .ss-message-user {
      background: #0b3b66;
      color: white;
      align-self: flex-end;
    }

    .ss-message-assistant {
      background: white;
      align-self: flex-start;
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
      <strong>Sunset Oia Assistant</strong>
    </div>

    <div id="ss-body"></div>

    <div id="ss-footer">
      <div id="ss-input-row">
        <input id="ss-input" placeholder="Write your message..." />
        <button id="ss-send">Send</button>
      </div>
    </div>
  `;

  document.body.appendChild(bubble);
  document.body.appendChild(container);

  const body = container.querySelector("#ss-body");
  const input = container.querySelector("#ss-input");
  const sendBtn = container.querySelector("#ss-send");

  let chatHistory = [];

  function isMobile() {
    return window.innerWidth <= 640;
  }

  function scrollToBottom() {
    body.scrollTop = body.scrollHeight;
  }

  function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.className = `ss-message ss-message-${sender}`;
    msg.textContent = text;
    body.appendChild(msg);
    scrollToBottom();
  }

  function adjustMobileViewport() {
    if (!isMobile()) return;

    if (window.visualViewport) {
      const vv = window.visualViewport;

      container.style.top = vv.offsetTop + "px";
      container.style.height = vv.height + "px";
    } else {
      container.style.top = "0";
      container.style.height = window.innerHeight + "px";
    }

    scrollToBottom();
  }

  function openWidget() {
    container.style.display = "flex";
    bubble.style.display = "none";
    adjustMobileViewport();
  }

  function closeWidget() {
    container.style.display = "none";
    bubble.style.display = "flex";
  }

  async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, "user");
    chatHistory.push({ role: "user", content: message });

    input.value = "";

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history: chatHistory })
      });

      const data = await res.json();
      const reply = data.reply || "Error";

      addMessage(reply, "assistant");
      chatHistory.push({ role: "assistant", content: reply });

    } catch {
      addMessage("Connection error", "assistant");
    }
  }

  bubble.onclick = openWidget;
  sendBtn.onclick = sendMessage;

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });

  input.addEventListener("focus", () => {
    setTimeout(adjustMobileViewport, 300);
  });

  window.addEventListener("resize", adjustMobileViewport);

  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", adjustMobileViewport);
    window.visualViewport.addEventListener("scroll", adjustMobileViewport);
  }
})();