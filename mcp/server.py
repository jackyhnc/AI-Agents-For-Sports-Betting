import os
import time
import requests
from fastmcp import FastMCP
import dotenv

dotenv.load_dotenv()

mcp = FastMCP("NBA Data 🏀")

API_KEY = os.environ.get("SPORTRADAR_API_KEY")
ACCESS = "trial"
LANG = "en"
BASE = f"https://api.sportradar.com/nba/{ACCESS}/v8/{LANG}"

MAX_RETRIES = 3
RETRY_DELAY = 1


def _request(url: str, retries: int = MAX_RETRIES):
    """
    Generic HTTP GET handler with retry logic.

    Attempts network call up to `retries` times, using exponential backoff.
    Retries are triggered for network errors, timeouts, and 429/5xx responses.

    Parameters:
        url (str): Fully formatted Sportradar endpoint URL
        retries (int): Number of retry attempts

    Returns:
        dict: JSON response from Sportradar or an error message
    """
    if not API_KEY:
        return {"error": "SPORTRADAR_API_KEY not set"}

    headers = {"accept": "application/json", "x-api-key": API_KEY}

    for attempt in range(retries):
        try:
            print(url)
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            res = resp.json()
            # Estimate token count as num words ≈ n tokens, so use len(str(res).split())
            max_tokens = 100000
            js = str(res)
            word_count = len(js.split())
            if word_count > max_tokens:
                print(
                    f"Response too large ({word_count} tokens), trimming to last {max_tokens} tokens"
                )
                js_words = js.split()
                js_trimmed = " ".join(js_words[:max_tokens])
                try:
                    import ast

                    res = ast.literal_eval(js_trimmed)
                except Exception:
                    res = js_trimmed
            print("--------------------------------")
            print(f"Response length: {len(res)}")
            return res

        except requests.exceptions.HTTPError as e:
            code = e.response.status_code

            if code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                delay = RETRY_DELAY * (2**attempt)
                time.sleep(delay)
                continue

            return {"error": f"HTTP {code}: {e.response.reason}"}

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if attempt < retries - 1:
                delay = RETRY_DELAY * (2**attempt)
                time.sleep(delay)
                continue
            return {"error": str(e)}

        except Exception as e:
            return {"error": str(e)}

    return {"error": "Request failed after retries"}


# ============================================================
# DAILY ENDPOINTS (3)
# ============================================================


@mcp.resource("nba://daily/change-log/{date}")
def daily_change_log(date: str):
    """
    Daily Change Log

    URL Format:
        league/{year}/{month}/{day}/changes.json

    Description:
        Provides IDs and timestamps for all modified NBA data (teams, players,
        schedules, standings, statistics) for a given date.

    Parameters:
        date (str): Date in YYYY-MM-DD format

    Returns:
        dict: JSON response containing the change log
    """
    y, m, d = date.split("-")
    url = f"{BASE}/league/{y}/{m}/{d}/changes.json"
    return str(_request(url))


@mcp.resource("nba://daily/injuries/{date}")
def daily_injuries(date: str):
    """
    Daily Injuries

    URL Format:
        league/{year}/{month}/{day}/daily_injuries.json

    Description:
        Returns all injury updates applied on the specified date.

    Parameters:
        date (str): Date in YYYY-MM-DD format

    Returns:
        dict: JSON containing daily injury updates
    """
    y, m, d = date.split("-")
    url = f"{BASE}/league/{y}/{m}/{d}/daily_injuries.json"
    return str(_request(url))


@mcp.resource("nba://daily/schedule/{date}")
def daily_schedule(date: str):
    """
    Daily Schedule

    URL Format:
        games/{year}/{month}/{day}/schedule.json

    Description:
        Provides all NBA games scheduled for the given day, with full venue and
        matchup metadata.

    Parameters:
        date (str): Date in YYYY-MM-DD format

    Returns:
        dict: JSON containing the daily schedule
    """
    y, m, d = date.split("-")
    url = f"{BASE}/games/{y}/{m}/{d}/schedule.json"
    return str(_request(url))


# ============================================================
# GAME ENDPOINTS (2)
# ============================================================


@mcp.resource("nba://game/pbp/{game_id}")
def game_play_by_play(game_id: str):
    """
    Game Play-by-Play

    URL Format:
        games/{game_id}/pbp.json

    Description:
        Returns real-time detailed event logs for every possession, action,
        substitution, shot, turnover, foul, and play participant.

    Parameters:
        game_id (str): Unique Sportradar game identifier

    Returns:
        dict: JSON play-by-play feed
    """
    url = f"{BASE}/games/{game_id}/pbp.json"
    return str(_request(url))


@mcp.resource("nba://game/summary/{game_id}")
def game_summary(game_id: str):
    """
    Game Summary

    URL Format:
        games/{game_id}/summary.json

    Description:
        Provides top-level boxscore statistics, team scoring breakdowns,
        player stats, starters, officials, and venue details.

    Parameters:
        game_id (str): Unique Sportradar game identifier

    Returns:
        dict: JSON containing game summary information
    """
    url = f"{BASE}/games/{game_id}/summary.json"
    return str(_request(url))


# ============================================================
# LEAGUE ENDPOINTS (7)
# ============================================================


@mcp.resource("nba://league/injuries")
def league_injuries():
    """
    League Injuries

    URL Format:
        league/injuries.json

    Description:
        Provides all active player injuries across all NBA teams.

    Returns:
        dict: JSON containing league-wide injury data
    """
    url = f"{BASE}/league/injuries.json"
    return str(_request(url))


@mcp.resource("nba://league/hierarchy")
def league_hierarchy():
    """
    League Hierarchy

    URL Format:
        league/hierarchy.json

    Description:
        Provides league → conference → division → team structure including
        venue associations.

    Returns:
        dict: JSON hierarchy definition
    """
    url = f"{BASE}/league/hierarchy.json"
    return str(_request(url))


@mcp.resource("nba://league/seasons")
def league_seasons():
    """
    Seasons

    URL Format:
        league/seasons.json

    Description:
        Returns all NBA seasons available in the Sportradar database, including
        preseason, regular season, tournaments, and playoffs.

    Returns:
        dict: JSON list of seasons
    """
    url = f"{BASE}/league/seasons.json"
    return str(_request(url))


@mcp.tool
def league_leaders(season_year: int, season_type: str):
    """
    League Leaders

    URL Format:
        seasons/{season_year}/{season_type}/leaders.json

    Description:
        Provides per-category league leaders along with full seasonal statistics,
        including totals and averages.

    Parameters:
        season_year (int): Year in YYYY format
        season_type (str): PRE, REG, IST, PIT, PST

    Returns:
        dict: JSON containing leader categories and ranked player data
    """
    url = f"{BASE}/seasons/{season_year}/{season_type}/leaders.json"
    return _request(url)


@mcp.tool
def season_rankings(season_year: int, season_type: str):
    """
    Rankings

    URL Format:
        seasons/{season_year}/{season_type}/rankings.json

    Description:
        Provides division and conference ranking for all teams, including
        clinching status and nightly records.

    Parameters:
        season_year (int): Season start year (e.g., 2024)
        season_type (str): PRE, REG, IST, PIT, PST

    Returns:
        dict: JSON containing team rankings
    """
    url = f"{BASE}/seasons/{season_year}/{season_type}/rankings.json"
    return _request(url)


@mcp.tool
def full_season_schedule(season_year: int, season_type: str):
    """
    Full Season Schedule

    URL Format:
        games/{season_year}/{season_type}/schedule.json

    Description:
        Returns the complete schedule (date, time, venue, opponents) for the
        given season and season type.

    Parameters:
        season_year (int): Season year in YYYY format
        season_type (str): PRE, REG, IST, PIT, PST

    Returns:
        dict: JSON schedule for the full season
    """
    url = f"{BASE}/games/{season_year}/{season_type}/schedule.json"
    return _request(url)


@mcp.resource("nba://league/teams")
def league_teams():
    """
    Teams

    URL Format:
        league/teams.json

    Description:
        Returns all active NBA teams.

    Returns:
        dict: JSON list of teams
    """
    url = f"{BASE}/league/teams.json"
    return str(_request(url))


# ============================================================
# PLAYER ENDPOINT (1)
# ============================================================


@mcp.resource("nba://player/{player_id}/profile")
def player_profile(player_id: str):
    """
    Player Profile

    URL Format:
        players/{player_id}/profile.json

    Description:
        Provides player biographical info, season-by-season statistics, draft
        details, and team associations.

    Parameters:
        player_id (str): Unique player identifier

    Returns:
        dict: JSON player profile
    """
    url = f"{BASE}/players/{player_id}/profile.json"
    return str(_request(url))


# ============================================================
# TEAM ENDPOINTS (3)
# ============================================================


@mcp.resource("nba://team/{team_id}/profile")
def team_profile(team_id: str):
    """
    Team Profile

    URL Format:
        teams/{team_id}/profile.json

    Description:
        Returns high-level team information including coaches, roster, injuries,
        venue details, and player references.

    Parameters:
        team_id (str): Unique team identifier

    Returns:
        dict: JSON team profile data
    """
    url = f"{BASE}/teams/{team_id}/profile.json"
    return str(_request(url))


@mcp.resource("nba://team/{team_id}/depth-chart")
def team_depth_chart(team_id: str):
    """
    Team Depth Chart

    URL Format:
        teams/{team_id}/depth_chart.json

    Description:
        Provides the current positional depth chart for the specified NBA team.
        Includes ordering at each position, coach information, and active roster
        relevant for depth assignments.

    Parameters:
        team_id (str): Unique team identifier

    Returns:
        dict: JSON team depth chart
    """
    url = f"{BASE}/teams/{team_id}/depth_chart.json"
    return str(_request(url))


@mcp.tool
def seasonal_statistics(season_year: int, season_type: str, team_id: str):
    """
    Seasonal Statistics

    URL Format:
        seasons/{season_year}/{season_type}/teams/{team_id}/statistics.json

    Description:
        Provides full seasonal statistics for the specified team, including totals
        and averages for team performance, player contributions, and opponent stats.

    Parameters:
        season_year (int): Season start year (YYYY)
        season_type (str): PRE, REG, IST, PIT, PST
        team_id (str): Unique team identifier

    Returns:
        dict: JSON containing detailed seasonal statistics
    """
    url = f"{BASE}/seasons/{season_year}/{season_type}/teams/{team_id}/statistics.json"
    return _request(url)


# ============================================================
# SERIES ENDPOINT (1)
# ============================================================


@mcp.tool
def series_statistics(series_id: str, team_id: str):
    """
    Series Statistics

    URL Format:
        series/{series_id}/teams/{team_id}/statistics.json

    Description:
        Provides detailed team and player statistics for a specific playoff series.
        Includes seasonal totals/averages, opponent stats, and team-level metrics.

    Parameters:
        series_id (str): Unique series identifier
        team_id (str): Team participating in the series

    Returns:
        dict: JSON statistics for the requested series-team pair
    """
    url = f"{BASE}/series/{series_id}/teams/{team_id}/statistics.json"
    return _request(url)


# ============================================================
# SPLITS ENDPOINTS (4)
# ============================================================


@mcp.tool
def splits_game(season_year: int, season_type: str, team_id: str):
    """
    Game Splits

    URL Format:
        seasons/{season_year}/{season_type}/teams/{team_id}/splits/game.json

    Description:
        Provides detailed team, player, and opponent game-based splits including:
        wins, losses, home, road, overtime, matchups, and performance above/below .500.

    Parameters:
        season_year (int): Season start year
        season_type (str): PRE, REG, IST, PIT, PST
        team_id (str): Unique team identifier

    Returns:
        dict: JSON containing game split statistics
    """
    url = f"{BASE}/seasons/{season_year}/{season_type}/teams/{team_id}/splits/game.json"
    return _request(url)


@mcp.tool
def splits_hierarchy(season_year: int, season_type: str, team_id: str):
    """
    Hierarchy Splits

    URL Format:
        seasons/{season_year}/{season_type}/teams/{team_id}/splits/hierarchy.json

    Description:
        Provides splits by conference and division opponents, including totals and
        averages for both team and opponent metrics.

    Parameters:
        season_year (int): Season start year
        season_type (str): PRE, REG, IST, PIT, PST
        team_id (str): Unique team identifier

    Returns:
        dict: JSON containing hierarchy-based split data
    """
    url = f"{BASE}/seasons/{season_year}/{season_type}/teams/{team_id}/splits/hierarchy.json"
    return _request(url)


@mcp.tool
def splits_ingame(season_year: int, season_type: str, team_id: str):
    """
    In-Game Splits

    URL Format:
        seasons/{season_year}/{season_type}/teams/{team_id}/splits/ingame.json

    Description:
        Provides in-game splits such as higher FG%, turnovers, rebounds, fouls,
        points over/under 100, and other in-game derived context categories.

    Parameters:
        season_year (int): Season start year
        season_type (str): PRE, REG, IST, PIT, PST
        team_id (str): Unique team identifier

    Returns:
        dict: JSON containing in-game split data
    """
    url = (
        f"{BASE}/seasons/{season_year}/{season_type}/teams/{team_id}/splits/ingame.json"
    )
    return _request(url)


@mcp.tool
def splits_schedule(season_year: int, season_type: str, team_id: str):
    """
    Schedule Splits

    URL Format:
        seasons/{season_year}/{season_type}/teams/{team_id}/splits/schedule.json

    Description:
        Provides schedule-based splits including days of rest, last 5/10 games,
        performance by weekday, month, and week of season.

    Parameters:
        season_year (int): Season start year
        season_type (str): PRE, REG, IST, PIT, PST
        team_id (str): Unique team identifier

    Returns:
        dict: JSON containing schedule split data
    """
    url = f"{BASE}/seasons/{season_year}/{season_type}/teams/{team_id}/splits/schedule.json"
    return _request(url)


# ============================================================
# STANDINGS ENDPOINT (1)
# ============================================================


@mcp.tool
def standings(season_year: int, season_type: str):
    """
    Standings

    URL Format:
        seasons/{season_year}/{season_type}/standings.json

    Description:
        Provides detailed standings including overall records, conference and
        division rankings, and playoff clinching indicators.

    Parameters:
        season_year (int): Season start year
        season_type (str): PRE, REG, IST, PIT, PST

    Returns:
        dict: JSON containing standings and ranking data
    """
    url = f"{BASE}/seasons/{season_year}/{season_type}/standings.json"
    return _request(url)


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8765)
