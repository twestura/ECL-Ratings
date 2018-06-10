"""Unit test for scrape_ratings"""
# TODO experiment with mocking to test remaining methods


import scrape_ratings
from nose.tools import assert_equal
from nose.tools import assert_raises


# Well formatted test file
TEST_PLAYERS = 'test_players.csv'


# Test file with invalid Voobly url
TEST_PLAYERS_BAD = 'test_players_bad.csv'


# Test file with players who have multiple accounts
TEST_PLAYERS_MULTIPLE = 'test_players_multiple.csv'


# Tests that a file without a header is processed correctly
TEST_PLAYERS_MULTIPLE_NOHDR = 'test_players_multiple.csv'


# Test a player file with no text
TEST_PLAYERS_EMPTY = 'test_players_empty.csv'


# Test a player file with only a header
TEST_PLAYERS_EMPTY_HDR = 'test_players_empty_hdr.csv'


# Test a player file with a single player
TEST_PLAYERS_SINGLE = 'test_players_single.csv'


# Test a player file with a single player and a header
TEST_PLAYERS_SINGLE_HDR = 'test_players_single_hdr.csv'

def test_load_players_success():
    """Tests loading the example players file."""
    players = scrape_ratings.load_players(TEST_PLAYERS)
    expected_players = {
        'TWest': ['123684015'],
        'robo_boro': ['123905987'],
        'smarthy_': ['124230162'],
        'Pete26196': ['123685133'],
        'AkeNo': ['123723545']
    }
    assert_equal(expected_players, players)


def test_load_players_multiple():
    """Tests loading a player file with a player who has multiple accounts."""
    players = scrape_ratings.load_players(TEST_PLAYERS_MULTIPLE)
    expected_players = {
        'TWest': ['123684015'],
        'robo_boro': ['123905987'],
        'smarthy_': ['124230162'],
        'Pete26196': ['123685133', '124976639'],
        'AkeNo': ['123723545']
    }
    assert_equal(expected_players, players)


def test_load_players_nohdr():
    """
    Tests loading a player file with a player who has multiple accounts,
    using a file that does not include the csv header.
    """
    players = scrape_ratings.load_players(TEST_PLAYERS_MULTIPLE_NOHDR)
    expected_players = {
        'TWest': ['123684015'],
        'robo_boro': ['123905987'],
        'smarthy_': ['124230162'],
        'Pete26196': ['123685133', '124976639'],
        'AkeNo': ['123723545']
    }
    assert_equal(expected_players, players)


def test_load_players_empty():
    """Tests loading an empty players file."""
    players = scrape_ratings.load_players(TEST_PLAYERS_EMPTY)
    expected_players = {}
    assert_equal(expected_players, players)


def test_load_players_empty_hdr():
    """Tests loading an empty players file with a header."""
    players = scrape_ratings.load_players(TEST_PLAYERS_EMPTY_HDR)
    expected_players = {}
    assert_equal(expected_players, players)


def test_load_players_single():
    """Tests loading a players file with a single player."""
    players = scrape_ratings.load_players(TEST_PLAYERS_SINGLE)
    expected_players = {'TWest': ['123684015']}
    assert_equal(expected_players, players)


def test_load_players_single_hdr():
    """Tests loading a players file with a single player and a header."""
    players = scrape_ratings.load_players(TEST_PLAYERS_SINGLE_HDR)
    expected_players = {'TWest': ['123684015']}
    assert_equal(expected_players, players)


def test_load_players_not_found():
    """Tests that a FileNotFoundError is thrown if the file does not exist."""
    with assert_raises(FileNotFoundError):
        scrape_ratings.load_players('i do not exist')


def test_load_players_bad_url():
    """
    Tests that a ValueError is raised when loading a list of players that
    contains a bad url.
    """
    with assert_raises(ValueError):
        scrape_ratings.load_players(TEST_PLAYERS_BAD)


def test_parse_id_basic():
    """Tests parsing a voobly url with a simple format."""
    url = 'https://www.voobly.com/profile/view/123684015'
    assert_equal('123684015', scrape_ratings.parse_id(url))


def test_parse_id_slash():
    """Tests parsing a voobly url that ends with a slash."""
    url = 'https://www.voobly.com/profile/view/123684015/'
    assert_equal('123684015', scrape_ratings.parse_id(url))


def test_parse_id_no_prefix():
    """Tests parsing a voobly url that starts with www."""
    url = 'www.voobly.com/profile/view/123684015'
    assert_equal('123684015', scrape_ratings.parse_id(url))


def test_parse_id_suffix():
    """Tests parsing a url that has extra links at the end."""
    url = 'https://www.voobly.com/profile/view/123684015/Ratings/games/profile/123684015/131' # pylint: disable=line-too-long
    assert_equal('123684015', scrape_ratings.parse_id(url))


def test_parse_id_no_view():
    """Tests that a ValueError is raised when the url does not contain view."""
    url = 'https://www.voobly.com/profile/123684015'
    with assert_raises(ValueError): scrape_ratings.parse_id(url)


def test_parse_id_view_last():
    """
    Tests that a ValueError is raised when view is the final part of the url.
    """
    url = 'https://www.voobly.com/profile/view'
    with assert_raises(ValueError): scrape_ratings.parse_id(url)


def test_parse_id_not_int():
    """
    Tests that a ValueError is raised when the entry after view is not an int.
    """
    url = 'https://www.voobly.com/profile/view/notanint'
    with assert_raises(ValueError): scrape_ratings.parse_id(url)
