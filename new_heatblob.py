import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from mplsoccer import Pitch
from preprocess_data import pitch
import analyse
from shapely.geometry import LineString, Point

# pitch details
pitch_length = pitch["x"]
pitch_width = pitch["y"]


def change_over(input_file, output_file):
    # Read the input CSV file
    data = pd.read_csv(input_file)

    poss_changed = (data["poss"].ne(data["poss"].shift())) & (data["inPlay"].shift() == "Alive") & (
            data["inPlay"] == "Alive")

    change_over_rows = data[poss_changed]
    change_over_rows.to_csv(output_file, index=False)


def extract_frame_nums(input_file, output_file):
    data = pd.read_csv(input_file)
    frame_nums = data["frame_num"]
    frame_nums.to_csv(output_file, index=False, header=True)


def collect_previous_frames(frame_nums_file, data_file, output_file):
    # Load frame numbers of interest
    frame_nums_of_interest = pd.read_csv(frame_nums_file)["frame_num"]

    # Load the main data file
    data = pd.read_csv(data_file)

    # Initialise an empty DataFrame for the results
    collected_data = pd.DataFrame()

    # For each frame number of interest, find the previous 3 unique frame numbers
    for frame_num in frame_nums_of_interest:
        # Find the index of the frame number in the data file
        index = data[data["frame_num"] == frame_num].index.min()

        if pd.notna(index):  # Check if the frame number was found
            # Collect unique frame numbers up to the found index
            unique_frames_up_to_index = data["frame_num"].iloc[:index].drop_duplicates(keep="last")

            # Get the last 3 entries and append the turnover
            if len(unique_frames_up_to_index) >= 3:
                previous_3_frames = unique_frames_up_to_index.iloc[-3:]._append(pd.Series(frame_num))
            else:
                previous_3_frames = unique_frames_up_to_index._append(pd.Series(frame_num))

            # Collect data for these frame numbers
            for prev_frame_num in previous_3_frames:
                collected_data = pd.concat([collected_data, data[data["frame_num"] == prev_frame_num]])

    # Write the collected data to a new CSV file
    collected_data.to_csv(output_file, index=False)


def clean_frames(input, output):
    data = pd.read_csv(input)
    filtered_data = pd.DataFrame()

    previous_frame_num = 0
    for index, row in data.iterrows():
        current_frame_num = row["frame_num"]
        # Include if "Alive" and frame number is greater or equal
        if (current_frame_num >= previous_frame_num) and (row["inPlay"] == "Alive"):
            filtered_data = filtered_data._append(row, ignore_index=True)
            previous_frame_num = current_frame_num

    filtered_data.to_csv(output, index=False)


def heatmap_clean(input_file, pitch_length, pitch_width, blocked_passes):
    # Load the filtered frame numbers
    closeness_df = pd.read_csv(input_file)

    # clear old heatmap images
    analyse.remove_old_files()

    # Generate heatmap for each unique frame found in the filtered frames
    unique_frames = closeness_df["frame_num"].unique()

    for frame in unique_frames:
        # Initialising the pitch
        fig, ax = plt.subplots(figsize=(10, 7))
        pitch = Pitch(pitch_type="custom", pitch_color="#22312b", line_color="white",
                      pitch_length=pitch_length, pitch_width=pitch_width)
        pitch.draw(ax=ax)

        frame_data = closeness_df[closeness_df["frame_num"] == frame]

        if frame_data["poss"].iloc[0] == "H":
            possession_status = "Home Possession"
            possessing_team_id = 1
        else:
            possession_status = "Away Possession"
            possessing_team_id = 0

        ball_x = frame_data["x_ball"].iloc[0]
        ball_y = frame_data["y_ball"].iloc[0]

        # Iterate through the frame data to plot each player and the ball
        for _, row in frame_data.iterrows():
            team_colour = "blue" if row["team_id"] == 0 else "red"
            player_label = f"{row["squadNum"]}"  # label with squad number

            # Plot player
            pitch.scatter(row["x_player"], row["y_player"], ax=ax, s=120, color=team_colour, edgecolors="black",
                          zorder=2)
            plt.text(row["x_player"] + 1, row["y_player"] + 1, player_label, color="white", fontsize=6, ha="center",
                     va="center", zorder=3, bbox=dict(facecolor=team_colour, alpha=0.25, edgecolor=team_colour))

            # Draw line to ball for players on the possessing team
            if row["team_id"] == possessing_team_id:
                pitch.lines(ball_x, ball_y, row["x_player"], row["y_player"], lw=0.6,
                            color="yellow", ax=ax, zorder=1)

            # Retrieve intersection information for the current frame
            frame_intersection_info = blocked_passes.get(frame, [])

            info_text = "".join(
                f"Team ID: {player['team_id']}, Player ID: {player['player_id']}, Squad Number: {player['squad_num']}\n"
                for player in frame_intersection_info)

            plt.figtext(0.5, 0.01, info_text, ha="center", fontsize=10, color="black")

        pitch.scatter(ball_x, ball_y, ax=ax, s=120, color="white", edgecolors="black", zorder=2, label="Ball")

        plt.title(f"Frame: {frame} - {possession_status}", color="Black")
        plt.legend(loc="upper right")

        # Save the heatmap for the current frame
        plt.savefig(f"figures/block_passes_heatmap{frame}.png", dpi=300)
        plt.close()


def create_linestrings(csv_path):
    # Load CSV  into a DataFrame
    df = pd.read_csv(csv_path)

    # dictionary to store the LineStrings for each frame
    linestrings_per_frame = {}

    # Iterate over unique frames
    for frame_num in df["frame_num"].unique():
        frame_data = df[df["frame_num"] == frame_num]

        # Determine team in possession
        possession_team = "1" if frame_data.iloc[0]["poss"] == "H" else "0"

        # Extract ball's position
        ball_origin = frame_data.iloc[0][["x_ball", "y_ball"]].values

        # Create a LineString from the ball to each player in possession
        linestrings = []
        for _, player in frame_data[frame_data["team_id"] == int(possession_team)].iterrows():
            player_origin = (player["x_player"], player["y_player"])
            line = LineString([ball_origin, player_origin])
            linestrings.append((player["player_id"], line))

        # Storing LineStrings for  current frame
        linestrings_per_frame[frame_num] = linestrings

    return linestrings_per_frame


def create_circles(csv_file, proportionality_constant=0.8):
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Initialise a dictionary to store circle geometries
    circles_per_frame = {}

    for frame_num in df["frame_num"].unique():
        frame_data = df[df["frame_num"] == frame_num]
        poss_team_id = 0 if frame_data["poss"].iloc[0] == "A" else 1
        players_not_in_possession = frame_data[frame_data["team_id"] != poss_team_id]  # team in possession

        circles = []
        # Iterate over rows in the filtered DataFrame
        for _, row in players_not_in_possession.iterrows():
            # Extract the player's position and speed
            x_center, y_center, speed = row["x_player"], row["y_player"], row["speed_player"]

            # Calculate the radius based on the player's speed
            radius = speed * proportionality_constant

            # Create a circle with the calculated radius
            circle = Point(x_center, y_center).buffer(radius)
            # Pair the circle with player_id
            circles.append((circle, row['player_id']))

        # Store the list of circles for the current frame in the dictionary
        circles_per_frame[frame_num] = circles

    # circles now contains a dictionary of circle geometries for each player not in possession, with radius related to their speed
    return circles_per_frame


def clean_team_id_data(csv_file_path):
    df = pd.read_csv(csv_file_path)
    # Filter the DataFrame to exclude rows where team_id is -1
    cleaned_df = df[df['team_id'].isin([0, 1])]

    # Save the cleaned DataFrame to csv
    cleaned_df.to_csv(csv_file_path, index=False)


def extract_matching_rows_and_save(frame_nums_csv_path, data_csv_path, output_csv_path):
    # Step 1: Load the frame numbers and data into DataFrames
    frame_nums_df = pd.read_csv(frame_nums_csv_path)
    data_df = pd.read_csv(data_csv_path)

    filtered_data_df = data_df[data_df['frame_num'].isin(frame_nums_df['frame_num'])]

    filtered_data_df.to_csv(output_csv_path, index=False)


def find_intersections(linestrings_per_frame, circles_per_frame, player_info_df):
    # Initialise a dictionary to hold the colored circles for each frame
    intersection_info = {}

    for frame_num, linestrings in linestrings_per_frame.items():
        # Initialise a list for this frame's intersection information
        frame_intersection_info = []

        # Retrieve player information for this frame
        frame_player_info = player_info_df[player_info_df['frame_num'] == frame_num]

        # Retrieve the circle geometries for the current frame
        circles = circles_per_frame.get(frame_num, [])

        unique_ids = set()
        for player_id, line_geom in linestrings:
            for circle, circle_player_id in circles:
                if line_geom.intersects(circle):
                    # Find the player info for the player causing the intersection
                    intersecting_player_info = frame_player_info[frame_player_info['player_id'] == circle_player_id]
                    if not intersecting_player_info.empty:
                        # intersecting_player_info contains all details
                        player_id = intersecting_player_info['player_id'].iloc[0]
                        if player_id not in unique_ids:
                            unique_ids.add(player_id)

                            frame_intersection_info.append({
                                'team_id': intersecting_player_info['team_id'].iloc[0],
                                'player_id': player_id,
                                'squad_num': intersecting_player_info['squadNum'].iloc[0]
                            })

        intersection_info[frame_num] = frame_intersection_info

    return intersection_info


def summarise_intersections(linestrings_per_frame, circles_per_frame, player_info_df):
    """
    Summarizes intersections by frame, counting unique intersections per frame and identifying involved team IDs.

    Parameters:
    - linestrings_per_frame: A dictionary mapping frame numbers to linestrings geometries (each associated with a player ID).
    - circles_per_frame: A dictionary mapping frame numbers to circle geometries (each associated with a player ID).
    - player_info_df: DataFrame containing player information, including team IDs.

    Returns:
    - A dictionary with frame numbers as keys and tuples of unique intersection counts and involved team IDs as values.
    """
    summary_info = {}

    for frame_num, linestrings in linestrings_per_frame.items():
        unique_ids = set()  # To track unique player IDs involved in intersections
        team_ids = set()    # To track unique team IDs involved in intersections

        circles = circles_per_frame.get(frame_num, [])
        for _, line_geom in linestrings:
            for circle, circle_player_id in circles:
                if line_geom.intersects(circle) and circle_player_id not in unique_ids:
                    unique_ids.add(circle_player_id)

                    # Retrieve team ID for the intersecting player
                    intersecting_player_team_id = player_info_df.loc[(player_info_df['frame_num'] == frame_num) &
                                                                     (player_info_df['player_id'] == circle_player_id),
                                                                     'team_id'].iloc[0]
                    team_ids.add(intersecting_player_team_id)

        # If there are intersections, store the count and the set of team IDs
        if unique_ids:
            summary_info[frame_num] = (len(unique_ids), team_ids)

    return summary_info


def main():
    # Working
    # change_over("data/player_and_ball.csv", "blob/new_heatblob.csv")
    # extract_frame_nums("blob/new_heatblob.csv", "blob/frame_nums.csv")
    # clean_team_id_data("blob/new_heatblob.csv")
    # collect_previous_frames("blob/frame_nums.csv", "data/player_and_ball.csv", "blob/previous_3_frames.csv")
    # clean_frames("blob/previous_3_frames.csv", "blob/previous_3_frames_clean.csv")

    # extract_frame_nums("blob/mean_dis_before_turnover1.csv", "blob/first_half_before_turnover_frames.csv")
    # extract_matching_rows_and_save("blob/first_half_before_turnover_frames.csv", "blob/previous_3_frames.csv", "blob/blocking_passes_1.csv")


    # # TODO: DOne
    line_strings = create_linestrings("blob/blocking_passes_2.csv")  # previous_3_frames_clean
    circles = create_circles("blob/blocking_passes_2.csv")
    player_info_df = pd.read_csv("blob/blocking_passes_2.csv")
    blocked_info = summarise_intersections(line_strings, circles, player_info_df)

    flat_data = []
    for frame, (count, team_ids) in blocked_info.items():
        # Since team_ids is a set, you might want to process it into a string or handle it differently
        # For simplicity, let's convert it to a string list
        team_ids_str = ', '.join(map(str, team_ids))
        flat_data.append({
            'frame_num': frame,
            'intersection_count': count,
            'team_ids': team_ids_str
        })

    # Convert the flat data list into a DataFrame
    reuseable_Data = pd.DataFrame(flat_data)

    # Save the DataFrame to a CSV file
    reuseable_Data.to_csv("blob/blocked_numbers2.csv", index=False)

    # csv_file_path = "blob/reuseable_Data.csv"
    # df = pd.read_csv(csv_file_path)
    # blocked_passes = {
    #     frame: group.drop('frame', axis=1).to_dict('records')
    #     for frame, group in df.groupby('frame')
    # }

    # heatmap_clean("blob/previous_3_frames_clean.csv", pitch_length, pitch_width, blocked_passes)

    print("Done.")


if __name__ == "__main__":
    main()
