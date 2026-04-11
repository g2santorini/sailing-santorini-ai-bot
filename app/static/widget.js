(function () {
  const API_URL = "/chat";

  const AUTO_OPEN_ENABLED = true;
  const AUTO_OPEN_DELAY = 5000;
  const AUTO_OPEN_SESSION_KEY = "ss_widget_auto_opened";
  const AUTO_OPEN_CLOSED_KEY = "ss_widget_closed";

  const style = document.createElement("style");
  style.innerHTML = `
    *,
    *::before,
    *::after {
      box-sizing: border-box;
    }

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
      -webkit-tap-highlight-color: transparent;
      touch-action: manipulation;
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
      overscroll-behavior: contain;
      -webkit-overflow-scrolling: auto;
      touch-action: none;
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
      width: 100%;
      min-width: 0;
    }

    #ss-logo {
      width: 42px;
      height: 42px;
      object-fit: contain;
      -webkit-user-drag: none;
      user-select: none;
      flex-shrink: 0;
    }

    #ss-close {
      border: none;
      background: transparent;
      font-size: 22px;
      cursor: pointer;
      color: #4b5563;
      -webkit-tap-highlight-color: transparent;
      touch-action: manipulation;
      flex-shrink: 0;
      margin-left: 10px;
    }

    #ss-body {
      flex: 1;
      min-height: 0;
      padding: 16px;
      overflow-y: auto;
      overflow-x: hidden;
      -webkit-overflow-scrolling: touch;
      overscroll-behavior-y: contain;
      background: #eef2f5;
      display: flex;
      flex-direction: column;
      gap: 10px;
      touch-action: pan-y;
      width: 100%;
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
      width: fit-content;
    }

    .ss-message {
      max-width: 85%;
      padding: 12px 14px;
      border-radius: 16px;
      font-size: 15px;
      line-height: 1.45;
      word-break: break-word;
      overflow-wrap: anywhere;
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
      padding:
        12px
        calc(14px + env(safe-area-inset-right))
        calc(12px + env(safe-area-inset-bottom))
        calc(14px + env(safe-area-inset-left));
      flex-shrink: 0;
      touch-action: manipulation;
      overflow: hidden;
      width: 100%;
    }

    #ss-input-row {
      display: flex;
      gap: 10px;
      align-items: center;
      width: 100%;
      min-width: 0;
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
      width: 100%;
      touch-action: manipulation;
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
      -webkit-tap-highlight-color: transparent;
      touch-action: manipulation;
      white-space: nowrap;
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
      width: 100%;
    }

    @media (max-width: 640px) {
      html.ss-widget-open,
      body.ss-widget-open {
        overflow: hidden !important;
        height: 100% !important;
        overscroll-behavior: none !important;
        touch-action: none !important;
      }

      #ss-widget-container {
        top: 0;
        left: 0;
        right: auto;
        bottom: auto;
        width: 100vw;
        max-width: 100vw;
        height: 100dvh;
        max-height: 100dvh;
        border-radius: 0;
      }

      #ss-header {
        padding-left: calc(14px + env(safe-area-inset-left));
        padding-right: calc(14px + env(safe-area-inset-right));
      }

      #ss-body {
        padding-left: calc(16px + env(safe-area-inset-left));
        padding-right: calc(16px + env(safe-area-inset-right));
      }

      #ss-footer {
        padding-left: calc(14px + env(safe-area-inset-left));
        padding-right: calc(14px + env(safe-area-inset-right));
      }

      #ss-widget-bubble {
        bottom: 16px;
        right: 16px;
      }

      .ss-message,
      #ss-welcome {
        max-width: 88%;
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
  let autoOpenTimer = null;

  function isMobile() {
    return window.innerWidth <= 640;
  }

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

  function lockPageScroll() {
    if (isMobile()) {
      document.documentElement.classList.add("ss-widget-open");
      document.body.classList.add("ss-widget-open");
    }
  }

  function unlockPageScroll() {
    document.documentElement.classList.remove("ss-widget-open");
    document.body.classList.remove("ss-widget-open");
  }

  function adjustMobileViewport() {
    if (!isMobile()) {
      container.style.top = "";
      container.style.left = "";
      container.style.right = "20px";
      container.style.bottom = "90px";
      container.style.width = "360px";
      container.style.maxWidth = "360px";
      container.style.height = "560px";
      container.style.maxHeight = "560px";
      return;
    }

    if (window.visualViewport) {
      const vv = window.visualViewport;
      const height = Math.round(vv.height);
      const width = Math.round(vv.width);
      const offsetTop = Math.round(vv.offsetTop);
      const offsetLeft = Math.round(vv.offsetLeft);

      container.style.top = `${offsetTop}px`;
      container.style.left = `${offsetLeft}px`;
      container.style.right = "auto";
      container.style.bottom = "auto";
      container.style.width = `${width}px`;
      container.style.maxWidth = `${width}px`;
      container.style.height = `${height}px`;
      container.style.maxHeight = `${height}px`;
    } else {
      const vh = window.innerHeight;
      const vw = window.innerWidth;

      container.style.top = "0";
      container.style.left = "0";
      container.style.right = "auto";
      container.style.bottom = "auto";
      container.style.width = `${vw}px`;
      container.style.maxWidth = `${vw}px`;
      container.style.height = `${vh}px`;
      container.style.maxHeight = `${vh}px`;
    }

    scrollToBottom();
  }

  function preventPageBounce(event) {
    if (!isMobile()) return;
    if (container.style.display !== "flex") return;

    const isInsideBody = body.contains(event.target);
    const isInsideInput = input === event.target;
    const isInsideSend = sendBtn === event.target;
    const isInsideClose = closeBtn === event.target;

    if (isInsideBody || isInsideInput || isInsideSend || isInsideClose) {
      return;
    }

    event.preventDefault();
  }

  function openWidget() {
    container.style.display = "flex";
    bubble.style.display = "none";
    lockPageScroll();
    adjustMobileViewport();

    setTimeout(() => {
      scrollToBottom();
    }, 50);
  }

  function closeWidget(markClosed = true) {
    container.style.display = "none";
    bubble.style.display = "flex";
    unlockPageScroll();

    if (markClosed) {
      sessionStorage.setItem(AUTO_OPEN_CLOSED_KEY, "true");
    }
  }

  function shouldAutoOpen() {
    if (!AUTO_OPEN_ENABLED) return false;
    if (sessionStorage.getItem(AUTO_OPEN_SESSION_KEY) === "true") return false;
    if (sessionStorage.getItem(AUTO_OPEN_CLOSED_KEY) === "true") return false;
    return true;
  }

  function scheduleAutoOpen() {
    if (!shouldAutoOpen()) return;

    autoOpenTimer = setTimeout(() => {
      if (!shouldAutoOpen()) return;
      sessionStorage.setItem(AUTO_OPEN_SESSION_KEY, "true");
      openWidget();
    }, AUTO_OPEN_DELAY);
  }

  async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, "user");
    chatHistory.push({ role: "user", content: message });

    input.value = "";
    input.disabled = true;
    sendBtn.disabled = true;

    if (document.activeElement === input) {
      input.blur();
    }

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
      scrollToBottom();
    }
  }

  bubble.onclick = () => {
    if (autoOpenTimer) {
      clearTimeout(autoOpenTimer);
    }

    sessionStorage.setItem(AUTO_OPEN_SESSION_KEY, "true");
    sessionStorage.removeItem(AUTO_OPEN_CLOSED_KEY);
    openWidget();
  };

  closeBtn.onclick = () => {
    closeWidget(true);
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

  document.addEventListener("touchmove", preventPageBounce, { passive: false });

  scheduleAutoOpen();
})(); 