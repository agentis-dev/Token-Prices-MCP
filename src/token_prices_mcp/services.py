"""Data services for retrieving token prices from various sources."""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import aiohttp
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential
from web3 import Web3
from web3.exceptions import Web3Exception

from .config import settings, CHAIN_CONFIGS, DEX_CONFIGS, CHAINLINK_FEEDS, POPULAR_TOKENS
from .models import (
    TokenPrice, TokenData, DEXPrice, LiquidityPool, ChainlinkPrice,
    TokenSupply, MarketOverview, TrendingToken, PriceHistory,
    SearchResult, ChainInfo, DEXInfo
)

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker for API calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e


class CoinGeckoService:
    """Service for CoinGecko API integration."""
    
    def __init__(self):
        self.base_url = settings.coingecko_base_url
        self.api_key = settings.coingecko_api_key
        self.session = None
        self.cache = TTLCache(maxsize=1000, ttl=settings.cache_price_ttl)
        self.circuit_breaker = CircuitBreaker()
        
    async def __aenter__(self):
        headers = {}
        if self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key
            
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make HTTP request to CoinGecko API."""
        url = urljoin(self.base_url, endpoint)
        
        async with self.session.get(url, params=params) as response:
            if response.status == 429:
                logger.warning("CoinGecko rate limit exceeded")
                await asyncio.sleep(60)  # Wait 1 minute for rate limit reset
                raise aiohttp.ClientError("Rate limit exceeded")
            
            response.raise_for_status()
            return await response.json()
    
    async def get_token_price(self, token_id: str, vs_currency: str = "usd") -> TokenPrice:
        """Get current token price."""
        cache_key = f"price_{token_id}_{vs_currency}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            data = await self.circuit_breaker.call(
                self._make_request,
                f"/simple/price",
                params={
                    "ids": token_id,
                    "vs_currencies": vs_currency,
                    "include_24hr_change": "true",
                    "include_market_cap": "true",
                    "include_24hr_vol": "true"
                }
            )
            
            if token_id not in data:
                raise ValueError(f"Token {token_id} not found")
            
            token_data = data[token_id]
            
            # Get token info for symbol and name
            info_data = await self.circuit_breaker.call(
                self._make_request,
                f"/coins/{token_id}",
                params={"localization": "false", "tickers": "false", "market_data": "false"}
            )
            
            price = TokenPrice(
                token_id=token_id,
                symbol=info_data.get("symbol", "").upper(),
                name=info_data.get("name", ""),
                price_usd=Decimal(str(token_data[vs_currency])),
                price_change_24h=Decimal(str(token_data.get(f"{vs_currency}_24h_change", 0))),
                market_cap=Decimal(str(token_data.get(f"{vs_currency}_market_cap", 0))),
                volume_24h=Decimal(str(token_data.get(f"{vs_currency}_24h_vol", 0))),
                last_updated=datetime.utcnow(),
                source="coingecko"
            )
            
            self.cache[cache_key] = price
            return price
            
        except Exception as e:
            logger.error(f"Error fetching price for {token_id}: {e}")
            raise
    
    async def get_multiple_prices(self, token_ids: List[str], vs_currency: str = "usd") -> List[TokenPrice]:
        """Get multiple token prices in a single request."""
        ids_str = ",".join(token_ids)
        
        try:
            data = await self.circuit_breaker.call(
                self._make_request,
                f"/simple/price",
                params={
                    "ids": ids_str,
                    "vs_currencies": vs_currency,
                    "include_24hr_change": "true",
                    "include_market_cap": "true",
                    "include_24hr_vol": "true"
                }
            )
            
            # Get token info for all tokens
            coins_data = await self.circuit_breaker.call(
                self._make_request,
                f"/coins/list"
            )
            
            coins_map = {coin["id"]: coin for coin in coins_data}
            
            prices = []
            for token_id in token_ids:
                if token_id in data:
                    token_data = data[token_id]
                    coin_info = coins_map.get(token_id, {})
                    
                    price = TokenPrice(
                        token_id=token_id,
                        symbol=coin_info.get("symbol", "").upper(),
                        name=coin_info.get("name", ""),
                        price_usd=Decimal(str(token_data[vs_currency])),
                        price_change_24h=Decimal(str(token_data.get(f"{vs_currency}_24h_change", 0))),
                        market_cap=Decimal(str(token_data.get(f"{vs_currency}_market_cap", 0))),
                        volume_24h=Decimal(str(token_data.get(f"{vs_currency}_24h_vol", 0))),
                        last_updated=datetime.utcnow(),
                        source="coingecko"
                    )
                    prices.append(price)
            
            return prices
            
        except Exception as e:
            logger.error(f"Error fetching multiple prices: {e}")
            raise
    
    async def get_token_data(self, token_id: str, include_24h_change: bool = False) -> TokenData:
        """Get detailed token information."""
        cache_key = f"token_data_{token_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            data = await self.circuit_breaker.call(
                self._make_request,
                f"/coins/{token_id}",
                params={"localization": "false", "tickers": "false", "community_data": "false", "developer_data": "false"}
            )
            
            market_data = data.get("market_data", {})
            
            token_data = TokenData(
                token_id=token_id,
                symbol=data.get("symbol", "").upper(),
                name=data.get("name", ""),
                image_url=data.get("image", {}).get("large"),
                current_price=Decimal(str(market_data.get("current_price", {}).get("usd", 0))),
                market_cap=Decimal(str(market_data.get("market_cap", {}).get("usd", 0))),
                market_cap_rank=market_data.get("market_cap_rank"),
                fully_diluted_valuation=Decimal(str(market_data.get("fully_diluted_valuation", {}).get("usd", 0))),
                total_volume=Decimal(str(market_data.get("total_volume", {}).get("usd", 0))),
                high_24h=Decimal(str(market_data.get("high_24h", {}).get("usd", 0))),
                low_24h=Decimal(str(market_data.get("low_24h", {}).get("usd", 0))),
                price_change_24h=Decimal(str(market_data.get("price_change_24h", 0))),
                price_change_percentage_24h=Decimal(str(market_data.get("price_change_percentage_24h", 0))),
                price_change_percentage_7d=Decimal(str(market_data.get("price_change_percentage_7d", 0))),
                price_change_percentage_30d=Decimal(str(market_data.get("price_change_percentage_30d", 0))),
                circulating_supply=Decimal(str(market_data.get("circulating_supply", 0))),
                total_supply=Decimal(str(market_data.get("total_supply", 0))),
                max_supply=Decimal(str(market_data.get("max_supply", 0))) if market_data.get("max_supply") else None,
                ath=Decimal(str(market_data.get("ath", {}).get("usd", 0))),
                ath_date=datetime.fromisoformat(market_data.get("ath_date", {}).get("usd", "1970-01-01T00:00:00.000Z").replace("Z", "+00:00")) if market_data.get("ath_date", {}).get("usd") else None,
                atl=Decimal(str(market_data.get("atl", {}).get("usd", 0))),
                atl_date=datetime.fromisoformat(market_data.get("atl_date", {}).get("usd", "1970-01-01T00:00:00.000Z").replace("Z", "+00:00")) if market_data.get("atl_date", {}).get("usd") else None,
                last_updated=datetime.utcnow()
            )
            
            self.cache[cache_key] = token_data
            return token_data
            
        except Exception as e:
            logger.error(f"Error fetching token data for {token_id}: {e}")
            raise
    
    async def get_price_history(self, token_id: str, days: int = 7) -> List[PriceHistory]:
        """Get historical price data."""
        try:
            data = await self.circuit_breaker.call(
                self._make_request,
                f"/coins/{token_id}/market_chart",
                params={"vs_currency": "usd", "days": days}
            )
            
            history = []
            prices = data.get("prices", [])
            market_caps = data.get("market_caps", [])
            volumes = data.get("total_volumes", [])
            
            for i, price_data in enumerate(prices):
                timestamp = datetime.fromtimestamp(price_data[0] / 1000)
                price = Decimal(str(price_data[1]))
                
                market_cap = None
                if i < len(market_caps):
                    market_cap = Decimal(str(market_caps[i][1]))
                
                volume = None
                if i < len(volumes):
                    volume = Decimal(str(volumes[i][1]))
                
                history.append(PriceHistory(
                    timestamp=timestamp,
                    price=price,
                    market_cap=market_cap,
                    volume=volume
                ))
            
            return history
            
        except Exception as e:
            logger.error(f"Error fetching price history for {token_id}: {e}")
            raise
    
    async def search_tokens(self, query: str) -> List[SearchResult]:
        """Search for tokens by name or symbol."""
        try:
            data = await self.circuit_breaker.call(
                self._make_request,
                f"/search",
                params={"query": query}
            )
            
            results = []
            for coin in data.get("coins", [])[:10]:  # Limit to top 10 results
                result = SearchResult(
                    token_id=coin.get("id", ""),
                    symbol=coin.get("symbol", "").upper(),
                    name=coin.get("name", ""),
                    image_url=coin.get("large"),
                    market_cap_rank=coin.get("market_cap_rank"),
                    relevance_score=Decimal("1.0")  # CoinGecko doesn't provide relevance score
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching tokens with query '{query}': {e}")
            raise
    
    async def get_trending_tokens(self, limit: int = 10) -> List[TrendingToken]:
        """Get trending tokens."""
        try:
            data = await self.circuit_breaker.call(
                self._make_request,
                f"/search/trending"
            )
            
            trending = []
            for i, coin_data in enumerate(data.get("coins", [])[:limit]):
                coin = coin_data.get("item", {})
                
                # Get current price
                price_data = await self.get_token_price(coin.get("id", ""))
                
                trending_token = TrendingToken(
                    token_id=coin.get("id", ""),
                    symbol=coin.get("symbol", "").upper(),
                    name=coin.get("name", ""),
                    rank=i + 1,
                    price_usd=price_data.price_usd,
                    price_change_24h=price_data.price_change_24h,
                    volume_24h=price_data.volume_24h,
                    search_score=Decimal(str(coin.get("score", 0)))
                )
                trending.append(trending_token)
            
            return trending
            
        except Exception as e:
            logger.error(f"Error fetching trending tokens: {e}")
            raise
    
    async def get_market_overview(self) -> MarketOverview:
        """Get overall market statistics."""
        cache_key = "market_overview"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            data = await self.circuit_breaker.call(
                self._make_request,
                f"/global"
            )
            
            global_data = data.get("data", {})
            
            overview = MarketOverview(
                total_market_cap=Decimal(str(global_data.get("total_market_cap", {}).get("usd", 0))),
                total_volume_24h=Decimal(str(global_data.get("total_volume", {}).get("usd", 0))),
                market_cap_change_percentage_24h=Decimal(str(global_data.get("market_cap_change_percentage_24h_usd", 0))),
                bitcoin_dominance=Decimal(str(global_data.get("market_cap_percentage", {}).get("btc", 0))),
                ethereum_dominance=Decimal(str(global_data.get("market_cap_percentage", {}).get("eth", 0))),
                active_cryptocurrencies=global_data.get("active_cryptocurrencies", 0),
                markets=global_data.get("markets", 0),
                last_updated=datetime.utcnow()
            )
            
            self.cache[cache_key] = overview
            return overview
            
        except Exception as e:
            logger.error(f"Error fetching market overview: {e}")
            raise


class BlockchainService:
    """Service for on-chain data retrieval."""
    
    def __init__(self):
        self.web3_instances = {}
        self.cache = TTLCache(maxsize=500, ttl=settings.cache_token_ttl)
        
        # Initialize Web3 instances for each chain
        for chain, config in CHAIN_CONFIGS.items():
            rpc_url = getattr(settings, config["rpc_url_env"].lower())
            try:
                self.web3_instances[chain] = Web3(Web3.HTTPProvider(rpc_url))
            except Exception as e:
                logger.warning(f"Failed to initialize Web3 for {chain}: {e}")
    
    async def get_chainlink_price(self, pair: str, chain: str = "ethereum") -> ChainlinkPrice:
        """Get price from Chainlink price feed."""
        if chain not in CHAINLINK_FEEDS:
            raise ValueError(f"Chain {chain} not supported for Chainlink feeds")
        
        if pair not in CHAINLINK_FEEDS[chain]:
            raise ValueError(f"Pair {pair} not available on {chain}")
        
        feed_address = CHAINLINK_FEEDS[chain][pair]
        web3 = self.web3_instances.get(chain)
        
        if not web3:
            raise ValueError(f"Web3 instance not available for {chain}")
        
        try:
            # Chainlink aggregator ABI (simplified)
            abi = [
                {
                    "inputs": [],
                    "name": "latestRoundData",
                    "outputs": [
                        {"internalType": "uint80", "name": "roundId", "type": "uint80"},
                        {"internalType": "int256", "name": "answer", "type": "int256"},
                        {"internalType": "uint256", "name": "startedAt", "type": "uint256"},
                        {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
                        {"internalType": "uint80", "name": "answeredInRound", "type": "uint80"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            contract = web3.eth.contract(address=feed_address, abi=abi)
            
            # Get latest round data
            round_data = contract.functions.latestRoundData().call()
            decimals = contract.functions.decimals().call()
            
            price_raw = round_data[1]
            price = Decimal(price_raw) / Decimal(10 ** decimals)
            
            return ChainlinkPrice(
                pair=pair,
                price=price,
                decimals=decimals,
                feed_address=feed_address,
                chain=chain,
                last_updated=datetime.fromtimestamp(round_data[3]),
                round_id=round_data[0],
                started_at=datetime.fromtimestamp(round_data[2])
            )
            
        except Exception as e:
            logger.error(f"Error fetching Chainlink price for {pair} on {chain}: {e}")
            raise
    
    async def get_token_supply(self, token_address: str, chain: str = "ethereum") -> TokenSupply:
        """Get token supply information."""
        cache_key = f"supply_{token_address}_{chain}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        web3 = self.web3_instances.get(chain)
        if not web3:
            raise ValueError(f"Web3 instance not available for {chain}")
        
        try:
            # ERC20 ABI (simplified)
            abi = [
                {
                    "inputs": [],
                    "name": "totalSupply",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            contract = web3.eth.contract(address=token_address, abi=abi)
            
            total_supply_raw = contract.functions.totalSupply().call()
            decimals = contract.functions.decimals().call()
            
            total_supply = Decimal(total_supply_raw) / Decimal(10 ** decimals)
            
            supply_info = TokenSupply(
                token_address=token_address,
                chain=chain,
                total_supply=total_supply,
                decimals=decimals,
                last_updated=datetime.utcnow()
            )
            
            self.cache[cache_key] = supply_info
            return supply_info
            
        except Exception as e:
            logger.error(f"Error fetching token supply for {token_address} on {chain}: {e}")
            raise


class DataAggregatorService:
    """Service that aggregates data from multiple sources."""
    
    def __init__(self):
        self.coingecko_service = None
        self.blockchain_service = BlockchainService()
    
    async def __aenter__(self):
        self.coingecko_service = CoinGeckoService()
        await self.coingecko_service.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.coingecko_service:
            await self.coingecko_service.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get_best_price(self, token_id: str) -> TokenPrice:
        """Get the best available price from multiple sources."""
        try:
            # Try CoinGecko first (most reliable for popular tokens)
            return await self.coingecko_service.get_token_price(token_id)
        except Exception as e:
            logger.warning(f"CoinGecko failed for {token_id}: {e}")
            # Could add fallback to other sources here
            raise
    
    async def get_comprehensive_token_data(self, token_id: str) -> Dict:
        """Get comprehensive token data from all available sources."""
        data = {}
        
        try:
            # Get CoinGecko data
            token_data = await self.coingecko_service.get_token_data(token_id)
            data["coingecko"] = token_data
        except Exception as e:
            logger.warning(f"Failed to get CoinGecko data for {token_id}: {e}")
        
        try:
            # Get price history
            history = await self.coingecko_service.get_price_history(token_id, days=7)
            data["price_history"] = history
        except Exception as e:
            logger.warning(f"Failed to get price history for {token_id}: {e}")
        
        return data
    
    def get_supported_chains(self) -> List[ChainInfo]:
        """Get list of supported blockchain networks."""
        chains = []
        for chain_id, config in CHAIN_CONFIGS.items():
            chain_info = ChainInfo(
                chain_id=chain_id,
                name=config["name"],
                symbol=config["symbol"],
                rpc_url=getattr(settings, config["rpc_url_env"].lower()),
                explorer_url=config.get("explorer_url"),
                is_testnet=config.get("is_testnet", False),
                supported_dexes=config.get("supported_dexes", [])
            )
            chains.append(chain_info)
        
        return chains
    
    def get_supported_dexes(self) -> List[DEXInfo]:
        """Get list of supported DEX platforms."""
        dexes = []
        for dex_id, config in DEX_CONFIGS.items():
            dex_info = DEXInfo(
                dex_id=dex_id,
                name=config["name"],
                website=config.get("website"),
                supported_chains=config.get("supported_chains", []),
                fee_structure=config.get("fee_structure")
            )
            dexes.append(dex_info)
        
        return dexes 