import os
import sys
import importlib.util
from dotenv import load_dotenv
from unittest.mock import MagicMock

# Load environment variables
load_dotenv()

# Mock fastmcp to preserve original functions so we can call them directly
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

# Import local mcp/server.py directly
spec = importlib.util.spec_from_file_location("local_mcp_server", os.path.join(os.getcwd(), "mcp", "server.py"))
local_server = importlib.util.module_from_spec(spec)
sys.modules["local_mcp_server"] = local_server
spec.loader.exec_module(local_server)

from local_mcp_server import get_seasons

def test_real_connection():
    print("Testing real connection to SportsRadar API...")
    api_key = os.environ.get("SPORTRADAR_API_KEY")
    if not api_key:
        print("WARNING: SPORTRADAR_API_KEY not found in environment. Skipping real test.")
        return

    print(f"API Key found (starts with {api_key[:4]}...)")
    
    try:
        # Try a simple endpoint
        print("Fetching seasons...")
        result = get_seasons()
        print("Success! Response length:", len(str(result)))
        print("First 200 chars:", str(result)[:200])
    except Exception as e:
        print(f"Error making real request: {e}")

if __name__ == "__main__":
    test_real_connection()
