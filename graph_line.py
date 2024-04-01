import pandas as pd
import matplotlib.pyplot as plt


def visualise_mean_distance(csv_file):
    # Load the CSV data into a DataFrame
    df = pd.read_csv(csv_file, sep=",")

    # Plotting
    plt.figure(figsize=(20, 10))

    # Plot each possession type with different colors
    for poss, color in [("A", "blue"), ("H", "red")]:
        # Filter the DataFrame by possession type
        filtered_df = df[df["poss"] == poss]

        # Plotting
        plt.plot(filtered_df["frame_num"], filtered_df["mean_distance"], "o", color=color, label=f"Possession: {poss}")

    # Adding labels and title
    plt.xlabel("Frame Numbers in Sequences of approx. 9 Minutes.")
    plt.ylabel("Mean Distance")
    plt.title("Mean Distance per Frame 1st Half")
    plt.legend()
    plt.grid(True)

    # Show the plot
    plt.show()


def visualise_intersection_counts(csv_file):
    # Load the CSV data into a DataFrame
    df = pd.read_csv(csv_file)

    # Setting up the plot
    plt.figure(figsize=(20, 10))

    team_labels = {0: "Away", 1: "Home"}

    # Plot each team's intersection count with labels for Home and Away
    for team_id, label in team_labels.items():
        # Filter the DataFrame by team_id
        filtered_df = df[df["team_ids"] == team_id]

        # Plotting
        plt.plot(filtered_df["frame_num"], filtered_df["intersection_count"], "o-", label=f"Team: {label}")

    # Adding labels and title
    plt.xlabel("Frame Numbers of grid steps of approx 7 minutes")
    plt.ylabel("Intersection Count")
    plt.title("Pass Blocking Count in Frames before Turnovers (2nd Half)")
    plt.legend()
    plt.grid(True)

    # Show the plot
    plt.show()


#visualise_mean_distance("mean_dis_before_turnover1.csv")
visualise_intersection_counts("blocked_numbers2.csv")