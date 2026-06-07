# RetailMind AI System Architecture

This document specifies the integration specifications, system instructions, domain guardrails, and streaming protocols of the AI Business Advisor.

---

## 1. Pipeline Overview

```text
 User Question ──► Input Sanitizer ──► Context Assembler
                                             │
   ┌─────────────────────────────────────────┘
   ▼
llm_service.stream_advisor()
   ├── Guardrail Check
   │     ├── If off-topic ──► Output default deflection response
   │     └── If on-topic  ──► Forward to Groq
   │
   └── API Call (AsyncGroq)
         ├── Model: llama-3.3-70b-versatile
         ├── Temp: 0.2 | Max Tokens: 600
         ├── Success ──► Stream chunks (SSE)
         └── Failure ──► Invoke fallback response
```

---

## 2. Groq Llama-3 Integration

The AI Advisor uses the Groq API for low-latency inference:
* **SDK**: `groq.AsyncGroq` (asynchronous, non-blocking client).
* **Model**: `llama-3.3-70b-versatile`.
* **Inference Parameters**:
  * `temperature`: `0.2` (forces factual correctness, low creativity).
  * `max_tokens`: `600` (limits output length).
  * `stream`: `true` (yields characters token-by-token for responsive streaming).

---

## 3. Strict Retail Guardrails & System Prompts

The advisor uses strict system prompts defining its role, boundaries, and instructions:

### 3.1 Role & Context Ingestion
> You are RetailMind's AI Business Advisor — a world-class retail analytics expert. You have access to the user's real store data. Give specific, data-driven advice. You ONLY answer questions about retail operations: sales, margins, inventory, dead stock, demand signals, pricing, and the RetailMind application.

### 3.2 System Directives
* **Data Loyalty**: Responses must cite actual telemetry metrics (percentages, revenue figures, category names) loaded in the session context.
* **No Speculation**: If data is insufficient, the advisor must explicitly state: *"I need more data."*
* **Brevity**: Responses are capped at 200 words unless detail is explicitly requested.
* **Factual Redirection**: If asked an off-topic question (e.g. recipes, code creation, general trivia), the advisor must deflect using the exact deflection phrase:
  > I am RetailMind's Business Intelligence Advisor. I can only assist with retail store sales, margins, dead stock, demand spikes, and inventory trends.

---

## 4. Fallback Execution Logic

If the Groq API key is missing or calls fail due to network outages, the client invokes rule-based fallback responses (`_fallback_answer` in `llm.py`):
* **Margin / COGS Keywords**: Guides the user to audit high-cost categories and negotiate bulk rates with suppliers.
* **Inventory / Stock Keywords**: Points the user to dead stock clearout markdowns and forecast timelines.
* **Trend / Anomaly Keywords**: Recommends checking sync schedules and ledger parameters.
* **General Questions**: Outputs operational instructions for loading CSV/Excel data to initialize the dashboard.
