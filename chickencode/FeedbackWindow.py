import tkinter as tk
from PIL import Image, ImageTk
from playsound import playsound
import os
from .run_funcs import compute_dprime
import threading

class FeedbackWindow:
    """
        A popup window for immediate 'CORRECT' or 'INCORRECT' feedback.
        The participant must close it manually to continue.
        """
    def __init__(self, master, is_correct):
        self.master = master
        self.is_correct = is_correct
        self.popup = tk.Toplevel(self.master)
        self.popup.title("Feedback")
        self.popup.attributes("-topmost", True)
        
        self._images = [] 

        # Background pic
        correct_image = 'correct.png'
        incorrect_image = 'wrong.png'
        image_path = os.path.join('resource',correct_image if self.is_correct else incorrect_image)
        self.original_img = Image.open(image_path)
        orig_width, orig_height = self.original_img.size
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        scale_factor = min(screen_width / orig_width, screen_height / orig_height)
        new_width = int(orig_width * scale_factor)
        new_height = int(orig_height * scale_factor)

        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = Image.ANTIALIAS
        resized_img = self.original_img.resize((new_width, new_height), resample_filter)
        
        self.popup.geometry(f"{new_width}x{new_height}")

        self.bg_image_tk = ImageTk.PhotoImage(resized_img)
        self.bg_label = tk.Label(self.popup, image=self.bg_image_tk)
        self.bg_label.pack() 

        # Chicken Sound playback
        self.play_sound_thread()
        self.popup.update_idletasks()  # Process pending GUI operations
        self.popup.update()

        self.popup.after(1000, self.popup.destroy)

    def play_sound_thread(self):
        """Play sound without blocking the GUI."""
        def _play():
            sound_file = 'correct.mp3' if self.is_correct else 'wrong.mp3'
            playsound(os.path.join('resource', sound_file))
        threading.Thread(target=_play, daemon=True).start()

class TrialEndWindow:
    """
    A window that pops up at the end of trial (on close).
    Two options provided:
    1) Close the trial and move on to the next
    2) Save and quit
    """

    def __init__(self, master, trial_idx, hits, false_alarms, misses, correct_rejections, missed_channels):
        self.master = master
        
        self.top = tk.Toplevel(self.master)
        self.top.title("Trial Feedback")
        self.top.attributes("-topmost", True)
        # self.top.geometry("500x300+500+300")

        self.user_wants_quit = False  # Flag

        denom = hits + false_alarms + misses + correct_rejections
        accuracy = (hits + correct_rejections) / denom if denom > 0 else 0
        dprime = compute_dprime(hits, false_alarms, misses, correct_rejections)
        
        if not missed_channels:
            missed_bads = "Missed Bads: None\n"
        else:
            missed_bads = "Missed Bads:\n" + "\n".join(str(ch) for ch in missed_channels) + "\n"

        info_text = (
            f"Trial {trial_idx} ended!\n\n"
            f"Hits: {hits}\n"
            f"False Alarms: {false_alarms}\n"
            f"Misses: {misses}\n"
            f"Correct Rejections: {correct_rejections}\n"
            f"Accuracy: {accuracy*100:.1f}\n"
            f"D-Prime: {dprime:.3f}\n"
            "\n"
            f"{missed_bads}"
        )

        self.label_info = tk.Label(self.top, text=info_text, font=("Arial", 14), justify="left")
        self.label_info.pack(padx=20, pady=20)

        btn_frame = tk.Frame(self.top)
        btn_frame.pack(pady=10)

        btn_close = tk.Button(btn_frame, text="Close", width=12, command=self._on_close)
        btn_close.pack(side="left", padx=5)

        btn_savequit = tk.Button(btn_frame, text="Save & Quit", width=12, command=self._on_save_quit)
        btn_savequit.pack(side="left", padx=5)

        self.top.grab_set()
        self.top.wait_window(self.top)

    def _on_close(self):

        self.user_wants_quit = False
        self.top.destroy()

    def _on_save_quit(self):
        self.user_wants_quit = True
        self.top.destroy()
