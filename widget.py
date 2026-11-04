"""
TokenKullanım - Masaüstü Yüzen Mini Widget (Universal AI Token HUD)
ChatGPT, Claude, Gemini, Antigravity ve tüm masaüstü/tarayıcı araçlarında
girilen promptları ve harcanan tokenları anında algılar, kalan kotanızı gösterir.
"""

import os
import sys
import glob
import json
import time
import re
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox

# --- CONSTANTS & CONFIG ---
CHECK_INTERVAL_MS = 600   # Check loop every 600ms
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "widget_state.json")

MODEL_PRICING = {
    "GPT-4o (ChatGPT)": {"in": 2.50, "out": 10.00, "max_context": 128_000, "alias": "ChatGPT"},
    "GPT-4o-mini": {"in": 0.15, "out": 0.60, "max_context": 128_000, "alias": "GPT-mini"},
    "Claude 3.5 Sonnet": {"in": 3.00, "out": 15.00, "max_context": 200_000, "alias": "Claude"},
    "Gemini 3.8 / 2.0 Flash": {"in": 0.10, "out": 0.40, "max_context": 1_000_000, "alias": "Gemini"},
    "Gemini 1.5 Pro": {"in": 1.25, "out": 5.00, "max_context": 2_000_000, "alias": "Gemini-Pro"},
    "DeepSeek-V3 / R1": {"in": 0.20, "out": 0.50, "max_context": 128_000, "alias": "DeepSeek"},
    "Genel / Özel Model": {"in": 1.00, "out": 2.00, "max_context": 1_000_000, "alias": "AI Model"},
}

def get_active_window_title():
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value
    except Exception:
        pass
    return ""

def detect_source_from_title(title):
    t_lower = (title or "").lower()
    if "chatgpt" in t_lower or "openai" in t_lower:
        return "ChatGPT", "GPT-4o (ChatGPT)"
    elif "claude" in t_lower or "anthropic" in t_lower:
        return "Claude", "Claude 3.5 Sonnet"
    elif "gemini" in t_lower or "aistudio" in t_lower:
        return "Gemini", "Gemini 3.8 / 2.0 Flash"
    elif "deepseek" in t_lower:
        return "DeepSeek", "DeepSeek-V3 / R1"
    elif "cursor" in t_lower:
        return "Cursor AI", "Claude 3.5 Sonnet"
    elif "perplexity" in t_lower:
        return "Perplexity", "GPT-4o (ChatGPT)"
    elif "antigravity" in t_lower:
        return "Antigravity", "Gemini 3.8 / 2.0 Flash"
    return "Masaüstü/Pano", None

def estimate_tokens(text):
    if not text:
        return 0
    words = text.match if hasattr(text, "match") else re.findall(r"\S+|\s+", text)
    token_count = 0
    for w in words:
        if re.match(r"^\s+$", w):
            token_count += max(1, len(w) // 4)
            continue
        non_ascii = len(re.findall(r"[^a-zA-Z0-9]", w))
        length = len(w)
        if non_ascii > 0:
            token_count += int(round((length + non_ascii * 0.8) / 3.2)) + 1
        elif length <= 4:
            token_count += 1
        else:
            token_count += int(round(length / 3.8)) + 1
    return max(1, token_count)

def get_brain_dir():
    user_home = os.path.expanduser("~")
    return os.path.join(user_home, ".gemini", "antigravity-cli", "brain")

def find_latest_transcript():
    brain_dir = get_brain_dir()
    if not os.path.exists(brain_dir):
        return None
    transcripts = glob.glob(os.path.join(brain_dir, "*", ".system_generated", "logs", "transcript.jsonl"))
    if not transcripts:
        return None
    transcripts.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return transcripts[0]

def parse_transcript(file_path):
    if not file_path or not os.path.exists(file_path):
        return None

    last_step = None
    last_prompt = ""
    total_input = 0
    total_output = 0
    prompt_count = 0
    latest_context = 0

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                if data.get("type") == "USER_INPUT":
                    last_prompt = data.get("content", "")
                    prompt_count += 1

                if "input_tokens" in data:
                    in_t = data.get("input_tokens", 0)
                    out_t = data.get("output_tokens", 0)
                    cache_t = data.get("cache_read_tokens", 0)
                    total_input += in_t
                    total_output += out_t
                    last_step = {
                        "input": in_t,
                        "output": out_t,
                        "cache": cache_t,
                        "timestamp": data.get("created_at", "")
                    }
                    latest_context = in_t + cache_t

        return {
            "last_step": last_step,
            "last_prompt": last_prompt,
            "total_input": total_input,
            "total_output": total_output,
            "latest_context": latest_context,
            "prompt_count": prompt_count
        }
    except Exception:
        return None


class UniversalFloatingWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TokenKullanım Universal HUD")
        self.root.overrideredirect(True)       # Frameless
        self.root.attributes("-topmost", True)  # Always on top

        # Colors
        self.bg_color = "#0b0f19"         # Dark background
        self.card_bg = "#151e32"          # Slate 800
        self.card_border = "#263550"      # Slate 700
        self.text_color = "#f8fafc"       # Text
        self.muted_color = "#94a3b8"      # Muted text
        self.accent_color = "#818cf8"     # Indigo
        self.cyan_color = "#22d3ee"       # Cyan
        self.success_color = "#34d399"    # Emerald
        self.warning_color = "#fbbf24"    # Amber
        self.danger_color = "#f87171"     # Rose

        self.root.configure(bg=self.bg_color)

        # State initialization
        self.load_state()

        # Runtime trackers
        self.last_clipboard_text = ""
        self.last_transcript_mtime = 0
        self.active_transcript_path = None
        self.is_compact = False
        self.auto_clipboard_enabled = True
        self.estimated_output_tokens = 350

        # Drag coords
        self.drag_x = 0
        self.drag_y = 0

        # Position top-right
        screen_w = self.root.winfo_screenwidth()
        init_x = screen_w - 360
        init_y = 50
        self.root.geometry(f"340x280+{init_x}+{init_y}")

        self.setup_ui()
        self.bind_events()

        # Start dual loop: Clipboard watcher + Transcript watcher
        self.watch_loop()

    def load_state(self):
        self.selected_model = "GPT-4o (ChatGPT)"
        self.max_quota = 1_000_000
        self.spent_tokens = 0
        self.total_prompts = 0
        self.last_source = "Başlatıldı"
        self.last_prompt_summary = "İzleme aktif..."
        self.last_in_tokens = 0
        self.last_out_tokens = 0

        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.selected_model = data.get("selected_model", self.selected_model)
                    self.max_quota = data.get("max_quota", self.max_quota)
                    self.spent_tokens = data.get("spent_tokens", 0)
                    self.total_prompts = data.get("total_prompts", 0)
                    self.last_source = data.get("last_source", self.last_source)
                    self.last_prompt_summary = data.get("last_prompt_summary", self.last_prompt_summary)
            except Exception:
                pass

    def save_state(self):
        try:
            data = {
                "selected_model": self.selected_model,
                "max_quota": self.max_quota,
                "spent_tokens": self.spent_tokens,
                "total_prompts": self.total_prompts,
                "last_source": self.last_source,
                "last_prompt_summary": self.last_prompt_summary
            }
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def setup_ui(self):
        self.border_frame = tk.Frame(self.root, bg=self.card_border, padx=1, pady=1)
        self.border_frame.pack(fill=tk.BOTH, expand=True)

        self.main_container = tk.Frame(self.border_frame, bg=self.bg_color, padx=14, pady=12)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # --- HEADER ---
        self.header_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))

        self.title_group = tk.Frame(self.header_frame, bg=self.bg_color)
        self.title_group.pack(side=tk.LEFT)

        self.status_dot = tk.Label(self.title_group, text="●", fg=self.success_color, bg=self.bg_color, font=("Segoe UI", 11, "bold"))
        self.status_dot.pack(side=tk.LEFT, padx=(0, 5))

        self.title_label = tk.Label(self.title_group, text="TokenKullanım", fg=self.text_color, bg=self.bg_color, font=("Segoe UI", 10, "bold"))
        self.title_label.pack(side=tk.LEFT)

        self.btn_group = tk.Frame(self.header_frame, bg=self.bg_color)
        self.btn_group.pack(side=tk.RIGHT)

        # Quick capture button on header
        self.btn_capture = tk.Label(self.btn_group, text="📋 Al", fg=self.cyan_color, bg=self.card_bg, font=("Segoe UI", 8, "bold"), padx=5, pady=2, cursor="hand2")
        self.btn_capture.pack(side=tk.LEFT, padx=3)

        self.btn_settings = tk.Label(self.btn_group, text="⚙", fg=self.muted_color, bg=self.bg_color, font=("Segoe UI", 10), cursor="hand2")
        self.btn_settings.pack(side=tk.LEFT, padx=3)

        self.btn_toggle = tk.Label(self.btn_group, text="—", fg=self.muted_color, bg=self.bg_color, font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.btn_toggle.pack(side=tk.LEFT, padx=3)

        self.btn_close = tk.Label(self.btn_group, text="✕", fg=self.muted_color, bg=self.bg_color, font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.btn_close.pack(side=tk.LEFT, padx=3)

        # --- EXPANDED BODY ---
        self.body_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.body_frame.pack(fill=tk.BOTH, expand=True)

        # Card 1: App Source & Model Detection
        self.card1 = tk.Frame(self.body_frame, bg=self.card_bg, padx=10, pady=8)
        self.card1.pack(fill=tk.X, pady=(0, 8))

        self.card1_top = tk.Frame(self.card1, bg=self.card_bg)
        self.card1_top.pack(fill=tk.X)

        self.source_badge = tk.Label(self.card1_top, text=f"Kaynak: {self.last_source}", fg=self.cyan_color, bg="#111d33", font=("Segoe UI", 8, "bold"), padx=6, pady=2)
        self.source_badge.pack(side=tk.LEFT)

        self.model_badge = tk.Label(self.card1_top, text=self.selected_model.split("(")[0].strip(), fg=self.accent_color, bg=self.card_bg, font=("Segoe UI", 8, "bold"))
        self.model_badge.pack(side=tk.RIGHT)

        self.last_prompt_lbl = tk.Label(self.card1, text=f"Son: {self.last_prompt_summary}", fg=self.text_color, bg=self.card_bg, font=("Segoe UI", 8, "bold"), anchor="w", justify="left")
        self.last_prompt_lbl.pack(fill=tk.X, pady=(4, 0))

        # Card 2: Progress & Quota Health
        self.card2 = tk.Frame(self.body_frame, bg=self.card_bg, padx=10, pady=8)
        self.card2.pack(fill=tk.X, pady=(0, 8))

        self.card2_header = tk.Frame(self.card2, bg=self.card_bg)
        self.card2_header.pack(fill=tk.X)

        self.quota_title = tk.Label(self.card2_header, text="Kalan Kota / Kullanım:", fg=self.muted_color, bg=self.card_bg, font=("Segoe UI", 8))
        self.quota_title.pack(side=tk.LEFT)

        self.percent_lbl = tk.Label(self.card2_header, text="%100 Kalan", fg=self.success_color, bg=self.card_bg, font=("Segoe UI", 8, "bold"))
        self.percent_lbl.pack(side=tk.RIGHT)

        self.progress_canvas = tk.Canvas(self.card2, height=8, bg="#0b0f19", highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X, pady=(6, 6))

        self.quota_numbers_lbl = tk.Label(self.card2, text="0 / 1.000.000 token", fg=self.text_color, bg=self.card_bg, font=("JetBrains Mono", 8))
        self.quota_numbers_lbl.pack(anchor="w")

        # Bottom Row
        self.bottom_row = tk.Frame(self.body_frame, bg=self.bg_color)
        self.bottom_row.pack(fill=tk.X)

        self.total_lbl = tk.Label(self.bottom_row, text=f"Toplam: {self.total_prompts} prompt", fg=self.muted_color, bg=self.bg_color, font=("Segoe UI", 8))
        self.total_lbl.pack(side=tk.LEFT)

        self.cost_lbl = tk.Label(self.bottom_row, text="$0.0000", fg=self.cyan_color, bg=self.bg_color, font=("JetBrains Mono", 8, "bold"))
        self.cost_lbl.pack(side=tk.RIGHT)

        # --- COMPACT VIEW ---
        self.compact_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.compact_lbl = tk.Label(self.compact_frame, text="🪙 %100 Kalan | 0 tok", fg=self.success_color, bg=self.bg_color, font=("Segoe UI", 9, "bold"))
        self.compact_lbl.pack(side=tk.LEFT)

        self.update_display()

    def bind_events(self):
        for w in [self.main_container, self.header_frame, self.title_group, self.title_label, self.status_dot]:
            w.bind("<Button-1>", self.on_drag_start)
            w.bind("<B1-Motion>", self.on_drag_motion)

        self.btn_close.bind("<Button-1>", lambda e: self.root.destroy())
        self.btn_toggle.bind("<Button-1>", lambda e: self.toggle_compact())
        self.btn_settings.bind("<Button-1>", lambda e: self.open_settings_dialog())
        self.btn_capture.bind("<Button-1>", lambda e: self.manual_capture_from_clipboard())

        for btn in [self.btn_close, self.btn_toggle, self.btn_settings]:
            btn.bind("<Enter>", lambda e, b=btn: b.configure(fg=self.text_color))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(fg=self.muted_color))

        self.btn_capture.bind("<Enter>", lambda e: self.btn_capture.configure(bg="#1e293b", fg="#ffffff"))
        self.btn_capture.bind("<Leave>", lambda e: self.btn_capture.configure(bg=self.card_bg, fg=self.cyan_color))

    def on_drag_start(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def on_drag_motion(self, event):
        x = self.root.winfo_x() + (event.x - self.drag_x)
        y = self.root.winfo_y() + (event.y - self.drag_y)
        self.root.geometry(f"+{x}+{y}")

    def toggle_compact(self):
        self.is_compact = not self.is_compact
        if self.is_compact:
            self.body_frame.pack_forget()
            self.compact_frame.pack(fill=tk.X, pady=(2, 0))
            self.btn_toggle.configure(text="□")
            x, y = self.root.winfo_x(), self.root.winfo_y()
            self.root.geometry(f"270x60+{x}+{y}")
        else:
            self.compact_frame.pack_forget()
            self.body_frame.pack(fill=tk.BOTH, expand=True)
            self.btn_toggle.configure(text="—")
            x, y = self.root.winfo_x(), self.root.winfo_y()
            self.root.geometry(f"340x280+{x}+{y}")

    def draw_progress(self, ratio):
        self.progress_canvas.delete("all")
        width = self.progress_canvas.winfo_width()
        if width <= 1:
            width = 300
        height = 8

        self.progress_canvas.create_rectangle(0, 0, width, height, fill="#0b0f19", width=0)

        fill_width = int(width * ratio)
        if ratio > 0.40:
            fill_color = self.success_color
        elif ratio > 0.15:
            fill_color = self.warning_color
        else:
            fill_color = self.danger_color

        if fill_width > 0:
            self.progress_canvas.create_rectangle(0, 0, fill_width, height, fill=fill_color, width=0)

    def update_display(self):
        remaining = max(0, self.max_quota - self.spent_tokens)
        ratio = (remaining / self.max_quota) if self.max_quota > 0 else 0
        pct = ratio * 100

        self.source_badge.configure(text=f"Kaynak: {self.last_source}")
        self.model_badge.configure(text=self.selected_model.split("(")[0].strip())
        self.last_prompt_lbl.configure(text=f"Son: {self.last_prompt_summary}")

        color = self.success_color if pct > 30 else (self.warning_color if pct > 15 else self.danger_color)
        self.percent_lbl.configure(text=f"%{pct:.1f} Kalan", fg=color)
        self.quota_numbers_lbl.configure(text=f"{self.spent_tokens:,} / {self.max_quota:,} (Kalan: {remaining:,})")

        self.draw_progress(ratio)

        pricing = MODEL_PRICING.get(self.selected_model, MODEL_PRICING["GPT-4o (ChatGPT)"])
        cost = (self.spent_tokens / 1_000_000) * ((pricing["in"] + pricing["out"]) / 2)
        self.total_lbl.configure(text=f"Toplam: {self.total_prompts} prompt")
        self.cost_lbl.configure(text=f"${cost:.4f}")

        self.compact_lbl.configure(
            text=f"🪙 %{pct:.0f} Kalan | {self.spent_tokens/1000:.1f}k",
            fg=color
        )

    def pulse_feedback(self):
        self.status_dot.configure(fg="#38bdf8")
        self.root.after(300, lambda: self.status_dot.configure(fg=self.success_color))

    def record_prompt_event(self, prompt_text, source_name, matched_model=None):
        if not prompt_text or len(prompt_text.strip()) == 0:
            return

        in_tokens = estimate_tokens(prompt_text)
        out_tokens = self.estimated_output_tokens

        total_consumed = in_tokens + out_tokens
        self.spent_tokens += total_consumed
        self.total_prompts += 1
        self.last_source = source_name
        if matched_model:
            self.selected_model = matched_model

        snippet = prompt_text.replace("\n", " ").strip()
        if len(snippet) > 36:
            snippet = snippet[:36] + "..."
        self.last_prompt_summary = f"+{total_consumed:,} tok ({snippet})"

        self.save_state()
        self.update_display()
        self.pulse_feedback()

    def manual_capture_from_clipboard(self):
        try:
            txt = self.root.clipboard_get()
            if txt and txt.strip():
                active_win = get_active_window_title()
                app_name, matched_model = detect_source_from_title(active_win)
                self.record_prompt_event(txt, app_name, matched_model)
        except Exception:
            pass

    def check_clipboard(self):
        if not self.auto_clipboard_enabled:
            return

        try:
            txt = self.root.clipboard_get()
            if txt and txt != self.last_clipboard_text:
                self.last_clipboard_text = txt
                clean = txt.strip()
                if len(clean) >= 4:
                    active_win = get_active_window_title()
                    app_name, matched_model = detect_source_from_title(active_win)
                    # If copied from an AI app or if explicitly flagged
                    if app_name in ["ChatGPT", "Claude", "Gemini", "DeepSeek", "Perplexity", "Cursor AI"]:
                        self.record_prompt_event(clean, app_name, matched_model)
        except Exception:
            pass

    def check_antigravity_transcript(self):
        latest_file = find_latest_transcript()
        if not latest_file:
            return

        try:
            mtime = os.path.getmtime(latest_file)
            if mtime != self.last_transcript_mtime or latest_file != self.active_transcript_path:
                self.last_transcript_mtime = mtime
                self.active_transcript_path = latest_file
                data = parse_transcript(latest_file)
                if data and data.get("last_step"):
                    last = data["last_step"]
                    in_t = last.get("input", 0)
                    out_t = last.get("output", 0)
                    tot = in_t + out_t
                    self.last_source = "Antigravity"
                    self.selected_model = "Gemini 3.8 / 2.0 Flash"
                    self.spent_tokens = data.get("latest_context", self.spent_tokens)
                    self.total_prompts = data.get("prompt_count", self.total_prompts)
                    self.last_prompt_summary = f"+{in_t:,} in / +{out_t:,} out"
                    self.save_state()
                    self.update_display()
                    self.pulse_feedback()
        except Exception:
            pass

    def watch_loop(self):
        self.check_clipboard()
        self.check_antigravity_transcript()
        self.root.after(CHECK_INTERVAL_MS, self.watch_loop)

    def open_settings_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Widget Ayarları")
        dialog.attributes("-topmost", True)
        dialog.geometry("300x320")
        dialog.configure(bg=self.bg_color)
        dialog.resizable(False, False)

        tk.Label(dialog, text="Varsayılan Model:", fg=self.text_color, bg=self.bg_color, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
        model_var = tk.StringVar(value=self.selected_model)
        model_combo = ttk.Combobox(dialog, textvariable=model_var, values=list(MODEL_PRICING.keys()), state="readonly")
        model_combo.pack(fill=tk.X, padx=14)

        tk.Label(dialog, text="Maksimum Context / Bütçe:", fg=self.text_color, bg=self.bg_color, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(10, 2))
        quota_var = tk.StringVar(value=str(self.max_quota))
        quota_entry = tk.Entry(dialog, textvariable=quota_var, bg=self.card_bg, fg=self.text_color, insertbackground=self.text_color)
        quota_entry.pack(fill=tk.X, padx=14)

        tk.Label(dialog, text="Tahmini Yanıt Tokenı (Çıktı):", fg=self.text_color, bg=self.bg_color, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(10, 2))
        out_var = tk.StringVar(value=str(self.estimated_output_tokens))
        out_entry = tk.Entry(dialog, textvariable=out_var, bg=self.card_bg, fg=self.text_color, insertbackground=self.text_color)
        out_entry.pack(fill=tk.X, padx=14)

        auto_cb_var = tk.BooleanVar(value=self.auto_clipboard_enabled)
        cb = tk.Checkbutton(dialog, text="ChatGPT / AI Kopyalamalarını Otomatik Yakala", variable=auto_cb_var, bg=self.bg_color, fg=self.text_color, selectcolor=self.card_bg, activebackground=self.bg_color)
        cb.pack(anchor="w", padx=14, pady=(10, 0))

        def reset_spent():
            self.spent_tokens = 0
            self.total_prompts = 0
            self.last_prompt_summary = "Sıfırlandı"
            self.save_state()
            self.update_display()
            messagebox.showinfo("Bilgi", "Harcanan token sayacı sıfırlandı!", parent=dialog)

        btn_row = tk.Frame(dialog, bg=self.bg_color)
        btn_row.pack(fill=tk.X, padx=14, pady=(16, 0))

        tk.Button(btn_row, text="Sayacı Sıfırla", command=reset_spent, bg="#dc2626", fg="#ffffff", font=("Segoe UI", 8, "bold"), relief="flat", padx=6, pady=4).pack(side=tk.LEFT)

        def save_and_close():
            chosen_model = model_var.get()
            try:
                self.max_quota = int(quota_var.get().replace(",", "").replace(".", ""))
            except ValueError:
                self.max_quota = 1_000_000

            try:
                self.estimated_output_tokens = int(out_var.get())
            except ValueError:
                self.estimated_output_tokens = 350

            self.selected_model = chosen_model
            self.auto_clipboard_enabled = auto_cb_var.get()
            self.save_state()
            self.update_display()
            dialog.destroy()

        tk.Button(btn_row, text="Kaydet", command=save_and_close, bg=self.accent_color, fg="#ffffff", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=4).pack(side=tk.RIGHT)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = UniversalFloatingWidget()
    app.run()
