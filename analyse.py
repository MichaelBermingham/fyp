import mplsoccer
import pandas as pd
from matplotlib import pyplot as plt, gridspec
import math
import statistics
from scipy.ndimage import gaussian_filter
from preprocess_data import pitch
# from utils import frame_to_time
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

# def generate_heatmaps(player_num_1, player_num_2, team_id1, team_id2, mins, d, less_more):
#     """
#     Compares the position of two players every 5 minutes and saves as png
#     :param less_more:
#     :param d:
#     :param mins: The number of minute intervals between heatmaps
#     :param team_id2: Team ID of player 2
#     :param team_id1: Team ID of player 1
#     :param player_num_1: player 1 shirt number, or a list of multiple players shirt numbers
#     :param player_num_2: player 2 shirt number, or a list of multiple players shirt numbers
#     """
#     # set var to determine how many rows to grab per figure (assuming each row is one second)
#     # **may not be a good assumption - make more dynamic
#
#     row_intervals = mins * 60
#
#     remove_old_files()
#
#     # determine if the function was passed a list or a single number and create the dataframe accordingly
#     if type(player_num_1) == list:
#         player1 = player_df.loc[
#             (player_df["squadNum"].isin(player_num_1)) & (player_df["team_id"] == team_id1)]
#     else:
#         player1 = player_df.loc[
#             (player_df["squadNum"] == player_num_1) & (player_df["team_id"] == team_id1)]
#
#     if type(player_num_2) == list:
#         player2 = player_df.loc[
#             (player_df["squadNum"].isin(player_num_2)) & (player_df["team_id"] == team_id2)]
#     else:
#         player2 = player_df.loc[
#             (player_df["squadNum"] == player_num_2) & (player_df["team_id"] == team_id2)]
#
#     """
#     Loop that handles creating the heatmaps every x minutes
#     Finds the player(s) position distribution at equal intervals, handles the case where were comparing permutations
#     of lists and players
#     """
#     for i in range(row_intervals, 6000, row_intervals):
#         # create matplotlib.gridspec with 2 figures on top and one below
#         fig = plt.figure(figsize=(14, 14))
#         gs = gridspec.GridSpec(2, 2, height_ratios=[1.5, 1], width_ratios=[1, 1])
#         ax1 = plt.subplot(gs[0, 0])
#         ax2 = plt.subplot(gs[0, 1])
#         ax3 = plt.subplot(gs[1, :])
#
#         # boolean to determine if each player parameter is a list or not
#         is_p1_list = True if type(player_num_1) == list else False
#         is_p2_list = True if type(player_num_2) == list else False
#
#         j = i - row_intervals
#
#         # create the figure with two subplots
#         ax1.set_title(f"Player {player_num_1} at minutes {(i // 60) - mins} - {i // 60}", fontsize=15)
#         ax2.set_title(f"Player {player_num_2} at minutes {(i // 60) - mins} - {i // 60}", fontsize=15)
#
#         # create the player object, which is a slice of the list of player x and y positions
#         p1 = player1.iloc[j:i] if not is_p1_list else player1.iloc[j * len(player_num_1):i * len(player_num_1)]
#         p2 = player2.iloc[j:i] if not is_p2_list else player2.iloc[j * len(player_num_2):i * len(player_num_2)]
#
#         if len(p1) == 0 or len(p2) == 0:
#             missing_data_for = "p1" if len(p1) == 0 else "p2"
#             player_nums_p1 = player_num_1 if type(player_num_1) == list else [player_num_1]
#             player_nums_p2 = player_num_2 if type(player_num_2) == list else [player_num_2]
#             print(f"Data missing for {missing_data_for} in the comparison from minutes {(i // 60) - mins} - {i // 60}")
#             print(
#                 f"Comparing players from team {team_id1}: {player_nums_p1} with players from team {team_id2}: {player_nums_p2}")
#             print(f"Available data for p1: {p1}")
#             print(f"Available data for p2: {p2}")
#             break
#
#         if d != 0:
#             if less_more == ">":
#                 if d <= distance(p1, p2, mins):
#                     continue
#             elif less_more == "<":
#                 if d >= distance(p1, p2, mins):
#                     continue
#
#         # creating both pitches using mplsoccer
#         pitch1 = mplsoccer.Pitch(pitch_type="custom", pitch_length=pitch_length, pitch_width=pitch_width, line_zorder=2,
#                                  pitch_color="#22312b", line_color="#efefef")
#         pitch2 = mplsoccer.Pitch(pitch_type="custom", pitch_length=pitch_length, pitch_width=pitch_width, line_zorder=2,
#                                  pitch_color="#22312b", line_color="#efefef")
#         pitch3 = mplsoccer.Pitch(pitch_type="custom", pitch_length=pitch_length, pitch_width=pitch_width, line_zorder=2,
#                                  pitch_color="grass", line_color="#efefef")
#
#         # draw the pitches on the axes
#         pitch1.draw(ax=ax1)
#         pitch2.draw(ax=ax2)
#         pitch3.draw(ax=ax3)
#
#         # bin statistics and plot the heatmap
#         bin_statistic1 = pitch1.bin_statistic(p1["x"], p1["y"], statistic="count", bins=(25, 25))
#         bin_statistic2 = pitch2.bin_statistic(p2["x"], p2["y"], statistic="count", bins=(25, 25))
#
#         bin_statistic1["statistic"] = gaussian_filter(bin_statistic1["statistic"], 1)
#         bin_statistic2["statistic"] = gaussian_filter(bin_statistic2["statistic"], 1)
#
#         # plot the heatmap
#         pitch1.heatmap(bin_statistic1, ax=ax1, cmap="hot", edgecolors="#22312b")
#         pitch2.heatmap(bin_statistic2, ax=ax2, cmap="hot", edgecolors="#22312b")
#
#         # generate distance graph
#
#         # get average x and y position of the players
#         avg_p1_x = statistics.mean(p1["x"])
#         avg_p1_y = statistics.mean(p1["y"])
#         avg_p2_x = statistics.mean(p2["x"])
#         avg_p2_y = statistics.mean(p2["y"])
#
#         # calculate distance between the average positions
#         dist = distance(p1, p2, mins)
#
#         # add a visual of this distance
#         pitch3.lines(avg_p1_x, avg_p1_y, avg_p2_x, avg_p2_y, lw=5, transparent=False, comet=False,
#                      label="distance between the two players", color="#FF0000", ax=ax3)
#
#         # add the points to the graph
#         ax3.scatter(avg_p1_x, avg_p1_y, s=50, color="black", zorder=3)
#         ax3.scatter(avg_p2_x, avg_p2_y, s=50, color="black", zorder=3)
#
#         # label the points and add a title
#         ax3.text(avg_p1_x, avg_p1_y - 4 if avg_p1_y < avg_p2_y else avg_p1_y + 4, f"{player_num_1}", fontsize=12,
#                  ha="center", va="center", zorder=4, fontweight="bold")
#         ax3.text(avg_p2_x, avg_p2_y + 4 if avg_p1_y < avg_p2_y else avg_p2_y - 4, f"{player_num_2}", fontsize=12,
#                  ha="center", va="center", zorder=4, fontweight="bold")
#
#         ax3.set_title(
#             f"Distance between avg pos of player{player_num_1} ({round(avg_p1_x)}, {round(avg_p1_y)}) and "
#             f"player{player_num_2} ({round(avg_p2_x)}, {round(avg_p2_y)}) = {dist}m",
#             fontsize=15)
#
#         # save the figures and close
#         file_path = f"figures\\playermap{i // 60}.png"
#         fig.savefig(file_path)
#
#         plt.close()


# generate_heatmaps([3, 5], [24, 25], 1, 0, 5, 0, ">")
