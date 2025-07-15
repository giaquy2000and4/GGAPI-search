import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import requests
from io import BytesIO
from PIL import Image
import time
from datetime import datetime, timedelta

# --------- CẤU HÌNH GOOGLE API ----------
API_KEY = "AIzaSyBYUEQzOl5wF5wObQaN0DDn6E7KDZHYhlc"
CX = "72be8b4014fac4e40"
RATE_LIMIT_DELAY = 0.25  # giây giữa hai call API
ALLOWED_FORMATS = ["jpeg", "jpg", "png"]
_last_api_call = datetime.min  # dùng cho rate‑limit


# ----------------------------------------

# ---------- HÀM TIỆN ÍCH ----------
def wait_if_needed():
    global _last_api_call
    elapsed = datetime.now() - _last_api_call
    if elapsed < timedelta(seconds=RATE_LIMIT_DELAY):
        time.sleep((timedelta(seconds=RATE_LIMIT_DELAY) - elapsed).total_seconds())
    _last_api_call = datetime.now()


def search_image_on_google(query, max_results=50):
    url = "https://www.googleapis.com/customsearch/v1"
    all_links, start = [], 1

    while len(all_links) < max_results and start <= 90:
        wait_if_needed()
        params = {
            "q": query,
            "cx": CX,
            "key": API_KEY,
            "searchType": "image",
            "num": 10,
            "start": start,
            "imgSize": "huge"
        }
        r = requests.get(url, params=params)
        if r.status_code != 200:
            break
        items = r.json().get("items", [])
        all_links.extend([item["link"] for item in items])
        if len(items) < 10:
            break
        start += 10

    return all_links[:max_results]


def download_image(url, save_folder, filename_index, log_cb):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        ctype = r.headers.get("Content-Type", "").lower()
        if not any(fmt in ctype for fmt in ALLOWED_FORMATS):
            log_cb(f"⛔ Định dạng không hợp lệ ({ctype}), bỏ qua.")
            return False

        img = Image.open(BytesIO(r.content))
        w, h = img.size
        log_cb(f"📐 {w}x{h}")
        os.makedirs(save_folder, exist_ok=True)
        fname = f"{filename_index:03d}.png"
        img.save(os.path.join(save_folder, fname), "PNG")
        log_cb(f"✅ Lưu: {fname}")
        return True
    except Exception as e:
        log_cb(f"❌ Lỗi: {e}")
        return False


def download_images(keywords, per_kw, folder, log_cb, progress_cb=None, stats_cb=None):
    idx = 1
    total_keywords = len(keywords)
    total_success = 0
    total_failed = 0

    for kw_idx, kw in enumerate(keywords):
        log_cb(f"\n🔍 Từ khóa: {kw}")
        urls = search_image_on_google(kw, 50)
        cnt = 0
        failed_cnt = 0

        for u in urls:
            if download_image(u, folder, idx, log_cb):
                idx += 1
                cnt += 1
                total_success += 1
            else:
                failed_cnt += 1
                total_failed += 1

            # Cập nhật thống kê sau mỗi ảnh
            if stats_cb:
                stats_cb(total_success + total_failed, total_success, total_failed)

            if cnt >= per_kw:
                break

        log_cb(f"🎯 {cnt}/{per_kw} ảnh cho \"{kw}\" (thất bại: {failed_cnt})")

        # Cập nhật progress bar
        if progress_cb:
            progress_cb((kw_idx + 1) / total_keywords * 100)


# ---------- HẾT TIỆN ÍCH ----------


# ---------- GUI ----------
class ImageDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📥 Google Image Downloader Pro")
        self.root.geometry("1200x700")
        self.root.configure(bg="#1a1a1a")
        self.root.resizable(True, True)
        self.root.minsize(1000, 600)

        # Thiết lập style
        self.setup_styles()

        # Tạo main container với scrollbar
        main_canvas = tk.Canvas(root, bg="#1a1a1a", highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg="#1a1a1a")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")

        # Main content trong scrollable frame
        main_frame = tk.Frame(scrollable_frame, bg="#1a1a1a")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Header nhỏ gọn hơn
        self.create_header(main_frame)

        # Content area với 2 cột
        content_frame = tk.Frame(main_frame, bg="#1a1a1a")
        content_frame.pack(fill="both", expand=True, pady=10)

        # Cột trái - Input
        left_frame = tk.Frame(content_frame, bg="#1a1a1a")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Cột phải - Output
        right_frame = tk.Frame(content_frame, bg="#1a1a1a")
        right_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # Tạo các sections
        self.create_input_section(left_frame)
        self.create_output_section(right_frame)
        self.create_control_section(main_frame)

        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Biến trạng thái
        self.is_downloading = False
        self.stats = {"total": 0, "success": 0, "failed": 0}

    def setup_styles(self):
        """Thiết lập style cho các widget"""
        style = ttk.Style()
        style.theme_use("clam")

        # Style cho button
        style.configure("Accent.TButton",
                        background="#4CAF50",
                        foreground="white",
                        borderwidth=0,
                        focuscolor="none",
                        font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton",
                  background=[("active", "#45a049"), ("pressed", "#3d8b40")])

        # Style cho secondary button
        style.configure("Secondary.TButton",
                        background="#555555",
                        foreground="white",
                        borderwidth=0,
                        focuscolor="none")
        style.map("Secondary.TButton",
                  background=[("active", "#666666"), ("pressed", "#444444")])

        # Style cho progressbar
        style.configure("Custom.Horizontal.TProgressbar",
                        background="#4CAF50",
                        troughcolor="#333333",
                        borderwidth=0,
                        lightcolor="#4CAF50",
                        darkcolor="#4CAF50")

    def create_header(self, parent):
        """Tạo header với title và description"""
        header_frame = tk.Frame(parent, bg="#1a1a1a")
        header_frame.pack(fill="x", pady=(0, 10))

        title_label = tk.Label(header_frame,
                               text="📥 Google Image Downloader Pro",
                               font=("Segoe UI", 18, "bold"),
                               bg="#1a1a1a", fg="#ffffff")
        title_label.pack(anchor="w")

        desc_label = tk.Label(header_frame,
                              text="Tải hàng loạt ảnh từ Google Images",
                              font=("Segoe UI", 9),
                              bg="#1a1a1a", fg="#cccccc")
        desc_label.pack(anchor="w", pady=(3, 0))

    def create_input_section(self, parent):
        """Tạo section nhập liệu"""
        # Keywords section
        keywords_frame = self.create_section_frame(parent, "🔍 Từ khóa tìm kiếm")

        # Text area với scrollbar
        text_frame = tk.Frame(keywords_frame, bg="#2a2a2a")
        text_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.key_text = tk.Text(text_frame,
                                height=8,
                                bg="#333333",
                                fg="#ffffff",
                                insertbackground="#ffffff",
                                font=("Consolas", 9),
                                wrap="word",
                                relief="flat",
                                bd=0,
                                padx=10,
                                pady=8)

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.key_text.yview)
        self.key_text.configure(yscrollcommand=scrollbar.set)

        self.key_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Placeholder text
        self.key_text.insert("1.0", "Nhập các từ khóa, mỗi dòng một từ khóa...\nVí dụ:\ncon mèo\ncon chó\nphong cảnh")
        self.key_text.bind("<FocusIn>", self.clear_placeholder)
        self.key_text.bind("<FocusOut>", self.add_placeholder)

        # Load file button
        load_btn = ttk.Button(keywords_frame,
                              text="📁 Tải file .txt",
                              style="Secondary.TButton",
                              command=self.load_txt)
        load_btn.pack(pady=(10, 0))

        # Settings section
        settings_frame = self.create_section_frame(parent, "⚙️ Cài đặt")

        # Số ảnh mỗi từ khóa
        num_frame = tk.Frame(settings_frame, bg="#2a2a2a")
        num_frame.pack(fill="x", pady=(10, 5))

        tk.Label(num_frame,
                 text="Số ảnh mỗi từ khóa:",
                 bg="#2a2a2a", fg="#ffffff",
                 font=("Segoe UI", 10)).pack(side="left")

        self.num_var = tk.IntVar(value=5)
        num_spinbox = tk.Spinbox(num_frame,
                                 from_=1, to=20,
                                 textvariable=self.num_var,
                                 width=8,
                                 font=("Segoe UI", 10),
                                 bg="#333333",
                                 fg="#ffffff",
                                 buttonbackground="#555555",
                                 relief="flat",
                                 bd=0)
        num_spinbox.pack(side="right")

        # Thư mục lưu
        dir_frame = tk.Frame(settings_frame, bg="#2a2a2a")
        dir_frame.pack(fill="x", pady=(5, 10))

        tk.Label(dir_frame,
                 text="Thư mục lưu:",
                 bg="#2a2a2a", fg="#ffffff",
                 font=("Segoe UI", 10)).pack(anchor="w")

        dir_input_frame = tk.Frame(dir_frame, bg="#2a2a2a")
        dir_input_frame.pack(fill="x", pady=(5, 0))

        self.dir_var = tk.StringVar()
        dir_entry = tk.Entry(dir_input_frame,
                             textvariable=self.dir_var,
                             bg="#333333",
                             fg="#ffffff",
                             font=("Segoe UI", 10),
                             relief="flat",
                             bd=0)
        dir_entry.pack(side="left", fill="x", expand=True, ipady=5)

        dir_btn = ttk.Button(dir_input_frame,
                             text="📂 Chọn",
                             style="Secondary.TButton",
                             command=self.pick_dir)
        dir_btn.pack(side="right", padx=(5, 0))

    def create_output_section(self, parent):
        """Tạo section output"""
        # Log section
        log_frame = self.create_section_frame(parent, "📊 Tiến trình tải")

        # Progress bar
        progress_frame = tk.Frame(log_frame, bg="#2a2a2a")
        progress_frame.pack(fill="x", pady=(10, 0))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame,
                                            variable=self.progress_var,
                                            maximum=100,
                                            style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=(0, 5))

        self.progress_label = tk.Label(progress_frame,
                                       text="Sẵn sàng tải...",
                                       bg="#2a2a2a", fg="#cccccc",
                                       font=("Segoe UI", 9))
        self.progress_label.pack(anchor="w")

        # Log text area
        log_text_frame = tk.Frame(log_frame, bg="#2a2a2a")
        log_text_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.log_box = tk.Text(log_text_frame,
                               height=8,
                               bg="#1e1e1e",
                               fg="#00ff99",
                               insertbackground="#ffffff",
                               font=("Consolas", 8),
                               wrap="word",
                               relief="flat",
                               bd=0,
                               padx=10,
                               pady=8)

        log_scrollbar = ttk.Scrollbar(log_text_frame, orient="vertical", command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=log_scrollbar.set)

        self.log_box.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")

        # Stats section
        stats_frame = self.create_section_frame(parent, "📈 Thống kê")

        self.stats_frame = tk.Frame(stats_frame, bg="#2a2a2a")
        self.stats_frame.pack(fill="x", pady=(10, 0))

        # Tạo các label thống kê
        self.total_label = tk.Label(self.stats_frame,
                                    text="Tổng ảnh: 0",
                                    bg="#2a2a2a", fg="#ffffff",
                                    font=("Segoe UI", 10))
        self.total_label.pack(anchor="w")

        self.success_label = tk.Label(self.stats_frame,
                                      text="Thành công: 0",
                                      bg="#2a2a2a", fg="#4CAF50",
                                      font=("Segoe UI", 10))
        self.success_label.pack(anchor="w")

        self.failed_label = tk.Label(self.stats_frame,
                                     text="Thất bại: 0",
                                     bg="#2a2a2a", fg="#FF5252",
                                     font=("Segoe UI", 10))
        self.failed_label.pack(anchor="w")

    def create_control_section(self, parent):
        """Tạo section điều khiển"""
        control_frame = tk.Frame(parent, bg="#1a1a1a")
        control_frame.pack(fill="x", pady=(15, 0))

        # Buttons
        btn_frame = tk.Frame(control_frame, bg="#1a1a1a")
        btn_frame.pack(anchor="center")

        self.start_btn = ttk.Button(btn_frame,
                                    text="🚀 Bắt đầu tải",
                                    style="Accent.TButton",
                                    command=self.thread_start)
        self.start_btn.pack(side="left", padx=(0, 10), ipady=10, ipadx=20)

        self.stop_btn = ttk.Button(btn_frame,
                                   text="⏹️ Dừng lại",
                                   style="Secondary.TButton",
                                   command=self.stop_download,
                                   state="disabled")
        self.stop_btn.pack(side="left", padx=(0, 10), ipady=10, ipadx=20)

        self.clear_btn = ttk.Button(btn_frame,
                                    text="🧹 Xóa log",
                                    style="Secondary.TButton",
                                    command=self.clear_log)
        self.clear_btn.pack(side="left", ipady=10, ipadx=20)

    def create_section_frame(self, parent, title):
        """Tạo frame cho từng section"""
        section_frame = tk.Frame(parent, bg="#1a1a1a")
        section_frame.pack(fill="both", expand=True, pady=(0, 15))

        # Title
        title_label = tk.Label(section_frame,
                               text=title,
                               font=("Segoe UI", 12, "bold"),
                               bg="#1a1a1a", fg="#ffffff")
        title_label.pack(anchor="w", pady=(0, 8))

        # Content frame
        content_frame = tk.Frame(section_frame, bg="#2a2a2a", relief="flat", bd=1)
        content_frame.pack(fill="both", expand=True, padx=2, pady=2)

        inner_frame = tk.Frame(content_frame, bg="#2a2a2a")
        inner_frame.pack(fill="both", expand=True, padx=10, pady=10)

        return inner_frame

    def clear_placeholder(self, event):
        """Xóa placeholder text"""
        if self.key_text.get("1.0",
                             "end-1c") == "Nhập các từ khóa, mỗi dòng một từ khóa...\nVí dụ:\ncon mèo\ncon chó\nphong cảnh":
            self.key_text.delete("1.0", "end")
            self.key_text.config(fg="#ffffff")

    def add_placeholder(self, event):
        """Thêm placeholder text nếu rỗng"""
        if not self.key_text.get("1.0", "end-1c").strip():
            self.key_text.insert("1.0",
                                 "Nhập các từ khóa, mỗi dòng một từ khóa...\nVí dụ:\ncon mèo\ncon chó\nphong cảnh")
            self.key_text.config(fg="#888888")

    def ui_log(self, msg):
        """Thêm log vào text box"""
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

    def update_progress(self, value):
        """Cập nhật progress bar"""
        self.progress_var.set(value)
        self.progress_label.config(text=f"Tiến trình: {value:.1f}%")

    def update_stats(self, total, success, failed):
        """Cập nhật thống kê"""
        self.stats = {"total": total, "success": success, "failed": failed}
        self.total_label.config(text=f"Tổng ảnh: {total}")
        self.success_label.config(text=f"Thành công: {success}")
        self.failed_label.config(text=f"Thất bại: {failed}")

    def reset_stats(self):
        """Reset thống kê"""
        self.stats = {"total": 0, "success": 0, "failed": 0}
        self.update_stats(0, 0, 0)

    def load_txt(self):
        """Load file txt"""
        path = filedialog.askopenfilename(
            title="Chọn file từ khóa",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                    self.key_text.delete("1.0", tk.END)
                    self.key_text.insert(tk.END, content)
                    self.key_text.config(fg="#ffffff")
                self.ui_log(f"✅ Đã tải file: {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc file: {str(e)}")

    def pick_dir(self):
        """Chọn thư mục lưu"""
        path = filedialog.askdirectory(title="Chọn thư mục lưu ảnh")
        if path:
            self.dir_var.set(path)
            self.ui_log(f"📂 Chọn thư mục: {path}")

    def clear_log(self):
        """Xóa log"""
        self.log_box.delete("1.0", tk.END)
        self.progress_var.set(0)
        self.progress_label.config(text="Sẵn sàng tải...")
        self.reset_stats()

    def stop_download(self):
        """Dừng tải (placeholder)"""
        self.ui_log("⏹️ Đang dừng tải...")
        # TODO: Implement stop functionality

    def thread_start(self):
        """Bắt đầu tải trong thread riêng"""
        keywords_text = self.key_text.get("1.0", tk.END).strip()

        # Kiểm tra placeholder
        if keywords_text == "Nhập các từ khóa, mỗi dòng một từ khóa...\nVí dụ:\ncon mèo\ncon chó\nphong cảnh":
            keywords_text = ""

        keywords = [kw.strip() for kw in keywords_text.splitlines() if kw.strip()]
        per_kw = self.num_var.get()
        folder = self.dir_var.get()

        if not keywords or not folder:
            messagebox.showerror("Thiếu thông tin",
                                 "Vui lòng nhập từ khóa và chọn thư mục lưu.")
            return

        # Cập nhật UI
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.is_downloading = True
        self.progress_var.set(0)
        self.progress_label.config(text="Bắt đầu tải...")
        self.reset_stats()

        # Bắt đầu thread tải
        threading.Thread(target=self.run_download,
                         args=(keywords, per_kw, folder),
                         daemon=True).start()

    def run_download(self, keywords, per_kw, folder):
        """Chạy tải ảnh"""

        def safe_log(msg):
            self.root.after(0, lambda: self.ui_log(msg))

        def safe_progress(value):
            self.root.after(0, lambda: self.update_progress(value))

        def safe_stats(total, success, failed):
            self.root.after(0, lambda: self.update_stats(total, success, failed))

        try:
            download_images(keywords, per_kw, folder, safe_log, safe_progress, safe_stats)
            self.root.after(0, lambda: self.ui_log("🎉 Hoàn thành tải ảnh!"))
        except Exception as e:
            self.root.after(0, lambda: self.ui_log(f"❌ Lỗi: {str(e)}"))
        finally:
            # Reset UI
            self.root.after(0, self.download_finished)

    def download_finished(self):
        """Kết thúc tải"""
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.is_downloading = False
        self.progress_label.config(text="Hoàn thành!")


# ---------- MAIN ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageDownloaderApp(root)
    root.mainloop()