"""
Modern YouTube Downloader GUI

Dependencies:
    pip install customtkinter yt-dlp

Place this file in the same directory as ytdownloader.py
"""
import customtkinter as ctk
import tkinter.filedialog as fd
import threading
import sys
import os
from ytdownloader import download_youtube_content, parse_multiple_urls

ctk.set_appearance_mode("dark")  # Default to dark mode
ctk.set_default_color_theme("blue")

class RedirectText(object):
    def __init__(self, text_widget):
        self.text_widget = text_widget
    def write(self, string):
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", string)
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")
    def flush(self):
        pass

class DownloaderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader - Modern GUI")
        self.geometry("700x600")
        self.resizable(False, False)

        # URL input
        self.url_label = ctk.CTkLabel(self, text="YouTube URLs (one per line or separated by comma/space):")
        self.url_label.pack(pady=(20, 5), anchor="w", padx=30)
        self.url_text = ctk.CTkTextbox(self, height=100, width=620)
        self.url_text.pack(padx=30, fill="x")

        # Output directory
        self.dir_frame = ctk.CTkFrame(self)
        self.dir_frame.pack(pady=10, padx=30, fill="x")
        self.dir_label = ctk.CTkLabel(self.dir_frame, text="Output Directory:")
        self.dir_label.pack(side="left", padx=(0, 10))
        self.dir_entry = ctk.CTkEntry(self.dir_frame, width=400)
        self.dir_entry.pack(side="left", fill="x", expand=True)
        self.dir_browse = ctk.CTkButton(self.dir_frame, text="Browse", command=self.browse_dir)
        self.dir_browse.pack(side="left", padx=10)

        # Format selection
        self.format_label = ctk.CTkLabel(self, text="Select Format:")
        self.format_label.pack(pady=(10, 0), anchor="w", padx=30)
        self.format_var = ctk.StringVar(value="mp4")
        self.format_frame = ctk.CTkFrame(self)
        self.format_frame.pack(padx=30, fill="x")
        self.mp4_radio = ctk.CTkRadioButton(self.format_frame, text="MP4 Video", variable=self.format_var, value="mp4")
        self.mp3_radio = ctk.CTkRadioButton(self.format_frame, text="MP3 Audio Only", variable=self.format_var, value="mp3")
        self.mp4_radio.pack(side="left", padx=10)
        self.mp3_radio.pack(side="left", padx=10)

        # Quality selection
        self.quality_label = ctk.CTkLabel(self, text="Select Video Quality:")
        self.quality_label.pack(pady=(10, 0), anchor="w", padx=30)
        self.quality_var = ctk.StringVar(value="1080p")
        self.quality_options = ["1080p", "720p", "480p", "360p", "Best Available"]
        self.quality_menu = ctk.CTkOptionMenu(self, variable=self.quality_var, values=self.quality_options)
        self.quality_menu.pack(padx=30, fill="x")

        # Concurrent downloads
        self.workers_label = ctk.CTkLabel(self, text="Concurrent Downloads:")
        self.workers_label.pack(pady=(10, 0), anchor="w", padx=30)
        self.workers_slider = ctk.CTkSlider(self, from_=1, to=5, number_of_steps=4, width=200)
        self.workers_slider.set(3)
        self.workers_slider.pack(padx=30, anchor="w")
        self.workers_value = ctk.CTkLabel(self, text="3")
        self.workers_value.pack(padx=30, anchor="w")
        self.workers_slider.bind("<Motion>", self.update_workers_value)
        self.workers_slider.bind("<ButtonRelease-1>", self.update_workers_value)

        # Start button
        self.start_button = ctk.CTkButton(self, text="Start Download", command=self.start_download)
        self.start_button.pack(pady=20)

        # Progress bar
        self.progress = ctk.CTkProgressBar(self, width=600)
        self.progress.set(0)
        self.progress.pack(pady=(0, 10), padx=30)

        # Log/output area
        self.log_label = ctk.CTkLabel(self, text="Log:")
        self.log_label.pack(anchor="w", padx=30)
        self.log_text = ctk.CTkTextbox(self, height=180, width=620, state="disabled")
        self.log_text.pack(padx=30, pady=(0, 20), fill="x")
        self.stdout_redirect = RedirectText(self.log_text)

    def browse_dir(self):
        path = fd.askdirectory()
        if path:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, path)

    def update_workers_value(self, event=None):
        val = int(self.workers_slider.get())
        self.workers_value.configure(text=str(val))

    def start_download(self):
        # Get URLs
        urls_input = self.url_text.get("1.0", "end").strip()
        urls = parse_multiple_urls(urls_input)
        if not urls:
            self.log("❌ No valid YouTube URLs found. Please check your input.")
            return
        # Output dir
        output_dir = self.dir_entry.get().strip()
        if not output_dir:
            output_dir = os.path.join(os.getcwd(), "downloads")
        os.makedirs(output_dir, exist_ok=True)
        # Format
        audio_only = self.format_var.get() == "mp3"
        # Workers
        max_workers = int(self.workers_slider.get())
        # Disable start button
        self.start_button.configure(state="disabled", text="Downloading...")
        # Clear log
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        # Progress
        self.progress.set(0)
        # Redirect stdout
        self._old_stdout = sys.stdout
        sys.stdout = self.stdout_redirect
        # Start download in thread
        threading.Thread(target=self.download_thread, args=(urls, output_dir, max_workers, audio_only), daemon=True).start()

    def get_format_selector(self):
        # Only select progressive MP4s (audio+video in one file)
        quality = self.quality_var.get()
        if quality == "1080p":
            # 1080p progressive is rare, fallback to best progressive
            return "best[ext=mp4][acodec!=none][vcodec!=none]"
        elif quality == "720p":
            return "best[ext=mp4][height<=720][acodec!=none][vcodec!=none]"
        elif quality == "480p":
            return "best[ext=mp4][height<=480][acodec!=none][vcodec!=none]"
        elif quality == "360p":
            return "best[ext=mp4][height<=360][acodec!=none][vcodec!=none]"
        else:
            return "best[ext=mp4][acodec!=none][vcodec!=none]"

    def download_thread(self, urls, output_dir, max_workers, audio_only):
        try:
            # Patch print to update progress
            total = len(urls)
            completed = [0]
            orig_print = print
            def progress_print(*args, **kwargs):
                orig_print(*args, **kwargs)
                completed[0] += 1 if any(s.startswith("✅") or s.startswith("❌") for s in args if isinstance(s, str)) else 0
                self.progress.set(min(completed[0]/total, 1.0))
            builtins_print = __builtins__["print"] if isinstance(__builtins__, dict) else __builtins__.print
            __builtins__["print"] = progress_print
            format_selector = self.get_format_selector() if not audio_only else (
                'bestaudio/best'  # fallback for audio only
            )
            download_youtube_content(urls, output_dir, max_workers=max_workers, audio_only=audio_only, format_selector=format_selector)
            __builtins__["print"] = builtins_print
        except Exception as e:
            self.log(f"❌ Error: {e}")
        finally:
            sys.stdout = self._old_stdout
            self.start_button.configure(state="normal", text="Start Download")
            self.progress.set(1.0)

    def log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

if __name__ == "__main__":
    app = DownloaderGUI()
    app.mainloop() 