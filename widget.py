"""
TokenKullanım - Çoklu Model & Otomatik Algılayıcı Masaüstü Yüzen Widget
IDE (Gemini 3.8 Flash), ChatGPT, Claude ve diğer AI araçlarındaki promptları
tamamen otomatik olarak algılar ve ilgili modelin kotasını/harcamasını gösterir.
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

CHECK_INTERVAL_MS = 500  # 500ms for instant responsiveness
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "widget_state.json")

# Default profiles for each environment
DEFAULT_PROFILES = {
    "gemini_ide": {
        "id": "gemini_ide",
        "name": "Gemini 3.8 Flash",
        "env": "IDE (Antigravity)",
        "tag": "IDE",
        "max_quota": 1_000_000,
        "spent_tokens": 0,
        "last_in": 0,
        "last_out": 0,
        "last_summary": "Dinleniyor...",
        "total_prompts": 0,
        "price_in": 0.10,
        "price_out": 0.40,
        "color": "#10b981"  # Emerald
    },
    "chatgpt": {
        "id": "chatgpt",
        "name": "GPT-4o",
        "env": "ChatGPT App / Web",
        "tag": "ChatGPT",
        "max_quota": 128_000,
        "spent_tokens": 0,
        "last_in": 0,
        "last_out": 0,
        "last_summary": "Dinleniyor...",
        "total_prompts": 0,
        "price_in": 2.50,
        "price_out": 10.00,
        "color": "#06b6d4"  # Cyan
    },
    "claude": {
        "id": "claude",
        "name": "Claude 3.5 Sonnet",
        "env": "Claude App / Web",
        "tag": "Claude",
        "max_quota": 200_000,
        "spent_tokens": 0,
        "last_in": 0,
        "last_out": 0,
        "last_summary": "Dinleniyor...",
        "total_prompts": 0,
        "price_in": 3.00,
        "price_out": 15.00,
        "color": "#f59e0b"  # Amber
    }
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

def detect_app_from_title(title):
    t_lower = (title or "").lower()
    if "chatgpt" in t_lower or "openai" in t_lower:
        return "chatgpt", "ChatGPT"
    elif "claude" in t_lower or "anthropic" in t_lower:
        return "claude", "Claude"
    elif "gemini" in t_lower or "aistudio" in t_lower:
        return "gemini_ide", "Gemini Web"
    elif "antigravity" in t_lower or "budget-control" in t_lower or "tokenkullanim" in t_lower:
        return "gemini_ide", "IDE (Gemini)"
    return None, None

def estimate_tokens(text):
    if not text:
        return 0
    words = re.findall(r"\S+|\s+", text)
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
            "total_input": total_input,
            "total_output": total_output,
            "latest_context": latest_context,
            "prompt_count": prompt_count
        }
    except Exception:
        return None


class AutoDetectHUDWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TokenKullanım Auto HUD")
        self.root.overrideredirect(True)       # Frameless
        self.root.attributes("-topmost", True)  # Always on top

        # Colors
        self.bg_color = "#090d16"         # Darker Slate
        self.card_bg = "#121a2c"          # Slate Container
        self.card_border = "#22314e"      # Border
        self.text_color = "#f8fafc"       # White
        self.muted_color = "#94a3b8"      # Gray
        self.accent_color = "#818cf8"     # Indigo
        self.success_color = "#10b981"    # Green
        self.warning_color = "#f59e0b"    # Yellow
        self.danger_color = "#ef4444"     # Red

        self.root.configure(bg=self.bg_color)

        # Multi-Profile Storage
        self.profiles = json.loads(json.dumps(DEFAULT_PROFILES))
        self.active_profile_id = "gemini_ide"
        self.load_state()

        # Engine states
        self.last_transcript_mtime = 0
        self.active_transcript_path = None
        self.last_clipboard_text = ""
        self.estimated_output_tokens = 350
        self.is_compact = False

        # Dragging
        self.drag_x = 0
        self.drag_y = 0

        # Position at top-right
        screen_w = self.root.winfo_screenwidth()
        init_x = screen_w - 380
        init_y = 45
        self.root.geometry(f"360x300+{init_x}+{init_y}")

        self.setup_ui()
        self.bind_events()

        # Initial IDE transcript sync
        self.sync_ide_transcript(force=True)

        # Launch auto-watcher loop
        self.auto_watcher_loop()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.active_profile_id = data.get("active_profile_id", "gemini_ide")
                    saved_profs = data.get("profiles", {})
                    for pid, pdata in saved_profs.items():
                        if pid in self.profiles:
                            self.profiles[pid].update(pdata)
            except Exception:
                pass

    def save_state(self):
        try:
            data = {
                "active_profile_id": self.active_profile_id,
                "profiles": self.profiles
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
        self.header_frame.pack(fill=tk.X, pady=(0, 8))

        self.title_group = tk.Frame(self.header_frame, bg=self.bg_color)
        self.title_group.pack(side=tk.LEFT)

        self.status_dot = tk.Label(self.title_group, text="●", fg=self.success_color, bg=self.bg_color, font=("Segoe UI", 11, "bold"))
        self.status_dot.pack(side=tk.LEFT, padx=(0, 5))

        self.title_label = tk.Label(self.title_group, text="TokenKullanım Auto HUD", fg=self.text_color, bg=self.bg_color, font=("Segoe UI", 10, "bold"))
        self.title_label.pack(side=tk.LEFT)

        self.btn_group = tk.Frame(self.header_frame, bg=self.bg_color)
        self.btn_group.pack(side=tk.RIGHT)

        self.btn_capture = tk.Label(self.btn_group, text="📋 Al", fg="#38bdf8", bg=self.card_bg, font=("Segoe UI", 8, "bold"), padx=5, pady=2, cursor="hand2")
        self.btn_capture.pack(side=tk.LEFT, padx=3)

        self.btn_settings = tk.Label(self.btn_group, text="⚙", fg=self.muted_color, bg=self.bg_color, font=("Segoe UI", 10), cursor="hand2")
        self.btn_settings.pack(side=tk.LEFT, padx=3)

        self.btn_toggle = tk.Label(self.btn_group, text="—", fg=self.muted_color, bg=self.bg_color, font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.btn_toggle.pack(side=tk.LEFT, padx=3)

        self.btn_close = tk.Label(self.btn_group, text="✕", fg=self.muted_color, bg=self.bg_color, font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.btn_close.pack(side=tk.LEFT, padx=3)

        # --- MULTI-MODEL PROFILE SELECTOR TABS ---
        self.tabs_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.tabs_frame.pack(fill=tk.X, pady=(0, 10))

        self.tab_buttons = {}
        for pid in ["gemini_ide", "chatgpt", "claude"]:
            p = self.profiles[pid]
            lbl = tk.Label(
                self.tabs_frame,
                text=p["tag"],
                fg=self.muted_color,
                bg=self.card_bg,
                font=("Segoe UI", 8, "bold"),
                padx=8,
                pady=3,
                cursor="hand2"
            )
            lbl.pack(side=tk.LEFT, padx=(0, 5))
            lbl.bind("<Button-1>", lambda e, p_id=pid: self.switch_profile(p_id))
            self.tab_buttons[pid] = lbl

        # --- EXPANDED BODY ---
        self.body_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.body_frame.pack(fill=tk.BOTH, expand=True)

        # Card 1: Active Model & Last Action
        self.card1 = tk.Frame(self.body_frame, bg=self.card_bg, padx=10, pady=8)
        self.card1.pack(fill=tk.X, pady=(0, 8))

        self.card1_top = tk.Frame(self.card1, bg=self.card_bg)
        self.card1_top.pack(fill=tk.X)

        self.active_badge = tk.Label(self.card1_top, text="Aktif: IDE", fg=self.success_color, bg="#0d231b", font=("Segoe UI", 8, "bold"), padx=6, pady=2)
        self.active_badge.pack(side=tk.LEFT)

        self.model_lbl = tk.Label(self.card1_top, text="Gemini 3.8 Flash", fg=self.text_color, bg=self.card_bg, font=("Segoe UI", 9, "bold"))
        self.model_lbl.pack(side=tk.RIGHT)

        self.last_prompt_lbl = tk.Label(self.card1, text="Son: Dinleniyor...", fg=self.muted_color, bg=self.card_bg, font=("Segoe UI", 8, "bold"), anchor="w", justify="left")
        self.last_prompt_lbl.pack(fill=tk.X, pady=(5, 0))

        # Card 2: Quota & Context Health
        self.card2 = tk.Frame(self.body_frame, bg=self.card_bg, padx=10, pady=8)
        self.card2.pack(fill=tk.X, pady=(0, 8))

        self.card2_top = tk.Frame(self.card2, bg=self.card_bg)
        self.card2_top.pack(fill=tk.X)

        self.quota_label = tk.Label(self.card2_top, text="Kalan Kullanım Kotası:", fg=self.muted_color, bg=self.card_bg, font=("Segoe UI", 8))
        self.quota_label.pack(side=tk.LEFT)

        self.percent_lbl = tk.Label(self.card2_top, text="%100 Kalan", fg=self.success_color, bg=self.card_bg, font=("Segoe UI", 8, "bold"))
        self.percent_lbl.pack(side=tk.RIGHT)

        # Progress bar
        self.progress_canvas = tk.Canvas(self.card2, height=8, bg="#090d16", highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X, pady=(6, 6))

        self.numbers_lbl = tk.Label(self.card2, text="0 / 1.000.000 token", fg=self.text_color, bg=self.card_bg, font=("JetBrains Mono", 8))
        self.numbers_lbl.pack(anchor="w")

        # Bottom Row: Total Prompts & Cost
        self.bottom_row = tk.Frame(self.body_frame, bg=self.bg_color)
        self.bottom_row.pack(fill=tk.X)

        self.totals_lbl = tk.Label(self.bottom_row, text="Toplam: 0 prompt", fg=self.muted_color, bg=self.bg_color, font=("Segoe UI", 8))
        self.totals_lbl.pack(side=tk.LEFT)

        self.cost_lbl = tk.Label(self.bottom_row, text="$0.0000", fg="#38bdf8", bg=self.bg_color, font=("JetBrains Mono", 8, "bold"))
        self.cost_lbl.pack(side=tk.RIGHT)

        # --- COMPACT VIEW (Hidden by default) ---
        self.compact_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.compact_lbl = tk.Label(self.compact_frame, text="🪙 IDE: %100 Kalan", fg=self.success_color, bg=self.bg_color, font=("Segoe UI", 9, "bold"))
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
        self.btn_capture.bind("<Leave>", lambda e: self.btn_capture.configure(bg=self.card_bg, fg="#38bdf8"))

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
            self.tabs_frame.pack_forget()
            self.compact_frame.pack(fill=tk.X, pady=(2, 0))
            self.btn_toggle.configure(text="□")
            x, y = self.root.winfo_x(), self.root.winfo_y()
            self.root.geometry(f"280x60+{x}+{y}")
        else:
            self.compact_frame.pack_forget()
            self.tabs_frame.pack(fill=tk.X, pady=(0, 10))
            self.body_frame.pack(fill=tk.BOTH, expand=True)
            self.btn_toggle.configure(text="—")
            x, y = self.root.winfo_x(), self.root.winfo_y()
            self.root.geometry(f"360x300+{x}+{y}")

    def switch_profile(self, profile_id, flash=False):
        if profile_id not in self.profiles:
            return
        self.active_profile_id = profile_id

        # Update tab visual highlights
        for pid, btn in self.tab_buttons.items():
            if pid == profile_id:
                btn.configure(bg="#223555", fg=self.profiles[pid]["color"])
            else:
                btn.configure(bg=self.card_bg, fg=self.muted_color)

        self.update_display()
        if flash:
            self.pulse_feedback()

    def draw_progress(self, ratio, color):
        self.progress_canvas.delete("all")
        width = self.progress_canvas.winfo_width()
        if width <= 1:
            width = 320
        height = 8

        self.progress_canvas.create_rectangle(0, 0, width, height, fill="#090d16", width=0)

        fill_width = int(width * ratio)
        if fill_width > 0:
            self.progress_canvas.create_rectangle(0, 0, fill_width, height, fill=color, width=0)

    def update_display(self):
        p = self.profiles[self.active_profile_id]

        remaining = max(0, p["max_quota"] - p["spent_tokens"])
        ratio = (remaining / p["max_quota"]) if p["max_quota"] > 0 else 0
        pct = ratio * 100

        self.active_badge.configure(text=f"Kaynak: {p['env']}", fg=p["color"])
        self.model_lbl.configure(text=p["name"])
        self.last_prompt_lbl.configure(text=f"Son: {p['last_summary']}")

        health_color = self.success_color if pct > 30 else (self.warning_color if pct > 15 else self.danger_color)
        self.percent_lbl.configure(text=f"%{pct:.1f} Kalan", fg=health_color)
        self.numbers_lbl.configure(text=f"{p['spent_tokens']:,} / {p['max_quota']:,} (Kalan: {remaining:,})")

        self.draw_progress(ratio, health_color)

        # Cost
        cost = (p["spent_tokens"] / 1_000_000) * ((p["price_in"] + p["price_out"]) / 2)
        self.totals_lbl.configure(text=f"Toplam: {p['total_prompts']} prompt")
        self.cost_lbl.configure(text=f"${cost:.4f}")

        # Compact label
        self.compact_lbl.configure(
            text=f"🪙 {p['tag']}: %{pct:.0f} Kalan ({p['spent_tokens']/1000:.1f}k)",
            fg=health_color
        )

    def pulse_feedback(self):
        self.status_dot.configure(fg="#38bdf8")
        self.root.after(300, lambda: self.status_dot.configure(fg=self.success_color))

    def manual_capture_from_clipboard(self):
        try:
            txt = self.root.clipboard_get()
            if txt and txt.strip():
                active_win = get_active_window_title()
                app_id, app_name = detect_app_from_title(active_win)
                target_id = app_id if app_id else self.active_profile_id
                self.record_external_prompt(txt, target_id)
        except Exception:
            pass

    def record_external_prompt(self, prompt_text, profile_id):
        if not prompt_text or len(prompt_text.strip()) == 0:
            return

        p = self.profiles[profile_id]
        in_tokens = estimate_tokens(prompt_text)
        out_tokens = self.estimated_output_tokens
        total_consumed = in_tokens + out_tokens

        p["spent_tokens"] += total_consumed
        p["total_prompts"] += 1
        p["last_in"] = in_tokens
        p["last_out"] = out_tokens

        snippet = prompt_text.replace("\n", " ").strip()
        if len(snippet) > 30:
            snippet = snippet[:30] + "..."
        p["last_summary"] = f"+{total_consumed:,} tok ({snippet})"

        self.save_state()
        self.switch_profile(profile_id, flash=True)

    def sync_ide_transcript(self, force=False):
        latest_file = find_latest_transcript()
        if not latest_file:
            return

        try:
            mtime = os.path.getmtime(latest_file)
            if force or mtime != self.last_transcript_mtime or latest_file != self.active_transcript_path:
                self.last_transcript_mtime = mtime
                self.active_transcript_path = latest_file

                data = parse_transcript(latest_file)
                if data and data.get("last_step"):
                    last = data["last_step"]
                    in_t = last.get("input", 0)
                    out_t = last.get("output", 0)
                    tot = in_t + out_t

                    p = self.profiles["gemini_ide"]
                    p["spent_tokens"] = data.get("latest_context", p["spent_tokens"])
                    p["total_prompts"] = data.get("prompt_count", p["total_prompts"])
                    p["last_in"] = in_t
                    p["last_out"] = out_t
                    p["last_summary"] = f"+{in_t:,} in / +{out_t:,} out"

                    self.save_state()
                    # Automatically flip active view to IDE if an IDE event occurred
                    if not force:
                        self.switch_profile("gemini_ide", flash=True)
                    else:
                        self.update_display()
        except Exception:
            pass

    def check_active_window_and_clipboard(self):
        # 1. Check window title
        active_title = get_active_window_title()
        app_id, app_name = detect_app_from_title(active_title)

        # 2. Check clipboard
        try:
            txt = self.root.clipboard_get()
            if txt and txt != self.last_clipboard_text:
                self.last_clipboard_text = txt
                clean = txt.strip()
                if len(clean) >= 4:
                    if app_id in ["chatgpt", "claude"]:
                        self.record_external_prompt(clean, app_id)
                    elif app_id == "gemini_ide":
                        # Handled by transcript watcher
                        pass
        except Exception:
            pass

    def auto_watcher_loop(self):
        # Run Engine A: IDE live transcript watcher
        self.sync_ide_transcript()

        # Run Engine B: Window and clipboard watcher
        self.check_active_window_and_clipboard()

        self.root.after(CHECK_INTERVAL_MS, self.auto_watcher_loop)

    def open_settings_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Kota ve Model Ayarları")
        dialog.attributes("-topmost", True)
        dialog.geometry("320x330")
        dialog.configure(bg=self.bg_color)
        dialog.resizable(False, False)

        tk.Label(dialog, text="Profil Ayarları:", fg=self.text_color, bg=self.bg_color, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(12, 6))

        entries = {}
        for pid, p in self.profiles.items():
            row = tk.Frame(dialog, bg=self.bg_color)
            row.pack(fill=tk.X, padx=14, pady=4)

            tk.Label(row, text=f"{p['tag']} Kota:", fg=self.text_color, bg=self.bg_color, font=("Segoe UI", 8)).pack(side=tk.LEFT)
            var = tk.StringVar(value=str(p["max_quota"]))
            e = tk.Entry(row, textvariable=var, bg=self.card_bg, fg=self.text_color, width=14, insertbackground=self.text_color)
            e.pack(side=tk.RIGHT)
            entries[pid] = var

        def reset_all_spent():
            for pid in self.profiles:
                self.profiles[pid]["spent_tokens"] = 0
                self.profiles[pid]["total_prompts"] = 0
                self.profiles[pid]["last_summary"] = "Sıfırlandı"
            self.save_state()
            self.update_display()
            messagebox.showinfo("Bilgi", "Tüm profillerin token sayaçları sıfırlandı!", parent=dialog)

        btn_row = tk.Frame(dialog, bg=self.bg_color)
        btn_row.pack(fill=tk.X, padx=14, pady=(20, 0))

        tk.Button(btn_row, text="Tümünü Sıfırla", command=reset_all_spent, bg="#dc2626", fg="#ffffff", font=("Segoe UI", 8, "bold"), relief="flat", padx=6, pady=4).pack(side=tk.LEFT)

        def save_and_close():
            for pid, var in entries.items():
                try:
                    self.profiles[pid]["max_quota"] = int(var.get().replace(",", "").replace(".", ""))
                except ValueError:
                    pass
            self.save_state()
            self.update_display()
            dialog.destroy()

        tk.Button(btn_row, text="Kaydet", command=save_and_close, bg=self.accent_color, fg="#ffffff", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=4).pack(side=tk.RIGHT)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AutoDetectHUDWidget()
    app.run()
