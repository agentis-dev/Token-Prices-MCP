"""Data models for token prices MCP."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class TokenPrice(BaseModel):
    """Token price information."""
    
    token_id: str = Field(..., description="Token identifier (e.g., 'bitcoin', 'ethereum')")
    symbol: str = Field(..., description="Token symbol (e.g., 'BTC', 'ETH')")
    name: str = Field(..., description="Token name (e.g., 'Bitcoin', 'Ethereum')")
    price_usd: Decimal = Field(..., description="Current price in USD")
    price_change_24h: Optional[Decimal] = Field(None, description="24h price change percentage")
    market_cap: Optional[Decimal] = Field(None, description="Market capitalization in USD")
    volume_24h: Optional[Decimal] = Field(None, description="24h trading volume in USD")
    last_updated: datetime = Field(..., description="Last update timestamp")
    source: str = Field(..., description="Data source (e.g., 'coingecko', 'dex', 'chainlink')")
    
    @validator("price_usd", "price_change_24h", "market_cap", "volume_24h", pre=True)
    def convert_to_decimal(cls, v):
        """Convert numeric values to Decimal."""
        if v is None:
            return v
        return Decimal(str(v))


class TokenData(BaseModel):
    """Extended token information."""
    
    token_id: str = Field(..., description="Token identifier")
    symbol: str = Field(..., description="Token symbol")
    name: str = Field(..., description="Token name")
    image_url: Optional[str] = Field(None, description="Token logo URL")
    current_price: Decimal = Field(..., description="Current price in USD")
    market_cap: Optional[Decimal] = Field(None, description="Market capitalization")
    market_cap_rank: Optional[int] = Field(None, description="Market cap rank")
    fully_diluted_valuation: Optional[Decimal] = Field(None, description="Fully diluted valuation")
    total_volume: Optional[Decimal] = Field(None, description="Total trading volume")
    high_24h: Optional[Decimal] = Field(None, description="24h high price")
    low_24h: Optional[Decimal] = Field(None, description="24h low price")
    price_change_24h: Optional[Decimal] = Field(None, description="24h price change")
    price_change_percentage_24h: Optional[Decimal] = Field(None, description="24h price change percentage")
    price_change_percentage_7d: Optional[Decimal] = Field(None, description="7d price change percentage")
    price_change_percentage_30d: Optional[Decimal] = Field(None, description="30d price change percentage")
    circulating_supply: Optional[Decimal] = Field(None, description="Circulating supply")
    total_supply: Optional[Decimal] = Field(None, description="Total supply")
    max_supply: Optional[Decimal] = Field(None, description="Maximum supply")
    ath: Optional[Decimal] = Field(None, description="All-time high price")
    ath_date: Optional[datetime] = Field(None, description="All-time high date")
    atl: Optional[Decimal] = Field(None, description="All-time low price")
    atl_date: Optional[datetime] = Field(None, description="All-time low date")
    last_updated: datetime = Field(..., description="Last update timestamp")


class DEXPrice(BaseModel):
    """DEX-specific price information."""
    
    token_address: str = Field(..., description="Token contract address")
    dex_name: str = Field(..., description="DEX name (e.g., 'uniswap_v3', 'pancakeswap')")
    chain: str = Field(..., description="Blockchain network")
    price_usd: Decimal = Field(..., description="Price in USD")
    liquidity_usd: Optional[Decimal] = Field(None, description="Liquidity in USD")
    volume_24h: Optional[Decimal] = Field(None, description="24h volume")
    pool_address: Optional[str] = Field(None, description="Liquidity pool address")
    pair_symbol: Optional[str] = Field(None, description="Trading pair symbol")
    last_updated: datetime = Field(..., description="Last update timestamp")


class LiquidityPool(BaseModel):
    """Liquidity pool information."""
    
    pool_address: str = Field(..., description="Pool contract address")
    dex_name: str = Field(..., description="DEX name")
    chain: str = Field(..., description="Blockchain network")
    token0_address: str = Field(..., description="Token 0 address")
    token0_symbol: str = Field(..., description="Token 0 symbol")
    token1_address: str = Field(..., description="Token 1 address")
    token1_symbol: str = Field(..., description="Token 1 symbol")
    fee_tier: Optional[Decimal] = Field(None, description="Pool fee tier")
    liquidity_usd: Decimal = Field(..., description="Total liquidity in USD")
    volume_24h: Decimal = Field(..., description="24h trading volume")
    apy: Optional[Decimal] = Field(None, description="Annual percentage yield")
    last_updated: datetime = Field(..., description="Last update timestamp")


class ChainlinkPrice(BaseModel):
    """Chainlink price feed data."""
    
    pair: str = Field(..., description="Price pair (e.g., 'ETH/USD')")
    price: Decimal = Field(..., description="Current price")
    decimals: int = Field(..., description="Price feed decimals")
    feed_address: str = Field(..., description="Price feed contract address")
    chain: str = Field(..., description="Blockchain network")
    last_updated: datetime = Field(..., description="Last update timestamp")
    round_id: Optional[int] = Field(None, description="Round ID")
    started_at: Optional[datetime] = Field(None, description="Round started timestamp")


class TokenSupply(BaseModel):
    """Token supply information."""
    
    token_address: str = Field(..., description="Token contract address")
    chain: str = Field(..., description="Blockchain network")
    total_supply: Decimal = Field(..., description="Total supply")
    circulating_supply: Optional[Decimal] = Field(None, description="Circulating supply")
    max_supply: Optional[Decimal] = Field(None, description="Maximum supply")
    burned_supply: Optional[Decimal] = Field(None, description="Burned supply")
    holders_count: Optional[int] = Field(None, description="Number of holders")
    decimals: int = Field(..., description="Token decimals")
    last_updated: datetime = Field(..., description="Last update timestamp")


class TokenHolder(BaseModel):
    """Token holder information."""
    
    address: str = Field(..., description="Holder address")
    balance: Decimal = Field(..., description="Token balance")
    percentage: Decimal = Field(..., description="Percentage of total supply")
    is_contract: bool = Field(False, description="Whether the address is a contract")
    label: Optional[str] = Field(None, description="Address label if known")


class MarketOverview(BaseModel):
    """Overall market statistics."""
    
    total_market_cap: Decimal = Field(..., description="Total market capitalization")
    total_volume_24h: Decimal = Field(..., description="Total 24h volume")
    market_cap_change_percentage_24h: Decimal = Field(..., description="Market cap change 24h")
    bitcoin_dominance: Decimal = Field(..., description="Bitcoin dominance percentage")
    ethereum_dominance: Decimal = Field(..., description="Ethereum dominance percentage")
    active_cryptocurrencies: int = Field(..., description="Number of active cryptocurrencies")
    markets: int = Field(..., description="Number of markets")
    last_updated: datetime = Field(..., description="Last update timestamp")


class TrendingToken(BaseModel):
    """Trending token information."""
    
    token_id: str = Field(..., description="Token identifier")
    symbol: str = Field(..., description="Token symbol")
    name: str = Field(..., description="Token name")
    rank: int = Field(..., description="Trending rank")
    price_usd: Decimal = Field(..., description="Current price in USD")
    price_change_24h: Decimal = Field(..., description="24h price change percentage")
    volume_24h: Decimal = Field(..., description="24h trading volume")
    search_score: Optional[Decimal] = Field(None, description="Search popularity score")


class PriceHistory(BaseModel):
    """Historical price data point."""
    
    timestamp: datetime = Field(..., description="Price timestamp")
    price: Decimal = Field(..., description="Price at timestamp")
    market_cap: Optional[Decimal] = Field(None, description="Market cap at timestamp")
    volume: Optional[Decimal] = Field(None, description="Volume at timestamp")


class ChainInfo(BaseModel):
    """Blockchain network information."""
    
    chain_id: str = Field(..., description="Chain identifier")
    name: str = Field(..., description="Chain name")
    symbol: str = Field(..., description="Native token symbol")
    rpc_url: str = Field(..., description="RPC endpoint URL")
    explorer_url: Optional[str] = Field(None, description="Block explorer URL")
    is_testnet: bool = Field(False, description="Whether this is a testnet")
    supported_dexes: List[str] = Field(default_factory=list, description="Supported DEXs on this chain")


class DEXInfo(BaseModel):
    """DEX platform information."""
    
    dex_id: str = Field(..., description="DEX identifier")
    name: str = Field(..., description="DEX name")
    website: Optional[str] = Field(None, description="DEX website")
    supported_chains: List[str] = Field(default_factory=list, description="Supported chains")
    fee_structure: Optional[Dict[str, Any]] = Field(None, description="Fee structure information")
    tvl_usd: Optional[Decimal] = Field(None, description="Total value locked in USD")


class APIResponse(BaseModel):
    """Generic API response wrapper."""
    
    success: bool = Field(True, description="Whether the request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if unsuccessful")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    source: str = Field(..., description="Data source")
    cache_hit: bool = Field(False, description="Whether data was served from cache")


class SearchResult(BaseModel):
    """Token search result."""
    
    token_id: str = Field(..., description="Token identifier")
    symbol: str = Field(..., description="Token symbol")
    name: str = Field(..., description="Token name")
    image_url: Optional[str] = Field(None, description="Token logo URL")
    market_cap_rank: Optional[int] = Field(None, description="Market cap rank")
    price_usd: Optional[Decimal] = Field(None, description="Current price")
    relevance_score: Decimal = Field(..., description="Search relevance score")


class RateLimitInfo(BaseModel):
    """Rate limit information."""
    
    requests_remaining: int = Field(..., description="Remaining requests")
    reset_time: datetime = Field(..., description="Rate limit reset time")
    limit_per_minute: int = Field(..., description="Requests per minute limit")
    current_usage: int = Field(..., description="Current usage count") 