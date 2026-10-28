"""
Teleprompter by tourrr - Invisible Floating Teleprompter Overlay
Style: Glassmorphic Floating Overlay with DWM Rounded Corners & 1:1 Gestures
Anti-Screen-Share via Win32 SetWindowDisplayAffinity (Invisible to Teams/Zoom/Meet/OBS)
"""

import sys
import os
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
from PIL import Image, ImageDraw

# 1. Immediately hide any stray console window
try:
    hwnd_console = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd_console:
        ctypes.windll.user32.ShowWindow(hwnd_console, 0)
except Exception:
    pass

import pystray

# Win32 Constants
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
VK_LBUTTON = 0x01
VK_MBUTTON = 0x04
VK_SHIFT = 0x10
KEY_PRESSED_MASK = 0x8000
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Windows 10 2004+ / Windows 11 Exclude from screen share

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SLIDES_JSON_PATH = os.path.join(SCRIPT_DIR, "slides_data.json")

DEFAULT_SLIDES = [
    {
        "id": 1,
        "title": "Slide 01: Selamat Datang di Teleprompter by tourrr",
        "duration": "30 Detik",
        "script": "Selamat datang di Teleprompter by tourrr. Tekan tombol panah kanan atau scroll mouse untuk berpindah slide, dan tekan Ctrl+E untuk membuka Slide Manager & mengedit naskah Anda."
    }
]

def create_tray_icon_image():
    """Load high quality emerald teleprompter icon from app_icon.png."""
    icon_png = os.path.join(SCRIPT_DIR, "app_icon.png")
    if os.path.exists(icon_png):
        try:
            return Image.open(icon_png).resize((64, 64), Image.Resampling.LANCZOS)
        except Exception:
            pass

    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, 60, 60), fill="#059669", outline="#34d399", width=3)
    draw.rectangle((18, 16, 46, 48), fill="#f8fafc")
    draw.line((24, 24, 40, 24), fill="#059669", width=2)
    draw.line((24, 30, 40, 30), fill="#059669", width=2)
    draw.line((24, 36, 40, 36), fill="#059669", width=2)
    draw.line((24, 42, 34, 42), fill="#059669", width=2)
    return img

class SpoLyricsTeleprompter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Teleprompter by tourrr")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        
        ico_file = os.path.join(SCRIPT_DIR, "app_icon.ico")
        if os.path.exists(ico_file):
            try:
                self.root.iconbitmap(ico_file)
            except Exception:
                pass
        
        # Color & Typography Palette (Glassmorphism Emerald Dark)
        self.accent_color = "#10b981"  # Emerald Accent
        self.bg_color = "#0b131e"      # Deep Glass Slate
        self.text_color = "#f8fafc"    # Bright Text
        
        self.opacity = 0.88
        self.root.attributes("-alpha", self.opacity)
        self.root.geometry("480x160+120+80")
        self.root.configure(bg=self.bg_color)

        # DWM Rounded Corners
        self.root.update_idletasks()
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if not hwnd:
                hwnd = self.root.winfo_id()
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(ctypes.c_int(2)), ctypes.sizeof(ctypes.c_int)
            )
        except Exception:
            pass

        # State Variables
        self.font_cur = 13
        self.is_pinned = False
        self.ghost_mode = False
        self.show_title = True
        self.timer_running = False
        self.timer_seconds = 0
        self.current_idx = 0
        self._offset_x = 0
        self._offset_y = 0
        self.resize_start_x = 0
        self.resize_start_y = 0
        self.orig_w = 480
        self.orig_h = 160
        self.last_scroll_time = 0

        # Load slides data
        self.load_slides()

        # Build UI Elements (SpoLyrics Layout)
        self.setup_ui()

        # Apply Anti-Screen-Share (Exclude from Teams/Zoom/OBS)
        self.apply_anti_capture()

        # Bind All SpoLyrics Gestures & Shortcuts
        self.bind_events()

        # Render first slide
        self.render_slide()

        # Start System Tray Icon
        self.start_system_tray()

    def load_slides(self):
        try:
            if os.path.exists(SLIDES_JSON_PATH):
                with open(SLIDES_JSON_PATH, "r", encoding="utf-8") as f:
                    self.slides = json.load(f)
            else:
                self.slides = DEFAULT_SLIDES
        except Exception:
            self.slides = DEFAULT_SLIDES
        self.reindex_slides()

    def reindex_slides(self):
        """Ensure all slides have sequential 1..N IDs"""
        for idx, s in enumerate(self.slides):
            s["id"] = idx + 1

    def save_slides_to_file(self):
        self.reindex_slides()
        try:
            with open(SLIDES_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(self.slides, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            return True
        except Exception:
            return False

    def apply_anti_capture(self):
        try:
            self.root.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if not hwnd:
                hwnd = self.root.winfo_id()
            res = ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            if res == 0:
                ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_MONITOR)
        except Exception:
            pass

    def setup_ui(self):
        # 1. Slide Title (Header pill at top center)
        self.lbl_title = tk.Label(
            self.root,
            text="",
            fg=self.accent_color,
            bg=self.bg_color,
            font=("Segoe UI", 9, "bold"),
            justify="center",
            wraplength=440
        )
        self.lbl_title.place(relx=0.5, y=6, anchor="n")

        # 2. Main Script Text (Pure Teleprompter Text)
        self.lbl_current = tk.Label(
            self.root,
            text="Memuat naskah...",
            fg=self.text_color,
            bg=self.bg_color,
            font=("Segoe UI", self.font_cur),
            wraplength=450,
            justify="center"
        )
        self.lbl_current.pack(expand=True, fill="both", padx=14, pady=(22, 12))

        # 3. Progress Bar at bottom (SpoLyrics style progress line)
        self.progress_bg = tk.Frame(self.root, bg="#1e293b", height=2)
        self.progress_bg.place(relx=0, rely=1.0, anchor="sw", relwidth=1.0)
        self.progress_fg = tk.Frame(self.progress_bg, bg=self.accent_color, height=2)
        self.progress_fg.place(relx=0, rely=0, anchor="nw", relwidth=0.0)

        # 4. Large Accessible Resize Grip icon at bottom right ⇲
        self.grip = tk.Label(
            self.root,
            text="⇲",
            fg="#475569",
            bg=self.bg_color,
            font=("Segoe UI", 12, "bold"),
            cursor="size_nw_se",
            padx=8,
            pady=4
        )
        self.grip.place(relx=1.0, rely=1.0, anchor="se")
        self.grip.lift()

    def render_slide(self):
        if not self.slides:
            self.lbl_title.config(text="Belum ada slide")
            self.lbl_current.config(text="Tekan Ctrl+E untuk menambah slide baru.")
            return

        self.current_idx = max(0, min(self.current_idx, len(self.slides) - 1))
        slide = self.slides[self.current_idx]
        total = len(self.slides)

        # Update progress bar ratio
        progress = (self.current_idx + 1) / total if total > 0 else 0
        self.progress_fg.place(relwidth=progress)

        # Update Title
        timer_str = f" ⏱ {self.timer_seconds // 60:02d}:{self.timer_seconds % 60:02d}" if (self.timer_running or self.timer_seconds > 0) else ""
        if self.show_title:
            self.lbl_title.config(text=f"[{slide['id']}/{total}] {slide['title']}{timer_str}")
        else:
            self.lbl_title.config(text="")

        # Update Pure Script Text
        self.lbl_current.config(text=slide.get("script", ""))

    # ==========================================
    # 🖱️ 1:1 SPOLYRICS GESTURES & CONTROLS
    # ==========================================

    def click(self, event):
        """Left Click: calculate mouse offset for dragging window"""
        self._offset_x = self.root.winfo_pointerx() - self.root.winfo_rootx()
        self._offset_y = self.root.winfo_pointery() - self.root.winfo_rooty()
        return "break"

    def drag(self, event):
        """Left Click (Hold): Move Window"""
        if self.is_pinned or event.widget == self.grip:
            return "break"
        x = self.root.winfo_pointerx() - self._offset_x
        y = self.root.winfo_pointery() - self._offset_y
        self.root.geometry(f"+{x}+{y}")
        return "break"

    def start_resize(self, event):
        """Record initial dimensions when grip is pressed"""
        if self.is_pinned:
            return "break"
        self.resize_start_x = self.root.winfo_pointerx()
        self.resize_start_y = self.root.winfo_pointery()
        self.orig_w = self.root.winfo_width()
        self.orig_h = self.root.winfo_height()
        return "break"

    def on_resize(self, event):
        """Drag bottom right grip ⇲: Resize Window smoothly"""
        if self.is_pinned:
            return "break"
        dx = self.root.winfo_pointerx() - self.resize_start_x
        dy = self.root.winfo_pointery() - self.resize_start_y
        new_w = max(260, self.orig_w + dx)
        new_h = max(90, self.orig_h + dy)
        self.root.geometry(f"{new_w}x{new_h}")
        self.lbl_current.config(wraplength=new_w - 30)
        self.lbl_title.config(wraplength=new_w - 40)
        return "break"

    def on_scroll(self, event):
        """Middle Mouse Scroll: Next / Previous Slide"""
        now = time.time()
        if now - self.last_scroll_time < 0.25:
            return "break"
        self.last_scroll_time = now

        if event.delta > 0:
            self.prev_slide()
        else:
            self.next_slide()
        return "break"

    def on_font_scroll(self, event):
        """Ctrl + Scroll: Resize Text"""
        if self.is_pinned:
            return "break"
        if event.delta > 0:
            self.font_cur += 1
        else:
            self.font_cur = max(8, self.font_cur - 1)

        self.lbl_current.config(font=("Segoe UI", self.font_cur))
        return "break"

    def toggle_title(self, event=None):
        """Ctrl + Left Click: Show / Hide Title"""
        if self.is_pinned:
            return "break"
        self.show_title = not self.show_title
        self.render_slide()
        return "break"

    def toggle_pin(self, event=None):
        """Middle Click or Shift + Left Click: Lock & Ghost Mode (Click-Through)"""
        self.toggle_ghost_mode()
        return "break"

    def toggle_ghost_mode(self, state=None):
        """Win32 WS_EX_TRANSPARENT Click-Through Lock Mode"""
        if state is None:
            self.ghost_mode = not getattr(self, "ghost_mode", False)
        else:
            self.ghost_mode = state

        self.is_pinned = self.ghost_mode

        if self.is_pinned:
            self.grip.config(text="🔒", fg=self.accent_color, cursor="arrow")
        else:
            self.grip.config(text="⇲", fg="#475569", cursor="size_nw_se")

        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if not hwnd:
                hwnd = self.root.winfo_id()
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

            if self.ghost_mode:
                ex_style |= WS_EX_TRANSPARENT
            else:
                ex_style &= ~WS_EX_TRANSPARENT

            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
        except Exception:
            pass

        if self.ghost_mode:
            self.root.after(400, self.monitor_ghost_unlock)

    def monitor_ghost_unlock(self):
        """Monitor middle click or shift+click to unlock ghost mode"""
        if not getattr(self, "ghost_mode", False):
            return

        mbutton = ctypes.windll.user32.GetAsyncKeyState(VK_MBUTTON) & KEY_PRESSED_MASK
        shift = ctypes.windll.user32.GetAsyncKeyState(VK_SHIFT) & KEY_PRESSED_MASK
        lbutton = ctypes.windll.user32.GetAsyncKeyState(VK_LBUTTON) & KEY_PRESSED_MASK

        if mbutton or (shift and lbutton):
            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            wx = self.root.winfo_rootx()
            wy = self.root.winfo_rooty()
            ww = self.root.winfo_width()
            wh = self.root.winfo_height()

            if wx <= pt.x <= wx + ww and wy <= pt.y <= wy + wh:
                self.toggle_ghost_mode(False)
                return

        self.root.after(100, self.monitor_ghost_unlock)

    def media_control(self, action):
        """Right Click: Play/Pause Presentation Timer"""
        if action == "play_pause":
            self.timer_running = not self.timer_running
            if self.timer_running:
                self.run_timer()

    def run_timer(self):
        if self.timer_running:
            self.timer_seconds += 1
            mins = self.timer_seconds // 60
            secs = self.timer_seconds % 60
            if self.show_title and self.slides:
                slide = self.slides[self.current_idx]
                total = len(self.slides)
                self.lbl_title.config(text=f"[{slide['id']}/{total}] {slide['title']} ⏱ {mins:02d}:{secs:02d}")
            self.root.after(1000, self.run_timer)

    def reset_timer(self):
        """Reset presentation timer to 00:00"""
        self.timer_seconds = 0
        self.render_slide()

    def next_slide(self, event=None):
        if self.current_idx < len(self.slides) - 1:
            self.current_idx += 1
            self.render_slide()

    def prev_slide(self, event=None):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.render_slide()

    def go_to_slide(self, idx):
        if 0 <= idx < len(self.slides):
            self.current_idx = idx
            self.root.after(0, self.render_slide)

    # =======================================================
    # 📝 FULL CRUD SLIDE MANAGER (Create, Read, Update, Delete)
    # =======================================================

    def open_editor(self):
        """Open Full 2-Column CRUD Slide Manager"""
        if hasattr(self, "editor_win") and self.editor_win.winfo_exists():
            self.editor_win.focus()
            return

        self.editor_win = tk.Toplevel(self.root)
        self.editor_win.title("Teleprompter by tourrr - Slide Manager (CRUD)")
        self.editor_win.geometry("740x540")
        self.editor_win.configure(bg="#0b131e")
        self.editor_win.attributes("-topmost", True)
        self.editor_win.minsize(620, 440)

        ico_file = os.path.join(SCRIPT_DIR, "app_icon.ico")
        if os.path.exists(ico_file):
            try:
                self.editor_win.iconbitmap(ico_file)
            except Exception:
                pass

        # Header bar
        header_frame = tk.Frame(self.editor_win, bg="#0b131e")
        header_frame.pack(fill="x", padx=18, pady=(14, 8))

        tk.Label(
            header_frame,
            text="📑 Slide Manager & Script Editor",
            fg=self.accent_color,
            bg="#0b131e",
            font=("Segoe UI", 14, "bold")
        ).pack(side="left")

        # Bottom Action Bar (Packed at bottom FIRST so it is always visible)
        bottom_frame = tk.Frame(self.editor_win, bg="#0b131e", height=45)
        bottom_frame.pack(side="bottom", fill="x", padx=18, pady=(0, 14))

        # Main 2-Column Split (Fills remaining space between header and bottom)
        body_frame = tk.Frame(self.editor_win, bg="#0b131e")
        body_frame.pack(fill="both", expand=True, padx=18, pady=(0, 10))

        # ==========================================
        # LEFT COLUMN: SLIDE LIST (Read / Select)
        # ==========================================
        left_col = tk.Frame(body_frame, bg="#0b131e", width=260)
        left_col.pack(side="left", fill="both", padx=(0, 10))
        left_col.pack_propagate(False)

        lbl_list_head = tk.Label(
            left_col,
            text="📋 Daftar Slide",
            fg="#94a3b8",
            bg="#0b131e",
            font=("Segoe UI", 9, "bold")
        )
        lbl_list_head.pack(anchor="w", pady=(0, 4))

        # Listbox with scrollbar
        list_container = tk.Frame(left_col, bg="#1e293b")
        list_container.pack(fill="both", expand=True)

        list_scroll = tk.Scrollbar(list_container, bg="#1e293b")
        list_scroll.pack(side="right", fill="y")

        self.editor_selected_idx = self.current_idx

        slide_listbox = tk.Listbox(
            list_container,
            bg="#1e293b",
            fg="#f8fafc",
            selectbackground="#059669",
            selectforeground="#ffffff",
            font=("Segoe UI", 9),
            relief="flat",
            highlightthickness=0,
            exportselection=False,
            yscrollcommand=list_scroll.set
        )
        slide_listbox.pack(side="left", fill="both", expand=True)
        list_scroll.config(command=slide_listbox.yview)

        # Left Column Buttons (Create, Delete, Reorder)
        left_btn_frame = tk.Frame(left_col, bg="#0b131e")
        left_btn_frame.pack(fill="x", pady=(6, 0))

        row1 = tk.Frame(left_btn_frame, bg="#0b131e")
        row1.pack(fill="x", pady=2)

        row2 = tk.Frame(left_btn_frame, bg="#0b131e")
        row2.pack(fill="x", pady=2)

        # ==========================================
        # RIGHT COLUMN: FORM (Update / Edit)
        # ==========================================
        right_col = tk.Frame(body_frame, bg="#0b131e")
        right_col.pack(side="right", fill="both", expand=True)

        # Title Field
        tk.Label(
            right_col,
            text="Judul Slide:",
            fg="#94a3b8",
            bg="#0b131e",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(0, 2))

        ent_title = tk.Entry(
            right_col,
            bg="#1e293b",
            fg="#ffffff",
            insertbackground="#10b981",
            font=("Segoe UI", 10),
            relief="flat"
        )
        ent_title.pack(fill="x", ipady=4, pady=(0, 8))

        # Duration Field
        dur_frame = tk.Frame(right_col, bg="#0b131e")
        dur_frame.pack(fill="x", pady=(0, 8))

        tk.Label(
            dur_frame,
            text="Estimasi Durasi:",
            fg="#94a3b8",
            bg="#0b131e",
            font=("Segoe UI", 9)
        ).pack(side="left", padx=(0, 6))

        ent_duration = tk.Entry(
            dur_frame,
            bg="#1e293b",
            fg="#6ee7b7",
            insertbackground="#10b981",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            width=18
        )
        ent_duration.pack(side="left", ipady=2)

        # Script Text Field
        tk.Label(
            right_col,
            text="Teks Naskah Ucap (Voice-Over):",
            fg="#94a3b8",
            bg="#0b131e",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(0, 2))

        txt_script_edit = tk.Text(
            right_col,
            bg="#1e293b",
            fg="#f8fafc",
            insertbackground="#10b981",
            font=("Segoe UI", 10),
            wrap="word",
            relief="flat",
            padx=10,
            pady=8
        )
        txt_script_edit.pack(fill="both", expand=True, pady=(0, 8))

        # ==========================================
        # CRUD LOGIC & CONTROLS
        # ==========================================

        def refresh_listbox(select_idx=0):
            slide_listbox.delete(0, tk.END)
            for idx, s in enumerate(self.slides):
                title_short = s.get("title", f"Slide {idx+1}")
                slide_listbox.insert(tk.END, f"[{idx+1}] {title_short}")
            lbl_list_head.config(text=f"📋 Daftar Slide ({len(self.slides)})")

            if self.slides:
                select_idx = max(0, min(select_idx, len(self.slides) - 1))
                self.editor_selected_idx = select_idx
                slide_listbox.selection_clear(0, tk.END)
                slide_listbox.selection_set(select_idx)
                slide_listbox.activate(select_idx)
                slide_listbox.see(select_idx)
                load_slide_into_form(select_idx)
            else:
                ent_title.delete(0, tk.END)
                ent_duration.delete(0, tk.END)
                txt_script_edit.delete("1.0", tk.END)

        def load_slide_into_form(idx):
            if 0 <= idx < len(self.slides):
                self.editor_selected_idx = idx
                s = self.slides[idx]
                ent_title.delete(0, tk.END)
                ent_title.insert(0, s.get("title", ""))
                ent_duration.delete(0, tk.END)
                ent_duration.insert(0, s.get("duration", "1 Menit"))
                txt_script_edit.delete("1.0", tk.END)
                txt_script_edit.insert("1.0", s.get("script", ""))

        def on_listbox_select(event=None):
            sel = slide_listbox.curselection()
            if sel:
                idx = sel[0]
                self.editor_selected_idx = idx
                load_slide_into_form(idx)
                self.current_idx = idx
                self.render_slide()

        slide_listbox.bind("<<ListboxSelect>>", on_listbox_select)

        # Real-time Live Typing Preview onto Overlay
        def live_update_overlay(event=None):
            idx = getattr(self, "editor_selected_idx", self.current_idx)
            if 0 <= idx < len(self.slides):
                self.current_idx = idx
                self.slides[idx]["title"] = ent_title.get().strip() or f"Slide {idx+1}"
                self.slides[idx]["duration"] = ent_duration.get().strip() or "1 Menit"
                self.slides[idx]["script"] = txt_script_edit.get("1.0", "end-1c").strip()
                self.render_slide()

        ent_title.bind("<KeyRelease>", live_update_overlay)
        txt_script_edit.bind("<KeyRelease>", live_update_overlay)

        # 💾 UPDATE (Save Current Slide)
        def save_slide():
            idx = getattr(self, "editor_selected_idx", self.current_idx)
            if idx < 0 or idx >= len(self.slides):
                if not self.slides:
                    add_new_slide()
                    idx = 0
                else:
                    idx = 0

            # Commit current form values
            self.slides[idx]["title"] = ent_title.get().strip() or f"Slide {idx+1}"
            self.slides[idx]["duration"] = ent_duration.get().strip() or "1 Menit"
            self.slides[idx]["script"] = txt_script_edit.get("1.0", "end-1c").strip()

            self.current_idx = idx
            self.editor_selected_idx = idx
            self.save_slides_to_file()
            self.render_slide()
            refresh_listbox(select_idx=idx)
            messagebox.showinfo("Tersimpan", f"✅ Naskah Slide {idx+1} berhasil disimpan permanen ke file!")

        # ➕ CREATE (Add New Slide)
        def add_new_slide():
            sel = slide_listbox.curselection()
            insert_pos = (sel[0] + 1) if sel else len(self.slides)
            new_slide = {
                "id": insert_pos + 1,
                "title": f"Slide {len(self.slides)+1:02d}: Judul Slide Baru",
                "duration": "1 Menit",
                "script": "Tulis naskah ucapan untuk slide baru ini..."
            }
            self.slides.insert(insert_pos, new_slide)
            self.save_slides_to_file()
            self.render_slide()
            refresh_listbox(select_idx=insert_pos)

        # 🗑️ DELETE (Delete Slide)
        def delete_slide():
            sel = slide_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            if len(self.slides) <= 1:
                messagebox.showwarning("Peringatan", "Minimal harus ada 1 slide tersisa.")
                return

            if messagebox.askyesno("Konfirmasi Hapus", f"Apakah Anda yakin ingin menghapus Slide {idx+1}?"):
                self.slides.pop(idx)
                self.save_slides_to_file()
                self.render_slide()
                new_sel = max(0, idx - 1)
                refresh_listbox(select_idx=new_sel)

        # ⬆ REORDER UP
        def move_up():
            sel = slide_listbox.curselection()
            if not sel or sel[0] == 0:
                return
            idx = sel[0]
            self.slides[idx], self.slides[idx - 1] = self.slides[idx - 1], self.slides[idx]
            self.save_slides_to_file()
            self.render_slide()
            refresh_listbox(select_idx=idx - 1)

        # ⬇ REORDER DOWN
        def move_down():
            sel = slide_listbox.curselection()
            if not sel or sel[0] >= len(self.slides) - 1:
                return
            idx = sel[0]
            self.slides[idx], self.slides[idx + 1] = self.slides[idx + 1], self.slides[idx]
            self.save_slides_to_file()
            self.render_slide()
            refresh_listbox(select_idx=idx + 1)

        # 📄 DUPLICATE SLIDE
        def duplicate_slide():
            sel = slide_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            orig = self.slides[idx]
            clone = {
                "id": idx + 2,
                "title": f"{orig['title']} (Salinan)",
                "duration": orig.get("duration", "1 Menit"),
                "script": orig.get("script", "")
            }
            self.slides.insert(idx + 1, clone)
            self.save_slides_to_file()
            self.render_slide()
            refresh_listbox(select_idx=idx + 1)

        # Place CRUD buttons on Left Column
        btn_add = tk.Button(
            row1,
            text="➕ Tambah",
            bg="#059669",
            fg="#ffffff",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=add_new_slide
        )
        btn_add.pack(side="left", fill="x", expand=True, padx=(0, 2))

        btn_del = tk.Button(
            row1,
            text="🗑️ Hapus",
            bg="#b91c1c",
            fg="#ffffff",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=delete_slide
        )
        btn_del.pack(side="right", fill="x", expand=True, padx=(2, 0))

        btn_up = tk.Button(
            row2,
            text="⬆ Naik",
            bg="#334155",
            fg="#ffffff",
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            command=move_up
        )
        btn_up.pack(side="left", fill="x", expand=True, padx=(0, 2))

        btn_down = tk.Button(
            row2,
            text="⬇ Turun",
            bg="#334155",
            fg="#ffffff",
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            command=move_down
        )
        btn_down.pack(side="left", fill="x", expand=True, padx=2)

        btn_dup = tk.Button(
            row2,
            text="📄 Duplikat",
            bg="#334155",
            fg="#ffffff",
            font=("Segoe UI", 8),
            relief="flat",
            cursor="hand2",
            command=duplicate_slide
        )
        btn_dup.pack(side="right", fill="x", expand=True, padx=(2, 0))

        # Bottom Bar Buttons
        btn_save = tk.Button(
            bottom_frame,
            text="💾 Simpan Perubahan",
            bg="#059669",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=6,
            command=save_slide
        )
        btn_save.pack(side="left")

        def open_json_in_notepad():
            os.system(f'start "" "{SLIDES_JSON_PATH}"')

        btn_open_file = tk.Button(
            bottom_frame,
            text="📂 Buka slides_data.json",
            bg="#334155",
            fg="#94a3b8",
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=open_json_in_notepad
        )
        btn_open_file.pack(side="left", padx=8)

        btn_close = tk.Button(
            bottom_frame,
            text="✕ Tutup Editor",
            bg="#1e293b",
            fg="#ffffff",
            font=("Segoe UI", 9),
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self.editor_win.destroy
        )
        btn_close.pack(side="right")

        # Initial populate
        refresh_listbox(select_idx=self.current_idx)

        # Keyboard Shortcut Ctrl+S to Save Instantly
        self.editor_win.bind("<Control-s>", lambda e: save_slide())
        self.editor_win.bind("<Control-S>", lambda e: save_slide())

    def open_info(self):
        """Open SpoLyrics-style Shortcuts Info Dialog"""
        if hasattr(self, "info_win") and self.info_win.winfo_exists():
            self.info_win.focus()
            return

        self.info_win = tk.Toplevel(self.root)
        self.info_win.title("Teleprompter by tourrr - Shortcuts & Info")
        self.info_win.geometry("440x520")
        self.info_win.configure(bg="#0b131e")
        self.info_win.attributes("-topmost", True)
        self.info_win.overrideredirect(True)

        ico_file = os.path.join(SCRIPT_DIR, "app_icon.ico")
        if os.path.exists(ico_file):
            try:
                self.info_win.iconbitmap(ico_file)
            except Exception:
                pass

        def start_drag_info(e):
            self.info_win._offset_x = self.info_win.winfo_pointerx() - self.info_win.winfo_rootx()
            self.info_win._offset_y = self.info_win.winfo_pointery() - self.info_win.winfo_rooty()

        def do_drag_info(e):
            x = self.info_win.winfo_pointerx() - self.info_win._offset_x
            y = self.info_win.winfo_pointery() - self.info_win._offset_y
            self.info_win.geometry(f"+{x}+{y}")

        self.info_win.bind("<Button-1>", start_drag_info)
        self.info_win.bind("<B1-Motion>", do_drag_info)

        lbl_head = tk.Label(
            self.info_win,
            text="📚 Teleprompter by tourrr",
            fg=self.accent_color,
            bg="#0b131e",
            font=("Segoe UI", 14, "bold")
        )
        lbl_head.pack(pady=(20, 15))
        lbl_head.bind("<Button-1>", start_drag_info)
        lbl_head.bind("<B1-Motion>", do_drag_info)

        shortcuts = [
            ("🖱️ Left Click (Hold)", "Geser Posisi Kotak"),
            ("📐 Tarik Pojok Kanan ⇲", "Resize Ukuran Kotak"),
            ("🖱️ Right Click", "Play / Pause Timer"),
            ("⌨️ Ctrl + R", "Reset Timer ke 00:00"),
            ("🖱️ Middle Mouse Click", "Lock & Ghost Mode (🔒 Tembus Klik)"),
            ("⌨️ Shift + Left Click", "Lock & Ghost Mode (Trackpad)"),
            ("🖱️ Middle Mouse Scroll", "Next / Previous Slide"),
            ("⌨️ Tombol Panah / Spasi", "Navigasi Slide (Next / Prev)"),
            ("⌨️ Ctrl + E", "Buka Slide Manager (CRUD Naskah)"),
            ("⌨️ Ctrl + Left Click", "Tampilkan / Sembunyikan Judul"),
            ("⌨️ Ctrl + Scroll", "Perbesar / Perkecil Teks"),
            ("🖱️ Double Left Click", "Tutup Aplikasi (Quit)")
        ]

        for k, v in shortcuts:
            frame = tk.Frame(self.info_win, bg="#0b131e")
            frame.pack(fill="x", padx=30, pady=4)
            frame.bind("<Button-1>", start_drag_info)
            frame.bind("<B1-Motion>", do_drag_info)

            lbl_k = tk.Label(frame, text=k, fg="white", bg="#0b131e", font=("Segoe UI", 9, "bold"))
            lbl_k.pack(side="left")
            lbl_k.bind("<Button-1>", start_drag_info)
            lbl_k.bind("<B1-Motion>", do_drag_info)

            lbl_v = tk.Label(frame, text=v, fg="#94a3b8", bg="#0b131e", font=("Segoe UI", 9))
            lbl_v.pack(side="right")
            lbl_v.bind("<Button-1>", start_drag_info)
            lbl_v.bind("<B1-Motion>", do_drag_info)

        close_btn = tk.Label(
            self.info_win,
            text="Tutup Info",
            bg="#1e293b",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            pady=6,
            cursor="hand2"
        )
        close_btn.pack(fill="x", padx=40, pady=(20, 10))
        close_btn.bind("<Button-1>", lambda e: self.info_win.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg="#334155"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg="#1e293b"))

        x = self.root.winfo_rootx() + 30
        y = self.root.winfo_rooty() + 30
        self.info_win.geometry(f"+{x}+{y}")

    def bind_events(self):
        """Bind all gestures to root, labels, and separate resize grip"""
        # 1. Grip Resizing Specific Bindings
        self.grip.bind("<Button-1>", self.start_resize)
        self.grip.bind("<B1-Motion>", self.on_resize)
        self.grip.bind("<Enter>", lambda e: not self.is_pinned and self.grip.config(fg=self.accent_color))
        self.grip.bind("<Leave>", lambda e: not self.is_pinned and self.grip.config(fg="#475569"))

        # 2. Window Drag Move Bindings (Labels and background)
        for w in (self.root, self.lbl_current, self.lbl_title):
            w.bind("<Button-1>", self.click)
            w.bind("<B1-Motion>", self.drag)
            w.bind("<Double-1>", lambda e: not self.is_pinned and self.exit_app())
            w.bind("<Button-3>", lambda e: self.media_control("play_pause"))
            w.bind("<MouseWheel>", self.on_scroll)
            w.bind("<Control-MouseWheel>", self.on_font_scroll)
            w.bind("<Button-2>", self.toggle_pin)
            w.bind("<Shift-Button-1>", self.toggle_pin)
            w.bind("<Control-Button-1>", self.toggle_title)

        # 3. Global Keyboard Shortcuts
        self.root.bind("<Right>", self.next_slide)
        self.root.bind("<Down>", self.next_slide)
        self.root.bind("<space>", self.next_slide)
        self.root.bind("<Next>", self.next_slide)

        self.root.bind("<Left>", self.prev_slide)
        self.root.bind("<Up>", self.prev_slide)
        self.root.bind("<BackSpace>", self.prev_slide)
        self.root.bind("<Prior>", self.prev_slide)

        self.root.bind("<Control-e>", lambda e: self.open_editor())
        self.root.bind("<Control-E>", lambda e: self.open_editor())
        self.root.bind("<Control-r>", lambda e: self.reset_timer())
        self.root.bind("<Control-R>", lambda e: self.reset_timer())
        self.root.bind("<Escape>", lambda e: self.exit_app())
        self.root.bind("<Control-q>", lambda e: self.exit_app())

    # ==========================================
    # 🖲️ SYSTEM TRAY INTEGRATION (pystray)
    # ==========================================

    def start_system_tray(self):
        threading.Thread(target=self._run_tray, daemon=True).start()

    def _run_tray(self):
        icon_img = create_tray_icon_image()

        def make_slide_menu():
            slide_items = []
            for idx, slide in enumerate(self.slides):
                def make_handler(i):
                    return lambda icon, itm: self.go_to_slide(i)

                title_short = f"Slide {slide['id']:02d}: {slide['title'].split(':')[-1].strip()}"
                slide_items.append(
                    pystray.MenuItem(
                        title_short,
                        make_handler(idx),
                        checked=lambda itm, i=idx: self.current_idx == i,
                        radio=True
                    )
                )
            return slide_items

        menu = pystray.Menu(
            pystray.MenuItem("📝 Kelola Slide (CRUD)", lambda icon, itm: self.root.after(0, self.open_editor)),
            pystray.MenuItem("📚 Shortcuts & Panduan", lambda icon, itm: self.root.after(0, self.open_info)),
            pystray.MenuItem(
                "🔒 Lock & Ghost Mode (Click-Through)",
                lambda icon, itm: self.root.after(0, self.toggle_ghost_mode),
                checked=lambda itm: getattr(self, "ghost_mode", False)
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⏱️ Play / Pause Timer", lambda icon, itm: self.root.after(0, lambda: self.media_control("play_pause"))),
            pystray.MenuItem("⏱️ Reset Timer (00:00)", lambda icon, itm: self.root.after(0, self.reset_timer)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("📑 Pilih Slide Naskah", pystray.Menu(lambda: make_slide_menu())),
            pystray.MenuItem("▶ Slide Berikutnya (Next)", lambda icon, itm: self.root.after(0, self.next_slide)),
            pystray.MenuItem("◀ Slide Sebelumnya (Prev)", lambda icon, itm: self.root.after(0, self.prev_slide)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("🔄 Muat Ulang Naskah (Reload)", lambda icon, itm: self.load_slides()),
            pystray.MenuItem("👁️ Sembunyikan / Tampilkan", lambda icon, itm: self.toggle_visibility()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("✕ Keluar (Quit)", lambda icon, itm: self.exit_app())
        )

        self.tray_icon = pystray.Icon(
            "teleprompter_by_tourrr",
            icon_img,
            "Teleprompter by tourrr",
            menu
        )
        self.tray_icon.run()

    def toggle_visibility(self):
        if self.root.winfo_viewable():
            self.root.withdraw()
        else:
            self.root.deiconify()
            self.apply_anti_capture()

    def exit_app(self):
        if hasattr(self, "tray_icon") and self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        try:
            self.root.destroy()
        except Exception:
            pass
        os._exit(0)

def main():
    app = SpoLyricsTeleprompter()
    app.root.mainloop()

if __name__ == "__main__":
    main()
