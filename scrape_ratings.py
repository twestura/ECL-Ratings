#!/usr/bin/env python
"""
A script for scrapping ratings from the Voobly website.

The list of players must be stored in a file named `players.csv`.
This file starts with a header line, then each following line is the player name
then the voobly profile link.
For example:
```
player-name, voobly-profile-link
TWest,https://www.voobly.com/profile/view/123684015
robo_boro,https://www.voobly.com/profile/view/123905987
smarthy_,https://www.voobly.com/profile/view/124230162
Pete26196,https://www.voobly.com/profile/view/123685133
AkeNo,https://www.voobly.com/profile/view/123723545
```

The output is saved in a file `ratings.csv`.
Each line contains a player name and their 4 ratings, separated by commas.
"""

import csv
import sys
import argparse
import requests
from bs4 import BeautifulSoup


# File path to the file storing the player names to scrap.
PLAYERS_FILE_PATH = 'players.csv'


# Error message to display if players.csv does not exist.
PLAYERS_FILE_NOT_FOUND = "The file 'players.csv' does not exist."


# Error message to display if there is an OSError when attempting to read the
# players file.
PLAYERS_FILE_ERROR_MSG = "Cannot read 'players.csv'."


# File in which to save the output.
OUT_FILE_PATH = 'ratings.csv'


# Error message to display when failing to write to the ratings file.
WRITE_ERROR_MSG = "Cannot write to 'ratings.csv'."


# Path to the file of invalid players and uids.
INVALID_FILE_PATH = 'invalid.csv'


# Error message to print when at least one player uid is invalid
INVALID_UID_MSG = "{} invalid player uid(s), writing to 'invalid.csv'."


# Error message to display when failing to write to the invalid uid file.
WRITE_ERROR_INVALID = "Cannot write to 'invalid.csv'"


# Message to display when failing to log in to Voobly.
VOOBLY_LOGIN_FAIL_MSG = ('Cannot log in to Voobly.'
                         +' Check your username and password.')


# Map of ladder names to their ids.
LADDERS = {
    'RM - Clans': 14,
    'CS - Europe': 100,
    'Beginners RM': 101,
    'Beginners DM': 102,
    'RM - 1v1': 131,
    'RM - Team Games': 132,
    'RM AoFE': 143,
    'AoFE Overall': 144,
    'AoFE RM - 1v1': 145,
    'AoFE RM - TG': 146,
    'VCOM Clan Wars': 148,
    'AoFE Castle Blood': 149,
    'AoFE CS': 150,
    'VCOM Ladder': 151,
    'DM TG': 162,
    'DM 1v1': 163
}


# URL for Voobly's login page
VOOBLY_LOGIN_URL = 'https://www.voobly.com/login'


# URL to which to send the post login request
VOOBLY_LOGIN_AUTH_URL = 'https://www.voobly.com/login/auth'


# Base url from which to grab a player's ratings profile
# Use the string format method to supply the user and ladder ids.
RATINGS_BASE_URL = 'https://www.voobly.com/profile/view/{uid}/Ratings/games/profile/{uid}/{lid}' # pylint: disable=line-too-long


# Start of geader for the ratings output csv file.
RATINGS_HEADER_START = 'Player Name'


def load_players(fname=None):
    """
    Returns a dictionary of player_name: uid.

    Args:
        fname: The file path to the players file.
    Returns:
        A dict mapping a string player name to their string Voobly user id.
    Raises:
        FileNotFoundError: If the file fname does not exist.
        OSError: If fname cannot be read.
    """
    if fname is None: fname = PLAYERS_FILE_PATH
    with open(fname) as player_file:
        profilereader = csv.reader(player_file)
        rows = [row for row in profilereader]
        if not rows: return {} # return if file is empty
        if rows[0][0] == 'player-name': rows = rows[1:] # skip header if present
    players = {} # maps a player name to a list of that player's uids
    for row in rows: players[row[0]] = [parse_id(uid) for uid in row[1:]]
    return players


def write_ratings(player_ratings, ladders, fname=None):
    """
    Saves player ratings to fname.

    Args:
        player_ratings: A dictonary mapping a string player name to a list of
            strings. Each string is a list representing the player's rating
            on a ladder. This list must be the same length as ladders.
        ladders: A list of string ladder names. Must be the same length as
            player_ratings.
        fname: The file path to the output file.
    Raises:
        OSError: If fname cannot be written to.
    """
    if fname is None: fname = OUT_FILE_PATH
    with open(fname, 'w') as output_file:
        header = [RATINGS_HEADER_START]
        for ladder in ladders:
            header.append('Current ' + ladder)
            header.append('Highest ' + ladder)
        output_file.write(', '.join(header) + '\n')
        for player, ratings in player_ratings.items():
            output_file.write('{}, {}\n'.format(player, ', '.join(ratings)))


def parse_id(voobly_url):
    """
    Returns the player user id from a voobly url.

    A Voobly url has the format 'www.voobly.com/profile/view/uid', where
    the uid is the users id number. The url may optionally have text prepended
    or appended, as long as it contains this string.

    Example URLs:
    www.voobly.com/profile/view/123684015
    https://www.voobly.com/profile/view/123684015
    https://www.voobly.com/profile/view/123684015/
    https://www.voobly.com/profile/view/123684015/Ratings/games/profile/123684015/131

    Note: this method simply parses the URL to obtain the uid, it does not
    check whether a Voobly profile with that uid exists.

    Args:
        voobly_url: A voobly url, must not end in a trailing slash.
    Returns:
        The player user id parsed from the url.
    Raises:
        ValueError: If the url is not correctly formatted.
    """
    try:
        split_url = voobly_url.split('/')
        view_index = split_url.index('view')
        uid = split_url[view_index + 1]
        int(uid) # ensure that the uid is an integer
        return uid
    except (ValueError, IndexError) as e:
        raise ValueError(
            "The url '{}' is incorrectly formatted.".format(voobly_url)) from e


def get_ratings(sess, uid_list, lid):
    """
    Returns the current and highest ratings of a player on the given ladder.

    If an account has 0 games, does not consider the rating on that ladder.
    Assigns a default value of 1600 if all of the accounts have 0 games.

    Args:
        sess: The current session logged in to access Voobly profiles.
        uid_list: A list of string Voobly user ids.
        lid: Ladder id, the id of a Voobly ladder, must be a value in LADDERS.
    Returns:
        Two strings: current_rating, highest_rating.
    Raises:
        ValueError: If a player uid is invalid. The ValueError contains the
            invalid uid as a message.
    """
    max_current = -1
    max_highest = -1
    for uid in uid_list:
        ratings_url = RATINGS_BASE_URL.format(uid=uid, lid=lid)
        ratings_response = sess.get(ratings_url)
        soup = BeautifulSoup(ratings_response.content, 'html.parser')
        if soup.title.get_text() == 'Page Not Found':
            raise ValueError("{}".format(uid))

        current = soup.find('td', text='Current Rating').find_next().get_text()
        # account for 0 games
        if current: max_current = max(max_current, int(current))
        highest = soup.find('td', text='Highest Rating').find_next().get_text()
        max_highest = max(max_highest, int(highest))

    if max_current == -1: max_current = 1600 # account for 0 games
    return str(max_current), str(max_highest)


def parse_args(args):
    """
    Parses args.

    Args:
        args: List of strings to parse.
    Returns:
        An object containing the parsed arguments. The object has three fields:
            username: Voobly username string.
            password: Voobly password string.
            ladders: List of string names of Voobly ladders from which to pull
                ratings.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('username', help='Voobly account username.')
    parser.add_argument('password', help='Voobly account password.')
    parser.add_argument('--ladders', default=['RM - 1v1', 'RM - Team Games'],
                        help='Select the ladders form which you want ratings.',
                        choices=sorted(LADDERS, key=LADDERS.get), nargs='*')
    parsed = parser.parse_args(args)
    # a single argument is parsed as a single string, turn it into a list
    if isinstance(parsed.ladders, str): parsed.ladders = [parsed.ladders]
    return parsed


def main(args):
    """
    Runs the script, loading player ratings from the Voobly website and saving
    them in `ratings.csv`.

    Args:
        args: Usually sys.argv[1:].
    """
    parsed = parse_args(args)

    try:
        player_profiles = load_players() # dict of player name to voobly uid
    except FileNotFoundError:
        print(PLAYERS_FILE_NOT_FOUND)
        return # terminate when no players are present
    except OSError:
        print(PLAYERS_FILE_ERROR_MSG)
        return # terminate when player data cannot be read
    except ValueError as e:
        print(e)
        return # terminate when player data contains an invalid url

    invalid_players = {} # maps a player name to their invalid uids
    with requests.Session() as sess:
        sess.get(VOOBLY_LOGIN_URL) # initial login page get to populate cookies
        # TODO handle failure of initial get (try with internet off)
        login_data = {'username': parsed.username, 'password': parsed.password}
        hdr = {'referer': VOOBLY_LOGIN_AUTH_URL}
        login_response = sess.post(VOOBLY_LOGIN_AUTH_URL, data=login_data,
                                   headers=hdr)
        # Voobly login failed if title of the result is 'Login'
        login_soup = BeautifulSoup(login_response.content, 'html.parser')
        if login_soup.title.get_text() == 'Login':
            print(VOOBLY_LOGIN_FAIL_MSG)
            return # terminate if Voobly login failed

        ratings = {} # maps a player name to their list of ratings
        for player, uid_list in player_profiles.items():
            try:
                ratings[player] = []
                for ladder in parsed.ladders:
                    lid = LADDERS[ladder]
                    current, highest = get_ratings(sess, uid_list, lid)
                    ratings[player].append(current)
                    ratings[player].append(highest)
            except ValueError as err:
                del ratings[player] # remove player from good output
                invalid_players[player] = str(err)

    try:
        write_ratings(ratings, parsed.ladders)
    except OSError:
        print(WRITE_ERROR_MSG)
        return # terminate if the ratings cannot be written
    if invalid_players:
        try:
            print(INVALID_UID_MSG.format(len(invalid_players)))
            with open(INVALID_FILE_PATH, 'w') as bad_uid_file:
                for player, uid in invalid_players.items():
                    bad_uid_file.write(
                        '{},{}\n'.format(player, uid))
        except OSError:
            print(WRITE_ERROR_INVALID)
            return # terminate if the invalid uids cannot be written


if __name__ == '__main__':
    main(sys.argv[1:])
