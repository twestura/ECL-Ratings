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


import sys
import argparse
import requests
from bs4 import BeautifulSoup


# File path to the file storing the player names to scrap.
PLAYERS_FILE_PATH = 'players.csv'


# Error message to display if players.csv does not exist.
PLAYERS_FILE_NOT_FOUND = "The file 'players.csv' does not exist."


# File in which to save the output
OUT_FILE_PATH = 'ratings.csv'


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
    Returns a dictionary of player_name: voobly_profile_link.

    Args:
        fname: The file path to the players file.
    Returns:
        A dict mapping a string player name to the string link to their
        Voobly profile.
    Raises:
        FileNotFoundError: The file fname does not exist.
    """
    if fname is None: fname = PLAYERS_FILE_PATH
    with open(fname) as player_file:
        players = {}
        # skip the header line
        for line in player_file.readlines()[1:]:
            player, profile = line.strip().split(',')
            players[player] = profile
        return players


def write_ratings(player_ratings, fname=None):
    """
    Saves player ratings to fname.

    Args:
        player_ratings: A dictonary mapping a string player name to a list with
            four strings, each representing a rating. This list contains:
                ['Current 1v1', 'Highest 1v1', 'Current TG', 'Highest TG']
        fname: The file path to the output file.
    """
    if fname is None: fname = OUT_FILE_PATH
    with open(fname, 'w') as output_file:
        output_file.write(RATINGS_HEADER)
        for player, ratings in player_ratings.items():
            output_file.write('{}, {}\n'.format(player, ', '.join(ratings)))


def get_id(voobly_url):
    """
    Returns the player user id from a voobly url.

    Args:
        voobly_url: A voobly url, must not end in a trailing slash.
    Returns:
        The player user id parsed from the url.
    """
    return voobly_url.split('/')[-1]


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
        player_profiles = load_players() # dict of player name to voobly profile
    except FileNotFoundError:
        print(PLAYERS_FILE_NOT_FOUND)
        return # terminate when no players are present

    with requests.Session() as sess:
        sess.get(VOOBLY_LOGIN_URL) # initial login page to populate cookies
        login_data = {'username': parsed.username, 'password': parsed.password}
        hdr = {'referer': VOOBLY_LOGIN_AUTH_URL}
        sess.post(VOOBLY_LOGIN_AUTH_URL, data=login_data, headers=hdr)
        # TODO handle failed login

        lid_1v1 = LADDERS['RM - 1v1']
        lid_tg = LADDERS['RM - Team Games']
        ratings = {}
        for player, link in player_profiles.items():
            # TODO handle incorrect url
            uid = get_id(link)
            current_1v1, highest_1v1 = get_ratings(sess, uid, lid_1v1)
            current_tg, highest_tg = get_ratings(sess, uid, lid_tg)
            ratings[player] = [current_1v1, highest_1v1, current_tg, highest_tg]
    write_ratings(ratings)


if __name__ == '__main__':
    main(sys.argv[1:])
