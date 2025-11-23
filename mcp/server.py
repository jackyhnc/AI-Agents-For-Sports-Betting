import os
import requests
from fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn

import dotenv
dotenv.load_dotenv()

mcp = FastMCP("NBA Data 🏀")

SPORTRADAR_API_KEY = os.environ.get("SPORTRADAR_API_KEY")
BASE_URL = "https://api.sportradar.us/nba/trial/v8/en"

def _make_request(endpoint: str) -> dict:
    """Helper to make requests to SportsRadar API"""
    if not SPORTRADAR_API_KEY:
        raise ValueError("SPORTRADAR_API_KEY environment variable is not set")
    
    url = f"{BASE_URL}/{endpoint}.json?api_key={SPORTRADAR_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

@mcp.resource("nba://league/daily-change-log/{date}")
def get_daily_change_log(date: str) -> str:
    """
    Get IDs and timestamps for updated teams, players, game statistics, schedules, and standings.
    Args:
        date: Date in YYYY-MM-DD format
    Returns:
        JSON object containing 'changes' list with 'id', 'type' (e.g. 'team', 'player'), and 'timestamp'.
    """
    try:
        y, m, d = date.split("-")
        endpoint = f"league/daily_change_log/{y}/{m}/{d}"
        data = _make_request(endpoint)
        return str(data)
    except Exception as e:
        return f"Error fetching daily change log: {str(e)}"

@mcp.resource("nba://league/daily-injuries/{date}")
def get_daily_injuries(date: str) -> str:
    """
    Get details for all injuries updated on a given date.
    Args:
        date: Date in YYYY-MM-DD format
    Returns:
        JSON object with 'injuries' list containing player info, injury description, status, and update date.
    """
    try:
        y, m, d = date.split("-")
        endpoint = f"league/injuries/{y}/{m}/{d}"
        data = _make_request(endpoint)
        return str(data)
    except Exception as e:
        return f"Error fetching daily injuries: {str(e)}"

@mcp.resource("nba://league/daily-transfers/{date}")
def get_daily_transfers(date: str) -> str:
    """
    Get information on player transfers added or edited during the day.
    Args:
        date: Date in YYYY-MM-DD format
    Returns:
        JSON object with 'transfers' list containing player info, from/to team info, and effective date.
    """
    try:
        y, m, d = date.split("-")
        endpoint = f"league/transfers/{y}/{m}/{d}"
        data = _make_request(endpoint)
        return str(data)
    except Exception as e:
        return f"Error fetching daily transfers: {str(e)}"

@mcp.resource("nba://league/hierarchy")
def get_league_hierarchy() -> str:
    """
    Get the organizational structure of the league (conferences, divisions, teams).
    Returns:
        JSON object with 'conferences' list. Each conference has 'divisions', which have 'teams'.
        Teams contain 'id', 'name', 'market', 'alias', and venue info.
    """
    endpoint = "league/hierarchy"
    data = _make_request(endpoint)
    return str(data)

@mcp.resource("nba://league/seasons")
def get_seasons() -> str:
    """
    Get list of available seasons.
    Returns:
        JSON object with 'seasons' list containing 'id', 'year', 'type' (REG/PRE/PST), and dates.
    """
    endpoint = "league/seasons"
    data = _make_request(endpoint)
    return str(data)

@mcp.resource("nba://league/free-agents")
def get_free_agents() -> str:
    """
    Get list of free agents.
    Returns:
        JSON object with 'free_agents' list containing player bio info (id, name, position, etc.).
    """
    endpoint = "league/free_agents"
    data = _make_request(endpoint)
    return str(data)

@mcp.resource("nba://league/injuries")
def get_league_injuries() -> str:
    """
    Get general injury information for the league.
    Returns:
        JSON object with 'teams' list. Each team contains 'players' list with injury details.
    """
    endpoint = "league/injuries"
    data = _make_request(endpoint)
    return str(data)

@mcp.resource("nba://games/{date}")
def get_daily_schedule(date: str) -> str:
    """
    Get the NBA daily schedule for a specific date.
    Args:
        date: Date in YYYY-MM-DD format
    Returns:
        JSON object with 'games' list. Each game contains 'id', 'status', 'scheduled', 'home', 'away', and venue info.
    """
    try:
        y, m, d = date.split("-")
        endpoint = f"games/{y}/{m}/{d}/schedule"
        data = _make_request(endpoint)
        return str(data)
    except Exception as e:
        return f"Error fetching schedule: {str(e)}"

@mcp.resource("nba://series/{year}/{season_type}/schedule")
def get_series_schedule(year: int, season_type: str) -> str:
    """
    Get the series schedule for a specific season.
    Args:
        year: Season year (e.g., 2023)
        season_type: 'PST' (Postseason) usually
    Returns:
        JSON object with 'series' list. Each series contains 'id', 'title', 'round', 'participants', and 'games'.
    """
    endpoint = f"series/{year}/{season_type}/schedule"
    data = _make_request(endpoint)
    return str(data)

@mcp.tool
def get_league_leaders(year: int, season_type: str) -> dict:
    """
    Get league leaders for a specific season.
    Args:
        year: Season year (e.g., 2023)
        season_type: 'REG', 'PRE', 'PST'
    Returns:
        JSON object with categories (e.g., 'points', 'rebounds'). Each category has a 'leaders' list of players with rank and value.
    """
    endpoint = f"seasons/{year}/{season_type}/leaders"
    return _make_request(endpoint)

@mcp.tool
def get_rankings(year: int, season_type: str) -> dict:
    """
    Get team rankings for a specific season.
    Args:
        year: Season year (e.g., 2023)
        season_type: 'REG', 'PRE', 'PST'
    Returns:
        JSON object with 'conferences' list. Each conference has 'divisions' and 'teams' with rank, wins, losses, etc.
    """
    endpoint = f"seasons/{year}/{season_type}/rankings"
    return _make_request(endpoint)

@mcp.tool
def get_seasonal_statistics(year: int, season_type: str, team_id: str) -> dict:
    """
    Get statistics for a team in a specific season.
    Args:
        year: Season year
        season_type: 'REG', 'PRE', 'PST'
        team_id: Team ID
    Returns:
        JSON object with 'own_record' (total, average) and 'opponents' stats. Includes field goals, rebounds, etc.
    """
    endpoint = f"seasons/{year}/{season_type}/teams/{team_id}/statistics"
    return _make_request(endpoint)

@mcp.tool
def get_series_statistics(series_id: str, team_id: str) -> dict:
    """
    Get statistics for a specific series.
    Args:
        series_id: Series ID
        team_id: Team ID
    Returns:
        JSON object with 'series' info and 'team' stats for that series.
    """
    endpoint = f"series/{series_id}/teams/{team_id}/statistics"
    return _make_request(endpoint)

@mcp.resource("nba://standings/{year}/{season_type}")
def get_standings(year: int, season_type: str) -> str:
    """
    Get NBA standings for a specific season.
    Args:
        year: Season year (e.g., 2023)
        season_type: 'REG' (Regular Season), 'PRE' (Preseason), 'PST' (Postseason)
    Returns:
        JSON object with 'conferences' list. Teams include 'wins', 'losses', 'win_pct', 'games_behind', 'streak'.
    """
    endpoint = f"seasons/{year}/{season_type}/standings"
    data = _make_request(endpoint)
    return str(data)

@mcp.tool
def get_game_boxscore(game_id: str) -> dict:
    """
    Get detailed boxscore for a specific NBA game.
    Args:
        game_id: The unique ID of the game
    Returns:
        JSON object with 'game' info, 'home' and 'away' teams.
        Teams contain 'scoring' (by quarter) and 'statistics' (totals and 'players' list with individual stats).
    """
    endpoint = f"games/{game_id}/boxscore"
    return _make_request(endpoint)

@mcp.tool
def get_game_play_by_play(game_id: str) -> dict:
    """
    Get detailed play-by-play data for a specific game.
    Args:
        game_id: The unique ID of the game
    Returns:
        JSON object with 'periods' list. Each period contains 'events' list (e.g., shots, fouls, subs) with description and clock.
    """
    endpoint = f"games/{game_id}/pbp"
    return _make_request(endpoint)

@mcp.tool
def get_game_summary(game_id: str) -> dict:
    """
    Get a summary of game details.
    Args:
        game_id: The unique ID of the game
    Returns:
        JSON object with 'game' info, 'home' and 'away' scoring by quarter, and high-level stats.
    """
    endpoint = f"games/{game_id}/summary"
    return _make_request(endpoint)

@mcp.tool
def get_team_profile(team_id: str) -> dict:
    """
    Get team details and roster.
    Args:
        team_id: The unique ID of the team
    Returns:
        JSON object with 'id', 'name', 'market', 'venue', 'hierarchy', and 'players' list (roster).
    """
    endpoint = f"teams/{team_id}/profile"
    return _make_request(endpoint)

@mcp.tool
def get_player_profile(player_id: str) -> dict:
    """
    Get player details.
    Args:
        player_id: The unique ID of the player
    Returns:
        JSON object with 'id', 'full_name', 'position', 'height', 'weight', 'birth_date', 'draft', and 'seasons' stats.
    """
    endpoint = f"players/{player_id}/profile"
    return _make_request(endpoint)

@mcp.tool
def get_team_depth_chart(team_id: str) -> dict:
    """
    Get the depth chart for a specific team.
    Args:
        team_id: The unique ID of the team
    Returns:
        JSON object with 'positions' list. Each position has 'players' list ordered by depth rank.
    """
    endpoint = f"teams/{team_id}/depth_chart"
    return _make_request(endpoint)

@mcp.tool
def get_season_teams(year: int, season_type: str) -> dict:
    """
    Get list of teams for a specific season.
    Args:
        year: Season year
        season_type: 'REG', 'PRE', 'PST'
    Returns:
        JSON object with 'teams' list containing basic team info for that season.
    """
    # Note: 'teams' endpoint might not exist directly in v8, but 'league/hierarchy' is standard.
    # However, some docs mention seasons/{year}/{season_type}/teams. Let's try that.
    endpoint = f"seasons/{year}/{season_type}/teams"
    return _make_request(endpoint)

# Splits Endpoints

@mcp.tool
def get_game_splits(game_id: str) -> dict:
    """
    Get splits for a specific game.
    Args:
        game_id: The unique ID of the game
    Returns:
        JSON object with 'home' and 'away' splits (e.g., shooting percentages by area).
    """
    endpoint = f"games/{game_id}/splits"
    return _make_request(endpoint)

@mcp.tool
def get_season_splits(year: int, season_type: str, team_id: str) -> dict:
    """
    Get season splits for a team.
    Args:
        year: Season year
        season_type: 'REG', 'PRE', 'PST'
        team_id: Team ID
    Returns:
        JSON object with 'total', 'average', and 'opponents' stats broken down by various categories.
    """
    endpoint = f"seasons/{year}/{season_type}/teams/{team_id}/splits"
    return _make_request(endpoint)

@mcp.tool
def get_in_game_splits(year: int, season_type: str, team_id: str) -> dict:
    """
    Get in-game splits for a team (e.g. performance by quarter).
    Args:
        year: Season year
        season_type: 'REG', 'PRE', 'PST'
        team_id: Team ID
    Returns:
        JSON object with stats broken down by 'quarters' or 'halves'.
    """
    endpoint = f"seasons/{year}/{season_type}/teams/{team_id}/splits/ingame"
    return _make_request(endpoint)

@mcp.tool
def get_schedule_splits(year: int, season_type: str, team_id: str) -> dict:
    """
    Get schedule splits for a team (e.g. home vs away).
    Args:
        year: Season year
        season_type: 'REG', 'PRE', 'PST'
        team_id: Team ID
    Returns:
        JSON object with stats broken down by 'home', 'away', etc.
    """
    endpoint = f"seasons/{year}/{season_type}/teams/{team_id}/splits/schedule"
    return _make_request(endpoint)

@mcp.tool
def get_hierarchy_splits(year: int, season_type: str, team_id: str) -> dict:
    """
    Get hierarchy splits for a team (e.g. vs conference/division).
    Args:
        year: Season year
        season_type: 'REG', 'PRE', 'PST'
        team_id: Team ID
    Returns:
        JSON object with stats broken down by 'conference' and 'division' opponents.
    """
    endpoint = f"seasons/{year}/{season_type}/teams/{team_id}/splits/hierarchy"
    return _make_request(endpoint)

app = FastAPI()
# mcp.mount(app) fails due to missing _lifespan on FastAPI
# Mount the SSE app directly
app.mount("/sse", mcp.sse_app())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)