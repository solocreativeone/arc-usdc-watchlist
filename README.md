# Arc USDC Watchlist Bot

A Telegram bot that watches wallet addresses on **Arc mainnet** and alerts a chat the moment a watched address sends or receives USDC. A small Solidity contract (`WatchlistRegistry`) anchors every watch on-chain as a public, auditable record; the actual transfer monitoring happens off-chain via polling, which is cheaper and faster than doing it fully on-chain.

It extends the architecture used in two earlier projects, NFTpulse and the Arbitrum Watchlist Bot: Telegram intake, off-chain logic, on-chain anchor.

## Why this is built the way it is

USDC on Arc is the chain's **native currency**, not an ERC-20 token contract, the way it is on most other chains. An ordinary USDC send is a plain native value transfer (from/to/value on the transaction itself), with no token contract call and no `Transfer` event log to watch.

That rules out the usual approach of filtering ERC-20 logs. Instead, the bot scans a recent, fixed window of blocks on every poll and checks each transaction's native `value` field directly against the watchlist. Arc produces a block roughly every half second, so a persisted "resume from here" cursor falls permanently behind; a fixed recent window is the more reliable design for a chain this fast.

## Features

- `/watch <address>` - start watching an address; anchors the watch on-chain and alerts this chat on future USDC transfers to or from it
- `/unwatch <address>` - stop watching
- `/list` - see what this chat is currently watching
- Alerts include the amount, both addresses, and a direct link to the transaction on Arcscan

## Project layout

```
contracts/WatchlistRegistry.sol   Solidity contract, the on-chain anchor
scripts/deploy.js                 Hardhat deploy script
hardhat.config.js                 Arc mainnet network config
bot/watchlist_bot.py              Telegram bot + block-scanning poll loop
bot/store.py                      Local JSON store (chat <-> address)
bot/abi.py                        Hand-written ABI for WatchlistRegistry
```

## Setup

### 1. Deploy the contract

```bash
npm install
cp .env.example .env
# fill in ARC_MAINNET_RPC_URL and PRIVATE_KEY
# (the deployer wallet needs a little USDC on Arc mainnet to pay gas)
npm run compile
npm run deploy:arc
```

Copy the printed contract address into `bot/.env` as `REGISTRY_ADDRESS`.

### 2. Run the bot

```bash
cd bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in TELEGRAM_BOT_TOKEN, ARC_MAINNET_RPC_URL, BOT_PRIVATE_KEY,
# and REGISTRY_ADDRESS (from step 1)
python watchlist_bot.py
```

The bot's wallet (`BOT_PRIVATE_KEY`) needs a small amount of USDC of its own, since every `/watch` and `/unwatch` anchors a transaction on Arc and gas there is paid in USDC.

## Known limitations

- **On-chain watches are anchored under the bot's own wallet**, not a per-Telegram-user address, since there's no wallet-linking flow yet. The private routing, which chat gets which alert, lives off-chain in `store.py`. A future version could let each user connect their own wallet.
- **The JSON store is a demo-scale solution.** It should move to SQLite or Postgres before handling more than a handful of watched addresses.
- **Alerting uses a fixed, recent block window** (`WINDOW_BLOCKS` in `watchlist_bot.py`), not a persisted cursor, by design, given Arc's block speed. It will not retroactively catch a transfer that happened before the bot started watching an address.
- The public Arc mainnet explorer is [arcscan.app](https://arcscan.app); `explorer.arc.io` is team-login-gated and not publicly usable.

## License

MIT
