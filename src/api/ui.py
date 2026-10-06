"""Interactive Web UI Dashboard for Big Data RAG."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

ui_router = APIRouter(tags=["UI"])

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Big Data RAG | Intelligence Substrate</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #111827;
      --card-border: #1f2937;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --accent-glow: rgba(59, 130, 246, 0.2);
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --purple: #8b5cf6;
      --cyan: #06b6d4;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* Header */
    header {
      background: rgba(17, 24, 39, 0.8);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--card-border);
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 50;
    }
    .logo-group {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .logo-badge {
      background: linear-gradient(135deg, #3b82f6, #8b5cf6);
      color: white;
      font-weight: 800;
      padding: 0.35rem 0.65rem;
      border-radius: 8px;
      font-size: 0.85rem;
      letter-spacing: 0.5px;
    }
    .logo-title {
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.3px;
    }
    .nav-links {
      display: flex;
      align-items: center;
      gap: 1.25rem;
    }
    .nav-link {
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.9rem;
      font-weight: 500;
      transition: color 0.2s;
    }
    .nav-link:hover { color: var(--text); }
    .status-pill {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background: #1e293b;
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 600;
      border: 1px solid var(--card-border);
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 8px var(--success);
    }

    /* Main Container */
    main {
      flex: 1;
      max-width: 1300px;
      width: 100%;
      margin: 0 auto;
      padding: 2rem;
      display: grid;
      grid-template-columns: 320px 1fr;
      gap: 2rem;
    }
    @media (max-width: 960px) {
      main { grid-template-columns: 1fr; }
    }

    /* Cards */
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    .card-title {
      font-size: 1.05rem;
      font-weight: 700;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: var(--text);
    }

    /* Sidebar controls */
    .sidebar {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .field-group {
      margin-bottom: 1rem;
    }
    .field-label {
      display: block;
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      margin-bottom: 0.4rem;
    }
    input, select, textarea {
      width: 100%;
      background: #1a2234;
      border: 1px solid var(--card-border);
      color: var(--text);
      padding: 0.65rem 0.85rem;
      border-radius: 8px;
      font-family: inherit;
      font-size: 0.9rem;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    input:focus, select:focus, textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-glow);
    }
    textarea { resize: vertical; min-height: 80px; }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      width: 100%;
      padding: 0.75rem 1.25rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.95rem;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
    }
    .btn-primary {
      background: linear-gradient(135deg, #3b82f6, #2563eb);
      color: white;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    .btn-primary:hover {
      background: linear-gradient(135deg, #2563eb, #1d4ed8);
      box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
      transform: translateY(-1px);
    }
    .btn-secondary {
      background: #1e293b;
      color: var(--text);
      border: 1px solid var(--card-border);
    }
    .btn-secondary:hover {
      background: #334155;
    }
    .btn:active { transform: translateY(0); }
    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }

    /* Content Area */
    .content-area {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .tab-bar {
      display: flex;
      gap: 0.5rem;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 0.75rem;
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-weight: 600;
      font-size: 0.9rem;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .tab-btn.active {
      background: #1e293b;
      color: var(--accent);
    }
    .tab-btn:hover:not(.active) {
      color: var(--text);
    }

    /* Prompt Box */
    .prompt-box {
      background: #161f30;
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    .prompt-input {
      background: transparent;
      border: none;
      color: var(--text);
      font-size: 1.05rem;
      min-height: 70px;
      padding: 0;
      resize: none;
      outline: none;
      font-family: inherit;
    }
    .prompt-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid var(--card-border);
      padding-top: 0.75rem;
    }
    .badge-pill {
      font-size: 0.75rem;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-weight: 600;
      text-transform: uppercase;
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.3);
    }

    /* Results */
    .result-container {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    .answer-card {
      background: linear-gradient(180deg, #162035 0%, #111827 100%);
      border: 1px solid #2b3954;
      border-radius: 12px;
      padding: 1.5rem;
      position: relative;
    }
    .answer-text {
      font-size: 1rem;
      line-height: 1.7;
      color: #e2e8f0;
      white-space: pre-wrap;
    }
    .meta-tags {
      display: flex;
      gap: 0.75rem;
      margin-top: 1rem;
      padding-top: 0.75rem;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      font-size: 0.8rem;
      color: var(--text-muted);
      font-family: 'JetBrains Mono', monospace;
    }

    .sources-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }
    @media (max-width: 768px) {
      .sources-grid { grid-template-columns: 1fr; }
    }
    .source-panel {
      background: #111827;
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 1rem;
    }
    .source-panel-title {
      font-size: 0.85rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 0.75rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .item-card {
      background: #172133;
      border: 1px solid #222f46;
      border-radius: 8px;
      padding: 0.75rem;
      margin-bottom: 0.5rem;
      font-size: 0.85rem;
      line-height: 1.4;
    }
    .triplet-tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      color: #a78bfa;
      background: rgba(139, 92, 246, 0.1);
      padding: 0.35rem 0.5rem;
      border-radius: 6px;
      border: 1px solid rgba(139, 92, 246, 0.25);
      margin-bottom: 0.4rem;
      display: inline-block;
      width: 100%;
    }

    /* Footer */
    footer {
      border-top: 1px solid var(--card-border);
      padding: 1rem 2rem;
      text-align: center;
      font-size: 0.85rem;
      color: var(--text-muted);
      background: var(--card-bg);
      margin-top: auto;
    }
  </style>
</head>
<body>

  <!-- Header -->
  <header>
    <div class="logo-group">
      <div class="logo-badge">RAG</div>
      <div class="logo-title">Big Data RAG <span style="font-weight: 400; color: var(--text-muted); font-size: 0.9rem;">| Intelligence Substrate</span></div>
    </div>
    <div class="nav-links">
      <div class="status-pill" id="healthPill">
        <div class="status-dot"></div>
        <span id="healthStatusText">API Online</span>
      </div>
      <a href="/docs" target="_blank" class="nav-link">Swagger API</a>
      <a href="/redoc" target="_blank" class="nav-link">ReDoc</a>
      <a href="/metrics" target="_blank" class="nav-link">Metrics</a>
    </div>
  </header>

  <!-- Main Grid -->
  <main>
    <!-- Left Sidebar: Controls & Authentication -->
    <div class="sidebar">
      <!-- Auth Card -->
      <div class="card">
        <div class="card-title">🔐 Authentication</div>
        <div class="field-group">
          <label class="field-label">Username</label>
          <input type="text" id="authUsername" value="admin">
        </div>
        <div class="field-group">
          <label class="field-label">Password</label>
          <input type="password" id="authPassword" value="admin">
        </div>
        <button class="btn btn-secondary" onclick="login()">Authenticate (Login)</button>
        <div id="authStatusMsg" style="font-size: 0.8rem; margin-top: 0.5rem; color: var(--success); display: none;">✓ Authenticated</div>
      </div>

      <!-- Settings Card -->
      <div class="card">
        <div class="card-title">⚙️ Query Parameters</div>
        <div class="field-group">
          <label class="field-label">Retrieval Limit</label>
          <input type="number" id="queryLimit" value="5" min="1" max="20">
        </div>
        <div class="field-group">
          <label class="field-label">LLM Model (Ollama)</label>
          <input type="text" id="modelName" value="llama3">
        </div>
        <div class="field-group">
          <label class="field-label">Execution Strategy</label>
          <select id="queryStrategy">
            <option value="generate">Full RAG Generation (LLM + Context)</option>
            <option value="hybrid">Hybrid Search Only (Vectors + Graph)</option>
          </select>
        </div>
      </div>

      <!-- Quick Health Monitor -->
      <div class="card">
        <div class="card-title">🩺 Component Health</div>
        <div style="font-size: 0.85rem; display: flex; flex-direction: column; gap: 0.5rem;" id="componentHealthList">
          <div>• Vector DB (Qdrant): <span id="qdrantHealth">checking...</span></div>
          <div>• Graph DB (Neo4j): <span id="neo4jHealth">checking...</span></div>
          <div>• Cache (Redis): <span id="redisHealth">active</span></div>
        </div>
      </div>
    </div>

    <!-- Right Content Area -->
    <div class="content-area">
      <!-- Tabs -->
      <div class="tab-bar">
        <button class="tab-btn active">🔍 Hybrid Knowledge Search & Reasoning</button>
      </div>

      <!-- Prompt Input Card -->
      <div class="prompt-box">
        <textarea id="promptInput" class="prompt-input" placeholder="Ask a question or search memory (e.g., 'What are the main events and connected entities?')..."></textarea>
        <div class="prompt-actions">
          <span class="badge-pill">Vector + Knowledge Graph</span>
          <button class="btn btn-primary" style="width: auto; padding: 0.5rem 1.5rem;" id="submitBtn" onclick="runQuery()">
            <span>Execute Query</span> ➔
          </button>
        </div>
      </div>

      <!-- Results Container -->
      <div class="result-container" id="resultsSection" style="display: none;">
        <!-- LLM Answer (if generated) -->
        <div class="answer-card" id="answerCard">
          <div class="card-title" style="color: #60a5fa;">💡 AI Synthesized Response</div>
          <div class="answer-text" id="answerContent">Generating response...</div>
          <div class="meta-tags" id="metaTags"></div>
        </div>

        <!-- Sources Grid -->
        <div class="sources-grid">
          <!-- Vector Results -->
          <div class="source-panel">
            <div class="source-panel-title" style="color: #38bdf8;">
              <span>📁 Semantic Vector Excerpts</span>
              <span id="vectorCountBadge" style="margin-left: auto; font-size: 0.75rem;" class="badge-pill">0 items</span>
            </div>
            <div id="vectorList"></div>
          </div>

          <!-- Knowledge Graph Triplets -->
          <div class="source-panel">
            <div class="source-panel-title" style="color: #c084fc;">
              <span>🕸️ Knowledge Graph Relations</span>
              <span id="graphCountBadge" style="margin-left: auto; font-size: 0.75rem;" class="badge-pill">0 triplets</span>
            </div>
            <div id="graphList"></div>
          </div>
        </div>
      </div>
    </div>
  </main>

  <footer>
    Big Data RAG Pipeline • Hybrid Retrieval Architecture (Qdrant + Neo4j + Ollama)
  </footer>

  <script>
    let authToken = localStorage.getItem("rag_token") || "";

    if (authToken) {
      document.getElementById("authStatusMsg").style.display = "block";
      document.getElementById("authStatusMsg").textContent = "✓ Session Active";
    }

    async function login() {
      const username = document.getElementById("authUsername").value.trim();
      const password = document.getElementById("authPassword").value.trim();
      const statusMsg = document.getElementById("authStatusMsg");

      try {
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);

        const res = await fetch("/auth/token", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: formData
        });

        if (res.ok) {
          const data = await res.json();
          authToken = data.access_token;
          localStorage.setItem("rag_token", authToken);
          statusMsg.style.display = "block";
          statusMsg.style.color = "var(--success)";
          statusMsg.textContent = "✓ Authenticated successfully!";
        } else {
          statusMsg.style.display = "block";
          statusMsg.style.color = "var(--danger)";
          statusMsg.textContent = "✗ Login failed: check credentials";
        }
      } catch (err) {
        statusMsg.style.display = "block";
        statusMsg.style.color = "var(--danger)";
        statusMsg.textContent = "✗ Error: " + err.message;
      }
    }

    async function checkHealth() {
      try {
        const res = await fetch("/health/hybrid");
        if (res.ok) {
          const data = await res.json();
          document.getElementById("qdrantHealth").textContent = data.components?.qdrant || "unknown";
          document.getElementById("neo4jHealth").textContent = data.components?.neo4j || "unknown";
        }
      } catch (e) {
        document.getElementById("qdrantHealth").textContent = "offline";
        document.getElementById("neo4jHealth").textContent = "offline";
      }
    }
    checkHealth();

    async function runQuery() {
      const text = document.getElementById("promptInput").value.trim();
      if (!text) {
        alert("Please enter a query or prompt.");
        return;
      }

      if (!authToken) {
        await login();
      }

      const limit = parseInt(document.getElementById("queryLimit").value, 10) || 5;
      const strategy = document.getElementById("queryStrategy").value;
      const modelName = document.getElementById("modelName").value.trim() || "llama3";
      const submitBtn = document.getElementById("submitBtn");

      submitBtn.disabled = true;
      submitBtn.innerHTML = "Thinking... ⏳";

      const resultsSection = document.getElementById("resultsSection");
      resultsSection.style.display = "flex";

      const answerCard = document.getElementById("answerCard");
      const answerContent = document.getElementById("answerContent");
      const metaTags = document.getElementById("metaTags");
      const vectorList = document.getElementById("vectorList");
      const graphList = document.getElementById("graphList");

      vectorList.innerHTML = "";
      graphList.innerHTML = "";

      const endpoint = strategy === "generate" ? "/memory/search/generate" : "/memory/search/hybrid";
      const bodyPayload = strategy === "generate" 
        ? { query_text: text, limit: limit, model_name: modelName, include_sources: true }
        : { query_text: text, limit: limit };

      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + authToken
          },
          body: JSON.stringify(bodyPayload)
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || "Request failed with status " + res.status);
        }

        const data = await res.json();

        // Render Answer
        if (strategy === "generate") {
          answerCard.style.display = "block";
          answerContent.textContent = data.answer || "No response generated.";
          metaTags.innerHTML = `
            <span>⚡ ${data.meta?.processing_time_ms || 0} ms</span>
            <span>🤖 Model: ${data.meta?.model || modelName}</span>
          `;
        } else {
          answerCard.style.display = "none";
        }

        // Render Sources
        const sources = strategy === "generate" ? (data.sources || {}) : (data.results || {});
        const semantic = sources.semantic || [];
        const structural = sources.structural || [];

        document.getElementById("vectorCountBadge").textContent = semantic.length + " items";
        document.getElementById("graphCountBadge").textContent = structural.length + " triplets";

        if (semantic.length === 0) {
          vectorList.innerHTML = "<div style='color: var(--text-muted); font-size: 0.85rem;'>No vector matches found.</div>";
        } else {
          semantic.forEach((item, idx) => {
            const card = document.createElement("div");
            card.className = "item-card";
            const textContent = item.payload?.text || item.text || JSON.stringify(item);
            card.innerHTML = `<strong>[#${idx + 1}]</strong> ${textContent}`;
            vectorList.appendChild(card);
          });
        }

        if (structural.length === 0) {
          graphList.innerHTML = "<div style='color: var(--text-muted); font-size: 0.85rem;'>No graph relations found.</div>";
        } else {
          structural.forEach(item => {
            const card = document.createElement("div");
            card.className = "item-card";
            if (item.source && item.target) {
              const src = item.source.props?.name || item.source.props?.title || "Node";
              const rel = item.relationship || "RELATED_TO";
              const tgt = item.target.props?.name || item.target.props?.title || "Node";
              card.innerHTML = `<div class="triplet-tag">(${src}) -[:${rel}]-> (${tgt})</div>`;
            } else {
              card.textContent = JSON.stringify(item);
            }
            graphList.appendChild(card);
          });
        }

      } catch (err) {
        answerCard.style.display = "block";
        answerContent.textContent = "Error: " + err.message;
        metaTags.innerHTML = "<span style='color: var(--danger)'>Execution Failed</span>";
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = "Execute Query ➔";
      }
    }
  </script>
</body>
</html>
"""

@ui_router.get("/ui", response_class=HTMLResponse)
@ui_router.get("/dashboard", response_class=HTMLResponse)
async def serve_ui():
    """Serve the Big Data RAG Interactive Web Dashboard."""
    return HTMLResponse(content=HTML_CONTENT)
