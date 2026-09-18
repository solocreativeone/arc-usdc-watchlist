# Arc USDC Watchlist Bot

Telegram bot that watches wallet addresses on **Arc mainnet** and alerts a
chat whenever a watched address sends or receives USDC. A small Solidity
contract (`WatchlistRegistry`) anchors every watch on-chain as a public,
auditable log; the actual transfer monitoring happens off-chain via polling,
since that's cheaper and faster than doing it fully on-chain.

Extends the architecture from the Arbitrum Watchlist Bot and NFTpulse:
Telegram intake -> off-chain logic -> Arc mainnet anchor.

## Project layout

```contracts/WatchlistRegistry.sol   Solidity contract, the on-chain anchor
scripts/deploy.js                 Hardhat deploy script
hardhat.config.js                 Arc mainnet network config
bot/watchlist_bot.py              Telegram bot + polling loop
bot/store.py                      Local JSON store (chat <-> address)
bot/abi.py                        Hand-written ABIs (registry + ERC20 Transfer)
```

## 1. Deploy the contract

```bash
npm install
cp .env.example .env
# fill in ARC_MAINNET_RPC_URL and PRIVATE_KEY (needs a little USDC on Arc
# mainnet to pay deploy gas)
npm run compile
npm run deploy:arc
```

Copy the printed contract address into `bot/.env` as `REGISTRY_ADDRESS`.

## 2. Run the bot

```bash
cd bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in TELEGRAM_BOT_TOKEN, ARC_MAINNET_RPC_URL, BOT_PRIVATE_KEY,
# REGISTRY_ADDRESS (from step 1), and double-check USDC_ADDRESS
python watchlist_bot.py
```

## 3. Use it

In Telegram:

- `/watch 0xAddress` - start watching an address, anchors the watch on-chain
- `/unwatch 0xAddress` - stop watching
- `/list` - see what your chat is watching

## Before submitting to Arc Microgrants

- [ ] Contract deployed and verified on Arc **mainnet** (not testnet)
- [ ] Bot running against the deployed contract, tested end-to-end with a
      real USDC transfer between two addresses you control
- [ ] Repo made public
- [ ] `.env` files are gitignored, never committed
- [ ] Short description ready: what it does, and what it uses Arc for
      (USDC-native gas + fast finality makes on-chain watch anchoring cheap
      and near-instant)
- [ ] Public builder profile link (GitHub/X/Farcaster) ready

## Known simplifications (be upfront about these in the submission)

- All on-chain watches are anchored under the bot's own wallet address, not
  a per-Telegram-user address, since there's no wallet-linking flow yet.
  The private routing (which chat gets which alert) lives off-chain in
  `store.py`. A v2 could let each user connect their own wallet.
- The JSON store is fine for a demo; swap for SQLite/Postgres before this
  handles more than a handful of watched addresses.
- `USDC_ADDRESS` in `.env.example` is sourced from public docs and may
  need to be re-verified against explorer.arc.io, since it's a very new
  mainnet.
