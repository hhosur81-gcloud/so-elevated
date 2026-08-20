/**
 * Altostrat HR & IT Autonomous Agentic UI — Frontend Application
 */

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Lucide icons
  lucide.createIcons();

  // State
  let currentEmployee = null;
  let employees = [];
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
  const sessionLabel = document.getElementById("sessionLabel");
  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");

  // User Dropdown Elements
  const userTrigger = document.getElementById("userTrigger");
  const userMenu = document.getElementById("userMenu");
  const userAvatar = document.getElementById("userAvatar");
  const currentUserName = document.getElementById("currentUserName");
  const currentUserId = document.getElementById("currentUserId");
  const employeeList = document.getElementById("employeeList");

  // Employee Card Elements
  const cardEmployeeName = document.getElementById("cardEmployeeName");
  const cardEmployeeRole = document.getElementById("cardEmployeeRole");
  const cardEmployeeDept = document.getElementById("cardEmployeeDept");
  const cardEmployeeLoc = document.getElementById("cardEmployeeLoc");
  const cardPtoRemaining = document.getElementById("cardPtoRemaining");
  const cardPtoAccrued = document.getElementById("cardPtoAccrued");
  const cardSickRemaining = document.getElementById("cardSickRemaining");

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
  // 1. Employee Personas Management
  // --------------------------------------------------------------------------
  async function loadEmployees() {
    try {
      const res = await fetch("/api/employees");
      employees = await res.json();
      renderEmployeeList();
      if (employees.length > 0) {
        selectEmployee(employees[0]);
      }
    } catch (err) {
      console.error("Failed to load employees:", err);
    }
  }

  function renderEmployeeList() {
    employeeList.innerHTML = "";
    employees.forEach(emp => {
      const opt = document.createElement("div");
      opt.className = `employee-option ${currentEmployee && currentEmployee.id === emp.id ? "selected" : ""}`;
      opt.innerHTML = `
        <img src="${emp.avatar}" alt="${emp.name}" class="emp-opt-avatar">
        <div class="emp-opt-info">
          <span class="emp-opt-name">${emp.name} (${emp.id})</span>
          <span class="emp-opt-role">${emp.role}</span>
        </div>
      `;
      opt.addEventListener("click", () => {
        selectEmployee(emp);
        userMenu.classList.remove("active");
      });
      employeeList.appendChild(opt);
    });
  }

  function selectEmployee(emp) {
    currentEmployee = emp;
    userAvatar.src = emp.avatar;
    currentUserName.textContent = emp.name;
    currentUserId.textContent = emp.id;

    cardEmployeeName.textContent = emp.name;
    cardEmployeeRole.textContent = emp.role;
    cardEmployeeDept.innerHTML = `<i data-lucide="building" class="detail-icon"></i> ${emp.dept}`;
    cardEmployeeLoc.innerHTML = `<i data-lucide="map-pin" class="detail-icon"></i> ${emp.location}`;
    cardPtoRemaining.innerHTML = `${emp.pto_remaining} <small>days</small>`;
    cardPtoAccrued.textContent = emp.pto_accrued;
    cardSickRemaining.innerHTML = `${emp.sick_remaining} <small>days</small>`;

    renderEmployeeList();
    lucide.createIcons();
  }

  userTrigger.addEventListener("click", (e) => {
    e.stopPropagation();
    userMenu.classList.toggle("active");
  });

  document.addEventListener("click", () => {
    userMenu.classList.remove("active");
  });

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
  // 3. Conversational Messaging & SSE Streaming Client
  // --------------------------------------------------------------------------
  async function sendMessage(text) {
    if (!text || !text.trim() || isGenerating) return;

    if (welcomeHero) {
      welcomeHero.style.display = "none";
    }

    const userText = text.trim();
    messageInput.value = "";
    adjustTextareaHeight();

    // 1. Render User Message Row
    appendUserMessage(userText);

    // 2. Prepare Agent Message Row
    const { agentRow, bubble, toolsContainer, contentContainer } = createAgentMessagePlaceholder();
    messagesStream.appendChild(agentRow);
    scrollToBottom();

    isGenerating = true;
    updateSendButtonState();

    const startTime = performance.now();
    let accumulatedMarkdown = "";

    try {
      const payload = {
        message: userText,
        user_id: currentEmployee ? currentEmployee.id : "EMP1001",
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
                  scrollToBottom();
                }
              });
            } catch (jsonErr) {
              console.error("JSON parse error on SSE event:", jsonErr, dataStr);
            }
          }
        }
      }

      const durationSec = ((performance.now() - startTime) / 1000).toFixed(2);
      telemLatency.textContent = `${durationSec}s`;

    } catch (err) {
      contentContainer.innerHTML += `<div style="color:var(--accent-error);margin-top:8px;">[Connection Error: ${err.message}]</div>`;
    } finally {
      isGenerating = false;
      updateSendButtonState();
      attachCitationListeners(contentContainer);
    }
  }

  function handleStreamEvent(event, { toolsContainer, contentContainer, appendMarkdown }) {
    if (event.type === "tool_call") {
      const pill = document.createElement("div");
      pill.className = "tool-invocation-pill active";
      pill.id = `tool_${event.id || Math.random().toString(36).substr(2, 5)}`;
      pill.innerHTML = `
        <i data-lucide="wrench" class="inline-icon" style="color:var(--accent-primary);"></i>
        <span>Calling <span class="tool-name-tag">${event.tool}</span></span>
        <span class="tool-badge-done"><i data-lucide="loader-2" class="spin-icon" style="width:12px;height:12px;"></i> running</span>
      `;
      toolsContainer.appendChild(pill);
      lucide.createIcons();
    } 
    else if (event.type === "tool_result") {
      const existing = toolsContainer.querySelector(`[id^="tool_"]`);
      if (existing) {
        existing.classList.remove("active");
        const badge = existing.querySelector(".tool-badge-done");
        if (badge) {
          badge.innerHTML = `<i data-lucide="check" style="width:12px;height:12px;"></i> executed`;
        }
      }
      lucide.createIcons();
    }
    else if (event.type === "text_chunk") {
      appendMarkdown(event.text);
    }
    else if (event.type === "done") {
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
      contentContainer.innerHTML = `<div style="color:var(--accent-error);">⚠️ ${event.message}</div>`;
    }
  }

  function appendUserMessage(text) {
    const row = document.createElement("div");
    row.className = "message-row user-row";
    row.innerHTML = `
      <div class="avatar-circle avatar-user">${currentEmployee ? currentEmployee.name.charAt(0) : "U"}</div>
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

  function scrollToBottom() {
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
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
  }

  clearChatBtn.addEventListener("click", () => {
    messagesStream.innerHTML = "";
    if (welcomeHero) {
      welcomeHero.style.display = "flex";
      messagesStream.appendChild(welcomeHero);
    }
    currentSessionId = null;
    sessionLabel.innerHTML = `Session: <span class="id-mono">auto</span>`;
  });

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
  loadEmployees();
  loadPolicies();
});
