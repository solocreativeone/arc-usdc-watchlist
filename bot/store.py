"""Tiny JSON-file store. Good enough for an MVP; swap for SQLite/Postgres
once this needs to survive more than a handful of watchers.
"""
import json
import os
from threading import Lock

STORE_PATH = os.path.join(os.path.dirname(__file__), "watchlist_store.json")
_lock = Lock()


def _load():
    if not os.path.exists(STORE_PATH):
        return {"watches": {}, "last_polled_block": None}
    with open(STORE_PATH, "r") as f:
        return json.load(f)


def _save(data):
    with open(STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def add_watch(chat_id: int, address: str):
    address = address.lower()
    with _lock:
        data = _load()
        chats = data["watches"].setdefault(address, [])
        if chat_id not in chats:
            chats.append(chat_id)
        _save(data)


def remove_watch(chat_id: int, address: str):
    address = address.lower()
    with _lock:
        data = _load()
        chats = data["watches"].get(address, [])
        if chat_id in chats:
            chats.remove(chat_id)
        if not chats:
            data["watches"].pop(address, None)
        else:
            data["watches"][address] = chats
        _save(data)


def list_watches(chat_id: int):
    with _lock:
        data = _load()
        return [addr for addr, chats in data["watches"].items() if chat_id in chats]


def all_watched_addresses():
    with _lock:
        data = _load()
        return list(data["watches"].keys())


def chats_for_address(address: str):
    with _lock:
        data = _load()
        return data["watches"].get(address.lower(), [])


def get_last_polled_block():
    with _lock:
        return _load().get("last_polled_block")


def set_last_polled_block(block_number: int):
    with _lock:
        data = _load()
        data["last_polled_block"] = block_number
        _save(data)
