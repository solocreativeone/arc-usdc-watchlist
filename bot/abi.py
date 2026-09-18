"""Minimal ABI for WatchlistRegistry. Hand-written from the contract source,
not from a Hardhat build artifact, so there's nothing to compile before the
bot can run. If you change WatchlistRegistry.sol, update this to match.

No ERC-20 ABI here: USDC on Arc is the chain's native currency (like ETH on
Ethereum), not a token contract, so transfer monitoring reads native
transaction values directly rather than filtering token event logs.
"""

REGISTRY_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "target", "type": "address"}],
        "name": "addWatch",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "target", "type": "address"}],
        "name": "removeWatch",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "getWatchlist",
        "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    },
]