# Voobly Ratings for ECL

A script for scraping Voobly ratings, inspired by a script from Jineapple.

## Usage

Run this script as a Python script by running the file `scrape_ratings.py`:
```
> python scrape_ratings.py <voobly-username> <voobly-password>
```
I recommend installing the Anaconda Python distribution if you do not already have Python installed: [https://www.anaconda.com/download/](https://www.anaconda.com/download/).

For example, place the `scrape_ratings.py` and `players.csv` files in the same directory.
Open a command line by typing `powershell` into the bar at the top of the Explorer window and pressing Enter.
![File Structure](images/file-structure.png "File Structure")

Then enter the command to run the file.
![Command Input](images/command-input.png "Command Input")

If there are spaces in your username or password, then you can surround them with double quotation marks, as done with the password in the preceding image.

You may specify the ladders from which to pull ratings by using the `--ladders` flag, followed by all of the ladders from which you want ratings.
Use double quotation marks to enclose ladder names that contain spaces.
For example, the following command pulls from four ladders:
```
> python scrape_ratings.py <username> <password> --ladders "RM - 1v1" "RM - Team Games" "DM 1v1" "DM TG"
```
By default, the RM 1v1 and Team Game ladders are used.
Run `python scrape_ratings.py -h` for a full list of help commands and available ladders.

The players are specified in a file named `players.csv` contained in the same directory as `scrap_ratings.py`
This file starts with an optional header line, then each line consists of a player name, a comma, and then the URLs of that player's Voobly profiles, separated by commas.
(This file may end optionally with a blank line.)

An example `players.csv` follows:
```
player-name, voobly-profile-link
TWest,https://www.voobly.com/profile/view/123684015
robo_boro,https://www.voobly.com/profile/view/123905987
smarthy_,https://www.voobly.com/profile/view/124230162
Pete26196,https://www.voobly.com/profile/view/123685133,https://www.voobly.com/profile/view/124976639
AkeNo,https://www.voobly.com/profile/view/123723545
```

The url must contain the `www.voobly.com/profile/view/uid` part of the URL.
There may optionally be a `https://` prefix or a suffix to the url, such as `https://www.voobly.com/profile/view/123684015/Ratings/games/profile/123684015/131`.

The result is saved to the file `ratings.csv`.
This file begins with a header line, and each subsequent line contains the name of a player and their ratings for each ladder, separated by commas.
The file ends in a blank line.
For example:
```
Player Name, Current RM - 1v1, Highest RM - 1v1, Current RM - Team Games, Highest RM - Team Games, Current DM 1v1, Highest DM 1v1, Current DM TG, Highest DM TG
TWest, 1709, 1748, 1650, 1680, 1600, 1600, 1600, 1600
robo_boro, 1901, 1914, 1674, 1753, 1600, 1600, 1594, 1600
smarthy_, 1490, 1652, 1534, 1644, 1600, 1600, 1603, 1610
Pete26196, 1753, 1834, 1616, 1648, 1600, 1600, 1600, 1600
AkeNo, 1814, 1858, 1689, 1777, 1600, 1600, 1600, 1600

```

If a player has multiple accounts, then the current rating is determined by using the maximum current rating across all of those accounts, not including accounts that have 0 games on a ladder (that is, if one account is 1450 and another is 1600 but with 0 games player, the current rating is given as 1450.)

If a URL appears to be formatted correctly but the player's Voobly user ID is invalid, then the player name and their id is written to the file `invalid.csv`.
This file is modified only if running the script encounters an invalid ID.

## Future Plans
* Integration with Google Forms and Sheets and Challonge to automate the signup and bracket creation process.
* GUI interface to make it easier to use for people not familar with a command line.
* Add an option for scraping the player name from the Voobly profile instead of needing to provide it in `players.csv`.
* Voobly provides an API for accessing information about user accounts and ladders here: `https://www.voobly.com/pages/view/147/External-API-Documentation`. Unfortunately, this API currently does not include the highest elo, only the current elo. I would prefer to use the API, if it's ever updated, instead of scraping the website.
