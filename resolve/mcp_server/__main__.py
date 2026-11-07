"""Allow `python -m mcp_server` as well as `python -m mcp_server.server`."""
from mcp_server.server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
