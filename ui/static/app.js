/**
 * Altostrat HR & IT Autonomous Agentic UI — Frontend Application
 */

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Lucide icons
  lucide.createIcons();

  // State
  const userId = "EMP-436"; // Hardcoded Swapna (Engineering Lead)
  let currentSessionId = null;
  let isGenerating = false;
  let allPolicies = [];

  // DOM Elements
  const messagesStream = document.getElementById("messagesStream");
  const welcomeHero = document.getElementById("welcomeHero");
  const messageInput = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const sendIcon = document.getElementById("sendIcon");
  const clearChatBtn = document.getElementById("clearChatBtn");
  const headerNewSessionBtn = document.getElementById("headerNewSessionBtn");
  const sidebarNewSessionBtn = document.getElementById("sidebarNewSessionBtn");
  const sessionLabel = document.getElementById("sessionLabel");
  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");

  // Policy Explorer & Drawer Elements
  const policyTree = document.getElementById("policyTree");
  const policySearchInput = document.getElementById("policySearchInput");
  const policyDrawer = document.getElementById("policyDrawer");
  const policyDrawerBackdrop = document.getElementById("policyDrawerBackdrop");
  const closeDrawerBtn = document.getElementById("closeDrawerBtn");
  const drawerPolicyTitle = document.getElementById("drawerPolicyTitle");
  const drawerPolicyPath = document.getElementById("drawerPolicyPath");
  const drawerPolicyContent = document.getElementById("drawerPolicyContent");
  const telemLatency = document.getElementById("telemLatency");

  // --------------------------------------------------------------------------
  // 1. Session Lifecycle Management
  // --------------------------------------------------------------------------
  function createNewSession() {
    currentSessionId = null;
    messagesStream.innerHTML = "";
    if (welcomeHero) {
      welcomeHero.style.display = "flex";
      messagesStream.appendChild(welcomeHero);
    }
    sessionLabel.innerHTML = `Session: <span class="id-mono">New (Auto)</span>`;
    telemLatency.textContent = "-";
    messageInput.value = "";
    adjustTextareaHeight();
    messageInput.focus();
    lucide.createIcons();
  }

  headerNewSessionBtn.addEventListener("click", createNewSession);
  sidebarNewSessionBtn.addEventListener("click", createNewSession);
  clearChatBtn.addEventListener("click", createNewSession);

  // --------------------------------------------------------------------------
  // 2. Policy Explorer & Slide-Over Drawer
  // --------------------------------------------------------------------------
  async function loadPolicies() {
    try {
      const res = await fetch("/api/policies");
      const data = await res.json();
      allPolicies = data.sections || [];
      renderPolicyTree(allPolicies);
    } catch (err) {
      policyTree.innerHTML = `<div class="loading-state">Failed to load policy index.</div>`;
    }
  }

  function renderPolicyTree(sections) {
    policyTree.innerHTML = "";
    if (!sections || sections.length === 0) {
      policyTree.innerHTML = `<div class="loading-state">No policy documents found.</div>`;
      return;
    }

    sections.forEach(sec => {
      const secGroup = document.createElement("div");
      secGroup.className = "policy-sec-group";

      const title = document.createElement("div");
      title.className = "policy-sec-title";
      title.textContent = sec.title;
      secGroup.appendChild(title);

      sec.items.forEach(item => {
        const link = document.createElement("div");
        link.className = "policy-item-link";
        link.innerHTML = `<i data-lucide="file-text" style="width:13px;height:13px;flex-shrink:0;"></i> <span>${item.title}</span>`;
        link.addEventListener("click", () => openPolicyDrawer(item.path, item.title));
        secGroup.appendChild(link);
      });

      policyTree.appendChild(secGroup);
    });
    lucide.createIcons();
  }

  policySearchInput.addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase().trim();
    if (!q) {
      renderPolicyTree(allPolicies);
      return;
    }
    const filtered = allPolicies.map(sec => {
      const matchingItems = sec.items.filter(it => 
        it.title.toLowerCase().includes(q) || it.path.toLowerCase().includes(q)
      );
      if (matchingItems.length > 0) {
        return { ...sec, items: matchingItems };
      }
      return null;
    }).filter(Boolean);
    renderPolicyTree(filtered);
  });

  async function openPolicyDrawer(policyPath, titleFallback = "Policy Document") {
    drawerPolicyTitle.textContent = "Loading...";
    drawerPolicyPath.textContent = policyPath;
    drawerPolicyContent.innerHTML = `<div class="loading-state"><i data-lucide="loader-2" class="spin-icon"></i> Fetching OKF document...</div>`;
    lucide.createIcons();

    policyDrawerBackdrop.classList.add("active");
    policyDrawer.classList.add("active");

    try {
      const res = await fetch(`/api/policies/read?path=${encodeURIComponent(policyPath)}`);
      if (!res.ok) throw new Error("Policy not found");
      const data = await res.json();

      drawerPolicyTitle.textContent = data.title || titleFallback;
      drawerPolicyPath.textContent = data.path;
      
      const cleanHtml = DOMPurify.sanitize(marked.parse(data.body));
      drawerPolicyContent.innerHTML = cleanHtml;
    } catch (err) {
      drawerPolicyTitle.textContent = "Document Error";
      drawerPolicyContent.innerHTML = `<div class="error-box">Unable to open policy document: ${err.message}</div>`;
    }
  }

  function closePolicyDrawer() {
    policyDrawerBackdrop.classList.remove("active");
    policyDrawer.classList.remove("active");
  }

  closeDrawerBtn.addEventListener("click", closePolicyDrawer);
  policyDrawerBackdrop.addEventListener("click", closePolicyDrawer);

  // --------------------------------------------------------------------------
  // 3. Conversational Messaging & Robust SSE Streaming Client
  // --------------------------------------------------------------------------
  async function sendMessage(text) {
    if (!text || !text.trim() || isGenerating) return;

    if (welcomeHero && welcomeHero.parentNode) {
      welcomeHero.style.display = "none";
    }

    const userText = text.trim();
    messageInput.value = "";
    adjustTextareaHeight();

    // 1. Render User Message Row
    appendUserMessage(userText);
    scrollStreamToBottom();

    // 2. Prepare Agent Message Row
    const { agentRow, bubble, toolsContainer, contentContainer } = createAgentMessagePlaceholder();
    messagesStream.appendChild(agentRow);
    scrollStreamToBottom();

    isGenerating = true;
    updateSendButtonState();

    const startTime = performance.now();
    let accumulatedMarkdown = "";
    let accumulatedToolOutputs = [];

    try {
      const payload = {
        message: userText,
        user_id: userId,
      };
      if (currentSessionId) {
        payload.session_id = currentSessionId;
      }

      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.replace("data: ", "").trim();
            if (!dataStr) continue;

            try {
              const event = JSON.parse(dataStr);
              handleStreamEvent(event, {
                toolsContainer,
                contentContainer,
                appendMarkdown: (chunk) => {
                  accumulatedMarkdown += chunk;
                  renderMarkdown(contentContainer, accumulatedMarkdown);
                  scrollStreamToBottom();
                },
                recordToolOutput: (textOut) => {
                  if (textOut) accumulatedToolOutputs.push(textOut);
                }
              });
            } catch (jsonErr) {
              console.error("JSON parse error on SSE event:", jsonErr);
            }
          }
        }
      }

      // If no text chunk was streamed but tools returned output, display the tool output directly
      if (!accumulatedMarkdown.trim() && accumulatedToolOutputs.length > 0) {
        const fallbackText = accumulatedToolOutputs.join("\n\n");
        renderMarkdown(contentContainer, fallbackText);
      } else if (!accumulatedMarkdown.trim()) {
        contentContainer.innerHTML = `<span style="color:var(--text-muted);">Request completed.</span>`;
      }

      const durationSec = ((performance.now() - startTime) / 1000).toFixed(2);
      telemLatency.textContent = `${durationSec}s`;

    } catch (err) {
      contentContainer.innerHTML += `<div style="color:var(--accent-error);margin-top:8px;">[Connection Error: ${err.message}]</div>`;
      scrollStreamToBottom();
    } finally {
      markAllToolsCompleted(toolsContainer);
      isGenerating = false;
      updateSendButtonState();
      attachCitationListeners(contentContainer);
      scrollStreamToBottom();
    }
  }

  function handleStreamEvent(event, { toolsContainer, contentContainer, appendMarkdown, recordToolOutput }) {
    if (event.type === "tool_call") {
      markAllToolsCompleted(toolsContainer);

      const pill = document.createElement("div");
      pill.className = "tool-invocation-pill active";
      const pillId = event.id ? `tool_${event.id}` : `tool_${event.tool}_${Date.now()}`;
      pill.id = pillId;
      pill.setAttribute("data-tool-name", event.tool);
      pill.innerHTML = `
        <i data-lucide="wrench" class="inline-icon" style="color:var(--accent-primary);"></i>
        <span>Calling <span class="tool-name-tag">${event.tool}</span></span>
        <span class="tool-badge-status status-running"><i data-lucide="loader-2" class="spin-icon" style="width:12px;height:12px;"></i> Running...</span>
      `;
      toolsContainer.appendChild(pill);
      lucide.createIcons();
      scrollStreamToBottom();
    } 
    else if (event.type === "tool_result") {
      let targetPill = null;
      if (event.id) {
        targetPill = toolsContainer.querySelector(`#tool_${event.id}`);
      }
      if (!targetPill && event.tool) {
        targetPill = toolsContainer.querySelector(`.tool-invocation-pill.active[data-tool-name="${event.tool}"]`);
      }
      if (!targetPill) {
        targetPill = toolsContainer.querySelector(`.tool-invocation-pill.active`);
      }
      if (targetPill) {
        markPillCompleted(targetPill);
      } else {
        markAllToolsCompleted(toolsContainer);
      }

      // Extract result text if available
      let resultText = "";
      if (event.result) {
        if (typeof event.result === "string") {
          resultText = event.result;
        } else if (event.result.content && Array.isArray(event.result.content)) {
          resultText = event.result.content.map(c => c.text || "").filter(Boolean).join("\n");
        } else if (event.result.result) {
          resultText = typeof event.result.result === "string" ? event.result.result : JSON.stringify(event.result.result, null, 2);
        }
      }
      if (resultText && recordToolOutput) {
        recordToolOutput(resultText);
      }

      lucide.createIcons();
      scrollStreamToBottom();
    }
    else if (event.type === "security_violation") {
      markAllToolsCompleted(toolsContainer);
      contentContainer.innerHTML = `
        <div style="background-color:var(--accent-error-subtle);border:1px solid var(--accent-error);border-radius:var(--radius-md);padding:12px 16px;color:var(--accent-error);font-size:0.88rem;line-height:1.5;">
          <strong>🛡️ Model Armor Security Sentinel Blocked Request:</strong><br>
          ${escapeHtml(event.message)}
        </div>
      `;
      scrollStreamToBottom();
    }
    else if (event.type === "security_notice") {
      const notice = document.createElement("div");
      notice.style.cssText = "background-color:var(--accent-warning-subtle);border:1px solid rgba(245,158,11,0.3);border-radius:var(--radius-sm);padding:6px 10px;font-size:0.75rem;color:var(--accent-warning);margin-bottom:8px;";
      notice.innerHTML = `<i data-lucide="shield-alert" style="width:13px;height:13px;display:inline-block;vertical-align:middle;margin-right:4px;"></i> ${escapeHtml(event.message)}`;
      toolsContainer.appendChild(notice);
      lucide.createIcons();
      scrollStreamToBottom();
    }
    else if (event.type === "text_chunk") {
      markAllToolsCompleted(toolsContainer);
      appendMarkdown(event.text);
    }
    else if (event.type === "done") {
      markAllToolsCompleted(toolsContainer);
      if (event.duration_ms) {
        telemLatency.textContent = `${(event.duration_ms / 1000).toFixed(2)}s`;
      }
      if (event.session_id) {
        currentSessionId = event.session_id;
        const shortId = event.session_id.split("/").pop();
        sessionLabel.innerHTML = `Session: <span class="id-mono">${shortId}</span>`;
      }
    }
    else if (event.type === "error") {
      markAllToolsCompleted(toolsContainer);
      contentContainer.innerHTML = `<div style="color:var(--accent-error);">⚠️ ${event.message}</div>`;
      scrollStreamToBottom();
    }
  }

  function markPillCompleted(pill) {
    if (!pill) return;
    pill.classList.remove("active");
    pill.classList.add("completed");
    const badge = pill.querySelector(".tool-badge-status");
    if (badge) {
      badge.className = "tool-badge-status status-complete";
      badge.innerHTML = `<i data-lucide="check-circle-2" style="width:12px;height:12px;"></i> Executed`;
    }
  }

  function markAllToolsCompleted(toolsContainer) {
    if (!toolsContainer) return;
    const activePills = toolsContainer.querySelectorAll(".tool-invocation-pill.active, .tool-invocation-pill:not(.completed)");
    activePills.forEach(pill => markPillCompleted(pill));
    lucide.createIcons();
  }

  function appendUserMessage(text) {
    const row = document.createElement("div");
    row.className = "message-row user-row";
    row.innerHTML = `
      <div class="avatar-circle avatar-user">S</div>
      <div class="message-bubble">${escapeHtml(text)}</div>
    `;
    messagesStream.appendChild(row);
  }

  function createAgentMessagePlaceholder() {
    const row = document.createElement("div");
    row.className = "message-row agent-row";

    const avatar = document.createElement("div");
    avatar.className = "avatar-circle avatar-agent";
    avatar.innerHTML = `<i data-lucide="bot" style="width:18px;height:18px;"></i>`;

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    const toolsContainer = document.createElement("div");
    toolsContainer.className = "tool-invocations-group";

    const contentContainer = document.createElement("div");
    contentContainer.className = "agent-markdown-body";
    contentContainer.innerHTML = `<span style="color:var(--text-muted);"><i data-lucide="loader-2" class="spin-icon" style="width:14px;height:14px;display:inline-block;vertical-align:middle;"></i> Formulating grounded response...</span>`;

    bubble.appendChild(toolsContainer);
    bubble.appendChild(contentContainer);
    row.appendChild(avatar);
    row.appendChild(bubble);

    lucide.createIcons();
    return { agentRow: row, bubble, toolsContainer, contentContainer };
  }

  function renderMarkdown(container, rawMarkdown) {
    const parsed = marked.parse(rawMarkdown);
    container.innerHTML = DOMPurify.sanitize(parsed);
  }

  function attachCitationListeners(container) {
    const links = container.querySelectorAll("a");
    links.forEach(a => {
      const href = a.getAttribute("href");
      if (href && (href.startsWith("/") || href.includes(".md"))) {
        a.addEventListener("click", (e) => {
          e.preventDefault();
          openPolicyDrawer(href, a.textContent);
        });
      }
    });
  }

  function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function scrollStreamToBottom() {
    messagesStream.scrollTop = messagesStream.scrollHeight;
  }

  function updateSendButtonState() {
    sendBtn.disabled = isGenerating;
    if (isGenerating) {
      sendIcon.setAttribute("data-lucide", "loader-2");
      sendIcon.classList.add("spin-icon");
    } else {
      sendIcon.setAttribute("data-lucide", "arrow-up");
      sendIcon.classList.remove("spin-icon");
    }
    lucide.createIcons();
  }

  // --------------------------------------------------------------------------
  // 4. Scenario Buttons & Event Handlers
  // --------------------------------------------------------------------------
  document.querySelectorAll(".scenario-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const prompt = btn.getAttribute("data-prompt");
      if (prompt) {
        sendMessage(prompt);
      }
    });
  });

  sendBtn.addEventListener("click", () => {
    sendMessage(messageInput.value);
  });

  messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(messageInput.value);
    }
  });

  messageInput.addEventListener("input", adjustTextareaHeight);

  function adjustTextareaHeight() {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 130) + "px";
  }

  // --------------------------------------------------------------------------
  // 5. Theme Toggle (Light / Dark)
  // --------------------------------------------------------------------------
  const savedTheme = localStorage.getItem("altostrat_theme");
  if (savedTheme === "dark") {
    document.body.classList.add("dark-mode");
    themeIcon.setAttribute("data-lucide", "sun");
  }

  themeToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
    const isDark = document.body.classList.contains("dark-mode");
    localStorage.setItem("altostrat_theme", isDark ? "dark" : "light");
    themeIcon.setAttribute("data-lucide", isDark ? "sun" : "moon");
    lucide.createIcons();
  });

  // Initial Load
  loadPolicies();
});
