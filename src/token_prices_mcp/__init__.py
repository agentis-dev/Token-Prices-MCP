"""Token Prices MCP - Message Control Protocol server for cryptocurrency token prices."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("token-prices-mcp")
except PackageNotFoundError:
    __version__ = "0.1.0"

from .server import create_server
from .client import TokenPricesMCPClient

__all__ = [
    "__version__",
    "create_server", 
    "TokenPricesMCPClient",
] 