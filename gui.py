import tkinter as tk
import pandas as pd
import analyse
from tkinter import messagebox
from PIL import Image, ImageTk

import line_player_v_player
import new_heatblob

# New global variables for team IDs
team_id1 = None
team_id2 = None
# Global variable to store the current mode
current_mode = None
# Declare widget variables globally
frame_team_id1 = None
frame_team_id2 = None
label_team_id1 = None
label_team_id2 = None
entry_player_num_1 = None
entry_player_num_2 = None
entry_mins = None
entry_d = None
entry_less_more = None
team_labels = {
    0: "Home",
    1: "Away",
    -1: "Other"
}


def clear_interface():
    for widget in root.winfo_children():
        if widget not in [btn_player_vs_player, btn_player_vs_ball, btn_team_closeness, current_interface_label]:
            widget.destroy()


def show_main_window():
    clear_interface()
    current_interface_label.config(text="Select analysis mode")
    current_interface_label.pack(pady=10)
    # Show the initial selection buttons
    btn_player_vs_player.pack(pady=5, padx=20, expand=True)
    btn_player_vs_ball.pack(pady=5, padx=20, expand=True)
    btn_team_closeness.pack(pady=5, padx=20, expand=True)


# def run_generate_heatmaps():
#     # Check if widgets are initialized
#     if entry_player_num_1 is None or entry_player_num_2 is None:
#         messagebox.showerror("Error", "Please select an analysis mode first.")
#         return
#
#     # Validate and read values from the GUI
#     valid1, player_num_1 = is_valid_number_list(entry_player_num_1.get())
#     valid2, player_num_2 = is_valid_number_list(entry_player_num_2.get())
#
#     if not (valid1 and valid2):
#         messagebox.showerror("Invalid Input", "Player numbers must be comma-separated integers.")
#         return
#
#     # Validate team IDs
#     if team_id1 is None or team_id2 is None:
#         messagebox.showerror("Invalid Input", "Please set both Team ID 1 and Team ID 2.")
#         return
#
#     try:
#         mins = int(entry_mins.get())
#         d = float(entry_d.get())  # Assuming 'd' can be a decimal
#         less_more = entry_less_more.get()
#         if less_more not in ("<", ">"):
#             raise ValueError("Invalid value for less or more.")
#     except ValueError as e:
#         messagebox.showerror("Invalid Input", str(e))
#         return
#
#     # Call the generate_heatmaps function with validated parameters
#     analyse.generate_heatmaps(player_num_1, player_num_2, team_id1, team_id2, mins, d, less_more)


def is_valid_number_list(input_str):
    try:
        # Attempt to convert each item in the comma-separated string to an integer
        numbers = list(map(int, input_str.split(",")))
        return True, numbers
    except ValueError:
        return False, None


def get_unique_squad_numbers_by_team():
    try:
        player_data = pd.read_csv("data/player.csv")
        team_ids = player_data["team_id"].unique()
        unique_squad_nums_by_team = {}
        for team_id in team_ids:
            unique_squad_nums = sorted(player_data[player_data["team_id"] == team_id]["squadNum"].unique())
            unique_squad_nums_by_team[team_id] = unique_squad_nums
        return unique_squad_nums_by_team
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load player data: {e}")
        return {}


# def update_interface_context(new_context):
#     current_interface_label.config(text=f"Current Mode: {new_context}")


# def show_player_vs_player_interface():
#     global current_mode, entry_player_num_1, entry_player_num_2, entry_mins, entry_d, entry_less_more
#     clear_interface()
#     current_mode = "Player_vs_Player"
#     current_interface_label.config(text="Player/s vs Player/s")
#     current_interface_label.pack(pady=10)
#     btn_player_vs_player.pack_forget()
#     btn_player_vs_ball.pack_forget()
#     btn_team_closeness.pack_forget()
#
#     # Identifying squad numbers and
#     # displaying the available numbers
#     unique_squad_nums_by_team = get_unique_squad_numbers_by_team()
#     label_squad_nums = tk.Label(root, text="")
#     texts = []
#     for team_id, squad_nums in unique_squad_nums_by_team.items():
#         # Get the label from the dictionary, default to "Unknown" if not found
#         team_label = team_labels.get(team_id, "Unknown")
#         texts.append(f"{team_label} Team Available Squad Numbers: " + ", ".join(map(str, squad_nums)))
#     label_squad_nums.config(text="\n".join(texts))
#     label_squad_nums.pack(pady=10)
#
#     # Show Player vs Player interface elements
#     # Create and pack widgets for collecting the necessary parameters
#     tk.Label(root, text="Player Number/s Team 1 (comma-separated):").pack()
#     entry_player_num_1 = tk.Entry(root)
#     entry_player_num_1.pack(pady=10)
#
#     tk.Label(root, text="Player Number/s Team 2 (comma-separated):").pack()
#     entry_player_num_2 = tk.Entry(root)
#     entry_player_num_2.pack(pady=10)
#
#     # Team ID 1 selection buttons
#     frame_team_id1 = tk.Frame(root)  # Frame for Team ID 1 buttons
#     label_team_id1 = tk.Label(frame_team_id1, text="Team ID 1: Not Set")
#     label_team_id1.pack(side=tk.LEFT)
#     tk.Button(frame_team_id1, text="Home", command=lambda: set_team_id1(0)).pack(side=tk.LEFT)
#     tk.Button(frame_team_id1, text="Away", command=lambda: set_team_id1(1)).pack(side=tk.LEFT)
#     frame_team_id1.pack(pady=10)  # Packing the entire frame
#
#     # Team ID 2 selection buttons
#     frame_team_id2 = tk.Frame(root)  # Frame for Team ID 2 buttons
#     label_team_id2 = tk.Label(frame_team_id2, text="Team ID 2: Not Set")
#     label_team_id2.pack(side=tk.LEFT)
#     tk.Button(frame_team_id2, text="Home", command=lambda: set_team_id2(0)).pack(side=tk.LEFT)
#     tk.Button(frame_team_id2, text="Away", command=lambda: set_team_id2(1)).pack(side=tk.LEFT)
#     frame_team_id2.pack(pady=10)  # Packing the entire frame
#
#     tk.Label(root, text="Time Interval (minutes):").pack()
#     entry_mins = tk.Entry(root)
#     entry_mins.pack(pady=10)
#
#     tk.Label(root, text="Distance Threshold (d):").pack()
#     entry_d = tk.Entry(root)
#     entry_d.pack(pady=10)
#
#     tk.Label(root, text="Less or More ('<' or '>'):").pack()
#     entry_less_more = tk.Entry(root)
#     entry_less_more.pack(pady=10)
#
#     # Button to run the analysis
#     run_button = tk.Button(root, text="Generate Heatmaps", command=run_generate_heatmaps)
#     run_button.pack(pady=10)
#
#     # Button to return to the main window
#     back_button = tk.Button(root, text="Back", command=show_main_window)
#     back_button.pack(pady=10)


# Start the GUI loop
def show_team_closeness_interface():
    global current_mode
    global frame_team_id1, label_team_id1, entry_interval
    current_mode = "Team_Closeness"
    # Hide initial options
    btn_player_vs_player.pack_forget()
    btn_player_vs_ball.pack_forget()
    btn_team_closeness.pack_forget()

    # Select Home or Away Team for analysis
    frame_team_id1 = tk.Frame(root)
    label_team_id1 = tk.Label(frame_team_id1, text="Select Team for Closeness Analysis: Not Set")
    label_team_id1.pack(side=tk.LEFT)
    tk.Button(frame_team_id1, text="Home", command=lambda: set_team_id1(0)).pack(side=tk.LEFT)
    tk.Button(frame_team_id1, text="Away", command=lambda: set_team_id1(1)).pack(side=tk.LEFT)
    frame_team_id1.pack(pady=10)

    # Time Interval for analysis
    tk.Label(root, text="Time Interval (minutes):").pack()
    entry_interval = tk.Entry(root)
    entry_interval.pack(pady=10)

    # Placeholder for a run button - functionality to be implemented
    run_button = tk.Button(root, text="Analyse Team Closeness",
                           command=line_player_v_player.main())
    run_button.pack(pady=10)

    # Button to return to the main window
    back_button = tk.Button(root, text="Back", command=show_main_window)
    back_button.pack(pady=10)


def show_player_vs_ball_interface():
    global current_mode, entry_player_squad_num, entry_distance, entry_less_more, entry_interval
    current_mode = "Player_vs_Ball"
    # Hide initial options
    btn_player_vs_player.pack_forget()
    btn_player_vs_ball.pack_forget()
    btn_team_closeness.pack_forget()
    current_interface_label.pack_forget()

    # Identifying squad numbers and
    # displaying the available numbers
    unique_squad_nums_by_team = get_unique_squad_numbers_by_team()
    for team_id, squad_nums in unique_squad_nums_by_team.items():
        # Get the label from the dictionary, default to "Unknown" if not found
        team_label = team_labels.get(team_id, "Unknown")

        squad_nums_info = f"{team_label} Team Available Squad Numbers: " + ", ".join(map(str, squad_nums))
        label_squad_nums = tk.Label(root, text=squad_nums_info)
        label_squad_nums.pack(pady=10)

    # Widgets for selecting a player and specifying parameters
    tk.Label(root, text="Player Squad Number:").pack()
    entry_player_squad_num = tk.Entry(root)
    entry_player_squad_num.pack(pady=10)

    # tk.Label(root, text="Select Home or Away Team:").pack()
    frame_team_id1 = tk.Frame(root)  # Frame for Team ID 1 buttons
    label_team_id1 = tk.Label(frame_team_id1, text="Select Home or Away Team: Not Set")
    label_team_id1.pack(side=tk.LEFT)
    tk.Button(frame_team_id1, text="Home", command=lambda: set_team_id1(0)).pack(side=tk.LEFT)
    tk.Button(frame_team_id1, text="Away", command=lambda: set_team_id1(1)).pack(side=tk.LEFT)
    frame_team_id1.pack(pady=10)  # Packing the entire frame

    tk.Label(root, text="Distance from Ball:").pack()
    entry_distance = tk.Entry(root)
    entry_distance.pack(pady=10)

    tk.Label(root, text="Less or More ('<' or '>'):").pack()
    entry_less_more = tk.Entry(root)
    entry_less_more.pack(pady=10)

    tk.Label(root, text="Time Interval (minutes):").pack()
    entry_interval = tk.Entry(root)
    entry_interval.pack(pady=10)

    # Button to run the analysis for Player vs Ball
    tk.Button(root, text="Analyse Player vs Ball", command=lambda: analyse.run_player_vs_ball_analysis(
        player_squad_num=int(entry_player_squad_num.get()),
        team_id=team_id1,
        distance_threshold=float(entry_distance.get()),
        less_more=entry_less_more.get(),
        mins=int(entry_interval.get())
    )).pack(pady=10)

    # Button to return to the main window
    back_button = tk.Button(root, text="Back", command=show_main_window)
    back_button.pack(pady=10)


def show_blocking_pass_interface():
    global current_mode, entry_player_squad_num, entry_distance, entry_less_more, entry_interval
    current_mode = "Player_vs_Ball"
    # Hide initial options
    btn_player_vs_player.pack_forget()
    btn_player_vs_ball.pack_forget()
    btn_team_closeness.pack_forget()

    # Identifying squad numbers and
    # displaying the available numbers
    unique_squad_nums_by_team = get_unique_squad_numbers_by_team()
    for team_id, squad_nums in unique_squad_nums_by_team.items():
        # Get the label from the dictionary, default to "Unknown" if not found
        team_label = team_labels.get(team_id, "Unknown")

        squad_nums_info = f"{team_label} Team Available Squad Numbers: " + ", ".join(map(str, squad_nums))
        label_squad_nums = tk.Label(root, text=squad_nums_info)
        label_squad_nums.pack(pady=10)

    # Widgets for selecting a player and specifying parameters
    tk.Label(root, text="Player Squad Number:").pack()
    entry_player_squad_num = tk.Entry(root)
    entry_player_squad_num.pack(pady=10)

    # tk.Label(root, text="Select Home or Away Team:").pack()
    frame_team_id1 = tk.Frame(root)  # Frame for Team ID 1 buttons
    label_team_id1 = tk.Label(frame_team_id1, text="Select Home or Away Team: Not Set")
    label_team_id1.pack(side=tk.LEFT)
    tk.Button(frame_team_id1, text="Home", command=lambda: set_team_id1(0)).pack(side=tk.LEFT)
    tk.Button(frame_team_id1, text="Away", command=lambda: set_team_id1(1)).pack(side=tk.LEFT)
    frame_team_id1.pack(pady=10)  # Packing the entire frame

    tk.Label(root, text="Distance from Ball:").pack()
    entry_distance = tk.Entry(root)
    entry_distance.pack(pady=10)

    tk.Label(root, text="Less or More ('<' or '>'):").pack()
    entry_less_more = tk.Entry(root)
    entry_less_more.pack(pady=10)

    tk.Label(root, text="Time Interval (minutes):").pack()
    entry_interval = tk.Entry(root)
    entry_interval.pack(pady=10)

    # Button to run the analysis for Player vs Ball
    tk.Button(root, text="Analyse Player vs Ball", command=new_heatblob.main())

    # Button to return to the main window
    back_button = tk.Button(root, text="Back", command=show_main_window)
    back_button.pack(pady=10)


def set_team_id1(id):
    global team_id1, label_team_id1
    if label_team_id1 is None:
        label_team_id1 = tk.Label(frame_team_id1, text="")
        label_team_id1.pack(side=tk.LEFT)
    team_id1 = id
    label_team_id1.config(text=f"Team ID 1: {"Away" if id == 0 else "Home"}")


def set_team_id2(id):
    global team_id2, label_team_id2
    if label_team_id2 is None:
        label_team_id2 = tk.Label(frame_team_id2, text="")
        label_team_id2.pack(side=tk.LEFT)
    team_id2 = id
    label_team_id2.config(text=f"Team ID 2: {"Away" if id == 0 else "Home"}")


# def resize_img(event):
#     img = Image.open("gui_background.jpeg")
#     resized_img = img.resize((event.width, event.height), Image.ADAPTIVE)
#     background_photo.image = ImageTk.PhotoImage(resized_img)
#     background_label.config(image=background_photo.image)


# TODO: Resize window, remove past buttons, allow option to go back.
# Create the main window
root = tk.Tk()
root.geometry("400x300")
root.title("Heatmap Generator")

# # Load the background image with PIL
# background_image = Image.open("gui_background.jpeg")
# background_photo = ImageTk.PhotoImage(background_image)
# background_label = tk.Label(root, image=background_photo)
# background_label.place(relwidth=1, relheight=1)
#
# root.bind("<Configure>", resize_img)

# label  displaying the current interface context
current_interface_label = tk.Label(root, text="Select an analysis mode", font=("Helvetica", 12, "bold"))
current_interface_label.pack(pady=10)

# Player Influence
btn_player_vs_ball = tk.Button(root, text="Player Influence", command=show_player_vs_ball_interface)
btn_player_vs_ball.pack(pady=5, padx=20, expand=True)

# Team Closeness
btn_player_vs_player = tk.Button(root, text="Team Closeness", command=show_team_closeness_interface)
btn_player_vs_player.pack(pady=5, padx=20, expand=True)

# Blocking Passing Lane interface
btn_team_closeness = tk.Button(root, text="Blocking Passing Lanes", command=show_blocking_pass_interface)
btn_team_closeness.pack(pady=5, padx=20, expand=True)

show_main_window()

# Start the GUI loop
root.mainloop()
