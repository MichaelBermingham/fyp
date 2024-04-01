# This file should prepare the data by splitting it into first and second halfs, removing noise, and shortening it
# down to a manageable size for efficiency.
import os
from xml.dom import minidom as mdom
# from utils import frame_to_time
import pandas as pd


def frame_to_time(frame_num, frame_rate, start_frame):
    adjusted_frame_num = frame_num - start_frame
    total_seconds = adjusted_frame_num / frame_rate
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    return f"{minutes} minutes, {seconds} seconds"


def get_attr_value(ele, attr):
    return ele.attributes[attr].value


def split_halves(metadata_filename):
    """
    extracts metadata of game from a provided file and returns the details in a dictionary
    :param metadata_filename: the metadata file given with the game data
    :return: 3 dictionaries: pitch, which is the size details of the game pitch; first_half and second half,
    which gives the frames of the start and end of the first and second half, respectively
    """

    metadata = mdom.parse(metadata_filename)

    # Finding the size of the pitch
    match = metadata.getElementsByTagName('match')[0]
    tracking_size = {'x': float(get_attr_value(match, 'fTrackingAreaXSizeMeters')),
                     'y': float(get_attr_value(match, 'fTrackingAreaYSizeMeters'))}

    pitch = {'x': float(get_attr_value(match, 'fPitchXSizeMeters')),
             'y': float(get_attr_value(match, 'fPitchYSizeMeters'))}

    # finding the beginning and end frames of the first + second half
    first = metadata.getElementsByTagName('period')[0]
    second = metadata.getElementsByTagName('period')[1]

    first_half = {'start': int(get_attr_value(first, 'iStartFrame')), 'end': int(get_attr_value(first, 'iEndFrame'))}
    second_half = {'start': int(get_attr_value(second, 'iStartFrame')), 'end': int(get_attr_value(second, 'iEndFrame'))}

    return [pitch, tracking_size, first_half, second_half]


pitch, tracking_size, first_half, second_half = split_halves('data/metadata/metadata.xml')


def eliminate_noise(half1, half2, datafile):
    """
    Producing a new DAT file containing active play (i.e. first and second halves).
    :param half1: Extracted metadata about the first half.
    :param half2: Extracted metadata about the second half.
    :param datafile: .dat file to be cleaned.
    :return: Name of the new file produced.
    """
    half1_start = half1['start']
    half1_end = half1['end']
    half2_start = half2['start']
    half2_end = half2['end']

    with open(datafile, "r") as input_file:
        with open("data/gamedata/in_play.dat", "w") as output_file:
            start_processing = False
            for line in input_file:
                # Getting the frame number. Casting it to an integer.
                frame = int(line.strip().split(":")[0])

                if not start_processing:
                    # Checking if the target column has the target value.
                    if frame == half1_start or \
                            frame == half2_start:
                        start_processing = True
                        output_file.write(line)
                # Checking if the frame is an end frame. If it is, then stop processing.
                elif frame == half1_end or \
                        frame == half2_end:
                    start_processing = False
                else:
                    # Writing the line to the new file.
                    output_file.write(line)

    return output_file.name


def shorten_data(seconds, filename):
    """
    Producing a new data file contains only every x seconds the user specifies.
    :param seconds: Real seconds per data capture.
    :param filename: Name of the file to be shortened down.
    :return: Name of the new file produced.
    """
    n = seconds * 25  # 25 frames per second.
    with open(filename, "r") as file:
        with open("data/gamedata/short_data.dat", "w") as newfile:
            for i, line in enumerate(file):
                if i % n == 0:
                    newfile.write(line)

    return newfile.name


# calculating amount to cut off tracking boundaries
excess_x = ((tracking_size['x'] - pitch['x']) / 2) * 100
excess_y = ((tracking_size['y'] - pitch['y']) / 2) * 100

max_x = (tracking_size['x'] * 50) - excess_x
max_y = (tracking_size['y'] * 50) - excess_y


def scale_data_to_pitch(orig_x, orig_y):
    """
    Calculating the pitch borders in tracking terms.
    :param orig_x: Original X
    :param orig_y: Original Y
    :return x, y: pitch borders
    """

    x = (int(orig_x) + max_x) / 100
    y = (int(orig_y) + max_y) / 100
    return x, y


def categorize_data(filename):
    """
    splits the data into two CSV files: players and ball
    :param filename: the name of the file to categorise
    :return: void
    """

    player_data = []
    ball_data = []

    with open(filename, 'r') as file:
        for i in file:
            # create frame num, list of players, and ball details
            frame_num = i.split(':')[0]
            players = i.split(':')[1].split(';')
            ball = i.split(':')[2].split(',')

            # add frame details to ball data and add to list
            ball[0], ball[1] = scale_data_to_pitch(ball[0], ball[1])

            if (0 < int(ball[0]) < pitch['x']) and (0 < int(ball[1]) < pitch['y']):
                ball_frame = [frame_num, ball[0], ball[1], ball[2], ball[3], ball[4], ball[5].strip(';')]
                ball_data.append(ball_frame)

            # add frame details to each player and add them to list
            for j in players:
                data = j.split(',')

                # getting rid of any data outside borders of the pitch
                # converting tracking data to meters
                if len(data) > 1:
                    # convert x and y to positive values and reduce scale to metres
                    data[3], data[4] = scale_data_to_pitch(data[3], data[4])

                    if (0 < int(data[3]) < pitch['x']) and (0 < int(data[4]) < pitch['y']):
                        # remove any frames that are outside the pitch borders
                        # if data[3] <= pitch['x'] and data[4] <= pitch['y']:
                        player_frame = [frame_num, data[0], data[1], data[2], data[3], data[4], data[5]]
                        player_data.append(player_frame)

    # Create directories if they don't exist
    output_directory = 'data'  # Change this to your desired output directory
    os.makedirs(output_directory, exist_ok=True)

    # add ball to CSV
    ball_df = pd.DataFrame(ball_data, columns=['frame_num', 'x', 'y', 'z', 'speed', 'poss', 'inPlay'])
    # Save DataFrames to CSV files
    ball_df.to_csv(os.path.join(output_directory, 'ball.csv'), index=False)

    # add players to CSV
    player_df = pd.DataFrame(player_data, columns=['frame_num', 'team_id', 'player_id', 'squadNum', 'x', 'y', 'speed'])
    # Save DataFrames to CSV files
    player_df.to_csv(os.path.join(output_directory, 'player.csv'), index=False)


# clean up file
categorize_data(shorten_data(1, eliminate_noise(first_half, second_half, 'C:\\Users\\mrmbe\\fyp\\data\\gamedata\\987632.dat')))

