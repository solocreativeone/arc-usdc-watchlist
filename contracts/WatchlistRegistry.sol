// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title WatchlistRegistry
/// @notice On-chain anchor for the Arc USDC Watchlist Bot. Each caller keeps
///         their own list of addresses they want the off-chain Telegram bot
///         to monitor for USDC transfers on Arc mainnet. The registry does
///         not do any monitoring itself; it just gives the watchlist an
///         immutable, publicly-auditable home on Arc, and emits the events
///         the bot listens for.
contract WatchlistRegistry {
    event WatchAdded(address indexed user, address indexed target, uint256 timestamp);
    event WatchRemoved(address indexed user, address indexed target, uint256 timestamp);

    mapping(address => address[]) private watchlists;
    // index+1 of `target` inside watchlists[user], 0 means "not present"
    mapping(address => mapping(address => uint256)) private indexOf;

    error AlreadyWatched();
    error NotWatched();
    error ZeroAddress();

    /// @notice Add `target` to the caller's watchlist.
    function addWatch(address target) external {
        if (target == address(0)) revert ZeroAddress();
        if (indexOf[msg.sender][target] != 0) revert AlreadyWatched();

        watchlists[msg.sender].push(target);
        indexOf[msg.sender][target] = watchlists[msg.sender].length; // store as length (1-indexed)

        emit WatchAdded(msg.sender, target, block.timestamp);
    }

    /// @notice Remove `target` from the caller's watchlist.
    function removeWatch(address target) external {
        uint256 idxPlusOne = indexOf[msg.sender][target];
        if (idxPlusOne == 0) revert NotWatched();

        uint256 idx = idxPlusOne - 1;
        address[] storage list = watchlists[msg.sender];
        uint256 lastIdx = list.length - 1;

        if (idx != lastIdx) {
            address moved = list[lastIdx];
            list[idx] = moved;
            indexOf[msg.sender][moved] = idx + 1;
        }

        list.pop();
        delete indexOf[msg.sender][target];

        emit WatchRemoved(msg.sender, target, block.timestamp);
    }

    /// @notice Read back everything `user` is currently watching.
    function getWatchlist(address user) external view returns (address[] memory) {
        return watchlists[user];
    }

    /// @notice Convenience check used by the bot before submitting a tx.
    function isWatched(address user, address target) external view returns (bool) {
        return indexOf[user][target] != 0;
    }
}
