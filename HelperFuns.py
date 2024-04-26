# HelperFuns.py

import tkinter as tk
import time
import threading

def display_message(message, color):
    # Create a new Tk root
    root = tk.Tk()

    # Hide the root window drag bar and close button
    root.overrideredirect(True)
    root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))

    # Make the root window always on top
    root.attributes('-topmost', True)

    # Create a label with the message
    label = tk.Label(root, text=message, fg=color, bg='black',
                     font=('Helvetica', 72), padx=root.winfo_screenwidth() // 2,
                     pady=root.winfo_screenheight() // 2)

    # Add the label to the root
    label.pack()

    # Update the GUI
    root.update()

    # Pause for 1 second
    time.sleep(1)

    # Destroy the root
    root.destroy()

def monitor_bads(fig, answer,shared):
    # Initialize previous_bads to an empty list
    previous_bads = []
    
    # Initialize a counter
    counter = 0

    try:
        print("start loop")

        while True:
            # Get the current bads
            current_bads = fig.mne.info['bads']
            # Check if the space key has been pressed
            if shared.get('space_pressed', False):
                print("Space key pressed.")
                
                answer_set = set(answer)
                current_bads_set = set(current_bads)

                # New : Trouver les channels manquants en comparant les deux ensembles
                missing_channels = answer_set - current_bads_set

                if missing_channels:
                    print(f"Missing channels: {', '.join(missing_channels)}")
                else:
                    print("All bad channels were correctly identified.")
                break
            
            # print("Current bads: ", current_bads)  # Check if current_bads is updating

            # Check if the length has changed
            if len(current_bads) != len(previous_bads):
                # print("Length of bads has changed.")

                # Find which elements were added
                added = set(current_bads) - set(previous_bads)
                if added:
                    print("Added: ", added)
                    # check if added is in the answer
                    added_in_answer = [item for item in added if item in answer]

                    if added_in_answer:
                        print("Correctly added: ", added_in_answer)
                        #display_message("Good Job!", "green")
                    else:
                        print("Incorrectly added: ", added)
                        #display_message("Incorrect! Try again", "red")

                # Find which elements were removed
                removed = set(previous_bads) - set(current_bads)
                if removed:
                    print("Removed: ", removed)
                    # check if removed is in the answer
                    removed_in_answer = [item for item in removed if item not in answer]
                    if removed_in_answer:
                        print("Correctly removed: ", removed_in_answer)
                    else:
                        print("Incorrectly removed: ", removed)

            # Update previous_bads
            previous_bads = current_bads.copy()

            # Increment the counter
            counter += 1

            # Break the loop after 20 iterations
            if shared.get('escape_pressed', False):
                break

            # Wait for a short period of time before checking again
            time.sleep(1)
            
        print("end loop")
        
    except Exception as e:
        print("Error in thread: ", e)  # Check if there's an error in the thread
        
def monitor_ICs(ica, answer, shared):
    # Initialize previous_bads to an empty list
    previous_bads = []
    
    # Initialize a counter
    counter = 0

    try:
        print("start loop")

        while True:
            # Get the current bads
            current_bads = ica.exclude
            # Check if the space key has been pressed
            if shared.get('space_pressed', False):
                print("Space key pressed.")
                
                answer_set = set(answer)
                current_bads_set = set(current_bads)

                # New : Trouver les channels manquants en comparant les deux ensembles
                missing_ICs = answer_set - current_bads_set

                if missing_ICs:
                    print(f"Missing ICs: {', '.join(map(str, missing_ICs))}")
                else:
                    print("All bad ICs were correctly identified.")
                break

            # print("Current bads: ", current_bads)  # Check if current_bads is updating

            # Check if the length has changed
            if len(current_bads) != len(previous_bads):
                # print("Length of bads has changed.")

                # Find which elements were added
                added = set(current_bads) - set(previous_bads)
                if added:
                    print("Added: ", added)
                    # check if added is in the answer
                    added_in_answer = [item for item in added if item in answer]

                    if added_in_answer:
                        print("Correctly added: ", added_in_answer)
                        #display_message("Good Job!", "green")
                    else:
                        print("Incorrectly added: ", added)
                        #display_message("Incorrect! Try again", "red")

                # Find which elements were removed
                removed = set(previous_bads) - set(current_bads)
                if removed:
                    print("Removed: ", removed)
                    # check if removed is in the answer
                    removed_in_answer = [item for item in removed if item not in answer]
                    if removed_in_answer:
                        print("Correctly removed: ", removed_in_answer)
                    else:
                        print("Incorrectly removed: ", removed)

            # Update previous_bads
            previous_bads = current_bads.copy()

            # Increment the counter
            counter += 1

            # Break the loop after 20 iterations
            if counter >= 20:
                break

            # Wait for a short period of time before checking again
            time.sleep(1)
            
        print("end loop")
        
    except Exception as e:
        print("Error in thread: ", e)  # Check if there's an error in the thread