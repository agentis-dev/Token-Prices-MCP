"""Configuration management for token prices MCP."""

import os
from typing import Dict, List, Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Server settings
    server_name: str = Field(default="Token Prices MCP", description="Server name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Cache settings
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    cache_price_ttl: int = Field(default=300, description="Price cache TTL in seconds")
    cache_market_ttl: int = Field(default=600, description="Market data cache TTL in seconds")
    cache_token_ttl: int = Field(default=3600, description="Token metadata cache TTL in seconds")
    cache_history_ttl: int = Field(default=86400, description="Historical data cache TTL in seconds")
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=100, description="Rate limit per minute")
    rate_limit_burst: int = Field(default=20, description="Rate limit burst")
    
    # API Keys
    coingecko_api_key: Optional[str] = Field(default=None, description="CoinGecko API key")
    
    # RPC URLs
    ethereum_rpc_url: str = Field(
        default="https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
        description="Ethereum RPC URL"
    )
    bsc_rpc_url: str = Field(
        default="https://bsc-dataseed.binance.org/",
        description="BSC RPC URL"
    )
    polygon_rpc_url: str = Field(
        default="https://polygon-rpc.com/",
        description="Polygon RPC URL"
    )
    arbitrum_rpc_url: str = Field(
        default="https://arb1.arbitrum.io/rpc",
        description="Arbitrum RPC URL"
    )
    optimism_rpc_url: str = Field(
        default="https://mainnet.optimism.io",
        description="Optimism RPC URL"
    )
    avalanche_rpc_url: str = Field(
        default="https://api.avax.network/ext/bc/C/rpc",
        description="Avalanche RPC URL"
    )
    fantom_rpc_url: str = Field(
        default="https://rpc.ftm.tools/",
        description="Fantom RPC URL"
    )
    
    # External API URLs
    coingecko_base_url: str = Field(
        default="https://api.coingecko.com/api/v3",
        description="CoinGecko API base URL"
    )
    
    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = Field(default=5, description="Circuit breaker failure threshold")
    circuit_breaker_recovery_timeout: int = Field(default=60, description="Circuit breaker recovery timeout")
    circuit_breaker_expected_exception: tuple = Field(default=(Exception,), description="Expected exceptions")
    
    # Retry settings
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay: float = Field(default=1.0, description="Initial retry delay in seconds")
    retry_backoff: float = Field(default=2.0, description="Retry backoff multiplier")
    
    class Config:
        env_prefix = "TOKEN_PRICES_"
        case_sensitive = False


# Chain configurations
CHAIN_CONFIGS = {
    "ethereum": {
        "chain_id": "1",
        "name": "Ethereum",
        "symbol": "ETH",
        "rpc_url_env": "ETHEREUM_RPC_URL",
        "explorer_url": "https://etherscan.io",
        "is_testnet": False,
        "supported_dexes": ["uniswap_v2", "uniswap_v3", "sushiswap", "curve", "balancer"],
        "wrapped_native": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "usdc_address": "0xA0b86a33E6D0bBa464f2E84905E6b68e4e30A9E"
    },
    "bsc": {
        "chain_id": "56",
        "name": "Binance Smart Chain",
        "symbol": "BNB",
        "rpc_url_env": "BSC_RPC_URL",
        "explorer_url": "https://bscscan.com",
        "is_testnet": False,
        "supported_dexes": ["pancakeswap_v2", "pancakeswap_v3", "biswap"],
        "wrapped_native": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        "usdt_address": "0x55d398326f99059fF775485246999027B3197955"
    },
    "polygon": {
        "chain_id": "137",
        "name": "Polygon",
        "symbol": "MATIC",
        "rpc_url_env": "POLYGON_RPC_URL",
        "explorer_url": "https://polygonscan.com",
        "is_testnet": False,
        "supported_dexes": ["quickswap", "sushiswap", "curve"],
        "wrapped_native": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        "usdc_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    },
    "arbitrum": {
        "chain_id": "42161",
        "name": "Arbitrum One",
        "symbol": "ETH",
        "rpc_url_env": "ARBITRUM_RPC_URL",
        "explorer_url": "https://arbiscan.io",
        "is_testnet": False,
        "supported_dexes": ["uniswap_v3", "sushiswap", "curve", "balancer"],
        "wrapped_native": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "usdc_address": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"
    },
    "optimism": {
        "chain_id": "10",
        "name": "Optimism",
        "symbol": "ETH",
        "rpc_url_env": "OPTIMISM_RPC_URL",
        "explorer_url": "https://optimistic.etherscan.io",
        "is_testnet": False,
        "supported_dexes": ["uniswap_v3", "curve"],
        "wrapped_native": "0x4200000000000000000000000000000000000006",
        "usdc_address": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607"
    },
    "avalanche": {
        "chain_id": "43114",
        "name": "Avalanche",
        "symbol": "AVAX",
        "rpc_url_env": "AVALANCHE_RPC_URL",
        "explorer_url": "https://snowtrace.io",
        "is_testnet": False,
        "supported_dexes": ["traderjoe", "pangolin"],
        "wrapped_native": "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",
        "usdc_address": "0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664"
    },
    "fantom": {
        "chain_id": "250",
        "name": "Fantom",
        "symbol": "FTM",
        "rpc_url_env": "FANTOM_RPC_URL",
        "explorer_url": "https://ftmscan.com",
        "is_testnet": False,
        "supported_dexes": ["spookyswap", "spiritswap"],
        "wrapped_native": "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83",
        "usdc_address": "0x04068DA6C83AFCFA0e13ba15A6696662335D5B75"
    }
}

# DEX configurations
DEX_CONFIGS = {
    "uniswap_v2": {
        "name": "Uniswap V2",
        "website": "https://uniswap.org",
        "supported_chains": ["ethereum"],
        "factory_address": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        "router_address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "fee_structure": {"swap_fee": "0.3%"}
    },
    "uniswap_v3": {
        "name": "Uniswap V3",
        "website": "https://uniswap.org",
        "supported_chains": ["ethereum", "arbitrum", "optimism", "polygon"],
        "factory_address": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "router_address": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "fee_structure": {"fee_tiers": ["0.01%", "0.05%", "0.3%", "1%"]}
    },
    "pancakeswap_v2": {
        "name": "PancakeSwap V2",
        "website": "https://pancakeswap.finance",
        "supported_chains": ["bsc"],
        "factory_address": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73",
        "router_address": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
        "fee_structure": {"swap_fee": "0.25%"}
    },
    "pancakeswap_v3": {
        "name": "PancakeSwap V3",
        "website": "https://pancakeswap.finance",
        "supported_chains": ["bsc", "ethereum"],
        "factory_address": "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865",
        "router_address": "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4",
        "fee_structure": {"fee_tiers": ["0.01%", "0.05%", "0.25%", "1%"]}
    },
    "sushiswap": {
        "name": "SushiSwap",
        "website": "https://sushi.com",
        "supported_chains": ["ethereum", "polygon", "arbitrum", "avalanche"],
        "factory_address": "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac",
        "router_address": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
        "fee_structure": {"swap_fee": "0.3%"}
    },
    "quickswap": {
        "name": "QuickSwap",
        "website": "https://quickswap.exchange",
        "supported_chains": ["polygon"],
        "factory_address": "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32",
        "router_address": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
        "fee_structure": {"swap_fee": "0.3%"}
    },
    "traderjoe": {
        "name": "Trader Joe",
        "website": "https://traderjoexyz.com",
        "supported_chains": ["avalanche"],
        "factory_address": "0x9Ad6C38BE94206cA50bb0d90783181662f0Cfa10",
        "router_address": "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",
        "fee_structure": {"swap_fee": "0.3%"}
    },
    "spookyswap": {
        "name": "SpookySwap",
        "website": "https://spookyswap.finance",
        "supported_chains": ["fantom"],
        "factory_address": "0x152eE697f2E276fA89E96742e9bB9aB1F2E61bE3",
        "router_address": "0xF491e7B69E4244ad4002BC14e878a34207E38c29",
        "fee_structure": {"swap_fee": "0.2%"}
    }
}

# Chainlink price feeds
CHAINLINK_FEEDS = {
    "ethereum": {
        "ETH/USD": "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419",
        "BTC/USD": "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c",
        "USDC/USD": "0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6",
        "USDT/USD": "0x3E7d1eAB13ad0104d2750B8863b489D65364e32D",
        "DAI/USD": "0xAed0c38402a5d19df6E4c03F4E2DceD6e29c1ee9",
        "LINK/USD": "0x2c1d072e956AFFC0D435Cb7AC38EF18d24d9127c",
        "UNI/USD": "0x553303d460EE0afB37EdFf9bE42922D8FF63220e"
    },
    "bsc": {
        "BNB/USD": "0x0567F2323251f0Aab15c8dFb1967E4e8A7D42aeE",
        "BTC/USD": "0x264990fbd0A4796A3E3d8E37C4d5F87a3aCa5Ebf",
        "ETH/USD": "0x9ef1B8c0E4F7dc8bF5719Ea496883DC6401d5b2e",
        "USDT/USD": "0xB97Ad0E74fa7d920791E90258A6E2085088b4320"
    },
    "polygon": {
        "MATIC/USD": "0xAB594600376Ec9fD91F8e885dADF0CE036862dE0",
        "ETH/USD": "0xF9680D99D6C9589e2a93a78A04A279e509205945",
        "BTC/USD": "0xc907E116054Ad103354f2D350FD2514433D57F6f",
        "USDC/USD": "0xfE4A8cc5b5B2366C1B58Bea3858e81843581b2F7"
    }
}

# Popular token IDs for CoinGecko API
POPULAR_TOKENS = [
    "bitcoin", "ethereum", "tether", "bnb", "solana", "cardano", "xrp", "dogecoin",
    "tron", "polygon", "avalanche-2", "shiba-inu", "polkadot", "chainlink", "uniswap",
    "litecoin", "bitcoin-cash", "ethereum-classic", "stellar", "monero", "cosmos",
    "algorand", "vechain", "filecoin", "theta-token", "tezos", "eos", "neo",
    "iota", "aave", "compound", "maker", "pancakeswap-token", "sushiswap"
]

# Create settings instance
settings = Settings() 