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
# TODO support multiple Voobly profiles
# TODO support multiple ladders

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


# Header for the ratings output csv file.
RATINGS_HEADER = 'Player, Current 1v1, Highest 1v1, Current TG, Highest TG\n'


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
    # TODO better csv parsing
    if fname is None: fname = PLAYERS_FILE_PATH
    with open(fname) as player_file:
        players = {} # maps a player name to that player's uid
        # skip the header line
        for line in player_file.readlines()[1:]:
            player, uid = line.strip().split(',')
            players[player] = parse_id(uid)
        return players


def write_ratings(player_ratings, fname=None):
    """
    Saves player ratings to fname.

    Args:
        player_ratings: A dictonary mapping a string player name to a list with
            four strings, each representing a rating. This list contains:
                ['Current 1v1', 'Highest 1v1', 'Current TG', 'Highest TG']
        fname: The file path to the output file.
    Raises:
        OSError: If fname cannot be written to.
    """
    if fname is None: fname = OUT_FILE_PATH
    with open(fname, 'w') as output_file:
        output_file.write(RATINGS_HEADER)
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
    except (ValueError, IndexError):
        raise ValueError(
            "The url '{}' is not formatted correctly.".format(voobly_url))


def get_ratings(sess, uid, lid):
    """
    Returns the current and highest ratings of a player on the given ladder.

    Args:
        sess: The current session logged in to access Voobly profiles.
        uid: User id, a string of a player's Voobly user id.
        lid: Ladder id, the id of a Voobly ladder, must be a value in LADDERS.
    Returns:
        Two strings: current_rating, highest_rating.
    """
    ratings_url = RATINGS_BASE_URL.format(uid=uid, lid=lid)
    ratings_response = sess.get(ratings_url)
    soup = BeautifulSoup(ratings_response.content, 'html.parser')
    # TODO handle 0 games
    current = soup.find('td', text='Current Rating').find_next().get_text()
    highest = soup.find('td', text='Highest Rating').find_next().get_text()
    return current, highest


def main(args):
    """
    Runs the script, loading player ratings from the Voobly website and saving
    them in `ratings.csv`.

    Args:
        args: Usually sys.argv[1:].
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('username', help='Voobly account username.')
    parser.add_argument('password', help='Voobly account password.')
    parsed = parser.parse_args(args)
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
        return # Terminate when player data contains an invalid url

    with requests.Session() as sess:
        sess.get(VOOBLY_LOGIN_URL) # initial login page get to populate cookies
        login_data = {'username': parsed.username, 'password': parsed.password}
        hdr = {'referer': VOOBLY_LOGIN_AUTH_URL}
        login_response = sess.post(VOOBLY_LOGIN_AUTH_URL, data=login_data,
                                   headers=hdr)
        # Voobly login failed if title of the result is 'Login'
        login_soup = BeautifulSoup(login_response.content, 'html.parser')
        if login_soup.title.get_text() == 'Login':
            print(VOOBLY_LOGIN_FAIL_MSG)
            return # terminate if Voobly login failed

        lid_1v1 = LADDERS['RM - 1v1']
        lid_tg = LADDERS['RM - Team Games']
        ratings = {}
        for player, uid in player_profiles.items():
            current_1v1, highest_1v1 = get_ratings(sess, uid, lid_1v1)
            current_tg, highest_tg = get_ratings(sess, uid, lid_tg)
            ratings[player] = [current_1v1, highest_1v1, current_tg, highest_tg]

    try:
        write_ratings(ratings)
    except OSError:
        print(WRITE_ERROR_MSG)
        return # terminate if the ratings cannot be written


if __name__ == '__main__':
    main(sys.argv[1:])
