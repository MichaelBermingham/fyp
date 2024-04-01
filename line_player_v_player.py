import matplotlib.pyplot as plt
import pandas as pd
from mplsoccer.pitch import Pitch
from matplotlib import gridspec
import numpy as np

from preprocess_data import pitch
import analyse

# pitch details
pitch_length = pitch["x"]
pitch_width = pitch["y"]


def calculate_closeness(input_data):
    # Calculate the distance to the ball for each player in each frame
    input_data["distance_to_ball"] = np.sqrt(
        (input_data["x_player"] - input_data["x_ball"]) ** 2 +
        (input_data["y_player"] - input_data["y_ball"]) ** 2
    )

    closeness_records = []
    for frame in input_data["frame_num"].unique():
        frame_data = input_data[input_data["frame_num"] == frame]

        # Split by team and sort by distance
        home_team = frame_data[frame_data["team_id"] == 0].sort_values(by="distance_to_ball").head(5)
        away_team = frame_data[frame_data["team_id"] == 1].sort_values(by="distance_to_ball").head(5)

        # Append or process data as needed
        closeness_records.append(home_team)
        closeness_records.append(away_team)

    # Combine all records into a DataFrame
    closeness_df = pd.concat(closeness_records, ignore_index=True)
    return closeness_df


# def player_v_player_closeness_calculation(input_data):
#     closeness_records = []
#
#     for frame in input_data["frame_num"].unique():
#         frame_data = input_data[input_data["frame_num"] == frame]
#
#         home_team = frame_data[frame_data["team_id"] == 1]
#         away_team = frame_data[frame_data["team_id"] == 0]
#
#         # Calculating all pairwise distances and store them with player identifiers.
#         distances = []
#         for _, home_player in home_team.iterrows():
#             for _, away_player in away_team.iterrows():
#                 distance = np.sqrt(
#                     (home_player["x_player"] - away_player["x_player"]) ** 2 +
#                     (home_player["y_player"] - away_player["y_player"]) ** 2
#                 )
#                 distances.append({
#                     "frame_num": frame,
#                     "home_player_id": home_player["player_id"],
#                     "away_player_id": away_player["player_id"],
#                     "distance": distance,
#                     "x_home_player": home_player["x_player"],
#                     "y_home_player": home_player["y_player"],
#                     "x_away_player": away_player["x_player"],
#                     "y_away_player": away_player["y_player"],
#                     "x_ball": home_player["x_ball"],
#                     "y_ball": home_player["y_ball"],
#                     "home_squadNum": home_player["squadNum"],
#                     "away_squadNum": away_player["squadNum"],
#                     "team_id": home_player["team_id"]
#                 })
#
#         # Convert to DataFrame to use pandas functionality for finding unique pairs
#         distances_df = pd.DataFrame(distances)
#         # Sort by distance to get the closest pairs first
#         distances_df.sort_values(by="distance", inplace=True)
#
#         # Loop through sorted distances and create unique pairings
#         paired_home_players = set()
#         paired_away_players = set()
#         for _, row in distances_df.iterrows():
#             home_id = row["home_player_id"]
#             away_id = row["away_player_id"]
#             # Skip if either player is already paired
#             if home_id in paired_home_players or away_id in paired_away_players:
#                 continue
#
#             # Add to record and mark as paired
#             closeness_records.append(row)
#             paired_home_players.add(home_id)
#             paired_away_players.add(away_id)
#
#     closeness_df = pd.DataFrame(closeness_records)
#     return closeness_df

#     # Find unique pairs, ensuring each player appears only once in the pairs
#     unique_pairs = distances_df.drop_duplicates(subset=["home_player_id", "away_player_id"], keep="first")
#
#     # Filter out duplicates, prioritizing closer distances, to ensure uniqueness among home and away players
#     unique_home_pairs = unique_pairs.drop_duplicates(subset="home_player_id", keep="first")
#     unique_away_pairs = unique_pairs.drop_duplicates(subset="away_player_id", keep="first")
#     unique_pairs = pd.concat([unique_home_pairs, unique_away_pairs]).drop_duplicates(keep=False)
#
#     closeness_records.extend(unique_pairs.to_dict("records"))
#
# closeness_df = pd.DataFrame(closeness_records)
# return closeness_df


def calculate_closeness_for_frames(frame_nums_file, input_data_file):
    frame_nums_data = pd.read_csv(frame_nums_file)
    p_b_data = pd.read_csv(input_data_file)

    def mplsoccer(player_ball_data, start_frame):
        closeness_records = []
        unique_frames = player_ball_data[player_ball_data["frame_num"] >= start_frame]["frame_num"].unique()[:3]

        for frame in unique_frames:
            frame_data = player_ball_data[player_ball_data["frame_num"] == frame]

            home_team = frame_data[frame_data["team_id"] == 1]
            away_team = frame_data[frame_data["team_id"] == 0]
            distances = []

            for _, home_player in home_team.iterrows():
                for _, away_player in away_team.iterrows():
                    distance = np.sqrt(
                        (home_player["x_player"] - away_player["x_player"]) ** 2 +
                        (home_player["y_player"] - away_player["y_player"]) ** 2
                    )
                    distances.append({
                        "frame_num": frame,
                        "poss": frame_data["poss"].iloc[0],
                        "home_player_id": home_player["player_id"],
                        "away_player_id": away_player["player_id"],
                        "distance": distance,
                        "x_home_player": home_player["x_player"],
                        "y_home_player": home_player["y_player"],
                        "x_away_player": away_player["x_player"],
                        "y_away_player": away_player["y_player"],
                        "x_ball": home_player["x_ball"],
                        "y_ball": home_player["y_ball"],
                        "home_squadNum": str(int(home_player["squadNum"])),
                        "away_squadNum": str(int(away_player["squadNum"])),
                        "team_id": home_player["team_id"]
                    })

            distances_df = pd.DataFrame(distances)
            distances_df.sort_values(by="distance", inplace=True)

            # Dropping the row with the largest distance (goalkeepers)
            if not distances_df.empty:
                distances_df = distances_df[:-1]  # Exclude the largest distance

            paired_home_players = set()
            paired_away_players = set()
            for _, row in distances_df.iterrows():
                home_id = row["home_player_id"]
                away_id = row["away_player_id"]
                if home_id in paired_home_players or away_id in paired_away_players:
                    continue
                closeness_records.append(row)
                paired_home_players.add(home_id)
                paired_away_players.add(away_id)

        return pd.DataFrame(closeness_records)

    all_closeness_records = []
    for frame_num in frame_nums_data["frame_num"]:
        closeness_df = mplsoccer(p_b_data, frame_num)
        all_closeness_records.append(closeness_df)

    # Concatenate all closeness records into a single DataFrame
    final_closeness_df = pd.concat(all_closeness_records, ignore_index=True)
    final_closeness_df.to_csv("blob/closeness_for_frames.csv", index=False)


def calculate_mean_distance_per_frame(csv_file):
    # Load the CSV file into a DF
    df = pd.read_csv(csv_file)
    # Group by frame_num and calculate the mean of distance
    mean_distances = df.groupby(["frame_num", "poss"])["distance"].mean().reset_index()
    # Rename columns
    mean_distances.columns = ["frame_num", "poss", "mean_distance"]

    return mean_distances


def preprocess_for_closeness(data):
    # This is a simplified placeholder logic
    relevant_frames = data[(data["inPlay"] == "Alive")].copy()
    return relevant_frames


def five_v_five_heatmap(closeness_df, pitch_length, pitch_width, mean_per_frame):
    analyse.remove_old_files()  # Clears old heatmap images

    # Generate heatmap for the first 10 unique frames
    unique_frames = closeness_df["frame_num"].unique()

    for frame in unique_frames:
        # Initialise the pitch
        fig, ax = plt.subplots(figsize=(10, 7))
        pitch = Pitch(pitch_type="custom", pitch_color="#22312b", line_color="white",
                      pitch_length=pitch_length, pitch_width=pitch_width)
        pitch.draw(ax=ax)

        frame_data = closeness_df[closeness_df["frame_num"] == frame]

        if frame_data["poss"].iloc[0] == "H":
            possession_status = "Home Possession"
        else:
            possession_status = "Away Possession"

        # Plot players and draw lines between home players and their closest opponents
        for _, row in frame_data.iterrows():
            # Colour code based on team_id
            # home_color = "red" if row["team_id"] == 1 else "blue"
            # away_color = "blue" if row["team_id"] == 0 else "red"

            # Home player
            pitch.scatter(row["x_home_player"], row["y_home_player"], ax=ax, s=120, color="red", edgecolors="black",
                          zorder=2)
            home_p = row["home_squadNum"]
            plt.text(row["x_home_player"] + 1, row["y_home_player"] + 1, home_p, color="white", fontsize=6, ha="center",
                     va="center", zorder=3, bbox=dict(facecolor="red", alpha=0.25, edgecolor="black"))

            # Away player
            pitch.scatter(row["x_away_player"], row["y_away_player"], ax=ax, s=120, color="blue", edgecolors="black",
                          zorder=2)
            away_p = row["away_squadNum"]
            plt.text(row["x_away_player"] + 1, row["y_away_player"] + 1, away_p, color="white", fontsize=6, ha="center",
                     va="center", zorder=3, bbox=dict(facecolor="blue", alpha=0.25, edgecolor="black"))

            # Line between home player and opponent indicating closeness
            pitch.lines(row["x_home_player"], row["y_home_player"], row["x_away_player"], row["y_away_player"], lw=1,
                        color="yellow", ax=ax, zorder=1)

        # Plot the ball's position
        ball_x = row["x_ball"]
        ball_y = row["y_ball"]
        pitch.scatter(ball_x, ball_y, ax=ax, s=120, color="white", edgecolors="black", zorder=2, label="Ball")

        plt.title(f"Frame: {frame} - {possession_status}", color="black")

        # Find the mean distance for the current frame from mean_per_frame DataFrame
        frame_mean_distance = mean_per_frame.loc[mean_per_frame['frame_num'] == frame, 'mean_distance'].iloc[0]
        info_text = f"Mean Distance: {frame_mean_distance:.2f}"

        plt.figtext(0.5, 0.01, info_text, ha="center", fontsize=10, color="black")

        plt.legend(loc="upper right")

        # Save the heatmap for the current frame
        plt.savefig(f"figures/player_v_player_heatmap_frame_{frame}.png", dpi=300)
        plt.close()


def detect_inplay_changes(csv_file, output_file):
    # Read the CSV file
    data = pd.read_csv(csv_file)

    # Find rows where the "inPlay" status changes
    status_changed = data["inPlay"].ne(data["inPlay"].shift())
    change_indices = data.index[status_changed][1:]

    # Create a list to hold the rows where status changes
    change_rows = []
    for idx in change_indices:
        # Append the row before the change and the row at the point of change
        change_rows.extend(data.iloc[[idx - 1, idx]].values.tolist())

    # Convert the list to a DataFrame
    change_df = pd.DataFrame(change_rows, columns=data.columns)

    # Output to a new CSV file, this will create the file if it does not exist
    change_df.to_csv(output_file, index=False)


def change_over(input_file, output_file):
    # Read the input CSV file
    data = pd.read_csv(input_file)

    # poss_changed = data["poss"].ne(data["poss"].shift()) & (data["inPlay"].shift() == "Dead") & (data["inPlay"] == "Alive")

    poss_changed = (data["poss"] != data["poss"].shift()) & (
                data["inPlay"] == "Alive" != data["inPlay"].shift() == "Dead")

    change_over_rows = data[poss_changed]
    change_over_rows.to_csv(output_file, index=False)


def extract_frame_nums(input_file, output_file):
    data = pd.read_csv(input_file)
    frame_nums = data["frame_num"]
    frame_nums.to_csv(output_file, index=False, header=True)


def extract_changes_in_possession(csv_file):
    # Load the CSV file into a DataFrame, assuming tab-separated values
    df = pd.read_csv(csv_file, sep='\t')

    # Identify rows where the 'poss' value changes from the previous row
    # We use shift(-1) to compare each row with the next row
    df['poss_change'] = df['poss'] != df['poss'].shift(-1)

    # Filter the DataFrame to include only the rows before a change in possession
    changes_df = df[df['poss_change']]

    # Drop the 'poss_change' column as it's no longer needed
    changes_df = changes_df.drop(columns=['poss_change'])
    before = changes_df[changes_df['frame_num'] < 1420876]
    after = changes_df[changes_df['frame_num'] > 1443541]

    before.to_csv("blob/mean_dis_before_turnover1.csv", index=False)
    after.to_csv("blob/mean_dis_before_turnover2.csv", index=False)


def main():
    # data = pd.read_csv("data/player_and_ball.csv")
    # data.sort_values(by="frame_num", inplace=True)
    # home_alive = data[(data["team_id"] == 0) & (data["inPlay"] == "Alive")]
    # away_alive = data[(data["team_id"] == 1) & (data["inPlay"] == "Alive")]
    # home_dead = data[(data["team_id"] == 0) & (data["inPlay"] == "Dead")]
    # away_dead = data[(data["team_id"] == 1) & (data["inPlay"] == "Dead")]
    # home_poss = data[(data["team_id"] == 0) & (data["poss"] == "H")]
    # away_poss = data[(data["team_id"] == 1) & (data["poss"] == "A")]
    # home_total = data[(data["team_id"] == 0) & (data["inPlay"] == "Alive") & (data["poss"] == "H")]
    # away_total = data[(data["team_id"] == 1) & (data["inPlay"] == "Alive") & (data["poss"] == "A")]

    # Pre-process data to find relevant frames for closeness calculation
    # preprocessed_data = preprocess_for_closeness(data)

    # input CSV file and the output CSV file
    # detect_inplay_changes("data/player_and_ball.csv", "inPlay_change.csv")
    # input CSV file and the output CSV file
    # change_over("inPlay_change.csv", "change_over.csv")

    # extract_frame_nums("blob/new_heatblob.csv", "blob/frame_nums.csv")
    # calculate_closeness_for_frames("blob/frame_nums.csv", "data/player_and_ball.csv")
    mean_per_frame = calculate_mean_distance_per_frame("blob/closeness_for_frames.csv")
    mean_per_frame.to_csv("blob/mean_distances.csv", index=False, sep="\t")
    # extract_changes_in_possession("blob/mean_distances.csv")

    data_for_mapping = pd.read_csv("blob/closeness_for_frames.csv")
    data_for_mapping.sort_values(by="frame_num", inplace=True)
    five_v_five_heatmap(data_for_mapping, pitch_length, pitch_width, mean_per_frame)

    # Calculate closeness for the preprocessed data
    # closeness_df = calculate_closeness(preprocessed_data)

    # closeness_df = player_v_player_closeness_calculation(preprocessed_data)

    # Output or further process the closeness_df as required
    print("player_v_player_closeness_calculation complete. Data:")
    # print(closeness_df.head())

    # Save the results to a txt file
    # closeness_df.to_csv("closeness_output.txt", index=False, sep="\t")
    # closeness_df.to_csv("player_v_player_closeness_calculation_output.txt", index=False, sep="\t")

    # print("Output saved to player_v_player_closeness_calculation_output.txt")
    # print("Generating Heatmap.")
    # # generate_heatmap(closeness_df)
    #
    # #player_v_player_heatmap(closeness_df, pitch_length, pitch_width)
    # print("Heatmap Generated.")


if __name__ == "__main__":
    main()
