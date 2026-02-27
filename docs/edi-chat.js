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
      "I have a design background. Am I suitable for EDI?",
      "I have a degree in Business and Management. Am I suitable for EDI?",
    ];

  const ACCENT =
    window.EDI_CHAT_ACCENT || "#0b5fff";

   /* ============================
   Session ID (anonymous)
   ============================ */
   const SESSION_KEY = "edi_chat_session_id";

   let SESSION_ID = localStorage.getItem(SESSION_KEY);

   if (!SESSION_ID) {
     SESSION_ID = crypto.randomUUID();
     localStorage.setItem(SESSION_KEY, SESSION_ID);
   }



  /* ============================
     Styles
     ============================ */
  document.documentElement.style.setProperty("--edi-accent", ACCENT);

  const style = document.createElement("style");
  style.textContent = `
  :root{
    --edi-accent:#0b5fff;   /* change this to any color you want */
    --edi-accent-ink:#ffffff;
    --edi-soft:#eef4ff;
  }

  #edi-chat-root{
    position:fixed;right:18px;bottom:10px;z-index:99999;
    font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial
  }
  #edi-chat-btn{
    width:56px;height:56px;border-radius:28px;border:0;cursor:pointer;
    box-shadow:0 10px 25px rgba(0,0,0,.18);
    font-size:22px;
    background:var(--edi-accent);
    color:var(--edi-accent-ink);
  }

  
  /* Panel becomes a flex column so everything stacks under the title */
  #edi-chat-panel{
    position:fixed;
    left:12px;
    right:12px;
    bottom:72px;

    width:auto;                 /* override old fixed width */
    max-width:none;

    height:82vh;                /* or 520px if you prefer */
    max-height:88vh;

    background:#fff;border-radius:14px;
    box-shadow:0 18px 45px rgba(0,0,0,.25);
    display:none;overflow:hidden;

    display:flex;
    flex-direction:column;
}


  /* Header */
  #edi-chat-header{
    flex:0 0 auto;background:#fff;
    padding:12px;border-bottom:2px solid var(--edi-accent);
    display:flex;align-items:center;justify-content:space-between; background:var(--edi-soft);
  }
  #edi-chat-title{font-weight:700;font-size:18px;color:#111;letter-spacing:0.2px;text-transform:none;}
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
  

  .edi-followups{
    display:flex;
    flex-wrap:wrap;
    gap:6px;
    margin:8px 0 14px 0;
    justify-content:flex-start;
  }
  .edi-followup-chip{
    border:1px solid rgba(0,0,0,.12);
    border-radius:999px;
    padding:6px 10px;
    font-size:11px;
    cursor:pointer;
    background:#fff;
  }
  .edi-followup-chip:hover{
    background:var(--edi-soft);
    border-color:rgba(0,0,0,.18);
  }


  .edi-chip{
    border:1px solid rgba(0,0,0,.12);
    border-radius:999px;
    padding:6px 10px;
    font-size:11px;
    cursor:pointer;
    background:#fff;
  }
  .edi-chip:hover{
    background:var(--edi-soft);
    border-color:rgba(0,0,0,.18);
  }

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
  .edi-msg.user .edi-bubble{background:var(--edi-accent);color:var(--edi-accent-ink);
     border-top-right-radius:4px}
  .edi-msg.bot .edi-bubble{background:#f4f4f5;color:#111;border-top-left-radius:4px}

  .edi-tools{margin-top:4px;text-align:right;font-size:11px}
  .edi-tools button{border:0;background:none;cursor:pointer;color:#666}

  /* Hint + meta sit above the footer and do not steal body height */
  #edi-chat-hint{
    flex:0 0 auto;
    padding:0 12px 4px;color:#666;font-size:10px;
  }
  #edi-chat-meta{display:none;}
    

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

  @media (max-width: 520px){
    #edi-chat-panel{
      left:8px; right:8px;
      bottom:68px;
     height:88vh;
      max-height:92vh;
    }
  }

  #edi-chat-send{
    border:0;border-radius:10px;padding:10px 12px;cursor:pointer;
    background:var(--edi-accent);color:var(--edi-accent-ink);
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

    const renderFollowups = (followups, anchorRow) => {
    if (!followups || !Array.isArray(followups) || followups.length === 0) return;

    const wrap = document.createElement("div");
    wrap.className = "edi-followups";

    followups.slice(0, 6).forEach((q) => {  // cap at 6 to avoid clutter
      const chip = document.createElement("button");
      chip.className = "edi-followup-chip";
      chip.type = "button";
      chip.textContent = q;

      chip.onclick = () => {
        input.value = q;
        onSend();
        wrap.remove(); // remove after click (keeps UI clean)
      };

      wrap.appendChild(chip);
    });

    // Insert right after the bot message row that just got added
    if (anchorRow && anchorRow.parentNode) {
      anchorRow.parentNode.insertBefore(wrap, anchorRow.nextSibling);
    } else {
      body.appendChild(wrap);
    }

    body.scrollTop = body.scrollHeight;
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
        body: JSON.stringify({
           question,
           session_id:SESSION_ID}),
      });

      // ✅ Handle 429 first, no matter what the body looks like
      if (res.status === 429) {
          if (typing.parentNode) body.removeChild(typing);
          addMsg("bot", "You’re sending questions too quickly. Please wait ~1 minute and try again.");
          return;
      }


      const data = await res.json().catch(() => ({}));
      if (typing.parentNode) body.removeChild(typing);

      if (!res.ok) {
         if (res.status === 429) {
            addMsg("bot", "You’re sending questions too quickly. Please wait ~1 minute and try again.");
         } else {
           addMsg("bot", data?.error || `Request failed (HTTP ${res.status}).`);
         }
         return;
      }

// ✅ SUCCESS: show the answer
const answer = data?.answer || data?.response || data?.result;
if (!answer) {
  addMsg("bot", "Server returned 200 OK but no answer field was found.");
  return;
}
const botRow = addMsg("bot", answer, true);
renderFollowups(data?.followups, botRow);

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
  addMsg("bot", "Hi! You can ask me about admissions, courses, or graduation requirements for MSc EDI.");
})();
