import tkinter as tk
from tkinter import messagebox
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.image as mpimg


def display_slides(slide_folder, master=None):
    """
    Displays slides in a separate, modal-like Tkinter window, blocking further code execution until closed.

    Args:
        slide_folder (str): Directory containing slides.
        master (tk.Tk or tk.Toplevel): The parent window. If None, uses the default root window.
    """
    # Load slides from folder
    slides = [os.path.join(slide_folder, f) for f in sorted(os.listdir(slide_folder)) if f.endswith(('.png', '.jpg'))]
    if not slides:
        print("No slides found in the folder.")
        return

    slide_window = tk.Toplevel(master)
    slide_window.title("Slide Show")
    slide_window.state('zoomed') # Full screen

    # Load the first image to get its resolution since the current one is kinda blurry?
    slide_image = mpimg.imread(slides[0])
    img_height, img_width, _ = slide_image.shape

    fig = plt.Figure(figsize=(img_width / 100, img_height / 100), dpi=100)  # Adjust dpi and size
    ax = fig.add_subplot(111)
    slide_image = plt.imread(slides[0])
    img_display = ax.imshow(slide_image)
    ax.axis('off')  # Hide axes
    

    canvas = FigureCanvasTkAgg(fig, master=slide_window)
    canvas.get_tk_widget().grid(row=0, column=0, columnspan=2)
    current_slide = [0]

    def update_slide():
        """Updates the displayed slide on the canvas and updates button states."""
        slide_image = plt.imread(slides[current_slide[0]])
        img_display.set_data(slide_image)
        canvas.draw()
        if current_slide[0] == len(slides) - 1:
            # Last slide: change "Next" button to "End"
            btn_next.config(text="End", command=end_slideshow)
        else:
            # Not last slide: ensure "Next" button is normal
            btn_next.config(text="Next", command=next_slide)
        if current_slide[0] == 0:
            btn_prev.config(state="disabled")
        else:
            btn_prev.config(state="normal")

    def next_slide():
        if current_slide[0] < len(slides) - 1:
            current_slide[0] += 1
            update_slide()

    def prev_slide():
        if current_slide[0] > 0:
            current_slide[0] -= 1
            update_slide()

    def end_slideshow():
        slide_window.destroy()
        
    # Previous and Next buttons
    btn_prev = tk.Button(slide_window, text="Previous", command=prev_slide)
    btn_prev.grid(row=1, column=0, sticky="ew")
    btn_next = tk.Button(slide_window, text="Next", command=next_slide)
    btn_next.grid(row=1, column=1, sticky="ew")

    # Wait for the slide window to close before returning to main code
    slide_window.transient()
    slide_window.grab_set()
    slide_window.wait_window()

