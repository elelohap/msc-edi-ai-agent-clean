(() => {
  /* ============================
     Config (override in HTML)
     ============================ */
  const API_URL =
    window.EDI_CHAT_API_URL ||
    "https://msc-edi-ai-agent.onrender.com/ask";

  const CHAT_TITLE =
    window.EDI_CHAT_TITLE ||
    "MSc EDI Programme Assistant";

  const SUGGESTIONS =
    window.EDI_CHAT_SUGGESTIONS || [
      "What are the admission requirements?",
      "What courses are taught in the MSc EDI programme?",
      "Do I need a visa to study at NUS?",
      "What is the GPA requirement to graduate?",
      "I am an engineer. Am I suitable for EDI?",
    ];

  /* ============================
     Styles
     ============================ */
  const style = document.createElement("style");
  style.textContent = `
  #edi-chat-root{
    position:fixed;right:18px;bottom:18px;z-index:99999;
    font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial
  }
  #edi-chat-btn{
    width:56px;height:56px;border-radius:28px;border:0;cursor:pointer;
    box-shadow:0 10px 25px rgba(0,0,0,.18);
    font-size:22px;background:#111;color:#fff
  }

  /* Panel becomes a flex column so everything stacks under the title */
  #edi-chat-panel{
    position:fixed;right:18px;bottom:86px;
    width:360px;max-width:calc(100vw - 36px);
    height:520px;max-height:70vh;
    background:#fff;border-radius:14px;
    box-shadow:0 18px 45px rgba(0,0,0,.25);
    display:none;overflow:hidden;

    display:flex;
    flex-direction:column;
  }

  /* Header */
  #edi-chat-header{
    flex:0 0 auto;
    padding:12px;border-bottom:1px solid #eee;
    display:flex;align-items:center;justify-content:space-between
  }
  #edi-chat-title{font-weight:600;font-size:14px}
  #edi-chat-close{border:0;background:transparent;font-size:20px;cursor:pointer;line-height:1}

  /* Suggestions are stacked right under title, and can scroll if many */
  #edi-chat-suggestions{
    flex:0 0 auto;
    padding:8px 12px;
    display:flex;flex-wrap:wrap;gap:6px;
    border-bottom:1px solid #f2f2f2;

    max-height:120px;
    overflow:auto;
  }
  .edi-chip{
    border:1px solid #ddd;border-radius:999px;
    padding:6px 10px;font-size:11px;
    cursor:pointer;background:#fafafa
  }
  .edi-chip:hover{background:#f0f0f0}

  /* Body fills the remaining space */
  #edi-chat-body{
    flex:1 1 auto;
    padding:12px;
    overflow-y:auto;
    background:#fff;
  }

  .edi-msg{margin:0 0 10px 0;display:flex}
  .edi-msg.user{justify-content:flex-end}
  .edi-bubble{
    max-width:85%;
    padding:10px 12px;border-radius:12px;
    font-size:13px;line-height:1.35;
    white-space:pre-wrap
  }
  .edi-msg.user .edi-bubble{background:#111;color:#fff;border-top-right-radius:4px}
  .edi-msg.bot .edi-bubble{background:#f4f4f5;color:#111;border-top-left-radius:4px}

  .edi-tools{margin-top:4px;text-align:right;font-size:11px}
  .edi-tools button{border:0;background:none;cursor:pointer;color:#666}

  /* Hint + meta sit above the footer and do not steal body height */
  #edi-chat-hint{
    flex:0 0 auto;
    padding:0 12px 6px;color:#666;font-size:11px
  }
  #edi-chat-meta{
    flex:0 0 auto;
    padding:0 12px 10px;color:#888;font-size:10px
  }

  /* Footer pinned at bottom */
  #edi-chat-footer{
    flex:0 0 auto;
    padding:10px;border-top:1px solid #eee;
    display:flex;gap:8px;background:#fff
  }
  #edi-chat-input{
    flex:1;border:1px solid #ddd;border-radius:10px;
    padding:10px;font-size:13px
  }
  #edi-chat-send{
    border:0;border-radius:10px;padding:10px 12px;cursor:pointer;
    background:#111;color:#fff
  }
  #edi-chat-send[disabled]{opacity:.5;cursor:not-allowed}
  `;
  document.head.appendChild(style);

  /* ============================
     DOM
     ============================ */
  const root = document.createElement("div");
  root.id = "edi-chat-root";
  root.innerHTML = `
    <button id="edi-chat-btn" aria-label="Open chat">💬</button>
    <div id="edi-chat-panel" role="dialog" aria-label="${CHAT_TITLE}">
      <div id="edi-chat-header">
        <div id="edi-chat-title">${CHAT_TITLE}</div>
        <button id="edi-chat-close" aria-label="Close">×</button>
      </div>
      <div id="edi-chat-suggestions"></div>
      <div id="edi-chat-body"></div>
      <div id="edi-chat-hint">
        Answers are based on official MSc EDI programme documents.
      </div>
      <div id="edi-chat-meta"></div>
      <div id="edi-chat-footer">
        <input id="edi-chat-input" placeholder="Type your question…" />
        <button id="edi-chat-send">Send</button>
      </div>
    </div>
  `;
  document.body.appendChild(root);

  const btn = root.querySelector("#edi-chat-btn");
  const panel = root.querySelector("#edi-chat-panel");
  const closeBtn = root.querySelector("#edi-chat-close");
  const body = root.querySelector("#edi-chat-body");
  const input = root.querySelector("#edi-chat-input");
  const send = root.querySelector("#edi-chat-send");
  const meta = root.querySelector("#edi-chat-meta");
  const sugBox = root.querySelector("#edi-chat-suggestions");

  /* ============================
     Helpers
     ============================ */
  const addMsg = (role, text, withTools = false) => {
    const row = document.createElement("div");
    row.className = `edi-msg ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "edi-bubble";
    bubble.textContent = text;
    row.appendChild(bubble);

    if (withTools) {
      const tools = document.createElement("div");
      tools.className = "edi-tools";
      const copyBtn = document.createElement("button");
      copyBtn.textContent = "Copy";
      copyBtn.onclick = () => navigator.clipboard.writeText(text);
      tools.appendChild(copyBtn);
      row.appendChild(tools);
    }

    body.appendChild(row);
    body.scrollTop = body.scrollHeight;
    return row;
  };

  const setOpen = (open) => {
    panel.style.display = open ? "flex" : "none";
    if (open) input.focus();
  };

  /* ============================
     Suggestions
     ============================ */
  const renderSuggestions = () => {
    sugBox.innerHTML = "";
    SUGGESTIONS.forEach((q) => {
      const chip = document.createElement("button");
      chip.className = "edi-chip";
      chip.type = "button";
      chip.textContent = q;
      chip.onclick = () => {
        input.value = q;
        onSend();
      };
      sugBox.appendChild(chip);
    });
  };

  /* ============================
     Ask logic
     ============================ */
  const ask = async (question) => {
    send.disabled = true;
    addMsg("user", question);

    const typing = addMsg("bot", "Typing…");
    meta.textContent = `Calling: ${API_URL}`;

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      const data = await res.json().catch(() => ({}));
      if (typing.parentNode) body.removeChild(typing);

      if (!res.ok) {
        addMsg("bot", data?.error || `HTTP ${res.status}`);
      } else {
        addMsg("bot", data?.answer || "No answer returned.", true);
      }
    } catch (e) {
      if (typing.parentNode) body.removeChild(typing);
      addMsg("bot", "Network error. Please try again.");
      console.error(e);
    } finally {
      send.disabled = false;
    }
  };

  const onSend = () => {
    const q = input.value.trim();
    if (!q) return;
    input.value = "";
    ask(q);
  };

  /* ============================
     Events
     ============================ */
  btn.onclick = () => setOpen(panel.style.display !== "flex");
  closeBtn.onclick = () => setOpen(false);
  send.onclick = onSend;
  input.onkeydown = (e) => {
    if (e.key === "Enter") onSend();
    if (e.key === "Escape") setOpen(false);
  };

  renderSuggestions();
  addMsg("bot", "Hi! Ask me about admissions, courses, or graduation requirements for MSc EDI.");
})();
