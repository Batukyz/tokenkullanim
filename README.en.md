# 🪙 TokenKullanim (LLM Token & Budget Tracker)

[🇹🇷 Türkçe](README.md) | [🇬🇧 English](README.en.md)

A lightweight, standalone web application designed to track real-time token consumption for prompts sent to Large Language Models (OpenAI GPT-4o, Claude 3.5 Sonnet, Gemini 2.0 Flash, DeepSeek-V3, etc.), estimate response costs, and monitor remaining token quotas and budgets with an intuitive visual dashboard.

---

## 🌟 Key Features

1. **Real-Time Prompt & Token Counter:**
   - Automatically computes **Characters**, **Words**, and **Estimated Tokens** as you type your prompt.
   - Utilizes a Byte-Pair Encoding (BPE) estimation algorithm optimized for multilingual texts, including special characters and suffixes.

2. **Interactive Visual Tokenizer:**
   - Visualize how language models fragment your text into token chunks using color-coded visual chips.

3. **Remaining Token Budget & Quota Bar:**
   - Set custom token limits (e.g., 100K, 500K, 1 Million, 5M, 10M, or any custom value).
   - Dynamic progress bar with adaptive health status colors (Green &rarr; Orange &rarr; Red) indicating remaining balance.

4. **Multi-Model Support & Cost Estimation:**
   - **OpenAI:** GPT-4o, GPT-4o-mini, o3-mini, GPT-4 Turbo
   - **Anthropic:** Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus
   - **Google:** Gemini 2.0 Flash, Gemini 1.5 Flash, Gemini 1.5 Pro
   - **DeepSeek & Open Source:** DeepSeek-V3, DeepSeek-R1, Llama 3.3 70B
   - Automatic USD ($) cost calculation based on current per-1M input and output token pricing.

5. **Prompt History & CSV Export:**
   - Each prompt submission logs timestamps, chosen model, input/output tokens, total consumption, cost, and remaining quota.
   - All data is securely persisted in browser `localStorage` (no backend database required).
   - Export audit logs to CSV for analysis in Excel or Google Sheets.

6. **Dark & Light Mode:**
   - Modern glassmorphic user interface with instant theme switching.

---

## 🚀 Getting Started

### Method 1: Direct Double-Click (Zero Setup)
Simply double-click [`index.html`](index.html) or [`start.bat`](start.bat) in your file explorer. It opens directly in any web browser without needing any installation or dependencies!

### Method 2: Local Python Server
Run the built-in lightweight Python server from your terminal:
```bash
python server.py
```
Your default browser will automatically open at `http://localhost:5000`.

---

## 📁 Repository Structure

```
tokenkullanim/
├── index.html        # Main web application (HTML5, Modern CSS & Vanilla JS)
├── server.py         # Optional lightweight Python HTTP server
├── start.bat         # 1-click Windows launcher
├── README.md         # Turkish documentation
├── README.en.md      # English documentation
└── .gitignore        # Git ignore rules
```

---

## 📜 License
MIT License. Feel free to use, modify, and integrate into your workflows.
