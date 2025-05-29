"""Token Prices MCP Server implementation."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .config import settings, POPULAR_TOKENS
from .models import TokenPrice, TokenData, SearchResult, MarketOverview, TrendingToken
from .services import DataAggregatorService

logger = logging.getLogger(__name__)


# Tool argument models
class GetTokenPriceArgs(BaseModel):
    """Arguments for get_token_price tool."""
    token_id: str = Field(..., description="Token identifier (e.g., 'bitcoin', 'ethereum')")
    vs_currency: str = Field(default="usd", description="Currency to compare against")


class GetMultiplePricesArgs(BaseModel):
    """Arguments for get_multiple_prices tool."""
    token_ids: List[str] = Field(..., description="List of token identifiers")
    vs_currency: str = Field(default="usd", description="Currency to compare against")


class GetTokenDataArgs(BaseModel):
    """Arguments for get_token_data tool."""
    token_id: str = Field(..., description="Token identifier")
    include_24h_change: bool = Field(default=False, description="Include 24h change data")


class GetPriceHistoryArgs(BaseModel):
    """Arguments for get_price_history tool."""
    token_id: str = Field(..., description="Token identifier")
    days: int = Field(default=7, description="Number of days of history")


class SearchTokensArgs(BaseModel):
    """Arguments for search_tokens tool."""
    query: str = Field(..., description="Search query (token name or symbol)")


class GetChainlinkPriceArgs(BaseModel):
    """Arguments for get_chainlink_price tool."""
    pair: str = Field(..., description="Price pair (e.g., 'ETH/USD')")
    chain: str = Field(default="ethereum", description="Blockchain network")


class GetTokenSupplyArgs(BaseModel):
    """Arguments for get_token_supply tool."""
    token_address: str = Field(..., description="Token contract address")
    chain: str = Field(default="ethereum", description="Blockchain network")


class GetTrendingTokensArgs(BaseModel):
    """Arguments for get_trending_tokens tool."""
    limit: int = Field(default=10, description="Number of trending tokens to return")


class GetTopGainersArgs(BaseModel):
    """Arguments for get_top_gainers tool."""
    limit: int = Field(default=10, description="Number of top gainers to return")
    timeframe: str = Field(default="24h", description="Timeframe for gains")


class GetTopLosersArgs(BaseModel):
    """Arguments for get_top_losers tool."""
    limit: int = Field(default=10, description="Number of top losers to return")
    timeframe: str = Field(default="24h", description="Timeframe for losses")


def create_server(name: str = None, cache_ttl: int = None, rate_limit: int = None) -> FastMCP:
    """Create and configure the Token Prices MCP server."""
    
    if name is None:
        name = settings.server_name
    
    # Initialize the MCP server
    mcp = FastMCP(name)
    
    # Global data service instance
    data_service = None
    
    @mcp.tool()
    async def get_token_price(args: GetTokenPriceArgs) -> Dict[str, Any]:
        """Get current token price from CoinGecko."""
        nonlocal data_service
        
        try:
            if not data_service:
                data_service = DataAggregatorService()
                await data_service.__aenter__()
            
            price = await data_service.coingecko_service.get_token_price(
                args.token_id, args.vs_currency
            )
            
            return {
                "success": True,
                "data": {
                    "token_id": price.token_id,
                    "symbol": price.symbol,
                    "name": price.name,
                    "price": float(price.price_usd),
                    "price_change_24h": float(price.price_change_24h) if price.price_change_24h else None,
                    "market_cap": float(price.market_cap) if price.market_cap else None,
                    "volume_24h": float(price.volume_24h) if price.volume_24h else None,
                    "last_updated": price.last_updated.isoformat(),
                    "source": price.source
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_token_price: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @mcp.tool()
    async def get_multiple_prices(args: GetMultiplePricesArgs) -> Dict[str, Any]:
        """Get multiple token prices in a single request."""
        nonlocal data_service
        
        try:
            if not data_service:
                data_service = DataAggregatorService()
                await data_service.__aenter__()
            
            prices = await data_service.coingecko_service.get_multiple_prices(
                args.token_ids, args.vs_currency
            )
            
            return {
                "success": True,
                "data": [
                    {
                        "token_id": price.token_id,
                        "symbol": price.symbol,
                        "name": price.name,
                        "price": float(price.price_usd),
                        "price_change_24h": float(price.price_change_24h) if price.price_change_24h else None,
                        "market_cap": float(price.market_cap) if price.market_cap else None,
                        "volume_24h": float(price.volume_24h) if price.volume_24h else None,
                        "last_updated": price.last_updated.isoformat(),
                        "source": price.source
                    }
                    for price in prices
                ],
                "count": len(prices),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_multiple_prices: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @mcp.tool()
    async def get_token_data(args: GetTokenDataArgs) -> Dict[str, Any]:
        """Get detailed token information including market data."""
        nonlocal data_service
        
        try:
            if not data_service:
                data_service = DataAggregatorService()
                await data_service.__aenter__()
            
            token_data = await data_service.coingecko_service.get_token_data(
                args.token_id, args.include_24h_change
            )
            
            return {
                "success": True,
                "data": {
                    "token_id": token_data.token_id,
                    "symbol": token_data.symbol,
                    "name": token_data.name,
                    "image_url": token_data.image_url,
                    "current_price": float(token_data.current_price),
                    "market_cap": float(token_data.market_cap) if token_data.market_cap else None,
                    "market_cap_rank": token_data.market_cap_rank,
                    "fully_diluted_valuation": float(token_data.fully_diluted_valuation) if token_data.fully_diluted_valuation else None,
                    "total_volume": float(token_data.total_volume) if token_data.total_volume else None,
                    "high_24h": float(token_data.high_24h) if token_data.high_24h else None,
                    "low_24h": float(token_data.low_24h) if token_data.low_24h else None,
                    "price_change_24h": float(token_data.price_change_24h) if token_data.price_change_24h else None,
                    "price_change_percentage_24h": float(token_data.price_change_percentage_24h) if token_data.price_change_percentage_24h else None,
                    "price_change_percentage_7d": float(token_data.price_change_percentage_7d) if token_data.price_change_percentage_7d else None,
                    "price_change_percentage_30d": float(token_data.price_change_percentage_30d) if token_data.price_change_percentage_30d else None,
                    "circulating_supply": float(token_data.circulating_supply) if token_data.circulating_supply else None,
                    "total_supply": float(token_data.total_supply) if token_data.total_supply else None,
                    "max_supply": float(token_data.max_supply) if token_data.max_supply else None,
                    "ath": float(token_data.ath) if token_data.ath else None,
                    "ath_date": token_data.ath_date.isoformat() if token_data.ath_date else None,
                    "atl": float(token_data.atl) if token_data.atl else None,
                    "atl_date": token_data.atl_date.isoformat() if token_data.atl_date else None,
                    "last_updated": token_data.last_updated.isoformat()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_token_data: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @mcp.tool()
    async def get_price_history(args: GetPriceHistoryArgs) -> Dict[str, Any]:
        """Get historical price data for a token."""
        nonlocal data_service
        
        try:
            if not data_service:
                data_service = DataAggregatorService()
                await data_service.__aenter__()
            
            history = await data_service.coingecko_service.get_price_history(
                args.token_id, args.days
            )
            
            return {
                "success": True,
                "data": [
                    {
                        "timestamp": point.timestamp.isoformat(),
                        "price": float(point.price),
                        "market_cap": float(point.market_cap) if point.market_cap else None,
                        "volume": float(point.volume) if point.volume else None
                    }
                    for point in history
                ],
                "count": len(history),
                "days": args.days,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_price_history: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @mcp.tool()
    async def search_tokens(args: SearchTokensArgs) -> Dict[str, Any]:
        """Search for tokens by name or symbol."""
        nonlocal data_service
        
        try:
            if not data_service:
                data_service = DataAggregatorService()
                await data_service.__aenter__()
            
            results = await data_service.coingecko_service.search_tokens(args.query)
            
            return {
                "success": True,
                "data": [
                    {
                        "token_id": result.token_id,
                        "symbol": result.symbol,
                        "name": result.name,
                        "image_url": result.image_url,
                        "market_cap_rank": result.market_cap_rank,
                        "price_usd": float(result.price_usd) if result.price_usd else None,
                        "relevance_score": float(result.relevance_score)
                    }
                    for result in results
                ],
                "query": args.query,
                "count": len(results),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in search_tokens: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @mcp.tool()
    async def get_chainlink_price(args: GetChainlinkPriceArgs) -> Dict[str, Any]:
        """Get price from Chainlink price feed."""
        nonlocal data_service
        
        try:
            if not data_service:
                data_service = DataAggregatorService()
                await data_service.__aenter__()
            
            price_data = await data_service.blockchain_service.get_chainlink_price(
                args.pair, args.chain
            )
            
            return {
                "success": True,
                "data": {
                    "pair": price_data.pair,
                    "price": float(price_data.price),
                    "decimals": price_data.decimals,
                    "feed_address": price_data.feed_address,
                    "chain": price_data.chain,
                    "last_updated": price_data.last_updated.isoformat(),
                    "round_id": price_data.round_id,
                    "started_at": price_data.started_at.isoformat() if price_data.started_at else None
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_chainlink_price: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @mcp.tool()
    async def get_token_supply(args: GetTokenSupplyArgs) -> Dict[str, Any]:
        """Get token supply information from blockchain."""
        nonlocal data_service
        
        try:
            if not data_service:
                data_service = DataAggregatorService()
                await data_service.__aenter__()
            
            supply_data = await data_service.blockchain_service.get_token_supply(
                args.token_address, args.chain
            )
            
            return {
                "success": True,
                "data": {
                    "token_address": supply_data.token_address,
                    "chain": supply_data.chain,
                    "total_supply": float(supply_data.total_supply),
                    "circulating_supply": float(supply_data.circulating_supply) if supply_data.circulating_supply else None,
                    "max_supply": float(supply_data.max_supply) if supply_data.max_supply else None,
                    "burned_supply": float(supply_data.burned_supply) if supply_data.burned_supply else None,
                    "holders_count": supply_data.holders_count,
                    "decimals": supply_data.decimals,
                    "last_updated": supply_data.last_updated.isoformat()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_token_supply: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @mcp.tool()
    async def get_trending_tokens(args: GetTrendingTokensArgs) -> Dict[str, Any]:
        """Get trending tokens from CoinGecko."""
        nonlocal data_service
        
        try:
            if not data_service:
                data_service = DataAggregatorService()
                await data_service.__aenter__()
            
            trending = await data_service.coingecko_service.get_trending_tokens(args.limit)
            
            return {
                "success": True,
                "data": [
                    {
                        "token_id": token.token_id,
                        "symbol": token.symbol,
                        "name": token.name,
                        "rank": token.rank,
                        "price_usd": float(token.price_usd),
                        "price_change_24h": float(token.price_change_24h),
                        "volume_24h": float(token.volume_24h),
                        "search_score": float(token.search_score) if token.search_score else None
                    }
                    for token in trending
                ],
                "limit": args.limit,
                "count": len(trending),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_trending_tokens: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @mcp.tool()
    async def get_market_overview() -> Dict[str, Any]:
        """Get overall cryptocurrency market statistics."""
        nonlocal data_service
        
        try:
            if not data_service:
                data_service = DataAggregatorService()
                await data_service.__aenter__()
            
            overview = await data_service.coingecko_service.get_market_overview()
            
            return {
                "success": True,
                "data": {
                    "total_market_cap": float(overview.total_market_cap),
                    "total_volume_24h": float(overview.total_volume_24h),
                    "market_cap_change_percentage_24h": float(overview.market_cap_change_percentage_24h),
                    "bitcoin_dominance": float(overview.bitcoin_dominance),
                    "ethereum_dominance": float(overview.ethereum_dominance),
                    "active_cryptocurrencies": overview.active_cryptocurrencies,
                    "markets": overview.markets,
                    "last_updated": overview.last_updated.isoformat()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_market_overview: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @mcp.tool()
    async def get_supported_chains() -> Dict[str, Any]:
        """Get list of supported blockchain networks."""
        nonlocal data_service
        
        try:
            if not data_service:
                data_service = DataAggregatorService()
            
            chains = data_service.get_supported_chains()
            
            return {
                "success": True,
                "data": [
                    {
                        "chain_id": chain.chain_id,
                        "name": chain.name,
                        "symbol": chain.symbol,
                        "rpc_url": chain.rpc_url,
                        "explorer_url": chain.explorer_url,
                        "is_testnet": chain.is_testnet,
                        "supported_dexes": chain.supported_dexes
                    }
                    for chain in chains
                ],
                "count": len(chains),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_supported_chains: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @mcp.tool()
    async def get_supported_dexes() -> Dict[str, Any]:
        """Get list of supported DEX platforms."""
        nonlocal data_service
        
        try:
            if not data_service:
                data_service = DataAggregatorService()
            
            dexes = data_service.get_supported_dexes()
            
            return {
                "success": True,
                "data": [
                    {
                        "dex_id": dex.dex_id,
                        "name": dex.name,
                        "website": dex.website,
                        "supported_chains": dex.supported_chains,
                        "fee_structure": dex.fee_structure,
                        "tvl_usd": float(dex.tvl_usd) if dex.tvl_usd else None
                    }
                    for dex in dexes
                ],
                "count": len(dexes),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in get_supported_dexes: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Resources
    @mcp.resource("prices://tokens")
    async def get_tokens_list() -> str:
        """Get list of popular tokens available for price queries."""
        return f"""# Popular Tokens

This resource provides a list of popular cryptocurrency tokens that are supported for price queries.

## Supported Tokens

{chr(10).join(f"- {token}" for token in POPULAR_TOKENS)}

## Usage

Use these token IDs with the `get_token_price`, `get_token_data`, or other price-related tools.

Example:
- get_token_price(token_id="bitcoin")
- get_token_data(token_id="ethereum", include_24h_change=True)

## Additional Tokens

You can also search for other tokens using the `search_tokens` tool or check CoinGecko's API for the complete list of supported tokens.

Last updated: {datetime.utcnow().isoformat()}
"""
    
    @mcp.resource("prices://tokens/{token_id}")
    async def get_token_info(token_id: str) -> str:
        """Get detailed information about a specific token."""
        nonlocal data_service
        
        try:
            if not data_service:
                data_service = DataAggregatorService()
                await data_service.__aenter__()
            
            token_data = await data_service.coingecko_service.get_token_data(token_id)
            
            return f"""# {token_data.name} ({token_data.symbol})

## Current Price Data
- **Price**: ${token_data.current_price:,.2f}
- **Market Cap**: ${token_data.market_cap:,.0f} (Rank #{token_data.market_cap_rank})
- **24h Volume**: ${token_data.total_volume:,.0f}

## Price Changes
- **24h Change**: {token_data.price_change_percentage_24h:.2f}%
- **7d Change**: {token_data.price_change_percentage_7d:.2f}%
- **30d Change**: {token_data.price_change_percentage_30d:.2f}%

## 24h Range
- **High**: ${token_data.high_24h:,.2f}
- **Low**: ${token_data.low_24h:,.2f}

## Supply Information
- **Circulating Supply**: {token_data.circulating_supply:,.0f} {token_data.symbol}
- **Total Supply**: {token_data.total_supply:,.0f} {token_data.symbol}
- **Max Supply**: {token_data.max_supply:,.0f if token_data.max_supply else "N/A"} {token_data.symbol}

## All-Time Records
- **All-Time High**: ${token_data.ath:,.2f} ({token_data.ath_date.strftime('%Y-%m-%d') if token_data.ath_date else 'N/A'})
- **All-Time Low**: ${token_data.atl:,.2f} ({token_data.atl_date.strftime('%Y-%m-%d') if token_data.atl_date else 'N/A'})

---
*Data provided by CoinGecko*
*Last updated: {token_data.last_updated.isoformat()}*
"""
        except Exception as e:
            return f"""# Token Information Error

Unable to retrieve information for token: {token_id}

Error: {str(e)}

Please check that the token ID is correct and try again.
"""
    
    @mcp.resource("prices://markets")
    async def get_markets_overview() -> str:
        """Get overall cryptocurrency market overview."""
        nonlocal data_service
        
        try:
            if not data_service:
                data_service = DataAggregatorService()
                await data_service.__aenter__()
            
            overview = await data_service.coingecko_service.get_market_overview()
            
            return f"""# Cryptocurrency Market Overview

## Market Statistics
- **Total Market Cap**: ${overview.total_market_cap:,.0f}
- **24h Volume**: ${overview.total_volume_24h:,.0f}
- **Market Cap Change (24h)**: {overview.market_cap_change_percentage_24h:.2f}%

## Market Dominance
- **Bitcoin Dominance**: {overview.bitcoin_dominance:.2f}%
- **Ethereum Dominance**: {overview.ethereum_dominance:.2f}%

## Market Coverage
- **Active Cryptocurrencies**: {overview.active_cryptocurrencies:,}
- **Markets**: {overview.markets:,}

---
*Data provided by CoinGecko*
*Last updated: {overview.last_updated.isoformat()}*
"""
        except Exception as e:
            return f"""# Market Overview Error

Unable to retrieve market overview data.

Error: {str(e)}

Please try again later.
"""
    
    return mcp 