(() => {
  // Config: you can override in index.html by setting window.EDI_CHAT_API_URL
  const API_URL = window.EDI_CHAT_API_URL || "https://msc-edi-ai-agent.onrender.com/ask";

  // ---- UI (minimal chat bubble) ----
  const style = document.createElement("style");
  style.textContent = `
    #edi-chat-root{position:fixed;right:18px;bottom:18px;z-index:99999;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial}
    #edi-chat-btn{width:56px;height:56px;border-radius:28px;border:0;cursor:pointer;box-shadow:0 10px 25px rgba(0,0,0,.18);font-size:22px;background:#111;color:#fff}
    #edi-chat-panel{position:fixed;right:18px;bottom:86px;width:360px;max-width:calc(100vw - 36px);height:520px;max-height:70vh;background:#fff;border-radius:14px;box-shadow:0 18px 45px rgba(0,0,0,.25);display:none;overflow:hidden}
    #edi-chat-header{padding:12px;border-bottom:1px solid #eee;display:flex;align-items:center;justify-content:space-between}
    #edi-chat-title{font-weight:600;font-size:14px}
    #edi-chat-close{border:0;background:transparent;font-size:20px;cursor:pointer;line-height:1}
    #edi-chat-body{padding:12px;height:calc(100% - 112px);overflow:auto}
    .edi-msg{margin:0 0 10px 0;display:flex}
    .edi-msg.user{justify-content:flex-end}
    .edi-bubble{max-width:85%;padding:10px 12px;border-radius:12px;font-size:13px;line-height:1.35;white-space:pre-wrap}
    .edi-msg.user .edi-bubble{background:#111;color:#fff;border-top-right-radius:4px}
    .edi-msg.bot .edi-bubble{background:#f4f4f5;color:#111;border-top-left-radius:4px}
    #edi-chat-footer{padding:10px;border-top:1px solid #eee;display:flex;gap:8px}
    #edi-chat-input{flex:1;border:1px solid #ddd;border-radius:10px;padding:10px;font-size:13px}
    #edi-chat-send{border:0;border-radius:10px;padding:10px 12px;cursor:pointer;background:#111;color:#fff}
    #edi-chat-hint{padding:0 12px 10px;color:#666;font-size:11px}
    #edi-chat-meta{padding:0 12px 10px;color:#888;font-size:10px}
  `;
  document.head.appendChild(style);

  const root = document.createElement("div");
  root.id = "edi-chat-root";
  root.innerHTML = `
    <button id="edi-chat-btn" aria-label="Open chat">💬</button>
    <div id="edi-chat-panel" role="dialog" aria-label="MSc EDI Chatbot">
      <div id="edi-chat-header">
        <div id="edi-chat-title">MSc EDI Admissions Assistant</div>
        <button id="edi-chat-close" aria-label="Close chat">×</button>
      </div>
      <div id="edi-chat-body"></div>
      <div id="edi-chat-hint">Answers are based on available programme documents.</div>
      <div id="edi-chat-meta"></div>
      <div id="edi-chat-footer">
        <input id="edi-chat-input" type="text" placeholder="Type your question…" />
        <button id="edi-chat-send">Send</button>
      </div>
    </div>
  `;
  document.body.appendChild(root);

  const btn = document.getElementById("edi-chat-btn");
  const panel = document.getElementById("edi-chat-panel");
  const closeBtn = document.getElementById("edi-chat-close");
  const body = document.getElementById("edi-chat-body");
  const meta = document.getElementById("edi-chat-meta");
  const input = document.getElementById("edi-chat-input");
  const send = document.getElementById("edi-chat-send");

  const addMsg = (role, text) => {
    const row = document.createElement("div");
    row.className = `edi-msg ${role}`;
    const bubble = document.createElement("div");
    bubble.className = "edi-bubble";
    bubble.textContent = text;
    row.appendChild(bubble);
    body.appendChild(row);
    body.scrollTop = body.scrollHeight;
  };

  const setOpen = (open) => {
    panel.style.display = open ? "block" : "none";
    if (open) input.focus();
  };

  const setMeta = (text) => { meta.textContent = text || ""; };

  btn.addEventListener("click", () => setOpen(panel.style.display !== "block"));
  closeBtn.addEventListener("click", () => setOpen(false));

  const ask = async (question) => {
    addMsg("user", question);
    addMsg("bot", "Thinking…");
    setMeta(`Calling: ${API_URL}`);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      const data = await res.json().catch(() => ({}));

      // remove placeholder
      body.removeChild(body.lastChild);

      if (!res.ok) {
        addMsg("bot", data?.error ? `Error: ${data.error}` : `Error: HTTP ${res.status}`);
        return;
      }

      addMsg("bot", data?.answer ?? "No answer returned.");
    } catch (e) {
      body.removeChild(body.lastChild);
      addMsg("bot", "Network/CORS error. See console for details.");
      console.error(e);
    }
  };

  const onSend = () => {
    const q = (input.value || "").trim();
    if (!q) return;
    input.value = "";
    ask(q);
  };

  send.addEventListener("click", onSend);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") onSend();
    if (e.key === "Escape") setOpen(false);
  });

  addMsg("bot", "Hi! Ask me about admissions, modules, or graduation requirements for MSc EDI.");
})();
