"""Unit test for scrape_ratings"""


import scrape_ratings
from nose.tools import assert_equal
from nose.tools import assert_raises


TEST_PLAYERS = 'test_players.csv'


def test_load_players_success():
    """Tests loading the example players file."""
    players = scrape_ratings.load_players('test_players.csv')
    expected_players = {
        'TWest': '123684015',
        'robo_boro': '123905987',
        'smarthy_': '124230162',
        'Pete26196': '123685133',
        'AkeNo': '123723545'
    }
    assert_equal(expected_players, players)


def test_load_players_not_found():
    """Tests that a FileNotFoundError is thrown if the file does not exist."""
    with assert_raises(FileNotFoundError):
        scrape_ratings.load_players('i do not exist')


def test_load_players_bad_url():
    """Tests loading a list of players that contains a bad url."""
    pass # TODO implement


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
