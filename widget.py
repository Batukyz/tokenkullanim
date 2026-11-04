"""
TokenKullanım - Masaüstü Yüzen Mini Widget (Desktop Floating HUD)
Kullandığınız AI modelindeki token harcamasını, her promptun ne kadar yediğini
ve kalan bakiye/kullanım hakkınızı masaüstünde daima en üstte gösterir.
"""

import os
import sys
import glob
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox

# --- CONFIG & DEFAULT VALUES ---
DEFAULT_QUOTA = 1_000_000  # 1 Million token default context/quota
CHECK_INTERVAL_MS = 1000   # Check transcript every 1 second

MODEL_PRICING = {
    "Gemini 3.8 / 2.0 Flash": {"in": 0.10, "out": 0.40, "max_context": 1_000_000},
    "Gemini 1.5 Pro": {"in": 1.25, "out": 5.00, "max_context": 2_000_000},
    "GPT-4o": {"in": 2.50, "out": 10.00, "max_context": 128_000},
    "GPT-4o-mini": {"in": 0.15, "out": 0.60, "max_context": 128_000},
    "Claude 3.5 Sonnet": {"in": 3.00, "out": 15.00, "max_context": 200_000},
    "DeepSeek-V3": {"in": 0.14, "out": 0.28, "max_context": 128_000},
    "Özel Model": {"in": 1.00, "out": 2.00, "max_context": 1_000_000},
}

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
    total_cache = 0
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
                    total_cache += cache_t
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
            "total_cache": total_cache,
            "latest_context": latest_context,
            "prompt_count": prompt_count
        }
    except Exception as e:
        return None


class FloatingTokenWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TokenKullanım Widget")
        self.root.overrideredirect(True)      # Borderless
        self.root.attributes("-topmost", True) # Always-on-top

        # Modern Dark Color Palette
        self.bg_color = "#0f172a"        # Slate 900
        self.card_bg = "#1e293b"         # Slate 800
        self.card_border = "#334155"     # Slate 700
        self.text_color = "#f8fafc"      # Slate 50
        self.muted_color = "#94a3b8"     # Slate 400
        self.accent_color = "#818cf8"    # Indigo
        self.cyan_color = "#22d3ee"      # Cyan
        self.success_color = "#34d399"   # Emerald
        self.warning_color = "#fbbf24"   # Amber
        self.danger_color = "#f87171"    # Rose

        self.root.configure(bg=self.bg_color)

        # State
        self.selected_model = "Gemini 3.8 / 2.0 Flash"
        self.max_quota = MODEL_PRICING[self.selected_model]["max_context"]
        self.last_transcript_mtime = 0
        self.active_transcript_path = None
        self.is_compact = False

        # Drag tracking
        self.drag_x = 0
        self.drag_y = 0

        # Position at top-right of screen
        screen_w = self.root.winfo_screenwidth()
        init_x = screen_w - 360
        init_y = 60
        self.root.geometry(f"340x250+{init_x}+{init_y}")

        self.setup_ui()
        self.bind_events()

        # Initial probe
        self.check_transcript_loop()

    def setup_ui(self):
        # Outer Border Frame
        self.border_frame = tk.Frame(self.root, bg=self.card_border, padx=1, pady=1)
        self.border_frame.pack(fill=tk.BOTH, expand=True)

        self.main_container = tk.Frame(self.border_frame, bg=self.bg_color, padx=14, pady=12)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # --- HEADER BAR ---
        self.header_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))

        # Title & Status Dot
        self.title_group = tk.Frame(self.header_frame, bg=self.bg_color)
        self.title_group.pack(side=tk.LEFT)

        self.status_dot = tk.Label(self.title_group, text="●", fg=self.success_color, bg=self.bg_color, font=("Segoe UI", 11, "bold"))
        self.status_dot.pack(side=tk.LEFT, padx=(0, 5))

        self.title_label = tk.Label(self.title_group, text="TokenKullanım", fg=self.text_color, bg=self.bg_color, font=("Segoe UI", 10, "bold"))
        self.title_label.pack(side=tk.LEFT)

        # Header Buttons
        self.btn_group = tk.Frame(self.header_frame, bg=self.bg_color)
        self.btn_group.pack(side=tk.RIGHT)

        self.btn_settings = tk.Label(self.btn_group, text="⚙", fg=self.muted_color, bg=self.bg_color, font=("Segoe UI", 10), cursor="hand2")
        self.btn_settings.pack(side=tk.LEFT, padx=4)

        self.btn_toggle = tk.Label(self.btn_group, text="—", fg=self.muted_color, bg=self.bg_color, font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.btn_toggle.pack(side=tk.LEFT, padx=4)

        self.btn_close = tk.Label(self.btn_group, text="✕", fg=self.muted_color, bg=self.bg_color, font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.btn_close.pack(side=tk.LEFT, padx=4)

        # --- EXPANDED BODY CONTAINER ---
        self.body_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.body_frame.pack(fill=tk.BOTH, expand=True)

        # Model & Last Step Card
        self.card1 = tk.Frame(self.body_frame, bg=self.card_bg, padx=10, pady=8)
        self.card1.pack(fill=tk.X, pady=(0, 8))

        self.model_lbl = tk.Label(self.card1, text=f"Model: {self.selected_model}", fg=self.accent_color, bg=self.card_bg, font=("Segoe UI", 8, "bold"))
        self.model_lbl.pack(anchor="w")

        self.last_prompt_lbl = tk.Label(self.card1, text="Son Prompt: Dinleniyor...", fg=self.text_color, bg=self.card_bg, font=("Segoe UI", 9, "bold"))
        self.last_prompt_lbl.pack(anchor="w", pady=(2, 0))

        # Progress & Quota Card
        self.card2 = tk.Frame(self.body_frame, bg=self.card_bg, padx=10, pady=8)
        self.card2.pack(fill=tk.X, pady=(0, 8))

        self.quota_header_frame = tk.Frame(self.card2, bg=self.card_bg)
        self.quota_header_frame.pack(fill=tk.X)

        self.quota_title = tk.Label(self.quota_header_frame, text="Kalan Kota / Bağlam:", fg=self.muted_color, bg=self.card_bg, font=("Segoe UI", 8))
        self.quota_title.pack(side=tk.LEFT)

        self.percent_lbl = tk.Label(self.quota_header_frame, text="%100 Kalan", fg=self.success_color, bg=self.card_bg, font=("Segoe UI", 8, "bold"))
        self.percent_lbl.pack(side=tk.RIGHT)

        # Canvas Progress Bar
        self.progress_canvas = tk.Canvas(self.card2, height=8, bg="#090d16", highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X, pady=(6, 6))

        self.quota_numbers_lbl = tk.Label(self.card2, text="0 / 1.000.000 token", fg=self.text_color, bg=self.card_bg, font=("JetBrains Mono", 8))
        self.quota_numbers_lbl.pack(anchor="w")

        # Bottom Stats Row
        self.bottom_row = tk.Frame(self.body_frame, bg=self.bg_color)
        self.bottom_row.pack(fill=tk.X)

        self.total_lbl = tk.Label(self.bottom_row, text="Toplam: 0 prompt", fg=self.muted_color, bg=self.bg_color, font=("Segoe UI", 8))
        self.total_lbl.pack(side=tk.LEFT)

        self.cost_lbl = tk.Label(self.bottom_row, text="$0.0000", fg=self.cyan_color, bg=self.bg_color, font=("JetBrains Mono", 8, "bold"))
        self.cost_lbl.pack(side=tk.RIGHT)

        # --- COMPACT PILL BAR (Hidden by default) ---
        self.compact_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.compact_lbl = tk.Label(self.compact_frame, text="🪙 0 / 1M (%100)", fg=self.success_color, bg=self.bg_color, font=("Segoe UI", 9, "bold"))
        self.compact_lbl.pack(side=tk.LEFT)

    def bind_events(self):
        # Dragging on headers and container
        for widget in [self.main_container, self.header_frame, self.title_group, self.title_label, self.status_dot]:
            widget.bind("<Button-1>", self.on_drag_start)
            widget.bind("<B1-Motion>", self.on_drag_motion)

        # Header buttons
        self.btn_close.bind("<Button-1>", lambda e: self.root.destroy())
        self.btn_toggle.bind("<Button-1>", lambda e: self.toggle_compact())
        self.btn_settings.bind("<Button-1>", lambda e: self.open_settings_dialog())

        # Hover effects
        for btn in [self.btn_close, self.btn_toggle, self.btn_settings]:
            btn.bind("<Enter>", lambda e, b=btn: b.configure(fg=self.text_color))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(fg=self.muted_color))

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
            w = self.root.winfo_x()
            h = self.root.winfo_y()
            self.root.geometry(f"260x60+{w}+{h}")
        else:
            self.compact_frame.pack_forget()
            self.body_frame.pack(fill=tk.BOTH, expand=True)
            self.btn_toggle.configure(text="—")
            w = self.root.winfo_x()
            h = self.root.winfo_y()
            self.root.geometry(f"340x250+{w}+{h}")

    def draw_progress(self, ratio):
        self.progress_canvas.delete("all")
        width = self.progress_canvas.winfo_width()
        if width <= 1:
            width = 300
        height = 8

        # Background track
        self.progress_canvas.create_rectangle(0, 0, width, height, fill="#1e293b", width=0)

        # Dynamic color
        fill_width = int(width * ratio)
        if ratio > 0.40:
            fill_color = self.success_color
        elif ratio > 0.15:
            fill_color = self.warning_color
        else:
            fill_color = self.danger_color

        if fill_width > 0:
            self.progress_canvas.create_rectangle(0, 0, fill_width, height, fill=fill_color, width=0)

    def update_ui_with_data(self, data):
        if not data:
            self.status_dot.configure(fg=self.muted_color)
            self.last_prompt_lbl.configure(text="Son Prompt: Bekleniyor...")
            return

        self.status_dot.configure(fg=self.success_color)

        # Last prompt stats
        last = data.get("last_step")
        if last:
            in_t = last.get("input", 0)
            out_t = last.get("output", 0)
            self.last_prompt_lbl.configure(
                text=f"Son Prompt: +{in_t:,} girdi / +{out_t:,} çıktı"
            )
        else:
            self.last_prompt_lbl.configure(text="Son Prompt: Henüz yok")

        # Context & Remaining
        ctx = data.get("latest_context", 0)
        remaining = max(0, self.max_quota - ctx)
        ratio = (remaining / self.max_quota) if self.max_quota > 0 else 0
        pct = ratio * 100

        self.percent_lbl.configure(
            text=f"%{pct:.1f} Kalan",
            fg=self.success_color if pct > 30 else (self.warning_color if pct > 15 else self.danger_color)
        )
        self.quota_numbers_lbl.configure(
            text=f"{ctx:,} / {self.max_quota:,} token (Kalan: {remaining:,})"
        )

        self.draw_progress(ratio)

        # Cost & Totals
        pricing = MODEL_PRICING.get(self.selected_model, MODEL_PRICING["Özel Model"])
        tot_in = data.get("total_input", 0)
        tot_out = data.get("total_output", 0)
        cost = (tot_in / 1_000_000 * pricing["in"]) + (tot_out / 1_000_000 * pricing["out"])

        count = data.get("prompt_count", 0)
        self.total_lbl.configure(text=f"Toplam: {count} prompt ({tot_in + tot_out:,} tok)")
        self.cost_lbl.configure(text=f"${cost:.4f}")

        # Compact label update
        self.compact_lbl.configure(
            text=f"🪙 {ctx/1000:.1f}k / {self.max_quota/1000:.0f}k (%{pct:.0f})",
            fg=self.success_color if pct > 30 else (self.warning_color if pct > 15 else self.danger_color)
        )

    def check_transcript_loop(self):
        latest_file = find_latest_transcript()
        if latest_file:
            try:
                mtime = os.path.getmtime(latest_file)
                if mtime != self.last_transcript_mtime or latest_file != self.active_transcript_path:
                    self.last_transcript_mtime = mtime
                    self.active_transcript_path = latest_file
                    data = parse_transcript(latest_file)
                    self.update_ui_with_data(data)
            except Exception:
                pass
        else:
            self.status_dot.configure(fg=self.muted_color)

        self.root.after(CHECK_INTERVAL_MS, self.check_transcript_loop)

    def open_settings_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Widget Ayarları")
        dialog.attributes("-topmost", True)
        dialog.geometry("280x260")
        dialog.configure(bg=self.bg_color)
        dialog.resizable(False, False)

        tk.Label(dialog, text="Kullanılan Model:", fg=self.text_color, bg=self.bg_color, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        model_var = tk.StringVar(value=self.selected_model)
        model_combo = ttk.Combobox(dialog, textvariable=model_var, values=list(MODEL_PRICING.keys()), state="readonly")
        model_combo.pack(fill=tk.X, padx=14)

        tk.Label(dialog, text="Maksimum Context / Kota:", fg=self.text_color, bg=self.bg_color, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        quota_var = tk.StringVar(value=str(self.max_quota))
        quota_entry = tk.Entry(dialog, textvariable=quota_var, bg=self.card_bg, fg=self.text_color, insertbackground=self.text_color)
        quota_entry.pack(fill=tk.X, padx=14)

        def save_and_close():
            chosen_model = model_var.get()
            try:
                q = int(quota_var.get().replace(",", "").replace(".", ""))
            except ValueError:
                q = MODEL_PRICING[chosen_model]["max_context"]
            self.selected_model = chosen_model
            self.max_quota = q
            self.model_lbl.configure(text=f"Model: {self.selected_model}")
            dialog.destroy()
            data = parse_transcript(self.active_transcript_path)
            self.update_ui_with_data(data)

        tk.Button(dialog, text="Kaydet", command=save_and_close, bg=self.accent_color, fg="#ffffff", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=4).pack(pady=18)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = FloatingTokenWidget()
    app.run()
