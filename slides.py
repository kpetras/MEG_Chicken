import matplotlib.pyplot as plt
import os
from matplotlib.widgets import Button

def display_slides(slide_folder):
    slides = [os.path.join(slide_folder, f) for f in sorted(os.listdir(slide_folder)) if f.endswith(('.png', '.jpg'))]
    current_slide = [0]  # Mutable object to change in nested function

    def next_slide(event):
        if current_slide[0] < len(slides) - 1:
            current_slide[0] += 1
            update_slide()

    def prev_slide(event):
        if current_slide[0] > 0:
            current_slide[0] -= 1
            update_slide()

    def update_slide():
        slide_image.set_data(plt.imread(slides[current_slide[0]]))
        fig.canvas.draw()

    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.2)
    slide_image = plt.imshow(plt.imread(slides[0]), aspect='auto')
    ax.axis('off')  # Hide axes

    axprev = plt.axes([0.1, 0.05, 0.1, 0.075])
    axnext = plt.axes([0.8, 0.05, 0.1, 0.075])
    bnext = Button(axnext, 'Next')
    bnext.on_clicked(next_slide)
    bprev = Button(axprev, 'Previous')
    bprev.on_clicked(prev_slide)

    plt.show()

# Usage
slide_folder = 'C:\\Users\\stagaire\\Desktop\\Coline\\MEG_Chicken\slides\\' 
display_slides(slide_folder)