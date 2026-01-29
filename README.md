# al-fiqh-hackathon

Nitroo Al-Fiqh Hackathon repository: Islamic finance and Shariah compliance tools powered by agentic AI.

## Overview

This repository contains two main deliverables:

- **Task 1 – Neo AI (ChatBot)**: RAG-based Q&A over Islamic finance and Shariah documents.
- **Task 2 – Tathqeeb**: AI-powered verification of Islamic contracts against Shariah regulations.

---

## Task 1 – Neo AI (ChatBot)

**Next‑Gen Optimized Advisor, driven by Agentic AI**

Neo AI is a RAG (Retrieval Augmented Generation) system for Islamic finance and Shariah compliance. It gathers official documents from trusted sources (e.g. BNM, IIFA, SC), indexes them in a vector database, and answers questions through an intelligent Q&A interface powered by LLMs. Built to stay current, Neo AI keeps you aligned with the latest Shariah regulations.

**Stack**: Next.js frontend, FastAPI + LangChain backend, Web Scraper (PDFs → Qdrant), Ollama/OpenAI.

**Quick links**: [Task 1 ChatBot README](Task%201%20ChatBot/README.md) – full setup, architecture, API, and development.

---

## Task 2 – Tathqeeb (تثقيب)

**Shariah Compliance Verification**

Tathqeeb (تثقيب – “Verification” & “Authentication”) is an AI Shariah compliance agent for contracts. It checks uploaded PDF contracts against Shariah regulations, reports violations with severity levels, and provides compliance scoring. Powered by the same vector and LLM stack for consistent oversight.

**Stack**: React + Vite + Tailwind frontend, FastAPI backend (PDF extraction, embeddings, Qdrant), local LLM (Ollama).

**Quick links**: [Task 2 Tathqeeb README](Task%202%20Tathqeeb/README.md) – setup, Docker, API, and tunnel scripts.

---

## Repository structure

```
nitroo-al-fiqh-hackathon/
├── Task 1 ChatBot/     # Neo AI – RAG Q&A, scraper, chat UI
├── Task 2 Tathqeeb/    # Tathqeeb – contract compliance verification
├── LICENSE
└── README.md           # This file
```

Each task folder has its own README with prerequisites, quick start, and detailed documentation.

---

## Demo

[Watch Demo Video](https://youtu.be/mO9mnDhZJ14)
