# token-prices-mcp

Message Control Protocol (MCP) server for retrieving cryptocurrency token prices from multiple blockchain sources. Built with fastmcp and supports real-time price data from CoinGecko, on-chain DEX aggregators, and blockchain price feeds.

## Features

* MCP server for token price data with multiple data sources
* Support for multiple transport protocols (stdio, SSE, WebSocket)
* Real-time price feeds from CoinGecko API
* On-chain price data from DEX aggregators (Uniswap, PancakeSwap, etc.)
* Chainlink price feed integration
* Easy-to-use client for interacting with the MCP server
* Command-line interface for running the server
* Integration with Claude Desktop
* Comprehensive caching with TTL
* Rate limiting and circuit breaker patterns
* Multi-chain support (Ethereum, BSC, Polygon, Arbitrum, etc.)

## Quick Start

```bash
# Install the package
pip install token-prices-mcp

# Run the server (stdio transport for Claude Desktop)
token-prices-mcp --transport stdio

# Or run with SSE transport
token-prices-mcp --transport sse --host 127.0.0.1 --port 8000
```

## Basic Usage

### Client with Network Transport

```python
import asyncio
import os
from token_prices_mcp.client import TokenPricesMCPClient

async def main():
    # Set the server URL (or use environment variable)
    server_url = "http://localhost:8000/sse"
    os.environ["TOKEN_PRICES_MCP_URL"] = server_url

    async with TokenPricesMCPClient() as client:
        # Get token price from CoinGecko
        btc_price = await client.get_token_price("bitcoin")
        print("BTC Price:", btc_price)

        # Get multiple token prices
        prices = await client.get_multiple_prices(["ethereum", "bitcoin", "cardano"])
        print("Multiple prices:", prices)

        # Get token price with historical data
        eth_data = await client.get_token_data("ethereum", include_24h_change=True)
        print("ETH Data:", eth_data)

        # Get price from specific DEX
        uniswap_price = await client.get_dex_price("0xA0b86a33E6D0bBa464", "uniswap_v3")
        print("Uniswap price:", uniswap_price)

if __name__ == "__main__":
    asyncio.run(main())
```

### Server Configuration

```python
from token_prices_mcp.server import create_server
import asyncio

# Create the server with custom configuration
server = create_server(
    name="Token Prices API",
    cache_ttl=300,  # 5 minutes cache
    rate_limit=100  # 100 requests per minute
)

# Run the server with desired transport
if __name__ == "__main__":
    asyncio.run(
        server.run(
            transport="stdio",  # or "sse"
            host="127.0.0.1",   # for network transports
            port=8000           # for network transports
        )
    )
```

## Available Tools

### Price Data

* `get_token_price(token_id: str, vs_currency: str = "usd")`: Get current token price
* `get_multiple_prices(token_ids: list, vs_currency: str = "usd")`: Get multiple token prices
* `get_token_data(token_id: str, include_24h_change: bool = False)`: Get detailed token data
* `get_price_history(token_id: str, days: int = 7)`: Get historical price data
* `search_tokens(query: str)`: Search for tokens by name or symbol

### DEX Integration

* `get_dex_price(token_address: str, dex: str, chain: str = "ethereum")`: Get price from specific DEX
* `get_liquidity_pools(token_address: str, chain: str = "ethereum")`: Get liquidity pool information
* `get_dex_volume(token_address: str, timeframe: str = "24h")`: Get trading volume from DEXs

### On-Chain Data

* `get_chainlink_price(pair: str)`: Get price from Chainlink price feeds
* `get_token_supply(token_address: str, chain: str = "ethereum")`: Get token supply information
* `get_token_holders(token_address: str, chain: str = "ethereum")`: Get top token holders
* `get_market_cap(token_id: str)`: Get real-time market cap

### Market Analytics

* `get_trending_tokens(limit: int = 10)`: Get trending tokens
* `get_top_gainers(limit: int = 10, timeframe: str = "24h")`: Get top gainers
* `get_top_losers(limit: int = 10, timeframe: str = "24h")`: Get top losers
* `get_market_overview()`: Get overall market statistics

### Resources

* `prices://tokens`: Get all supported tokens
* `prices://tokens/{token_id}`: Get specific token information
* `prices://markets`: Get all markets information
* `prices://chains`: Get supported blockchain networks
* `prices://dexes`: Get supported DEX platforms

## Environment Variables

```bash
# CoinGecko API (optional, for higher rate limits)
COINGECKO_API_KEY=your_api_key_here

# Ethereum RPC endpoint (for on-chain data)
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/your_project_id

# BSC RPC endpoint
BSC_RPC_URL=https://bsc-dataseed.binance.org/

# Polygon RPC endpoint  
POLYGON_RPC_URL=https://polygon-rpc.com/

# Arbitrum RPC endpoint
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc

# Cache settings
CACHE_TTL=300
RATE_LIMIT_PER_MINUTE=100

# Server settings
TOKEN_PRICES_MCP_URL=http://localhost:8000/sse
```

## Command-line Interface

```bash
# Show help
token-prices-mcp --help

# Run with stdio transport (for Claude Desktop)
token-prices-mcp --transport stdio

# Run with SSE transport
token-prices-mcp --transport sse --host localhost --port 8000

# Run with custom cache TTL
token-prices-mcp --transport stdio --cache-ttl 600

# Run with debug logging
token-prices-mcp --transport stdio --debug
```

## Supported Chains

- Ethereum
- Binance Smart Chain (BSC)
- Polygon
- Arbitrum
- Optimism
- Avalanche
- Fantom
- Cronos
- Aurora

## Supported DEXs

- Uniswap V2/V3
- PancakeSwap V2/V3
- SushiSwap
- QuickSwap
- TraderJoe
- SpookySwap
- Curve Finance
- Balancer
- 1inch

## Data Sources

1. **CoinGecko API**: Primary source for token prices and market data
2. **On-chain DEX Data**: Real-time prices from decentralized exchanges
3. **Chainlink Price Feeds**: Decentralized oracle price data
4. **Blockchain RPCs**: Direct on-chain token and contract data

## Caching Strategy

- Price data cached for 5 minutes by default
- Market data cached for 10 minutes
- Token metadata cached for 1 hour
- Historical data cached for 24 hours
- Configurable TTL per data type

## Rate Limiting

- CoinGecko API: 100 requests/minute (free tier)
- On-chain calls: 50 requests/minute per RPC
- Internal rate limiting with exponential backoff
- Circuit breaker pattern for failed requests

## Development

```bash
# Clone the repository
git clone https://github.com/tokenprices/token-prices-mcp.git
cd token-prices-mcp

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run type checking
pyright src/token_prices_mcp

# Run linting
ruff check .
```

## Examples

Check the `examples/` directory for more usage examples:

* `claude_desktop_server.py`: Run the server with stdio transport for Claude Desktop
* `claude_desktop_client.py`: Client for connecting to a stdio server
* `sse_server.py`: Run the server with SSE transport
* `sse_client.py`: Client for connecting to an SSE server
* `price_monitoring.py`: Real-time price monitoring example
* `dex_arbitrage.py`: DEX price comparison example

## API Rate Limits

### CoinGecko (Free Tier)
- 100 requests/minute
- 1000 requests/hour

### CoinGecko (Pro Tier)
- 500 requests/minute
- 10000 requests/hour

### On-Chain RPCs
- Varies by provider
- Built-in rate limiting and retry logic

## Error Handling

The server implements comprehensive error handling:

- Automatic retry with exponential backoff
- Circuit breaker for failed API endpoints
- Fallback to cached data when APIs are unavailable
- Graceful degradation of service quality
- Detailed error logging and monitoring

## License

Apache License 2.0

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Support

- Documentation: [GitHub README](https://github.com/tokenprices/token-prices-mcp#readme)
- Issues: [GitHub Issues](https://github.com/tokenprices/token-prices-mcp/issues)
- Community: [Discussions](https://github.com/tokenprices/token-prices-mcp/discussions) 