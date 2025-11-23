import os
import sys
import json
from unittest.mock import MagicMock, patch

# Mock fastmcp to preserve original functions
mock_fastmcp = MagicMock()
def identity_decorator(*args, **kwargs):
    # Check if used as @mcp.tool (bare decorator)
    if len(args) == 1 and callable(args[0]):
        return args[0]
    # Used as @mcp.resource("...") or @mcp.tool(...)
    def wrapper(func):
        return func
    return wrapper
mock_fastmcp.FastMCP.return_value.resource.side_effect = identity_decorator
mock_fastmcp.FastMCP.return_value.tool.side_effect = identity_decorator
sys.modules["fastmcp"] = mock_fastmcp

# Set dummy API key for testing BEFORE importing server
os.environ["SPORTRADAR_API_KEY"] = "test_key"

import importlib.util

# Import local mcp/server.py directly to avoid conflict with installed 'mcp' package
spec = importlib.util.spec_from_file_location("local_mcp_server", os.path.join(os.getcwd(), "mcp", "server.py"))
local_server = importlib.util.module_from_spec(spec)
sys.modules["local_mcp_server"] = local_server
spec.loader.exec_module(local_server)

from local_mcp_server import (
    get_daily_change_log, get_daily_injuries, get_daily_transfers, get_league_hierarchy,
    get_seasons, get_free_agents, get_league_injuries, get_daily_schedule,
    get_game_boxscore, get_game_play_by_play, get_game_summary,
    get_series_schedule, get_league_leaders, get_rankings, get_seasonal_statistics,
    get_series_statistics, get_standings, get_team_depth_chart, get_season_teams,
    get_game_splits, get_season_splits, get_in_game_splits, get_schedule_splits, get_hierarchy_splits
)

def test_nba_mcp():
    print("Testing NBA MCP functions...")

    # Mock requests.get to avoid actual API calls during basic logic verification
    with patch("requests.get") as mock_get:
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success", "data": "mock_data"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Helper to verify calls
        def verify_call(func, args, expected_url_part):
            print(f"\nTesting {func.__name__}...")
            try:
                if args:
                    result = func(*args)
                else:
                    result = func()
                
                # Check result
                if isinstance(result, str):
                    assert "mock_data" in result
                else:
                    assert result["data"] == "mock_data"
                
                # Check URL
                call_args, _ = mock_get.call_args
                print(f"Called URL: {call_args[0]}")
                assert expected_url_part in call_args[0]
            except Exception as e:
                print(f"FAILED: {e}")

        # League & Daily
        verify_call(get_daily_change_log, ["2023-10-25"], "league/daily_change_log/2023/10/25.json")
        verify_call(get_daily_injuries, ["2023-10-25"], "league/injuries/2023/10/25.json")
        verify_call(get_daily_transfers, ["2023-10-25"], "league/transfers/2023/10/25.json")
        verify_call(get_league_hierarchy, [], "league/hierarchy.json")
        verify_call(get_seasons, [], "league/seasons.json")
        verify_call(get_free_agents, [], "league/free_agents.json")
        verify_call(get_league_injuries, [], "league/injuries.json")
        verify_call(get_daily_schedule, ["2023-10-25"], "games/2023/10/25/schedule.json")

        # Game
        verify_call(get_game_boxscore, ["game_123"], "games/game_123/boxscore.json")
        verify_call(get_game_play_by_play, ["game_123"], "games/game_123/pbp.json")
        verify_call(get_game_summary, ["game_123"], "games/game_123/summary.json")

        # Season & Series
        verify_call(get_series_schedule, [2023, "PST"], "series/2023/PST/schedule.json")
        verify_call(get_league_leaders, [2023, "REG"], "seasons/2023/REG/leaders.json")
        verify_call(get_rankings, [2023, "REG"], "seasons/2023/REG/rankings.json")
        verify_call(get_seasonal_statistics, [2023, "REG", "team_1"], "seasons/2023/REG/teams/team_1/statistics.json")
        verify_call(get_series_statistics, ["series_1", "team_1"], "series/series_1/teams/team_1/statistics.json")
        verify_call(get_standings, [2023, "REG"], "seasons/2023/REG/standings.json")

        # Team & Player
        verify_call(get_team_depth_chart, ["team_1"], "teams/team_1/depth_chart.json")
        verify_call(get_season_teams, [2023, "REG"], "seasons/2023/REG/teams.json")

        # Splits
        verify_call(get_game_splits, ["game_123"], "games/game_123/splits.json")
        verify_call(get_season_splits, [2023, "REG", "team_1"], "seasons/2023/REG/teams/team_1/splits.json")
        verify_call(get_in_game_splits, [2023, "REG", "team_1"], "seasons/2023/REG/teams/team_1/splits/ingame.json")
        verify_call(get_schedule_splits, [2023, "REG", "team_1"], "seasons/2023/REG/teams/team_1/splits/schedule.json")
        verify_call(get_hierarchy_splits, [2023, "REG", "team_1"], "seasons/2023/REG/teams/team_1/splits/hierarchy.json")

    print("\nVerification complete.")

if __name__ == "__main__":
    test_nba_mcp()
