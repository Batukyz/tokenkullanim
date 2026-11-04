# 🪙 TokenKullanim (Desktop Floating HUD & Token Tracker)

[🇹🇷 Türkçe](README.md) | [🇬🇧 English](README.en.md)

A lightweight, **always-on-top desktop floating mini widget** designed to run alongside your AI workflows (Antigravity, Gemini, OpenAI, Claude, etc.). It monitors in real time how many tokens each of your prompts consumes, tracks your remaining model context/quota, and calculates estimated usage costs right on your screen.

---

## 🖥️ Launching the Desktop Floating Mini Widget

To launch the floating HUD widget on your desktop:

1. Double-click **`start_widget.bat`** in your project folder.
2. Or run from the terminal:
   ```bash
   pythonw widget.py
   ```

### 🎛️ Mini Widget Features:
- **Always on Top:** Stays pinned on your screen while you code or chat with your AI assistant.
- **Draggable:** Click and drag from anywhere on the header to move it around your screen.
- **Live Auto-Sync:** Automatically reads your active conversation transcript; pulses and updates the instant a prompt completes.
- **Compact & Expanded Modes:** Click `—` to collapse into an ultra-compact mini pill.
- **Configurable Models & Quotas:** Click `⚙` to adjust your model (Gemini, GPT-4o, Claude 3.5, DeepSeek) and token quota limits.

---

## 🌐 Web Dashboard Version

For in-depth analytics, visual tokenizer chips, and CSV exporting:

- **Live Web App:** 👉 **[https://batukyz.github.io/tokenkullanim/](https://batukyz.github.io/tokenkullanim/)**
- **Local Browser:** Double-click `start.bat` or `index.html`.

---

## 📁 Repository Structure

```
tokenkullanim/
├── widget.py          # Desktop floating mini widget (Native Tkinter, 0 dependencies)
├── start_widget.bat   # 1-click launcher without command window
├── index.html         # Web dashboard & tokenizer
├── start.bat          # 1-click web launcher
├── README.md          # Turkish documentation
└── README.en.md       # English documentation
```

---

## 📜 License
MIT License.
