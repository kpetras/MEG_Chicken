import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import Image, ImageTk
from playsound import playsound
import os
from run_funcs import compute_dprime

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
        self.popup.geometry("500x300+500+300")  # Offset but im not sure if it's generally a good one
        
        # Background pic
        correct_image = 'correct.png'
        incorrect_image = 'wrong.png'
        image_path = os.path.join('resource',correct_image if self.is_correct else incorrect_image)
        self.original_img = Image.open(image_path)
        self.bg_image_tk = None
        self.bg_label = tk.Label(self.popup)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        self.popup.bind("<Configure>", self.on_resize)
        
        # Chicken Sound playback
        if is_correct:
            playsound(os.path.join('resource', 'correct.mp3'))
        else:
            playsound(os.path.join('resource', 'wrong.mp3'))
               
        # Use global grab so that we can block other windows, but sometimes it doesnt work
        self.popup.grab_set_global()
        self.popup.wait_window(self.popup)

    def on_resize(self, event):
        new_w = event.width
        new_h = event.height
        resized_img = self.original_img.resize((new_w, new_h), Image.LANCZOS)
        self.bg_image_tk = ImageTk.PhotoImage(resized_img)
        self.bg_label.config(image=self.bg_image_tk)


class TrialResultWindow:
    """
        A white-background window that stays open throughout the experiment,
        displaying trial-by-trial accuracy in a line plot.
        """
    def __init__(self, master=None):
        if master is None:
            self.master = tk.Toplevel()
        else:
            self.master = tk.Toplevel(master)
        self.master.title("Trial Result Window")
        self.master.configure(bg="white")
        # self.master.geometry("500x300+500+300")
        self.master.attributes("-top", True)
        self.plot_created = False # Flag
        self.master.protocol("WM_DELETE_WINDOW", self._on_user_close)
        self.instruction_label = tk.Label(
                                          self.master,
                                          text="Here's some random instruction.\n"
                                          "Click on the title if and only if you are certain about the answer.\n"
                                          "Click on the lines if you are not sure and what to verify.",
                                          fg="black",
                                          bg="white",
                                          font=("Arial", 24, "bold"),
                                          justify="left"
                                          )
        self.instruction_label.pack(side="top", fill="both", padx=10, pady=20)
                                          
    def _on_user_close(self):
        """
        Just making sure that it IS closed when we closed it, so that when we accidently close it
        the program would regenerate a window
        """
        if self.master.winfo_exists():
            self.master.destroy()

    def create_plot(self):
        self.instruction_label.pack_forget()
        
        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        
        self.ax.set_title("Trial-by-Trial Accuracy")
        self.ax.set_xlabel("Trial #")
        self.ax.set_ylabel("Accuracy")
        self.ax.set_ylim(0, 1)
        self.ax.grid(True)
        self.fig.tight_layout()
        self.line, = self.ax.plot([], [], marker='o', linestyle='-', color='b')
        
        self.plot_created = True # Flag to True
    
    def set_accuracies(self, full_list):
        if not self.plot_created:
            self.create_plot()

        x_data = range(1, len(list(full_list)) + 1)
        y_data = list(full_list)

        self.line.set_xdata(x_data)
        self.line.set_ydata(y_data)
        self.ax.set_xlim(1, max(1, len(x_data)+1))
        self.ax.set_ylim(0, 1.05)
        self.canvas.draw()


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
