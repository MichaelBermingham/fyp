import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from mplsoccer import Pitch

import analyse
from preprocess_data import pitch

data = pd.read_csv('data/player_and_ball.csv')

# Separate DataFrames for each scenario allowing easier.
home_alive = data[(data['team_id'] == 0) & (data['inPlay'] == 'Alive')]
away_alive = data[(data['team_id'] == 1) & (data['inPlay'] == 'Alive')]
home_dead = data[(data['team_id'] == 0) & (data['inPlay'] == 'Dead')]
away_dead = data[(data['team_id'] == 1) & (data['inPlay'] == 'Dead')]
home_poss = data[(data['team_id'] == 0) & (data['poss'] == 'H')]
away_poss = data[(data['team_id'] == 1) & (data['poss'] == 'A')]
home_total = data[(data["team_id"] == 0) & (data["inPlay"] == "Alive") & (data["poss"] == "H")]
away_total = data[(data["team_id"] == 1) & (data["inPlay"] == "Alive") & (data["poss"] == "A")]

def calculate_closeness_2(input_data):
    # Assuming 'x_ball', 'y_ball', 'x_player', and 'y_player' columns exist
    # Calculate distance to ball if not already calculated
    input_data['distance_to_ball'] = np.sqrt((input_data['x_ball'] - input_data['x_player'])**2 + (input_data['y_ball'] - input_data['y_player'])**2)

    closeness_records = []

    # Iterate over each unique frame number
    for frame in input_data['frame_num'].unique():
        frame_data = input_data[input_data['frame_num'] == frame]

        # Separate data by team
        home_team = frame_data[frame_data['team_id'] == 0]
        away_team = frame_data[frame_data['team_id'] == 1]

        # Sort by distance and select top 5 for each team
        closest_home = home_team.nsmallest(5, 'distance_to_ball')
        closest_away = away_team.nsmallest(5, 'distance_to_ball')

        # Combine the closest players from both teams
        closest_players_frame = pd.concat([closest_home, closest_away])

        # Append or concat to a list or DataFrame
        closeness_records.append(closest_players_frame)

    # Combine all frames' data into a single DataFrame
    closeness_df = pd.concat(closeness_records)
    return closeness_df


def calculate_closeness(input_data):
    # Initialize an empty list to store closeness records
    closeness_records = []

    # Group by frame to process each moment in the game separately
    grouped = input_data.groupby('frame_num')

    for frame, group in grouped:
        # Extract ball coordinates for the current frame
        ball_x = group.iloc[0]['x_ball']
        ball_y = group.iloc[0]['y_ball']

        # Calculate the distance of each player to the ball
        group['distance_to_ball'] = np.sqrt((group['x_player'] - ball_x) ** 2 + (group['y_player'] - ball_y) ** 2)

        # Sort the players by their distance to the ball and select the top 5
        closest_players = group.sort_values('distance_to_ball').head(5)

        # Append the details of the closest players to the closeness_records list
        closeness_records.extend(closest_players.to_dict('records'))

    # Convert the list of records into a DataFrame
    closeness_df = pd.DataFrame(closeness_records)

    print("Calculated closeness for players.")
    return closeness_df


def calculate_closeness(data):
    """
    Calculate the average distance of the 5 closest players to the ball for each frame.

    Parameters:
    - data: DataFrame containing the player and ball positions.

    Returns:
    - closeness_df: DataFrame containing frame numbers and the average closeness.
    """
    closeness_records = []

    # Iterate over each frame
    for frame, frame_data in data.groupby('frame_num'):
        distances = []

        ball_position = frame_data.iloc[0][['x_ball', 'y_ball']].values
        for _, row in frame_data.iterrows():
            player_position = row[['x_player', 'y_player']].values
            distance = np.linalg.norm(ball_position - player_position)
            distances.append(distance)

        # Sort distances and take the average of the 5 closest players
        closest_distances = sorted(distances)[:5]
        average_closeness = np.mean(closest_distances)
        closeness_records.append((frame, average_closeness))

    closeness_df = pd.DataFrame(closeness_records, columns=['frame_num', 'average_closeness'])
    print(closeness_df)
    return generate_heatmap(closeness_df, data)


def generate_heatmap(closeness_df, data):
    """
    Generate a heat map based on the closeness data.

    Parameters:
    - closeness_df: DataFrame containing frame numbers and average closeness.
    - data: Original DataFrame for accessing player positions.
    """
    # Example: Plotting for a specific frame
    specific_frame = closeness_df.loc[closeness_df['average_closeness'] == closeness_df['average_closeness'].min(), 'frame_num'].iloc[0]
    frame_data = data[data['frame_num'] == specific_frame]

    plt.figure(figsize=(10, 7))
    plt.scatter(frame_data['x_player'], frame_data['y_player'], c='blue', label='Players')
    plt.scatter(frame_data.iloc[0]['x_ball'], frame_data.iloc[0]['y_ball'], c='red', label='Ball')
    plt.xlabel('Field Length')
    plt.ylabel('Field Width')
    plt.title(f'Player Positions at Frame {specific_frame}')
    plt.legend()
    plt.show()


def generate_heatmap(closeness_df):
    # pitch details
    pitch_length = pitch['x']
    pitch_width = pitch['y']

    # Get unique frames to plot
    unique_frames = closeness_df['frame_num'].unique()[:10]

    for frame in unique_frames:
        fig, ax = plt.subplots(figsize=(10.5, 6.8))
        # Set the soccer field background
        ax.set_xlim(0, pitch_length)
        ax.set_ylim(0, pitch_width)
        ax.set_xticks([])
        ax.set_yticks([])

        # Draw the pitch
        plt.plot([0, 0, pitch_length, pitch_length, 0], [0, pitch_width, pitch_width, 0, 0], color="black")

        frame_data = closeness_df[closeness_df['frame_num'] == frame]

        # Plot players and ball positions
        for _, row in frame_data.iterrows():
            if row['team_id'] == 0:  # Home team
                player_color = 'red'
            else:  # Away team
                player_color = 'blue'

            # Player position and label
            plt.plot(row['x_player'], row['y_player'], 'o', color=player_color)
            plt.text(row['x_player'], row['y_player'], f"({row['squadNum']}, {round(row['distance_to_ball'], 2)})",
                     color=player_color)

            # Line from player to ball
            plt.plot([row['x_player'], row['x_ball']], [row['y_player'], row['y_ball']], color=player_color,
                     linestyle='-', linewidth=1)

        # Plot ball position
        plt.plot(frame_data['x_ball'].iloc[0], frame_data['y_ball'].iloc[0], 'o', color='white', markersize=10)

        plt.title(f"Frame: {frame}")
        plt.show()


def generate_heatmap(closeness_df):
    analyse.remove_old_files()

    pitch = Pitch(pitch_type='custom', pitch_color='#22312b', line_color='white', figsize=(10, 7),
                  pitch_length=105, pitch_width=68, constrained_layout=True, tight_layout=False)

    # Filter for unique frames, but ensure we're only processing the first 10 for performance
    unique_frames = closeness_df['frame_num'].unique()[:10]

    for frame in unique_frames:
        fig, ax = pitch.draw()
        frame_data = closeness_df[closeness_df['frame_num'] == frame]

        # Plot players by team and connect lines to ball
        for team_id in frame_data['team_id'].unique():
            team_data = frame_data[frame_data['team_id'] == team_id]
            color = 'red' if team_id == 0 else 'blue'  # Assuming 0 is home, 1 is away

            # Plot players
            pitch.scatter(team_data['x_player'], team_data['y_player'], ax=ax, s=120, color=color, edgecolors='black',
                          zorder=2)
            for _, row in team_data.iterrows():
                # Player number and distance to ball
                label = f"{row['squadNum']} ({round(row['distance_to_ball'], 2)})"
                plt.text(row['x_player'], row['y_player'], label, color=color, fontsize=8, ha='center', va='center',
                         zorder=3)

                # Draw line to ball
                pitch.lines(row['x_player'], row['y_player'], row['x_ball'], row['y_ball'], lw=2, color=color, ax=ax,
                            zorder=1)

        # Plot ball position
        pitch.scatter(frame_data['x_ball'].iloc[0], frame_data['y_ball'].iloc[0], ax=ax, s=120, color='white',
                      edgecolors='black', zorder=2, label='Ball')

        plt.title(f"Frame: {frame}", color='white')
        plt.legend(loc='upper right')

        # Save figure
        plt.savefig(f'figures/heatmap_frame_{frame}.png', dpi=300)
        plt.close()

def generate_heatmap(closeness_df):
    analyse.remove_old_files()
    # Assuming the pitch is already drawn in the function
    unique_frames = closeness_df['frame_num'].unique()[:10]

    for frame in unique_frames:
        # Create the pitch outside of the Pitch constructor
        fig, ax = plt.subplots(figsize=(10, 7))
        pitch = Pitch(pitch_type='custom', pitch_color='#22312b', line_color='white',
                      pitch_length=pitch_length, pitch_width=pitch_width)
        pitch.draw(ax=ax)

        frame_data = closeness_df[closeness_df['frame_num'] == frame]

        for team_id in frame_data['team_id'].unique():
            team_data = frame_data[frame_data['team_id'] == team_id]
            color = 'red' if team_id == 0 else 'blue'

            pitch.scatter(team_data['x_player'], team_data['y_player'], ax=ax, s=120, color=color, edgecolors='black',
                          zorder=2)
            for _, row in team_data.iterrows():
                label = f"{row['squadNum']} ({round(row['distance_to_ball'], 2)})"
                plt.text(row['x_player'], row['y_player'], label, color=color, fontsize=8, ha='center', va='center',
                         zorder=3)
                pitch.lines(row['x_player'], row['y_player'], row['x_ball'], row['y_ball'], lw=2, color=color, ax=ax,
                            zorder=1)

        pitch.scatter(frame_data['x_ball'].iloc[0], frame_data['y_ball'].iloc[0], ax=ax, s=120, color='white',
                      edgecolors='black', zorder=2, label='Ball')

        plt.title(f"Frame: {frame}", color='white')
        plt.legend(loc='upper right')

        plt.savefig(f'figures/heatmap_frame_{frame}.png', dpi=300)
        plt.close()


# Here we call calculate_closeness with the DataFrame you want to analyze.
# For example, let's calculate closeness for the home team when they have possession and the play is alive:
# print("Home info: \n", home_total.head())
# print(home_total.head())
# print("Away info: \n", away_total.head())
# print(away_total.head())
# print("Calling calculate_closeness...")
closeness_df = calculate_closeness(away_total)
closeness_df.to_csv('closeness_data_away_total.txt', sep=',', index=False)
#  print("Outputting:\n", closeness_df)


# Mark rows where the ball status changes from 'Dead' to 'Alive'
data['status_change'] = ((data['inPlay'] == 'Alive') & (data['inPlay'].shift(1) == 'Dead'))

# Find frames where possession changes within 30 frames after being 'Alive'
# This is a placeholder for logic; you'll need to iterate through 'status_change' marked True
# and check for possession changes in the subsequent frames (up to 30 frames ahead)

# Placeholder for storing indices where the conditions are met
valid_indices = []

# Iterate through the DataFrame
for index, row in data.iterrows():
    if row['status_change']:
        start_frame = row['frame_num']
        end_frame = start_frame + (30 * 25)  # Assuming 30 frames ahead, increment by 25

        # Check for possession change in the next 30 frames
        future_frames = data[(data['frame_num'] > start_frame) & (data['frame_num'] <= end_frame)]
        if not future_frames.empty:
            # Check if 'poss' changes within these frames
            if any(future_frames['poss'] != row['poss']):
                valid_indices.append(index)

# Filter the DataFrame for the identified valid indices
filtered_data = data.loc[valid_indices]


