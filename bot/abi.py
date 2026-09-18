"""Minimal ABIs. Hand-written from the contract source, not from a Hardhat
build artifact, so there's nothing to compile before the bot can run. If you
change WatchlistRegistry.sol, update this to match.
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

# Standard ERC-20 Transfer event, used to filter USDC logs on Arc.
ERC20_TRANSFER_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }
]
