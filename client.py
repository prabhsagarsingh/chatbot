import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class MCPClient:
    def __init__(self):
        self.session : Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

    
    async def connect_to_server(self, server_script_path: str):
        """
        Connect to an MCP server

        Args:
            server_script_path: Path to server script     
        """

        server_params = StdioServerParameters(
            command = "python",
            args = [server_script_path],
            env = None
        )

        stdio_transport = await self.exit_stack.enter