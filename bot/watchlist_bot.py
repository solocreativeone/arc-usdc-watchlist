"""
Arc USDC Watchlist Bot
======================
Telegram bot that lets someone register an address, then alerts their chat
whenever that address sends or receives USDC on Arc mainnet.

Every /watch call also anchors the watch on-chain via WatchlistRegistry
(one shared bot wallet submits the tx), so there's a public, immutable log
of what's been watched, alongside the private per-chat routing that lives
in store.py. Extends the same "Telegram intake -> off-chain logic -> Arc
mainnet anchor" pattern used in NFTpulse and the Arbitrum Watchlist Bot.

Env vars needed (see .env.example in this folder):
  TELEGRAM_BOT_TOKEN   - from @BotFather
  ARC_MAINNET_RPC_URL  - Arc mainnet RPC (Alchemy/Blockdaemon/dRPC/QuickNode)
  BOT_PRIVATE_KEY      - wallet the bot uses to call addWatch/removeWatch
  REGISTRY_ADDRESS     - address printed by `npm run deploy:arc`
  POLL_INTERVAL_SECONDS - how often to check for new transfers (default 15)
"""
import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
from web3 import Web3

import store
from abi import REGISTRY_ABI

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
# httpx (the HTTP client python-telegram-bot uses) logs every request at
# INFO, and Telegram's API puts the bot token directly in the URL path, so
# leaving this at INFO prints the token to the terminal on every poll.
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("arc-watchlist-bot")

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ARC_MAINNET_RPC_URL = os.environ["ARC_MAINNET_RPC_URL"]
BOT_PRIVATE_KEY = os.environ["BOT_PRIVATE_KEY"]
REGISTRY_ADDRESS = Web3.to_checksum_address(os.environ["REGISTRY_ADDRESS"])
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "15"))

w3 = Web3(Web3.HTTPProvider(ARC_MAINNET_RPC_URL))
bot_account = w3.eth.account.from_key(BOT_PRIVATE_KEY)
registry = w3.eth.contract(address=REGISTRY_ADDRESS, abi=REGISTRY_ABI)


def _submit_registry_tx(fn):
    """Build, sign, and send a tx to the registry contract; gas is paid in
    USDC automatically since that's Arc's native gas token."""
    tx = fn.build_transaction(
        {
            "from": bot_account.address,
            "nonce": w3.eth.get_transaction_count(bot_account.address),
        }
    )
    signed = bot_account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📡 <b>Arc USDC Watchlist Bot</b>\n\n"
        "Get alerted the moment USDC moves on an address you care about, on Arc mainnet.\n\n"
        "👁️ <code>/watch &lt;address&gt;</code> — alert this chat on USDC transfers to/from an address\n"
        "🔕 <code>/unwatch &lt;address&gt;</code> — stop watching an address\n"
        "📋 <code>/list</code> — show what this chat is watching",
        parse_mode=ParseMode.HTML,
    )


async def watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: <code>/watch 0xAddress</code>", parse_mode=ParseMode.HTML)
        return
    address = context.args[0]
    if not Web3.is_address(address):
        await update.message.reply_text("⚠️ That doesn't look like a valid address.")
        return
    address = Web3.to_checksum_address(address)

    try:
        _submit_registry_tx(registry.functions.addWatch(address))
    except Exception as exc:  # e.g. AlreadyWatched from a previous /watch
        log.warning("addWatch failed (continuing, likely already anchored): %s", exc)

    store.add_watch(update.effective_chat.id, address)
    await update.message.reply_text(
        f"✅ <b>Now watching</b>\n<code>{address}</code>\nfor USDC transfers on Arc.",
        parse_mode=ParseMode.HTML,
    )


async def unwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: <code>/unwatch 0xAddress</code>", parse_mode=ParseMode.HTML)
        return
    address = context.args[0]
    if not Web3.is_address(address):
        await update.message.reply_text("⚠️ That doesn't look like a valid address.")
        return
    address = Web3.to_checksum_address(address)

    store.remove_watch(update.effective_chat.id, address)

    # Only clear the on-chain anchor once nobody else's chat is watching it.
    if not store.chats_for_address(address):
        try:
            _submit_registry_tx(registry.functions.removeWatch(address))
        except Exception as exc:
            log.warning("removeWatch failed: %s", exc)

    await update.message.reply_text(
        f"🔕 <b>Stopped watching</b>\n<code>{address}</code>", parse_mode=ParseMode.HTML
    )


async def list_watched(update: Update, context: ContextTypes.DEFAULT_TYPE):
    addresses = store.list_watches(update.effective_chat.id)
    if not addresses:
        await update.message.reply_text(
            "You're not watching anything yet.\nTry <code>/watch 0xAddress</code>",
            parse_mode=ParseMode.HTML,
        )
        return
    lines = "\n".join(f"👁️ <code>{a}</code>" for a in addresses)
    await update.message.reply_text(f"📋 <b>Watching</b>\n{lines}", parse_mode=ParseMode.HTML)


WINDOW_BLOCKS = 80  # Arc produces a block roughly every 0.5s, so a fixed,
# recent window is far more reliable here than resuming from a persisted
# cursor: on a chain this fast, a cursor that falls behind can never catch
# up. 80 blocks covers ~40s of chain time, comfortably more than one poll
# interval, so a slightly slow poll still won't miss anything.
_seen_tx_hashes: set[str] = set()  # in-memory de-dupe across overlapping
# windows; resets on restart, which is fine for a demo


async def poll_transfers(context: ContextTypes.DEFAULT_TYPE):
    """Runs every POLL_INTERVAL_SECONDS. USDC is Arc's native currency, so
    an ordinary "send USDC" is a plain native value transfer, not an
    ERC-20 Transfer event, there's no token contract to watch logs on.
    Scans a small, recent window of blocks directly and checks each
    transaction's native value against the watchlist.
    """
    watched = {a.lower() for a in store.all_watched_addresses()}
    if not watched:
        return

    latest_block = w3.eth.block_number
    start_block = max(0, latest_block - WINDOW_BLOCKS)

    try:
        for block_num in range(start_block, latest_block + 1):
            block = w3.eth.get_block(block_num, full_transactions=True)
            for tx in block["transactions"]:
                if tx["value"] == 0:
                    continue
                tx_hash = tx["hash"].hex()
                if tx_hash in _seen_tx_hashes:
                    continue
                sender = tx["from"].lower()
                recipient = (tx["to"] or "").lower()
                if sender not in watched and recipient not in watched:
                    continue

                _seen_tx_hashes.add(tx_hash)
                value = tx["value"] / 1_000_000_000_000_000_000  # 18 decimals
                text = (
                    f"💸 <b>USDC transfer on Arc</b>\n"
                    f"<code>{tx['from']}</code>\n"
                    f"   ⬇️\n"
                    f"<code>{tx['to']}</code>\n\n"
                    f"💰 <b>{value:.6f} USDC</b>\n"
                    f'🔗 <a href="https://arcscan.app/tx/{tx_hash}">View on Arcscan</a>'
                )
                for address in (sender, recipient):
                    for chat_id in store.chats_for_address(address):
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=text,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True,
                        )
    except Exception as exc:
        log.error("block scan failed: %s", exc)
        return

    if len(_seen_tx_hashes) > 5000:  # simple unbounded-growth guard
        _seen_tx_hashes.clear()


def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("watch", watch))
    application.add_handler(CommandHandler("unwatch", unwatch))
    application.add_handler(CommandHandler("list", list_watched))

    application.job_queue.run_repeating(poll_transfers, interval=POLL_INTERVAL_SECONDS, first=5)

    log.info("Arc USDC Watchlist Bot starting (chain id %s)...", w3.eth.chain_id)
    application.run_polling()


if __name__ == "__main__":
    main()