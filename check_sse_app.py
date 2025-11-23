from fastmcp import FastMCP
mcp = FastMCP("test")
print(f"Type of sse_app: {type(mcp.sse_app)}")
print(f"Is callable? {callable(mcp.sse_app)}")
