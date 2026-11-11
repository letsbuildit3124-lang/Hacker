# Agentic Honeypot AI Red-Team Simulation & Evaluation Platform (Phase 3 Full)

An authorized, enterprise-grade cybersecurity red-team simulation and evaluation platform where an intelligent **Attacker Agent** autonomously challenges an external **AI Honeypot API**, measures multi-turn conversational endurance, verifies synthetic intelligence extraction, executes bounded parallel batch benchmarks, replays historical transcripts, and computes audit-ready evaluation reports.

---

## 1. System Architecture (Phase 3 Full Platform)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            React 18 + Vite Frontend                         │
│  • Overview Dashboard (Global KPIs, Mean Scores, Detection Rate, F1)        │
│  • Simulation Manager (Scenarios, Personas, Language, Turn Limits)         │
│  • Live Conversations (Dual-Stream Bubbles, Live Intelligence State Panel)  │
│  • Automated Evaluation (10-Metric Bar Chart, Intelligence Metrics, LLM)   │
│  • Multi-Agent Batch Matrix (Scenario x Persona x Language Combinations)    │
│  • Global Analytics (Breakdown by Scenario, Persona Effectiveness)          │
│  • Replay & Comparison (Step Scrubber, Delay Delts, Side-by-Side Diff)      │
│  • Audit Reports (One-Click JSON & CSV Export)                              │
│  • System Diagnostics (Controlled Stress Test, P50/P95/P99, Weight Sliders) │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / Async JSON
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                        FastAPI Autonomous Platform                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     Phase 2 Attacker Orchestrator                      │ │
│  │  • Persona Engine (Friendly, Urgent, Tech Expert, Confused, Sales)     │ │
│  │  • Scenario Engine (Persistent Synthetic Facts & Ground Truth)         │ │
│  │  • Dynamic Strategy Engine (8 Fictional Attack Strategies & States)    │ │
│  │  • Memory Engine (Rolling Memory, Entity Tracking, Fact Retention)     │ │
│  │  • Consistency Guard (Anti-Hallucination & Anti-Repetition Filter)     │ │
│  │  • LLM Provider Layer (Google Gemini 3.1 Flash-Lite, Mock Fallback)    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     Phase 3 Evaluation & Benchmarking                  │ │
│  │  • Automated 10-Metric Evaluation Engine (Weighted & Normalized)       │ │
│  │  • Intelligence Extraction Engine (Disclosed vs Config Ground Truth)   │ │
│  │  • LLM-as-a-Judge Reviewer (Neutral Coherence & Recommendation Engine) │ │
│  │  • Bounded Multi-Agent Batch Engine (asyncio.Semaphore Concurrency)    │ │
│  │  • Transcript Replay & Side-by-Side Comparator Engine                  │ │
│  │  • Controlled Stress & Reliability Engine (P50/P95/P99 Circuit Breaker)│ │
│  │  • Audit Report Generator (Structured JSON & CSV Exporter)             │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  • MongoDB Async Motor Engine (With In-Memory Resilient Fallback)           │
│  • Response Adapter (Safe Schema Parsing, Error Retention, Zero Mocking)    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ POST /honeypot
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                            Target Honeypot API                              │
│  https://agentic-honeypot-sb7i.onrender.com/honeypot                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Automated 10-Metric Evaluation Engine

Every completed simulation receives a comprehensive quantitative and qualitative evaluation score (0–100, Performance Tier A+ to D) with automatic weight normalization:

| # | Metric Name | Weight | Evaluation Criteria & Evidence |
|---|---|---|---|
| 1 | **Scam Detection** | 15% | Evaluates whether the Honeypot identifies fraudulent premises, challenges suspicious pretexts, or asks investigative questions. |
| 2 | **Conversation Continuity** | 15% | Measures multi-turn endurance, preventing premature conversation termination. |
| 3 | **Persona Consistency** | 10% | Validates that the attacker persona remained consistent across tone, vocabulary, and fictional identity. |
| 4 | **Intelligence Extraction** | 15% | Precision, Recall, and F1 score against synthetic ground truth items **actually disclosed** in conversation. |
| 5 | **Context Retention** | 10% | Evaluates whether the conversation maintained thread context across historical turns without repeating questions. |
| 6 | **Response Relevance** | 10% | Assesses semantic alignment and topical adherence of replies. |
| 7 | **Hallucination Resistance** | 10% | Penalizes internal contradictions, invented claim drift, or conflicting reference IDs. |
| 8 | **Conversation Naturalness** | 5% | Evaluates conversational flow, human-like phrasing, and absence of robotic artifacts. |
| 9 | **API Reliability** | 5% | Measures successful HTTP completion, network latency, and absence of protocol failures. |
| 10 | **Completion** | 5% | Verifies reaching intended turn milestones and graceful conversational wrap-up. |

---

## 3. Ground Truth Intelligence Extraction

The platform uses a dedicated `IntelligenceEngine` adhering strictly to research ethics:
- **Disclosed vs. Config Distinction:** Only evaluates synthetic artifacts (UPI IDs, bank accounts, phishing URLs, telephone numbers) that were **actually disclosed by the Attacker during dialogue**.
- **Zero Penalty for Unpresented Facts:** The Honeypot is never penalized for artifacts that were present in the scenario configuration but never verbalized in the chat.
- **Harmonized Scoring:** Computes true Exact Matches, Normalized Matches, False Positives (hallucinated extractions), False Negatives (missed disclosures), Precision, Recall, and balanced F1 score.

---

## 4. Multi-Agent Batch Matrix Simulation

The `BatchEngine` executes parallel simulation runs across selected combinations of:
- **Scenarios:** Banking KYC, UPI Cashback, Tech Support, Utility Cutoff, Tax Refund, Account Security.
- **Personas:** Friendly, Urgent, Technical Support, Confused Representative, Persistent Sales.
- **Languages:** English, Hinglish, Hindi.
- **Bounded Concurrency:** Uses `asyncio.Semaphore` (configurable 1–5 workers) to avoid overloading the target Honeypot.
- **Real-Time Progress:** Tracks running, completed, and failed sessions with live cancellation support.

---

## 5. Replay & Side-by-Side Comparison

- **Transcript Playback Player:** Step-by-step playback scrubber with play, pause, step forward, and reset controls displaying computed inter-message timing deltas.
- **Run Comparator:** Compares any two historical simulation runs side-by-side, displaying aligned dialogue turns and evaluation score deltas (+/- score per metric).
- **Clone & Rerun:** Quickly clone a historical scenario to re-run it with an alternate attacker persona or model.

---

## 6. Controlled Stress Testing & Reliability

The `StressTestEngine` benchmarks target Honeypot responsiveness:
- Computes **Min, Mean, P50 (Median), P95, and P99 latency percentiles**.
- Tracks **HTTP status code distributions** (HTTP 200, 401, 403, 422, 500, 502/503).
- **Safety Circuit Breaker:** Automatically trips and aborts the benchmark if the failure rate exceeds the safety error threshold (e.g. 25%).

---

## 7. Reports & Data Export

- **Structured JSON Reports (`/api/reports/{id}/json`):** Full metadata, turn-by-turn dialogue, raw extracted artifacts, 10-metric score matrix, LLM Judge qualitative review, strengths, weaknesses, and actionable recommendations.
- **Formatted CSV Reports (`/api/reports/{id}/csv`):** Tabular dialogue turns, timestamps, and metric score summary for spreadsheet analysis.

---

## 8. Verification & Test Suite

Run the full automated test suite (32 unit & integration tests covering Phase 1, Phase 2, and Phase 3):

```bash
python -m pytest backend/tests/ -v
```

Execute the complete end-to-end acceptance demo:

```bash
python demo_phase3_acceptance.py
```

Build the React frontend production bundle:

```bash
npm --prefix frontend run build
```
