import mplsoccer
import pandas as pd
from matplotlib import pyplot as plt, gridspec
import math
import statistics
from scipy.ndimage import gaussian_filter
from preprocess_data import pitch
import os

# ball and player
player_df = pd.read_csv("data/player.csv")
ball_df = pd.read_csv("data/ball.csv")

# pitch details
pitch_length = pitch["x"]
pitch_width = pitch["y"]


def frame_to_time(frame_num, frame_rate, start_frame):
    adjusted_frame_num = frame_num - start_frame
    total_seconds = adjusted_frame_num / frame_rate
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    return f"{minutes} minutes, {seconds} seconds"


def remove_old_files():
    # remove all heatmaps in the directory
    dir = "figures"

    # Create the directory if it doesn"t exist
    os.makedirs(dir, exist_ok=True)

    for f in os.listdir(dir):
        os.remove(os.path.join(dir, f))


def distance(p1, p2, mins):
    """
    Generate distance between the average x,y of one player, and the average x,y of another
    :param mins: minutes between points
    :param p1: player 1
    :param p2: player 2
    :return: distance
    """

    if len(p1["x"]) == 0 or len(p1["y"]) == 0 or len(p2["x"]) == 0 or len(p2["y"]) == 0:
        return "Undefined"

    # if there is more than one player in the analysis, take an average of their positions for every second
    # max rows for one player
    row_intervals = mins * 60

    p1_x_coords = []
    p1_y_coords = []
    p2_x_coords = []
    p2_y_coords = []

    # account for multiple groups of players
    if len(p1) > row_intervals:
        j = len(p1) // row_intervals
        for i in range(0, len(p1), j):
            temp_slice = p1.iloc[i:i + j]
            p1_x_coords.append(statistics.mean(temp_slice["x"]))
            p1_y_coords.append(statistics.mean(temp_slice["y"]))
    else:
        for i in range(0, len(p1)):
            p1_x_coords.append(p1.iloc[i]["x"])
            p1_y_coords.append(p1.iloc[i]["y"])

    if len(p2) > row_intervals:
        j = len(p2) // row_intervals
        for i in range(0, len(p2), j):
            temp_slice = p2.iloc[i:i + j]
            p2_x_coords.append(statistics.mean(temp_slice["x"]))
            p2_y_coords.append(statistics.mean(temp_slice["y"]))
    else:
        for i in range(0, len(p2)):
            p2_x_coords.append(p2.iloc[i]["x"])
            p2_y_coords.append(p2.iloc[i]["y"])

    average_distance = []

    for i in range(0, row_intervals):
        if i == min(len(p1), len(p2)):
            break
        a = p1_x_coords[i] - p2_x_coords[i]
        b = p1_y_coords[i] - p2_y_coords[i]
        h = math.sqrt((a ** 2) + (b ** 2))

        average_distance.append(h)

    mean_dist = statistics.mean(average_distance)

    return round(mean_dist, 2)


def run_player_vs_ball_analysis(player_squad_num, team_id, distance_threshold, less_more, mins):
    """
    Analyses the distance between a player and the ball over time.
    :param player_squad_num: Squad number of the player
    :param team_id: Team ID of the player
    :param distance_threshold: Distance threshold for comparison
    :param less_more: Whether the distance should be less than or greater than the threshold
    :param mins: Time interval for analysis in minutes
    """
    # one second per row
    row_intervals = mins * 60

    # Load player and ball data
    player_df = pd.read_csv("data/player.csv")
    ball_df = pd.read_csv("data/ball.csv")

    # Filter data for the selected player and the ball
    player_data = player_df.loc[(player_df["squadNum"] == player_squad_num) & (player_df["team_id"] == team_id)]
    # Ball data is assumed to be in the ball_df

    for i in range(row_intervals, len(player_data), row_intervals):
        j = i - row_intervals
        player_slice = player_data.iloc[j:i]
        ball_slice = ball_df.iloc[j:i]

        if player_slice.empty or ball_slice.empty:
            print(f"No data for player or ball in the interval from {j} to {i}")
            continue

        # Calculate distance between player and ball for each frame
        distances = calculate_distances(player_slice, ball_slice)

        # Create the figure with three subplots
        fig = plt.figure(figsize=(14, 7))

        # creating a grid specification object
        gs = gridspec.GridSpec(1, 3)  # 1 row, 3 columns

        # Initialise the pitch
        pitch = mplsoccer.Pitch(pitch_type="custom", pitch_length=pitch_length, pitch_width=pitch_width, line_zorder=2,
                                pitch_color="#22312b", line_color="#efefef")

        ax1 = plt.subplot(gs[0, 0])  # Player heatmap
        ax2 = plt.subplot(gs[0, 1])  # Ball heatmap
        ax3 = plt.subplot(gs[0, 2])  # Distance heatmap

        # Draw the pitch on each subplot
        pitch.draw(ax=ax1)
        pitch.draw(ax=ax2)
        pitch.draw(ax=ax3)

        # Heatmap for player
        # calculating a 2D histogram of the player’s positions. pitch is divided into a grid of 25x25 bins
        # the number of times the player is found in each bin is counted.
        bin_statistic_player = pitch.bin_statistic(player_slice["x"], player_slice["y"], statistic="count",
                                                   bins=(25, 25))
        # applying a Gaussian filter to the 2D histogram.
        # smooths the data, highlighting trends in the player’s position over time.
        bin_statistic_player["statistic"] = gaussian_filter(bin_statistic_player["statistic"], 1)

        # creating a heatmap from the smoothed 2D histogram.
        # heatmap plotted on the subplot ax1, with a hot colormap (higher values are  warmer colors), edge colours dark green
        pitch.heatmap(bin_statistic_player, ax=ax1, cmap="hot", edgecolors="#22312b")

        # Heatmap for ball
        bin_statistic_ball = pitch.bin_statistic(ball_slice["x"], ball_slice["y"], statistic="count", bins=(25, 25))
        bin_statistic_ball["statistic"] = gaussian_filter(bin_statistic_ball["statistic"], 1)
        pitch.heatmap(bin_statistic_ball, ax=ax2, cmap="hot", edgecolors="#22312b")

        print("Length of player_slice:", len(player_slice))
        print("Length of distances:", len(distances))

        # Initialise relevant_positions outside the inner loop
        relevant_positions = []

        counter = 0  # Initialise a counter to align with the distances list
        for index, row in player_slice.iterrows():
            if counter >= len(distances):
                print("Counter exceeds length of distances list:", counter)
                break

            # Distance heatmap
            # Determine player positions within the specified distance from the ball
            # uses counter to access elements in distances
            if ((less_more == ">" and distances[counter] > distance_threshold) or
                    (less_more == "<" and distances[counter] < distance_threshold)):
                relevant_positions.append((row["x"], row["y"]))

            counter += 1  # Increment the counter

        # Convert to DataFrame for easier processing
        relevant_positions_df = pd.DataFrame(relevant_positions, columns=["x", "y"])

        # Create a heatmap for these positions
        if not relevant_positions_df.empty:
            bin_statistic_distance = mplsoccer.Pitch().bin_statistic(relevant_positions_df["x"],
                                                                     relevant_positions_df["y"], statistic="count",
                                                                     bins=(25, 25))
            bin_statistic_distance["statistic"] = gaussian_filter(bin_statistic_distance["statistic"], 1)
            mplsoccer.Pitch().heatmap(bin_statistic_distance, ax=ax3, cmap="hot", edgecolors="#22312b")
            ax3.set_title("Player's Positions Within Specified Distance from Ball")
        else:
            ax3.text(0.5, 0.5, "No Data within Specified Distance", horizontalalignment="center",
                     verticalalignment="center", transform=ax3.transAxes)

        # Add titles
        ax1.set_title("Player Movement")
        ax2.set_title("Ball Movement")
        ax3.set_title(f"Player's Positions Within Specified {distance_threshold} metre/s from Ball")

        # Save the figure
        fig.savefig(f"figures/player_ball_distance_{j // 60}_{i // 60}.png")

        plt.close(fig)
        print("Done.")


def calculate_distances(player_data, ball_data):
    """
    Calculate distances between player and ball for each frame.
    :param player_data: DataFrame containing player positions
    :param ball_data: DataFrame containing ball positions
    :return: Series or list of distances
    """
    distances = []
    for player_row, ball_row in zip(player_data.itertuples(), ball_data.itertuples()):
        player_pos = (player_row.x, player_row.y)
        ball_pos = (ball_row.x, ball_row.y)
        # Euclidean distance between the two points
        distance = math.sqrt((player_pos[0] - ball_pos[0]) ** 2 + (player_pos[1] - ball_pos[1]) ** 2)
        distances.append(distance)
    return distances
