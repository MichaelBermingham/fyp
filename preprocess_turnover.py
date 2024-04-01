import re


def parse_line(line):
    """
    Extracts possession, status and action from line.
    format at the end: ":<misc_numbers>,<possession>,<status>;"
    """
    match = re.search(r":.*?,(A|H),(Alive|Dead)(?:,(SetAway|SetHome|Whistle|B4))?;:$", line)
    if match:
        possession = match.group(1)
        status = match.group(2)
        return possession, status
    else:
        print("No match found for this entry: ", match)
    return None, None


def process_file(input_path):
    last_possession, last_status = None, None
    transitions = {'A_to_H': [], 'H_to_A': []}  # To store lines where transitions occur

    try:
        with open(input_path, 'r') as infile, \
                open('data/home_team_turnover.dat', 'w') as home_out, \
                open('data/away_team_turnover.dat', 'w') as away_out:

            for line in infile:
                possession, status = parse_line(line.strip())
                if not possession or not status:
                    print(f"Failed to match line: {line.strip()}")

                # Check for valid data and transition logic
                if possession and status:  # Ensure they are not None
                    # Detecting transitions based on status change and possession change
                    if last_status == "Dead" and status == "Alive" and last_possession != possession:
                        # Log the transition based on possession changing.
                        if last_possession == "A" and possession == "H":
                            transitions['A_to_H'].append(line)
                            home_out.write(line)
                        elif last_possession == "H" and possession == "A":
                            transitions['H_to_A'].append(line)
                            away_out.write(line)

                    # Update last known states
                    last_possession, last_status = possession, status

    except IOError as e:
        print(f"An error occurred while processing the file: {e}")
        # Handle or log the error as needed

    return transitions


input_path = 'data/gamedata/in_play.dat'
transitions = process_file(input_path)
print("Transitions from Away to Home:", len(transitions['A_to_H']))
print("Transitions from Home to Away:", len(transitions['H_to_A']))
