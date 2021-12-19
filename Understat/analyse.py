import os
import pathlib
from typing import List
from gen import get_path, get_dirs, get_csv_data, str2num, csv2pd

HERE = str(pathlib.Path(__file__).parent)
LEAGUES = get_dirs(HERE)
TEAM_HISTORY = 'team_data'
TEAMS_DATA = 'teamsData'
PLAYERS_DATA = 'playersData'
GAMES_DATA = 'datesData'
FORMAT = 'csv'
LOCATIONS = ('home', 'away')


def get_league_path(league: str, year: str = None, teams: List[str] = None):
    """Build path from input parameters
    :param league: league string, required
    :param year: year string or integer, optional
    :param teams: team string or list of teams, optional
    :return: absolute paths to required directories
    """

    path_segments = [HERE, league]

    if year:
        path_segments.append(year)

    if teams:
        path = [get_path(*path_segments, team) for team in teams]
    else:
        path = get_path(*path_segments)

    return path


def get_league_years(league: str):
    """Get years in database for a given league
    :param league: string of league within database
    :returns years: years in database
             paths: paths to data for each year
    """
    league_path = get_path(HERE, league)
    years = get_dirs(league_path)
    paths = [get_path(league_path, year) for year in years]
    return years, paths


def get_most_recent_year(league: str):
    """Get most recent season in database for a given league
    :param league: string of league within database
    :returns year: string of most recent year
             path: absolute path to most recent year directory
    """
    # TODO: Has season started?
    years, _ = get_league_years(league)
    # Convert to integer, find maximum, return to string
    year = str(max(map(int, years)))
    path = get_path(HERE, league, year)
    return year, path


def get_teams_in_league(league: str = 'EPL', year: str = None):
    """Get all teams in a given league for a given year
    :param league: string with league (checked within function)
    :param year: string of requested year, default = most recent
    :return: all teams in league year
    """
    if league not in LEAGUES:
        raise ValueError(f"Invalid league. Expected one of: {LEAGUES}")

    league_dir = get_path(HERE, league)
    years = get_dirs(league_dir)

    if year not in years:
        # Getting most recent year as default
        recent_year, _ = get_most_recent_year(league)

        if year is None:
            print(f"No year specified. Using most recent year ({recent_year})")
        else:
            print(f"Year {year} not found. Using most recent year ({recent_year})")

        year = recent_year

    teams_file = get_path(league_dir, year, f"{TEAMS_DATA}.{FORMAT}")
    teams_data = get_csv_data(teams_file)

    all_teams = [t['title'] for t in teams_data]
    return all_teams


def find_team_league(team: str, year: str, fatal=False):
    """Find which league a given team is in
    :param team: team name
    :param year:
    :param fatal: boolean defining whether team not found gives warning (default), or error
    :return: league in which team was found, or None if team not found
    """
    for league in LEAGUES:
        teams = get_teams_in_league(league, year)
        if team in teams:
            # Team found, return league
            return league
        elif league == LEAGUES[-1]:

            string = f"Team '{team}' could not be found in any league: {LEAGUES}"
            if fatal:
                raise ValueError(string)
            else:
                print(string)
            return None


def get_players_in_team(team: str, year: str, league: str = None):
    """Get all players in given team, find team if league not specified
    :param team: team name string
    :param league: league team is in, default = search leagues for team
    :param year: year string or integer, default = most recent
    :return: list of players in team
    """
    # If no league specified, loop through available to find team
    if league is None:
        league = find_team_league(team, year, fatal=True)

    path = get_league_path(league, year)
    # TODO: Not working with pandas (csv2pd), potentially loaned player issue?
    data = get_csv_data(get_path(path, f"{PLAYERS_DATA}.{FORMAT}"))
    # Filtering players, then converting strings to numbers
    players = [row for row in data if team == row['team_title']]
    players = str2num(players)

    return players


def is_team_in_league(league: str, team: List[str], year: str = None):
    """Check requested team is within requested league
    :param league: league directory string
    :param team: string or list containing requested team
    :param year: year directory string or integer, default = most recent
    """
    all_teams = get_teams_in_league(league, year)

    boolean = []
    for t in team:
        b = t in all_teams
        if not b:
            print(f"Requested team '{t}' not found")

        boolean.append(b)

    return boolean


def get_team_history(league, year, n: int = 0, teams: List[str] = None, location: str = None):
    """Get game history of requested teams
    :param league: which league
    :param year: which year
    :param n: number of games to go back, default = full season
    :param teams: team or list of teams requested (assumed pre-checked)
    :param location: option to only take 'home' or 'away' games
    """
    path = check_league_year(league, year)

    if not teams:
        teams = get_teams_in_league(league)

    if location and location not in LOCATIONS:
        raise ValueError(f"Invalid league. Expected one of: {LOCATIONS}")

    matches = csv2pd(get_path(path, f"{GAMES_DATA}.{FORMAT}"))

    history = []
    for t in teams:
        team_path = os.path.join(path, t.replace(" ", "_"))
        games = csv2pd(os.path.join(team_path, f"{TEAM_HISTORY}.{FORMAT}"))

        # TODO: Hacky way to attach opponent name to data, should be processed this way from start
        team_matches = matches.loc[(matches["h_title"] == t) | (matches["a_title"] == t)]
        opp = []
        for i in range(0, len(games)):

            if games.iloc[i]["h_a"] == 'h':
                opp.append(team_matches.iloc[i]["a_title"])
            else:
                opp.append(team_matches.iloc[i]["h_title"])

        games["opp"] = opp

        if location:
            games = games.loc[games['h_a'] == location[0]]

        if n:
            games = games[-n:]

        history.append(games)

    return history


def check_league_year(league: str, year: str):
    """Check league/year path, return if exists
    :param league: league directory string
    :param year: year directory string or integer
    """
    league_bool = league_exists(league)
    year_bool = year_exists(league, year)

    if league_bool and year_bool:
        return get_path(HERE, league, year)


def league_exists(league):
    """Check league exists in database
    :param league: league directory string
    :returns: boolean, true if league directory found
    """
    exists = os.path.exists(get_path(HERE, league))
    if not exists:
        print(f"League: {league} not found")

    return exists


def year_exists(league: str, year: str):
    """Check year exists in league
    :param league: league directory string
    :param year: year directory string or integer
    """
    exists = os.path.exists(get_path(HERE, league, year))

    if not exists:
        print(f"Year: {year} not found in league: {league}")

    return exists
