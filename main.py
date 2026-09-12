#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔══════════════════════════════════════════════════════════════╗
║   ⚡ MARKCPM1TOOLS V25.0 - FINAL EDITION ⚡                 ║
║   Firebase: cpm1new-default-rtdb                            ║
╚══════════════════════════════════════════════════════════════╝
"""

# ================================================================
#  IMPORTS
# ================================================================
import requests
import time
import json
import telebot
import random
import base64
import sys
import os
import glob
import string
import struct
import brotli
import hashlib
import zlib
import threading
import concurrent.futures
import sqlite3
import uuid
import html
import re
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from telebot import types
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import urllib3
from pymongo import MongoClient

# ================================================================
#  FIREBASE CONFIG
# ================================================================
FIREBASE_URL = "https://newtoolcpm1-default-rtdb.firebaseio.com"
FIREBASE_SECRET = "xenPl7tYl28lkhZr9AOzUavzzIEP3nOh9h1WmWOj"

# ================================================================
#  BOT CONFIG
# ================================================================
ADMIN_ID = 6531314640
ADMIN_USERNAME = "@Maarkryan"
GROUP_LOG_ID = -1004441134033
USD_TO_PHP = 62.0
MAX_WARNINGS = 3

# ================================================================
#  TOKEN-BASED PREMIUM CONFIG
# ================================================================
PREMIUM_TOKEN_THRESHOLD = 50
PREMIUM_AUTO_UNLOCK_AMOUNT = 200

# ================================================================
#  TOKEN COSTS
# ================================================================
TOKEN_COSTS = {
    "unlock_by_id": 30,
    "unlock_all_cars": 75,
    "clone_single": 90,
    "bulk_1_5": 120,
    "bulk_6_10": 150,
    "default": 20,
}

# ================================================================
#  FIREBASE HELPERS
# ================================================================
def fb_get(path):
    try:
        url = f"{FIREBASE_URL}/{path}.json?auth={FIREBASE_SECRET}"
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def fb_put(path, data):
    try:
        url = f"{FIREBASE_URL}/{path}.json?auth={FIREBASE_SECRET}"
        return requests.put(url, json=data, timeout=10).status_code == 200
    except:
        return False

def fb_patch(path, data):
    try:
        url = f"{FIREBASE_URL}/{path}.json?auth={FIREBASE_SECRET}"
        return requests.patch(url, json=data, timeout=10).status_code == 200
    except:
        return False

def fb_delete(path):
    try:
        url = f"{FIREBASE_URL}/{path}.json?auth={FIREBASE_SECRET}"
        return requests.delete(url, timeout=10).status_code == 200
    except:
        return False

# ================================================================
#  TOKEN MANAGEMENT
# ================================================================
def get_user_tokens(user_id):
    data = fb_get(f"cpm1_users/{user_id}")
    return data.get("tokens", 0) if data else 0

def set_user_tokens(user_id, amount):
    fb_patch(f"cpm1_users/{user_id}", {"tokens": max(0, int(amount))})

def add_tokens(user_id, amount):
    current = get_user_tokens(user_id)
    set_user_tokens(user_id, current + amount)

def remove_tokens(user_id, amount):
    current = get_user_tokens(user_id)
    new_balance = max(0, current - amount)
    set_user_tokens(user_id, new_balance)
    return new_balance

def deduct_tokens(user_id, amount):
    if is_admin(user_id):
        return True
    current = get_user_tokens(user_id)
    if current < amount:
        return False
    new_balance = current - amount
    set_user_tokens(user_id, new_balance)
    try:
        data = fb_get(f"cpm1_users/{user_id}")
        if data and data.get("premium_by_tokens") and new_balance <= PREMIUM_TOKEN_THRESHOLD:
            fb_patch(f"cpm1_users/{user_id}", {"premium_by_tokens": False})
            try:
                bot.send_message(
                    user_id,
                    f"{get_premium_emoji('warning')} <b>PREMIUM ACCESS ENDED</b>\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"Your token balance is now <code>{new_balance}</code>.\n\n"
                    f"{get_premium_emoji('info')} Premium requires more than <b>{PREMIUM_TOKEN_THRESHOLD} tokens</b>.\n\n"
                    f"Top up with /buytokens to restore premium features.",
                    parse_mode="HTML"
                )
            except:
                pass
    except:
        pass
    return True

def has_enough_tokens(user_id, amount):
    if is_admin(user_id):
        return True
    return get_user_tokens(user_id) >= amount

def token_shortage_msg(chat_id, need, have):
    return (
        f"{get_premium_emoji('cancel_failed_error')} <b>INSUFFICIENT TOKENS</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🪙 Needed: <code>{need}</code>\n"
        f"💎 Your Balance: <code>{have}</code>\n\n"
        f"Buy more: /buytokens"
    )

# ================================================================
#  SUBSCRIPTION MANAGEMENT
# ================================================================
def get_user_subscription(user_id):
    data = fb_get(f"cpm1_users/{user_id}")
    if not data:
        return None
    sub = data.get("subscription")
    if not sub:
        return None
    if sub.get("expiry"):
        try:
            if datetime.fromisoformat(sub["expiry"]) <= datetime.now():
                return None
        except:
            pass
    return sub

def has_active_subscription(user_id):
    return get_user_subscription(user_id) is not None

def has_premium_access(user_id):
    if is_admin(user_id):
        return True
    data = fb_get(f"cpm1_users/{user_id}")
    if not data:
        return False
    sub = data.get("subscription")
    if sub:
        prem_exp = sub.get("premium_expiry")
        if prem_exp:
            try:
                if datetime.fromisoformat(prem_exp) > datetime.now():
                    return True
            except:
                pass
    if data.get("premium_by_tokens"):
        tokens = data.get("tokens", 0)
        if tokens > PREMIUM_TOKEN_THRESHOLD:
            return True
        else:
            fb_patch(f"cpm1_users/{user_id}", {"premium_by_tokens": False})
    return False

def activate_subscription(user_id, days, premium_days=0):
    expiry = (datetime.now() + timedelta(days=days)).isoformat()
    prem_expiry = None
    if premium_days > 0:
        prem_expiry = (datetime.now() + timedelta(days=premium_days)).isoformat()
    fb_patch(f"cpm1_users/{user_id}", {
        "subscription": {
            "expiry": expiry,
            "premium_expiry": prem_expiry,
            "activated_at": datetime.now().isoformat(),
            "duration_days": days,
            "premium_days": premium_days
        }
    })

def revoke_subscription(user_id):
    fb_patch(f"cpm1_users/{user_id}", {"subscription": None})

# ================================================================
#  WARNING / BAN SYSTEM
# ================================================================
def get_user_warnings(user_id):
    data = fb_get(f"cpm1_users/{user_id}")
    return data.get("warnings", 0) if data else 0

def get_user_banned(user_id):
    data = fb_get(f"cpm1_users/{user_id}")
    return data.get("banned", False) if data else False

def add_warning(user_id):
    data = fb_get(f"cpm1_users/{user_id}") or {}
    current = data.get("warnings", 0) + 1
    update = {"warnings": current}
    if current >= MAX_WARNINGS:
        update["banned"] = True
        update["banned_at"] = datetime.now().isoformat()
    fb_patch(f"cpm1_users/{user_id}", update)
    return current

def unban_user_cpm1(user_id):
    fb_patch(f"cpm1_users/{user_id}", {"banned": False, "warnings": 0})
    return True

# ================================================================
#  BAN ENFORCEMENT HELPERS
# ================================================================
def is_blocked_by_ban(chat_id):
    if is_admin(chat_id):
        return False
    return get_user_banned(chat_id)

def send_ban_message(chat_id):
    try:
        bot.send_message(
            chat_id,
            f"{get_premium_emoji('cancel_failed_error')} <b>YOU ARE BANNED</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"You have been banned from using this bot.\n"
            f"You cannot use any commands or features.\n\n"
            f"{get_premium_emoji('info')} If you believe this is a mistake,\n"
            f"contact the admin: {ADMIN_USERNAME}",
            parse_mode="HTML"
        )
    except:
        pass

# ================================================================
#  CUSTOM EMOJIS
# ================================================================
CUSTOM_EMOJIS = {
    "core_commands": {"id": "5246749129878561406", "fallback": "🚀"},
    "message_router": {"id": "5449862290834735715", "fallback": "🎯"},
    "economy_profile": {"id": "5375296873982604963", "fallback": "💰"},
    "account_info": {"id": "5258011929993026890", "fallback": "👤"},
    "unlocks_login": {"id": "5256143829672672750", "fallback": "🔓"},
    "premium_hub": {"id": "5251422397893989847", "fallback": "👑"},
    "overseer_panel": {"id": "5433758796289685818", "fallback": "👑"},
    "free_user": {"id": "6269543218589731276", "fallback": "🆓"},
    "cpm_dashboard": {"id": "5359765421836757718", "fallback": "🏍️"},
    "access_granted": {"id": "5316930493223025689", "fallback": "♾️"},
    "role": {"id": "5332547853304734597", "fallback": "🎖️"},
    "choose_section": {"id": "5470177992950946662", "fallback": "👇"},
    "refresh": {"id": "5219934485113493317", "fallback": "🔄"},
    "info": {"id": "5452026937172048380", "fallback": "ℹ️"},
    "set_name": {"id": "5837003105228558796", "fallback": "✏️"},
    "set_id": {"id": "5890864241388293875", "fallback": "🆔"},
    "email": {"id": "5472239203590888751", "fallback": "📧"},
    "password": {"id": "5870972873450984431", "fallback": "🔒"},
    "back": {"id": "5357165441909279397", "fallback": "🔙"},
    "source_account": {"id": "4929214028657460019", "fallback": "🗂️"},
    "not_logged_in": {"id": "5330066942755615469", "fallback": "🕶️"},
    "create_account": {"id": "5382357040008021292", "fallback": "🆕"},
    "terminal_hybrid": {"id": "5431449001532594346", "fallback": "⚡"},
    "missing_variables": {"id": "5460860830201430838", "fallback": "🚧"},
    "flask_server": {"id": "5332289648460853008", "fallback": "📋"},
    "db_config": {"id": "5330194932781050507", "fallback": "🛡️"},
    "encryption": {"id": "5258096772776991776", "fallback": "⚙️"},
    "car_injection": {"id": "4972415571384599106", "fallback": "🎮"},
    "bulk_clone": {"id": "5893255507380014983", "fallback": "💼"},
    "bot_state": {"id": "5258093637450866522", "fallback": "🤖"},
    "money": {"id": "5447591434251158839", "fallback": "💵"},
    "coin": {"id": "5199552030615558774", "fallback": "🪙"},
    "w16_engine": {"id": "5332272404167140865", "fallback": "🛠️"},
    "max_fuel": {"id": "5271782239389106958", "fallback": "⛽"},
    "no_damage": {"id": "5271782239389106958", "fallback": "🛡️"},
    "horns": {"id": "5343761750921601316", "fallback": "📯"},
    "animations": {"id": "5931782330392778765", "fallback": "🔥"},
    "all_houses": {"id": "5326006424839407935", "fallback": "🏠"},
    "wheels": {"id": "5377521684221815300", "fallback": "🛞"},
    "complete_all_levels": {"id": "6194737030165959506", "fallback": "🏆"},
    "all_clothes": {"id": "5429526891998505619", "fallback": "👕"},
    "ultimate_glitch": {"id": "5798855098331304419", "fallback": "💀"},
    "vehicles_cars_w124": {"id": "6143050792430473209", "fallback": "🚗"},
    "unlock_camry_id": {"id": "5249166535041245970", "fallback": "🪙"},
    "group_unlock": {"id": "6001526766714227911", "fallback": "👥"},
    "vinyls_designs": {"id": "5318870237892865788", "fallback": "🎨"},
    "add_admin": {"id": "5870458774455587120", "fallback": "👤"},
    "remove_admin": {"id": "5060037611507156079", "fallback": "🗑️"},
    "stats_telemetry": {"id": "6325544614262475392", "fallback": "📈"},
    "broadcast_announcement": {"id": "5298609030321691620", "fallback": "📢"},
    "success_preserved": {"id": "5980930633298350051", "fallback": "✅"},
    "cancel_failed_error": {"id": "5974083768233760323", "fallback": "❌"},
    "warning": {"id": "5285139029333919650", "fallback": "⚠️"},
    "loading_progress": {"id": "5451732530048802485", "fallback": "⏳"},
    "account_created": {"id": "5461151367559141950", "fallback": "🎉"},
    "smoke": {"id": "5197450872484815271", "fallback": "💨"}
}

def get_premium_emoji(emoji_name):
    data = CUSTOM_EMOJIS.get(emoji_name)
    if data:
        return f'<tg-emoji emoji-id="{data["id"]}">{data["fallback"]}</tg-emoji>'
    return ""

def get_btn(emoji_name, button_text, **kwargs):
    data = CUSTOM_EMOJIS.get(emoji_name)
    if data and "id" in data:
        return types.InlineKeyboardButton(text=button_text, icon_custom_emoji_id=data["id"], **kwargs)
    return types.InlineKeyboardButton(text=button_text, **kwargs)

# ================================================================
#  LIBRARY FLAGS & WARNINGS
# ================================================================
HAS_BROTLI = True
HAS_CRYPTO = True
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================================================================
#  FLASK HEALTH SERVER
# ================================================================
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "MARKCPM1TOOLS Online"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()

# ================================================================
#  BOT INITIALIZATION
# ================================================================
BOT_TOKEN = '8857657486:AAGSrrT7PHNJso5t1xil83mdARwuiCMAb1k'
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=4)

try:
    bot.set_my_commands([
        telebot.types.BotCommand("/start", "Open Main Terminal"),
        telebot.types.BotCommand("/admin", "Open Overseer Panel"),
        telebot.types.BotCommand("/buytokens", "Buy Tokens"),
        telebot.types.BotCommand("/subscribe", "View Subscription Plans"),
        telebot.types.BotCommand("/info", "Bot Information"),
        telebot.types.BotCommand("/profile", "My Profile"),
        telebot.types.BotCommand("/listpremium", "View premium users (Admin)"),
        telebot.types.BotCommand("/listwarned", "View warned users (Admin)"),
        telebot.types.BotCommand("/ban", "Ban a user (Admin)"),
        telebot.types.BotCommand("/unban", "Unban a user (Admin)"),
        telebot.types.BotCommand("/clearwarn", "Clear warnings (Admin)"),
        telebot.types.BotCommand("/addtokens", "Add tokens (Admin)"),
        telebot.types.BotCommand("/removetoken", "Remove tokens (Admin)"),
        telebot.types.BotCommand("/addsubs", "Add subscription (Admin)"),
    ])
except:
    pass

# ================================================================
#  GAME API CONFIG
# ================================================================
FK = "AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"
SOURCE_ACCOUNT = ('glitchyn00000@gmail.com', '110022')

LOAD_URL = "https://europe-west1-cp-multiplayer.cloudfunctions.net/GetPlayerRecords3"
SAVE_URL = "https://europe-west1-cp-multiplayer.cloudfunctions.net/SavePlayerRecordsPartially8"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating5"
MAX_MONEY = 50_000_000
MAX_COIN = 500_000

GAME_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json",
    "User-Agent": "UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
    "X-Unity-Version": "2022.3.62f2",
}

http_session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=3)
http_session.mount('https://', adapter)
http_session.mount('http://', adapter)

# ================================================================
#  DATABASE CONFIG (MONGO + SQLITE FALLBACK)
# ================================================================
MONGO_URI = "mongodb+srv://sixtysecondswipes_db_user:eL1aAV73sCuyOJ2c@cluster0.5n928ih.mongodb.net/?appName=Cluster0"

ADMIN_IDS = {ADMIN_ID, 8254935096}
TRACKED_USERS_CACHE = set()
USE_MONGO = False
PREMIUM_EXPIRY = {}

db_path = "glitchyn_data.db"
with sqlite3.connect(db_path) as c:
    c.execute("CREATE TABLE IF NOT EXISTS premium_users (user_id INTEGER PRIMARY KEY, expires_at REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS tokens (user_id INTEGER PRIMARY KEY, auth_token TEXT, email TEXT, password TEXT, refresh_token TEXT, firebase_uid TEXT, token_expires_at REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS user_data (cache_key TEXT PRIMARY KEY, email TEXT, data_json TEXT, saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS bot_users (user_id INTEGER PRIMARY KEY)")
    c.execute("CREATE TABLE IF NOT EXISTS bot_admins (user_id INTEGER PRIMARY KEY)")
    c.commit()

try:
    mongo_client = MongoClient(MONGO_URI, maxPoolSize=50, serverSelectionTimeoutMS=2000)
    mongo_client.server_info()
    db = mongo_client["glitchyn_bot_db"]
    users_col = db["bot_users"]
    premium_col = db["premium_users"]
    tokens_col = db["tokens"]
    user_data_col = db["user_data"]
    admins_col = db["bot_admins"]
    USE_MONGO = True

    if admins_col.count_documents({}) == 0:
        for aid in [ADMIN_ID, 8254935096]:
            admins_col.update_one({"user_id": aid}, {"$set": {"user_id": aid}}, upsert=True)

    for doc in admins_col.find({}, {"user_id": 1}):
        ADMIN_IDS.add(doc["user_id"])
    for u in users_col.find({}, {"user_id": 1}):
        TRACKED_USERS_CACHE.add(u["user_id"])
    for doc in premium_col.find({}):
        if doc.get("user_id") and doc.get("expires_at"):
            PREMIUM_EXPIRY[doc["user_id"]] = doc["expires_at"]

except Exception as e:
    with sqlite3.connect(db_path) as c:
        if c.execute("SELECT COUNT(*) FROM bot_admins").fetchone()[0] == 0:
            for aid in [ADMIN_ID, 8254935096]:
                c.execute("INSERT INTO bot_admins (user_id) VALUES (?)", (aid,))
            c.commit()
        for row in c.execute("SELECT user_id FROM bot_admins").fetchall():
            ADMIN_IDS.add(row[0])
        for row in c.execute("SELECT user_id FROM bot_users").fetchall():
            TRACKED_USERS_CACHE.add(row[0])
        for row in c.execute("SELECT user_id, expires_at FROM premium_users").fetchall():
            PREMIUM_EXPIRY[row[0]] = row[1]

# ================================================================
#  USER TRACKING
# ================================================================
def track_user(user_id, username=None):
    if user_id in TRACKED_USERS_CACHE:
        if username:
            fb_patch(f"cpm1_users/{user_id}", {"username": username})
        return
    TRACKED_USERS_CACHE.add(user_id)
    if USE_MONGO:
        try:
            users_col.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)
        except:
            pass
    else:
        with sqlite3.connect(db_path) as c:
            c.execute("INSERT OR IGNORE INTO bot_users (user_id) VALUES (?)", (user_id,))
            c.commit()
    if not fb_get(f"cpm1_users/{user_id}"):
        fb_put(f"cpm1_users/{user_id}", {
            "tokens": 0, "subscription": None, "warnings": 0, "banned": False,
            "premium_by_tokens": False,
            "username": username or "Unknown",
            "joined": datetime.now().isoformat()
        })
    elif username:
        fb_patch(f"cpm1_users/{user_id}", {"username": username})

def get_total_users():
    return len(TRACKED_USERS_CACHE)

def get_all_tracked_users():
    return list(TRACKED_USERS_CACHE)

# ================================================================
#  ADMIN MANAGEMENT
# ================================================================
def is_admin(user_id):
    return user_id in ADMIN_IDS

def add_admin(user_id):
    ADMIN_IDS.add(user_id)
    if USE_MONGO:
        try:
            admins_col.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)
        except:
            pass
    else:
        with sqlite3.connect(db_path) as c:
            c.execute("INSERT OR IGNORE INTO bot_admins (user_id) VALUES (?)", (user_id,))
            c.commit()
    return True

def remove_admin(user_id):
    ADMIN_IDS.discard(user_id)
    if USE_MONGO:
        try:
            admins_col.delete_one({"user_id": user_id})
        except:
            pass
    else:
        with sqlite3.connect(db_path) as c:
            c.execute("DELETE FROM bot_admins WHERE user_id=?", (user_id,))
            c.commit()
    return True

def get_all_admins():
    return list(ADMIN_IDS)

# ================================================================
#  PREMIUM MANAGEMENT
# ================================================================
def is_premium(user_id):
    if is_admin(user_id):
        return True
    expiry = PREMIUM_EXPIRY.get(user_id, 0)
    if expiry < time.time():
        revoke_premium(user_id)
        return False
    return True

def approve_premium(user_id, days=30):
    expiry = time.time() + (days * 86400)
    PREMIUM_EXPIRY[user_id] = expiry
    if USE_MONGO:
        try:
            premium_col.update_one(
                {"user_id": user_id},
                {"$set": {"user_id": user_id, "expires_at": expiry, "approved_at": datetime.now()}},
                upsert=True
            )
        except:
            pass
    else:
        with sqlite3.connect(db_path) as c:
            c.execute("INSERT OR REPLACE INTO premium_users (user_id, expires_at) VALUES (?, ?)", (user_id, expiry))
            c.commit()
    return expiry

def revoke_premium(user_id):
    PREMIUM_EXPIRY.pop(user_id, None)
    if USE_MONGO:
        try:
            premium_col.delete_one({"user_id": user_id})
        except:
            pass
    else:
        with sqlite3.connect(db_path) as c:
            c.execute("DELETE FROM premium_users WHERE user_id=?", (user_id,))
            c.commit()
    try:
        fb_patch(f"cpm1_users/{user_id}", {
            "subscription": None,
            "premium_by_tokens": False
        })
    except:
        pass

def get_all_approved():
    current_time = time.time()
    if USE_MONGO:
        try:
            return [(doc["user_id"], doc.get("expires_at", 0))
                    for doc in premium_col.find({}) if doc.get("expires_at", 0) > current_time]
        except:
            return []
    else:
        with sqlite3.connect(db_path) as c:
            return c.execute("SELECT user_id, expires_at FROM premium_users WHERE expires_at > ?",
                             (current_time,)).fetchall()

# ================================================================
#  STRING & ENCRYPTION UTILITIES
# ================================================================
def clean_str(text):
    if not text:
        return "Unknown"
    return (str(text).replace('_', '-').replace('*', '•').replace('`', "'")
            .replace('[', '(').replace(']', ')'))

def make_xor_key(uid: str) -> bytes:
    chars = list(str(uid or ""))
    if len(chars) >= 9:
        chars[1], chars[8] = chars[8], chars[1]
    if len(chars) >= 3:
        chars.pop(2)
    if len(chars) >= 5:
        chars.append(chars[4])
    return "".join(chars).encode("utf-8") or b"0"

def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))

def decompress(data: bytes):
    if HAS_BROTLI:
        try:
            return brotli.decompress(data)
        except:
            pass
    for args in ((zlib.MAX_WBITS | 16,), tuple()):
        try:
            return zlib.decompress(data, *args)
        except:
            pass
    return None

def decrypt_aes(data: bytes, key: bytes):
    if not HAS_CRYPTO:
        return None
    try:
        return unpad(AES.new(key[:16], AES.MODE_CBC, b"\x00" * 16).decrypt(data), 16)
    except:
        return None

def _md5(text: str) -> bytes:
    return hashlib.md5(str(text).encode()).digest()

def _sha1(text: str) -> bytes:
    return hashlib.sha1(str(text).encode()).digest()[:16]

def build_aes_keys(uid: str, password: str = None, email: str = None) -> list:
    keys = [_md5("olzhas_carparking")]
    if password:
        keys.extend([_md5(password), _sha1(password)])
    if uid:
        keys.extend([_md5(uid), _sha1(uid)])
    if email:
        keys.append(_md5(email))
    return keys

# ================================================================
#  PLAYER RECORD READER
# ================================================================
class Reader:
    def __init__(self, data: bytes):
        self.buf, self.pos = data, 0

    def has_bytes(self, n: int) -> bool:
        return self.pos + n <= len(self.buf)

    def read_byte(self) -> int:
        if not self.has_bytes(1):
            return 0
        v = self.buf[self.pos]
        self.pos += 1
        return v

    def read_int(self) -> int:
        if not self.has_bytes(4):
            self.pos = len(self.buf)
            return 0
        v = struct.unpack_from("<i", self.buf, self.pos)[0]
        self.pos += 4
        return v

    def read_float(self) -> float:
        if not self.has_bytes(4):
            self.pos = len(self.buf)
            return 0.0
        v = struct.unpack_from("<f", self.buf, self.pos)[0]
        self.pos += 4
        return v

    def read_string(self) -> str:
        marker = self.read_int()
        if marker in (0, -1):
            return ""
        length = (-marker) - 1 if marker < -1 else marker
        if marker < -1:
            self.read_int()
        length = max(0, min(length, 1000000))
        if not self.has_bytes(length):
            return ""
        text = self.buf[self.pos:self.pos + length].decode("utf-8", errors="replace")
        self.pos += length
        return text.replace("\x00", "").strip()

    def read_list(self, item_fn):
        count = self.read_int()
        if count <= 0 or count > 1000000:
            return []
        res = []
        for _ in range(count):
            if self.pos >= len(self.buf):
                break
            val = item_fn()
            if val is not None:
                res.append(val)
        return res

    def read_dict(self) -> dict:
        count = self.read_int()
        if count <= 0 or count > 1000000:
            return {}
        return {self.read_int(): self.read_int() for _ in range(count) if self.pos < len(self.buf)}

    def read_equipment(self):
        if self.read_byte() == 0:
            return None
        return {k: self.read_list(self.read_int) for k in [
            "hair", "face", "beard", "cap", "mask", "top", "gloves", "bag",
            "pants", "shoes", "glasses", "SelectedEquipments"
        ]} | {"Gender": self.read_int()}

def parse_player(buf: bytes) -> dict:
    r = Reader(buf)
    if r.read_byte() == 0:
        return None
    player = {
        "Name": r.read_string(),
        "money": r.read_int(),
        "coin": r.read_int(),
        "localID": r.read_string(),
        "boughtFsos": r.read_list(r.read_int)
    }
    player["FriendsID"] = r.read_list(lambda: (r.read_byte(), {
        "id": r.read_string(), "Name": r.read_string(), "accountID": r.read_string()
    })[1])
    player.update({
        "LevelsDoneTime": r.read_list(r.read_float),
        "floats": r.read_list(r.read_float),
        "integers": r.read_list(r.read_int),
        "fcar": r.read_list(r.read_int),
        "favouriteWheels": r.read_list(r.read_int),
        "favouriteVinyls": r.read_list(r.read_int),
        "favouriteEmojis": r.read_list(r.read_int),
        "personEquipmentsMale": r.read_equipment(),
        "personEquipmentsFemale": r.read_equipment()
    })

    if r.read_byte() == 0:
        player["platesData"] = None
    else:
        def read_vinyl():
            r.read_byte()
            return {
                "vectors": r.read_list(lambda: {"x": r.read_float(), "y": r.read_float(), "z": r.read_float()}),
                "v": r.read_list(r.read_string),
                "floats": r.read_list(r.read_float),
                "text": r.read_string()
            }

        def read_plate():
            r.read_byte()
            return {
                "plateId": r.read_int(),
                "frontCarId": r.read_int(),
                "rearCarId": r.read_int(),
                "vinyls": r.read_list(read_vinyl)
            }

        player["platesData"] = {"allPlates": r.read_list(read_plate)}

    if r.read_byte() == 0:
        player["carIDnStatus"] = None
    else:
        player["carIDnStatus"] = {
            "carGeneratedIDs": r.read_list(r.read_string),
            "carStatus": r.read_list(r.read_int)
        }

    player["allData"] = r.read_string()
    player["flags"] = r.read_dict()
    player["animations"] = r.read_list(r.read_int)
    player["emojiPacks"] = r.read_list(r.read_int)
    player["wheels"] = r.read_list(r.read_int)
    player["boughtPoliceLights"] = r.read_list(r.read_int)
    player["boughtPoliceSirens"] = r.read_list(r.read_int)
    return player

def try_parse(buf: bytes) -> dict:
    candidates = [buf, decompress(buf)]
    if candidates[1]:
        candidates.append(decompress(candidates[1]))
    for candidate in filter(None, candidates):
        if candidate[0] in (17, 23, 24):
            try:
                p = parse_player(candidate)
                if p and p.get("Name") is not None:
                    return p
            except:
                pass
        try:
            clean = candidate[3:] if len(candidate) >= 3 and candidate[:2] == b"\xef\xbb" else candidate
            if clean and clean[0] == 123:
                return json.loads(clean.decode("utf-8"))
        except:
            pass
    return None

def decrypt_player_record(base64_text: str, uid: str, password: str = None, email: str = None) -> dict:
    try:
        buf = base64.b64decode(base64_text)
    except:
        return {"success": False, "message": "Bad base64"}
    if len(buf) < 10:
        return {"success": False, "message": "Too small"}
    direct = try_parse(buf)
    if direct:
        return {"success": True, "record": direct}
    if uid:
        try:
            decoded = decompress(xor_bytes(buf, make_xor_key(uid)))
            if decoded:
                parsed = try_parse(decoded)
                if parsed:
                    return {"success": True, "record": parsed}
        except:
            pass
    for key in build_aes_keys(uid or "", password, email):
        plain = decrypt_aes(buf, key)
        if not plain:
            continue
        parsed = try_parse(plain)
        if parsed:
            return {"success": True, "record": parsed}
    return {"success": False, "message": "Could not decrypt"}

# ================================================================
#  PLAYER RECORD WRITER
# ================================================================
class Writer:
    def __init__(self):
        self._p: List[bytes] = []

    def write_byte(self, v):
        self._p.append(bytes([int(v or 0) & 0xFF]))

    def write_int(self, v):
        self._p.append(struct.pack("<i", int(v or 0)))

    def write_float(self, v):
        self._p.append(struct.pack("<f", float(v or 0.0)))

    def write_string(self, s):
        if s is None:
            self._p.append(struct.pack("<i", -1))
            return
        s = str(s)
        if s == "":
            self._p.append(struct.pack("<i", 0))
            return
        enc = s.encode("utf-8")
        self._p.append(struct.pack("<ii", -(len(enc)) - 1, len(s)) + enc)

    def write_list(self, lst, fn):
        if lst is None:
            self._p.append(struct.pack("<i", -1))
            return
        self._p.append(struct.pack("<i", len(lst)))
        for item in lst:
            fn(item)

    def write_equipment(self, data):
        if not data:
            self.write_byte(0)
            return
        self.write_byte(13)
        for key in ["hair", "face", "beard", "cap", "mask", "top", "gloves",
                    "bag", "pants", "shoes", "glasses", "SelectedEquipments"]:
            self.write_list(data.get(key, []), self.write_int)
        self.write_int(data.get("Gender", 0))

    def write_plates(self, data):
        if not data:
            self.write_byte(0)
            return
        self.write_byte(1)
        plates = data.get("allPlates", [])
        self._p.append(struct.pack("<i", len(plates)))
        for plate in plates:
            self.write_byte(4)
            self.write_int(plate.get("plateId", 0))
            self.write_int(plate.get("frontCarId", 0))
            self.write_int(plate.get("rearCarId", 0))
            vinyls = plate.get("vinyls", [])
            self._p.append(struct.pack("<i", len(vinyls)))
            for vinyl in vinyls:
                self.write_byte(4)
                vecs = vinyl.get("vectors", [])
                self._p.append(struct.pack("<i", len(vecs)))
                for vec in vecs:
                    self._p.append(struct.pack("<fff", vec.get("x", 0), vec.get("y", 0), vec.get("z", 0)))
                self.write_list(vinyl.get("v", []), self.write_string)
                self.write_list(vinyl.get("floats", []), self.write_float)
                self.write_string(vinyl.get("text", ""))

    def write_car_id_status(self, data):
        if not data:
            self.write_byte(0)
            return
        self.write_byte(2)
        self.write_list(data.get("carGeneratedIDs", []), self.write_string)
        self.write_list(data.get("carStatus", []), self.write_int)

    def to_bytes(self):
        return b"".join(self._p)

# ================================================================
#  FIELD MAPPING
# ================================================================
FIELD_MAPPING = [
    (1, "localID"), (2, "money"), (3, "Name"), (4, "coin"), (5, "allData"),
    (6, "boughtFsos"), (7, "boughtPoliceLights"), (8, "boughtPoliceSirens"),
    (9, "FriendsID"), (10, "LevelsDoneTime"), (11, "floats"), (12, "integers"),
    (13, "fcar"), (14, "favouriteWheels"), (15, "favouriteVinyls"),
    (16, "favouriteEmojis"), (18, "emojiPacks"), (41, "personEquipmentsMale"),
    (42, "personEquipmentsFemale"), (43, "platesData"), (44, "carIDnStatus"),
    (45, "flags"), (46, "animations"), (48, "wheels")
]
INT_LIST_FIELDS = {6, 7, 8, 12, 13, 14, 15, 16, 18, 46, 48}
FLOAT_LIST_FIELDS = {10, 11}

def _field_modified(new_value, old_value) -> bool:
    if new_value is None and old_value is None:
        return False
    if new_value is None or old_value is None:
        return True
    if type(new_value) != type(old_value):
        return True
    if isinstance(new_value, (dict, list)):
        return json.dumps(new_value, sort_keys=True) != json.dumps(old_value, sort_keys=True)
    return new_value != old_value

def serialize_field(fid: int, value: Any) -> Optional[bytes]:
    w = Writer()
    if fid in (1, 3, 5):
        w.write_string(value)
        return w.to_bytes()
    if fid in (2, 4):
        w.write_int(value or 0)
        return w.to_bytes()
    if fid == 9:
        friends = value or []
        w._p.append(struct.pack("<i", len(friends)))
        for friend in friends:
            w.write_byte(3)
            w.write_string(friend.get("id", ""))
            w.write_string(friend.get("Name", ""))
            w.write_string(friend.get("accountID", ""))
        return w.to_bytes()
    if fid in INT_LIST_FIELDS:
        w.write_list(value or [], w.write_int)
        return w.to_bytes()
    if fid in FLOAT_LIST_FIELDS:
        w.write_list(value or [], w.write_float)
        return w.to_bytes()
    if fid in (41, 42):
        w.write_equipment(value)
        return w.to_bytes()
    if fid == 43:
        w.write_plates(value)
        return w.to_bytes()
    if fid == 44:
        w.write_car_id_status(value)
        return w.to_bytes()
    if fid == 45:
        w._p.append(struct.pack("<i", len(value or {})))
        for key, val in (value or {}).items():
            w.write_int(int(key))
            w.write_int(int(val))
        return w.to_bytes()
    return None

def build_payload(record: Dict[str, Any], uid: str,
                  original: Optional[Dict[str, Any]] = None,
                  force_fields: Optional[set] = None) -> str:
    force_fields = set(force_fields or [])
    fields = []
    for fid, key in FIELD_MAPPING:
        value = record.get(key)
        if value is None:
            continue
        if key == "allData":
            should_send = isinstance(value, str) and len(value) > 0
        elif key in force_fields:
            should_send = True
        elif original is not None:
            should_send = _field_modified(value, original.get(key))
        else:
            should_send = True
        if not should_send:
            continue
        raw = serialize_field(fid, value)
        if raw is not None:
            fields.append((fid, raw))
    parts = [struct.pack("<i", len(fields))]
    for fid, raw in fields:
        parts.extend([struct.pack("<hi", fid, len(raw)), raw])
    combined = b"".join(parts)
    compressed = brotli.compress(combined) if HAS_BROTLI else zlib.compress(combined)
    encrypted = xor_bytes(compressed, make_xor_key(uid))
    return base64.b64encode(encrypted).decode("ascii")

# ================================================================
#  SYNC CPM NUKER (MAIN CLASS)
# ================================================================
class SyncCPMNuker:
    def __init__(self):
        self.cache = {}

    def _ck(self, uid: int, email: Optional[str] = None) -> str:
        td = self.get_token_data(uid)
        return f"{uid}_{email or (td.get('email') if td else '')}"

    def save_token(self, uid: int, auth: str, email: str, pw: Optional[str] = None,
                   rt: Optional[str] = None, fuid: Optional[str] = None):
        if USE_MONGO:
            try:
                tokens_col.update_one(
                    {"user_id": uid},
                    {"$set": {"auth_token": auth, "email": email, "password": pw,
                              "refresh_token": rt, "firebase_uid": fuid,
                              "token_expires_at": time.time() + 3600}},
                    upsert=True
                )
            except:
                pass
        else:
            with sqlite3.connect(db_path) as c:
                c.execute(
                    "INSERT OR REPLACE INTO tokens (user_id, auth_token, email, password, refresh_token, firebase_uid, token_expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (uid, auth, email, pw, rt, fuid, time.time() + 3600)
                )
                c.commit()

    def get_token_data(self, uid: int) -> Optional[Dict[str, Any]]:
        if USE_MONGO:
            try:
                row = tokens_col.find_one({"user_id": uid})
                if not row:
                    return None
                return row
            except:
                return None
        else:
            with sqlite3.connect(db_path) as c:
                row = c.execute(
                    "SELECT auth_token, email, password, refresh_token, firebase_uid, token_expires_at FROM tokens WHERE user_id=?",
                    (uid,)
                ).fetchone()
            if not row:
                return None
            return {
                "auth_token": row[0], "email": row[1], "password": row[2],
                "refresh_token": row[3], "firebase_uid": row[4], "token_expires_at": row[5]
            }

    def update_token(self, uid: int, auth: str, rt: Optional[str] = None):
        if USE_MONGO:
            try:
                update_data = {"auth_token": auth, "token_expires_at": time.time() + 3600}
                if rt:
                    update_data["refresh_token"] = rt
                tokens_col.update_one({"user_id": uid}, {"$set": update_data})
            except:
                pass
        else:
            with sqlite3.connect(db_path) as c:
                if rt:
                    c.execute("UPDATE tokens SET auth_token=?, refresh_token=?, token_expires_at=? WHERE user_id=?",
                              (auth, rt, time.time() + 3600, uid))
                else:
                    c.execute("UPDATE tokens SET auth_token=?, token_expires_at=? WHERE user_id=?",
                              (auth, time.time() + 3600, uid))
                c.commit()

    def delete_token(self, uid: int):
        if USE_MONGO:
            try:
                tokens_col.delete_one({"user_id": uid})
            except:
                pass
        else:
            with sqlite3.connect(db_path) as c:
                c.execute("DELETE FROM tokens WHERE user_id=?", (uid,))
                c.commit()
        for key in list(self.cache.keys()):
            if key.startswith(str(uid)):
                del self.cache[key]

    def is_expired(self, uid: int) -> bool:
        td = self.get_token_data(uid)
        return not td or not td.get("token_expires_at") or td.get("token_expires_at") < time.time()

    def get_record(self, uid: int, email: Optional[str] = None) -> Dict[str, Any]:
        ck = self._ck(uid, email)
        if ck not in self.cache:
            if USE_MONGO:
                try:
                    doc = user_data_col.find_one({"cache_key": ck})
                    if doc and "data_json" in doc:
                        self.cache[ck] = json.loads(doc["data_json"])
                except:
                    pass
            else:
                with sqlite3.connect(db_path) as c:
                    row = c.execute("SELECT data_json FROM user_data WHERE cache_key=?", (ck,)).fetchone()
                if row:
                    try:
                        self.cache[ck] = json.loads(row[0])
                    except:
                        pass
        return self.cache.get(ck, {})

    def set_record(self, uid: int, data: Dict[str, Any], email: Optional[str] = None):
        ck = self._ck(uid, email)
        self.cache[ck] = data
        if USE_MONGO:
            try:
                user_data_col.update_one(
                    {"cache_key": ck},
                    {"$set": {"email": email, "data_json": json.dumps(data), "saved_at": datetime.now()}},
                    upsert=True
                )
            except:
                pass
        else:
            with sqlite3.connect(db_path) as c:
                c.execute("INSERT OR REPLACE INTO user_data (cache_key, email, data_json) VALUES (?, ?, ?)",
                          (ck, email, json.dumps(data)))
                c.commit()

    def _post(self, url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        try:
            clean_headers = {k: v for k, v in headers.items() if k.lower() != "host"}
            resp = http_session.post(url, json=payload, headers=clean_headers, timeout=15)
            try:
                return resp.json()
            except:
                return {"raw": resp.text, "status": resp.status_code, "ok": False}
        except Exception as e:
            return {"ok": False, "message": f"CONNECTION FAILED."}

    def login(self, email: str, password: str) -> Dict[str, Any]:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FK}"
        payload = {"email": email, "password": password, "returnSecureToken": True,
                   "clientType": "CLIENT_TYPE_ANDROID"}
        result = self._post(url, payload, GAME_HEADERS)
        if result.get("ok") is False:
            return result
        if "idToken" in result:
            return {"ok": True, "message": "OK", "auth": result["idToken"],
                    "refresh_token": result.get("refreshToken", ""),
                    "firebase_uid": result.get("localId", "")}
        err = "INVALID_CREDENTIALS"
        try:
            if isinstance(result.get("error"), dict):
                err = str(result["error"].get("message", "INVALID_CREDENTIALS"))
            elif isinstance(result.get("error"), str):
                err = result["error"]
        except:
            pass
        return {"ok": False, "message": err.upper()[:80]}

    def register(self, email: str, password: str) -> Dict[str, Any]:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FK}"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        result = self._post(url, payload, GAME_HEADERS)
        if result.get("ok") is False:
            return result
        if "idToken" in result:
            return {"ok": True, "message": "OK", "auth": result["idToken"],
                    "refresh_token": result.get("refreshToken", ""),
                    "firebase_uid": result.get("localId", "")}
        err = "REGISTRATION_FAILED"
        try:
            if isinstance(result.get("error"), dict):
                err = str(result["error"].get("message", "FAILED"))
            elif isinstance(result.get("error"), str):
                err = result["error"]
        except:
            pass
        return {"ok": False, "message": err.upper()[:80]}

    def _refresh(self, uid: int) -> Tuple[bool, str]:
        td = self.get_token_data(uid)
        if not td:
            return False, "NO_TOKEN"
        rt, em, pw = td.get("refresh_token"), td.get("email"), td.get("password")
        if rt:
            res = self._post(
                f"https://securetoken.googleapis.com/v1/token?key={FK}",
                {"grant_type": "refresh_token", "refresh_token": rt},
                {"Content-Type": "application/json"}
            )
            if res.get("id_token"):
                self.update_token(uid, res["id_token"], res.get("refresh_token", rt))
                return True, "OK"
        if em and pw:
            res = self.login(em, pw)
            if res.get("ok"):
                self.save_token(uid, res["auth"], em, pw, res.get("refresh_token", ""),
                                res.get("firebase_uid", ""))
                return True, "OK"
        return False, "REFRESH_FAILED"

    def get_auth(self, uid: int) -> Tuple[bool, str, str]:
        if self.is_expired(uid):
            ok, msg = self._refresh(uid)
            if not ok:
                return False, msg, ""
        td = self.get_token_data(uid)
        if td and td.get("auth_token"):
            return True, "OK", td.get("auth_token")
        return False, "NO_TOKEN", ""

    def load(self, uid: int, force: bool = False) -> bool:
        td = self.get_token_data(uid)
        if not td:
            return False
        if not force and self._ck(uid) in self.cache:
            return True
        ok, msg, auth = self.get_auth(uid)
        if not ok:
            return False
        res = self._post(LOAD_URL, {"data": None}, {**GAME_HEADERS, "Authorization": f"Bearer {auth}"})
        if res.get("ok") is False or not res.get("result"):
            return False
        dec = decrypt_player_record(res["result"], td.get("firebase_uid", ""),
                                    td.get("password", ""), td.get("email", ""))
        if dec.get("success") and dec.get("record"):
            self.set_record(uid, dec["record"], td.get("email", ""))
            return True
        return False

    def _ok(self, value: Any) -> bool:
        if value in (1, True, "1"):
            return True
        if value in (0, False, None, "0"):
            return False
        if isinstance(value, str):
            try:
                return self._ok(json.loads(value.strip()))
            except:
                return False
        if isinstance(value, dict):
            for k in ("result", "ok", "success"):
                if k in value:
                    return self._ok(value[k])
        return False

    def _send(self, auth: str, record: Dict[str, Any], fuid: str,
              original: Optional[Dict[str, Any]] = None,
              force_fields: Optional[set] = None) -> Tuple[bool, str]:
        if not fuid:
            return False, "NO_FIREBASE_UID"
        try:
            payload = build_payload(record, fuid, original, force_fields=force_fields)
            res = self._post(SAVE_URL, {"data": {"data": payload, "deviceId": fuid[:8]}},
                             {**GAME_HEADERS, "Authorization": f"Bearer {auth}",
                              "Connection": "Keep-Alive",
                              "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/SD1A.210817.036)"})
            if res.get("ok") is False:
                return False, res.get("message", "API TIMEOUT")
            if res and self._ok(res):
                return True, "OK"
            return False, f"SAVE-FAILED"
        except Exception as e:
            return False, str(e)

    def _save(self, uid: int, data: Dict[str, Any],
              force_fields: Optional[set] = None) -> Dict[str, Any]:
        ok, msg, auth = self.get_auth(uid)
        if not ok:
            return {"ok": False, "message": msg}
        td = self.get_token_data(uid)
        fuid = td.get("firebase_uid", "") if td else ""
        email = td.get("email", "") if td else ""
        original = self.get_record(uid, email) or None
        ok2, msg2 = self._send(auth, data, fuid, original, force_fields=force_fields)
        if ok2:
            self.set_record(uid, data, email)
            return {"ok": True, "message": "OK"}
        return {"ok": False, "message": msg2}

    def _modify(self, uid: int, mods: Dict[str, Any],
                force_fields: Optional[set] = None) -> Dict[str, Any]:
        if not self.load(uid):
            return {"ok": False, "message": "ACCOUNT LOAD FAILED. CHECK CREDENTIALS."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        if not data or data.get("Name") is None:
            return {"ok": False, "message": "PROFILE DATA CORRUPTED."}
        for k, v in mods.items():
            if k == "money":
                v = min(int(v), MAX_MONEY)
            if k == "coin":
                v = min(int(v), MAX_COIN)
            data[k] = v
        return self._save(uid, data, force_fields=set(force_fields or mods.keys()))

    def _set_floats(self, uid: int, indices_values: List[Tuple[int, float]]) -> Dict[str, Any]:
        if not self.load(uid):
            return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        if not data or data.get("Name") is None:
            return {"ok": False, "message": "PROFILE DATA CORRUPTED."}
        floats = data.get("floats", [])
        max_idx = max(idx for idx, _ in indices_values)
        while len(floats) <= max_idx:
            floats.append(0.0)
        for idx, val in indices_values:
            floats[idx] = float(val)
        data["floats"] = floats
        return self._save(uid, data, force_fields={"floats"})

    def _set_integers(self, uid: int, indices_values: List[Tuple[int, int]]) -> Dict[str, Any]:
        if not self.load(uid):
            return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        if not data or data.get("Name") is None:
            return {"ok": False, "message": "PROFILE DATA CORRUPTED."}
        integers = data.get("integers", [])
        max_idx = max(idx for idx, _ in indices_values)
        while len(integers) <= max_idx:
            integers.append(0)
        for idx, val in indices_values:
            integers[idx] = int(val)
        data["integers"] = integers
        return self._save(uid, data, force_fields={"integers"})

    def set_money(self, uid: int, amount: int) -> Dict[str, Any]:
        return self._modify(uid, {"money": min(int(amount), MAX_MONEY)}, force_fields={"money"})

    def set_coin(self, uid: int, amount: int) -> Dict[str, Any]:
        return self._modify(uid, {"coin": min(int(amount), MAX_COIN)}, force_fields={"coin"})

    def change_player_id(self, uid: int, new_id: str) -> Dict[str, Any]:
        if not self.load(uid, force=True):
            return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        if not data or data.get("Name") is None:
            return {"ok": False, "message": "PROFILE DATA CORRUPTED."}
        new_id_upper = str(new_id).strip().upper()
        data["localID"] = new_id_upper
        result = self._save(uid, data, force_fields={"localID"})
        if result.get("ok"):
            return {"ok": True, "message": f"TAG MASKED TO {new_id_upper}", "new_id": new_id_upper}
        return {"ok": False, "message": result.get("message", "SAVE FAILED")}

    def change_player_name(self, uid: int, new_name: str) -> Dict[str, Any]:
        if not self.load(uid, force=True):
            return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        data["Name"] = new_name
        return self._save(uid, data, force_fields={"Name"})

    def change_email(self, uid: int, new_email: str) -> Dict[str, Any]:
        td = self.get_token_data(uid)
        if not td:
            return {"ok": False, "message": "Not logged in"}
        return {"ok": True, "message": "OK"}

    def unlock_w16(self, uid: int) -> Dict[str, Any]:
        return self._set_floats(uid, [(32, 1.0)])

    def unlock_horns(self, uid: int) -> Dict[str, Any]:
        return self._set_floats(uid, [(27, 1.0), (28, 1.0), (29, 1.0), (30, 1.0), (31, 1.0)])

    def disable_damage(self, uid: int) -> Dict[str, Any]:
        return self._set_floats(uid, [(34, 1.0)])

    def unlimited_fuel(self, uid: int) -> Dict[str, Any]:
        return self._set_floats(uid, [(3, 1.0)])

    def unlock_smoke(self, uid: int) -> Dict[str, Any]:
        return self._set_floats(uid, [(33, 1.0)])

    def unlock_animations(self, uid: int) -> Dict[str, Any]:
        if not self.load(uid):
            return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        data["animations"] = sorted(set(data.get("animations", []) + list(range(301))))
        return self._save(uid, data, force_fields={"animations"})

    def unlock_wheels(self, uid: int) -> Dict[str, Any]:
        if not self.load(uid):
            return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        data["wheels"] = sorted(set(data.get("wheels", []) + list(range(73, 221))))
        integers = data.get("integers", [])
        while len(integers) < 113:
            integers.append(0)
        for idx in [0, 1, 2, 3, 4, 5, 110, 111, 112]:
            integers[idx] = 1
        data["integers"] = integers
        return self._save(uid, data, force_fields={"wheels", "integers"})

    def unlock_houses(self, uid: int) -> Dict[str, Any]:
        return self._set_integers(uid, [(8, 1), (110, 1), (111, 1), (112, 1)])

    def complete_all_levels(self, uid: int) -> Dict[str, Any]:
        return self._modify(
            uid,
            {"LevelsDoneTime": [0] + [120 if i == 43 else 1 for i in range(1, 110)]},
            force_fields={"LevelsDoneTime"}
        )

    def set_rank(self, uid: int) -> Dict[str, Any]:
        self.load(uid)
        ok, msg, auth = self.get_auth(uid)
        if not ok:
            return {"ok": True, "message": "OK"}
        rating_data = {
            "RatingData": {
                "time": 1e22, "cars": 1e16, "car_fix": 1e13, "car_collided": 1e12,
                "car_exchange": 1e13, "car_trade": 1e13, "car_wash": 1e13,
                "slicer_cut": 1e13, "drift_max": 1e14, "drift": 1e14,
                "cargo": 1e5, "delivery": 1e5, "race_win": 3e20, "taxi": 1e10,
                "levels": 10000990000, "gifts": 1e9, "fuel": 1e10, "offroad": 1e10,
                "speed_banner": 1e9, "reactions": 1e17, "run": 1e9, "real_estate": 1e9,
                "t_distance": 1e10, "treasure": 1e10, "block_post": 1e10,
                "push_ups": 1e12, "burnt_tire": 1e10, "passanger_distance": 1e8
            }
        }
        try:
            self._post(RANK_URL, {"data": json.dumps(rating_data)},
                       {**GAME_HEADERS, "Authorization": f"Bearer {auth}"})
        except:
            pass
        return {"ok": True, "message": "OK"}

    def _normalize_equipment(self, equipment: Dict[str, Any], gender: int) -> Dict[str, Any]:
        list_fields = ["hair", "face", "beard", "cap", "mask", "top", "gloves",
                       "bag", "pants", "shoes", "glasses", "SelectedEquipments"]
        normalized = {
            key: [int(v) for v in (equipment.get(key, []) if isinstance(equipment, dict) else [])]
            for key in list_fields
        }
        normalized["Gender"] = int(gender)
        return normalized

    def unlock_all_clothes(self, uid: int) -> Dict[str, Any]:
        if not self.load(uid, force=True):
            return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))

        eq_male = {
            "Gender": 0, "bag": list(range(101)),
            "beard": list(range(6, 21)) + [100], "cap": list(range(3, 64)),
            "face": [0, 1, 2, 100], "glasses": list(range(10)) + [100],
            "gloves": list(range(6)) + [100], "hair": list(range(3, 20)) + [100],
            "mask": list(range(3, 9)) + [100], "pants": list(range(26)),
            "shoes": list(range(31)), "top": list(range(2, 109)),
            "SelectedEquipments": [-1, 10, 19, 41, 100, 4, 20, 9, 22, 21, 74]
        }
        eq_female = {
            "Gender": 1, "bag": list(range(6)), "beard": [],
            "cap": list(range(3, 41)), "face": [0], "glasses": list(range(10)),
            "gloves": [1], "hair": [0, 7, 8, 9, 10], "mask": list(range(3, 8)),
            "pants": list(range(12)), "shoes": list(range(3, 15)),
            "top": list(range(5, 80)),
            "SelectedEquipments": [0, 0, -1, -1, -1, -1, -1, -1, 0, -1, -1]
        }

        data["personEquipmentsMale"] = self._normalize_equipment(eq_male, 0)
        data["personEquipmentsFemale"] = self._normalize_equipment(eq_female, 1)

        return self._save(uid, data, force_fields={"personEquipmentsMale", "personEquipmentsFemale"})

    def unlock_all_features(self, uid: int) -> Dict[str, Any]:
        feature_calls = [
            ("W16 Engine", self.unlock_w16), ("Horns", self.unlock_horns),
            ("No Damage", self.disable_damage), ("Unlimited Fuel", self.unlimited_fuel),
            ("Smoke", self.unlock_smoke), ("Animations", self.unlock_animations),
            ("Wheels", self.unlock_wheels), ("Houses", self.unlock_houses),
            ("All Levels", self.complete_all_levels), ("Max Rank", self.set_rank)
        ]
        if not self.load(uid, force=True):
            return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        results, failed = [], []
        for name, fn in feature_calls:
            res = fn(uid)
            if res.get("ok"):
                results.append(name)
            else:
                failed.append(f"{name}: {res.get('message', 'Failed')}")
        return {"ok": not failed, "message": f"Unlocked {len(results)}/{len(feature_calls)} features"}

    def fix_account(self, uid: int) -> Dict[str, Any]:
        if not self.load(uid, force=True):
            return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        if data.get("money", 0) > MAX_MONEY:
            data["money"] = MAX_MONEY
        if data.get("coin", 0) > MAX_COIN:
            data["coin"] = MAX_COIN
        flags = data.get("flags", {})
        if isinstance(flags, dict):
            for bad_flag in [0, 1, 2, "0", "1", "2"]:
                flags.pop(bad_flag, None)
            data["flags"] = flags
        return self._save(uid, data, force_fields={"money", "coin", "flags"})

    def get_account_info(self, uid: int, force_refresh: bool = False) -> Dict[str, Any]:
        if not self.load(uid, force=force_refresh):
            return {"ok": False}
        td = self.get_token_data(uid)
        if not td:
            return {"ok": False}
        data = self.get_record(uid, td.get("email"))
        if not data or data.get("Name") is None:
            return {"ok": False}

        cars_count = 0
        try:
            c_status = data.get('carIDnStatus')
            if isinstance(c_status, dict):
                c_list = c_status.get('carStatus', [])
                if isinstance(c_list, list):
                    cars_count = len(c_list)
        except:
            pass

        if cars_count == 0:
            try:
                ad = data.get('allData', '{}')
                if isinstance(ad, str):
                    ad_json = json.loads(ad)
                    if isinstance(ad_json, dict):
                        cars_count = len(ad_json.get('cars', []))
            except:
                pass

        return {
            "ok": True, "name": data.get("Name", "Unknown"),
            "money": data.get("money", 0), "coin": data.get("coin", 0),
            "localID": data.get("localID", "Unknown"),
            "email": td.get("email"), "cars": cars_count
        }

nuker = SyncCPMNuker()

# ================================================================
#  CPM1 CAR CLONE FUNCTIONS
# ================================================================
CPM_CARS_FETCH_URL = "https://europe-west1-cp-multiplayer.cloudfunctions.net/GetAllCars2"
CPM_CARS_SAVE_URL = "https://europe-west1-cp-multiplayer.cloudfunctions.net/SaveCarsPartially8"

CPM_FIELD_NAMES = {
    1: 'CarID', 2: 'dataVersion', 3: 'vectors', 4: 'floats', 5: 'gears',
    6: 'typeToInstall', 7: 'BoughtParts', 8: 'texts', 9: 'flagID',
    10: 'fsoData', 11: 'installedPoliceLights', 12: 'Vynils', 13: 'WindowVinyls',
}

def cpm1_ios_headers(token):
    return {
        'accept': '*/*',
        'authorization': f'Bearer {token}',
        'content-type': 'application/json; charset=utf-8',
        'user-agent': 'CarParking/265 CFNetwork/3860.600.12 Darwin/25.5.0',
        'x-client-platform': 'IOS',
        'x-client-version': '4.9.10',
        'x-client-deviceid': str(uuid.uuid4()).upper(),
        'x-request-nonce': str(uuid.uuid4()),
        'x-unity-version': '2022.3.62f2',
        'accept-encoding': 'gzip',
        'connection': 'Keep-Alive',
    }

def cpm1_write_memorypack_string(s):
    if s is None or s == "":
        return struct.pack("<i", 0)
    sb = str(s).encode("utf-8")
    return struct.pack("<ii", -len(sb) - 1, len(sb)) + sb

def cpm1_looks_like_base64(val):
    if not isinstance(val, str):
        return False
    if len(val) < 4 or len(val) % 4 != 0:
        return False
    return bool(re.match(r'^[A-Za-z0-9+/]+={0,2}$', val))

def cpm1_deserialize_string_list(b64):
    if not b64 or not isinstance(b64, str):
        return []
    try:
        compressed = base64.b64decode(b64)
    except:
        return []
    try:
        decompressed = brotli.decompress(compressed)
    except:
        try:
            decompressed = zlib.decompress(compressed, zlib.MAX_WBITS | 16)
        except:
            decompressed = compressed
    if not decompressed or len(decompressed) < 4:
        return []
    out = []
    pos = 0
    count = struct.unpack_from("<i", decompressed, 0)[0]
    pos = 4
    if count <= 0 or count > 100000:
        return []
    for _ in range(count):
        if pos + 4 > len(decompressed):
            break
        marker = struct.unpack_from("<i", decompressed, pos)[0]
        pos += 4
        if marker == 0:
            out.append("")
            continue
        if marker == -1:
            break
        if marker < -1:
            byte_len = -marker - 1
            if pos + 4 > len(decompressed):
                break
            pos += 4
        else:
            byte_len = marker
        if pos + byte_len > len(decompressed):
            break
        s = decompressed[pos:pos+byte_len].decode("utf-8", errors="replace")
        pos += byte_len
        out.append(s.replace("\x00", "").strip())
    return out

def cpm1_is_readonly_cpm_id(v):
    if not isinstance(v, str):
        return False
    x = v.strip().upper()
    return len(x) == 8 and bool(re.match(r'^[A-Z]{2}\d{6}$', x))

def cpm1_generate_random_cpm_id():
    L = string.ascii_uppercase
    D = string.digits
    return ''.join(random.choice(L) for _ in range(2)) + ''.join(random.choice(D) for _ in range(6))

def cpm1_resolve_cpm_id(record):
    val = (record or {}).get("localID")
    if not val or not cpm1_is_readonly_cpm_id(val):
        val = cpm1_generate_random_cpm_id()
    return str(val).strip().upper()

def cpm1_generated_id_from_car(car):
    for k in ("generatedID", "generatedId", "carGeneratedID", "carGeneratedId"):
        v = car.get(k)
        if v and isinstance(v, str):
            return v
    texts = car.get("texts")
    if isinstance(texts, str):
        try:
            texts = cpm1_deserialize_string_list(texts)
        except:
            texts = []
    if isinstance(texts, list):
        for v in texts:
            if v and isinstance(v, str) and '_' in v and re.search(r'\d', v):
                return v
    return None

def cpm1_merge_cars_by_id(*car_lists):
    merged = {}
    for lst in car_lists:
        if not isinstance(lst, list):
            continue
        for car in lst:
            if not isinstance(car, dict):
                continue
            try:
                cid = int(car.get("CarID"))
            except:
                continue
            if cid < 0:
                continue
            merged[cid] = car
    return [merged[k] for k in sorted(merged.keys())]

def cpm1_replace_uid_in_value(value, src_uid, tgt_uid):
    if not src_uid or src_uid == tgt_uid:
        return value
    if isinstance(value, str):
        if cpm1_looks_like_base64(value):
            return value
        return value.replace(str(src_uid), str(tgt_uid))
    if isinstance(value, list):
        return [cpm1_replace_uid_in_value(v, src_uid, tgt_uid) for v in value]
    if isinstance(value, dict):
        return {k: cpm1_replace_uid_in_value(v, src_uid, tgt_uid) for k, v in value.items()}
    return value

def cpm1_prepare_car(stock_car, cpm_id):
    car_copy = json.loads(json.dumps(stock_car))
    car_id = int(car_copy.get("CarID") or 0)
    if isinstance(car_copy.get("Vynils"), dict):
        car_copy["Vynils"]["CarID"] = car_id
    texts = car_copy.get("texts")
    if isinstance(texts, str):
        try:
            texts = cpm1_deserialize_string_list(texts)
        except:
            texts = []
    if not isinstance(texts, list):
        texts = []
    while len(texts) < 4:
        texts.append('')
    orig = texts[2]
    if isinstance(orig, str) and '_' in orig:
        parts = orig.split('_')
        texts[2] = f"{cpm_id}_" + "_".join(parts[1:])
    else:
        texts[2] = f"{cpm_id}_{car_id}XX000"
    car_copy["texts"] = texts
    return car_copy

def cpm1_build_car_entries(cars, cpm_id):
    entries = []
    for car in cars:
        try:
            cid = int(car.get("CarID"))
        except:
            continue
        if cid < 0:
            continue
        gen = cpm1_generated_id_from_car(car) or f"{cpm_id}_{cid}XX000"
        entries.append([cid, gen])
    return entries

def cpm1_entries_to_sparse(car_entries):
    if not car_entries:
        return {"carGeneratedIDs": [], "carStatus": []}
    ids = []
    for e in car_entries:
        try:
            ids.append(int(e[0]))
        except:
            pass
    ids = [i for i in ids if i >= 0]
    if not ids:
        return {"carGeneratedIDs": [], "carStatus": []}
    max_id = max(ids)
    gen_ids = [''] * (max_id + 1)
    statuses = [0] * (max_id + 1)
    for e in car_entries:
        try:
            cid = int(e[0])
        except:
            continue
        if 0 <= cid <= max_id:
            gen_ids[cid] = str(e[1]) if e[1] is not None else ''
            statuses[cid] = 1
    return {"carGeneratedIDs": gen_ids, "carStatus": statuses}

def cpm1_sanitize_car_for_encoding(car):
    clean = {}
    for key, value in car.items():
        if isinstance(value, str) and cpm1_looks_like_base64(value):
            clean[key] = value
            continue
        if key == 'floats':
            arr = value if isinstance(value, list) else []
            out = []
            for v in arr:
                try:
                    f = float(v)
                except:
                    f = 0.0
                out.append(f)
            while len(out) < 48:
                out.append(0.0)
            clean[key] = out
        elif key == 'gears':
            arr = value if isinstance(value, list) else []
            out = []
            for v in arr:
                try:
                    f = float(v)
                except:
                    f = -10.0
                out.append(f)
            clean[key] = out
        elif key == 'vectors':
            arr = value if isinstance(value, list) else []
            out = []
            for vec in arr:
                if isinstance(vec, dict):
                    try:
                        x = float(vec.get('x') or 0)
                    except:
                        x = 0.0
                    try:
                        y = float(vec.get('y') or 0)
                    except:
                        y = 0.0
                    try:
                        z = float(vec.get('z') or 0)
                    except:
                        z = 0.0
                    out.append({'x': x, 'y': y, 'z': z})
                else:
                    out.append({'x': 0.0, 'y': 0.0, 'z': 0.0})
            clean[key] = out
        elif key in ('typeToInstall', 'BoughtParts', 'fsoData', 'installedPoliceLights'):
            arr = value if isinstance(value, list) else []
            out = []
            for v in arr:
                try:
                    iv = int(v)
                except:
                    iv = 0
                out.append(iv)
            clean[key] = out
        elif key == 'texts':
            arr = value if isinstance(value, list) else []
            clean[key] = [str(v) if v is not None else '' for v in arr]
        elif key == 'Vynils':
            if isinstance(value, dict) and isinstance(value.get('allVynils'), list):
                fc = int(value.get('_fieldCount', 2) or 2)
                if fc < 2:
                    fc = 2
                nv = {'_fieldCount': fc, 'allVynils': [], 'CarID': int(car.get('CarID', 0) or 0)}
                if isinstance(value.get('_remainingHex'), str):
                    nv['_remainingHex'] = value['_remainingHex']
                for vinyl in value['allVynils']:
                    if not isinstance(vinyl, dict):
                        continue
                    cv = {'_fieldCount': int(vinyl.get('_fieldCount', 6) or 6)}
                    for fn in ('position', 'scaleRotation', 'iconPosition'):
                        vec = vinyl.get(fn) or {}
                        if not isinstance(vec, dict):
                            vec = {}
                        try:
                            x = float(vec.get('x') or 0)
                        except:
                            x = 0.0
                        try:
                            y = float(vec.get('y') or 0)
                        except:
                            y = 0.0
                        try:
                            z = float(vec.get('z') or 0)
                        except:
                            z = 0.0
                        cv[fn] = {'x': x, 'y': y, 'z': z}
                    cv['text'] = str(vinyl.get('text', '') or '')
                    cv['color'] = int(vinyl.get('color', 0) or 0)
                    cv['packedData'] = int(vinyl.get('packedData', 0) or 0)
                    nv['allVynils'].append(cv)
                clean[key] = nv
            else:
                clean[key] = value
        elif key == 'WindowVinyls':
            if isinstance(value, list):
                out = []
                for vinyl in value:
                    if not isinstance(vinyl, dict):
                        continue
                    cv = {'_fieldCount': int(vinyl.get('_fieldCount', 6) or 6)}
                    for fn in ('position', 'scaleRotation', 'iconPosition'):
                        vec = vinyl.get(fn) or {}
                        if not isinstance(vec, dict):
                            vec = {}
                        try:
                            x = float(vec.get('x') or 0)
                        except:
                            x = 0.0
                        try:
                            y = float(vec.get('y') or 0)
                        except:
                            y = 0.0
                        try:
                            z = float(vec.get('z') or 0)
                        except:
                            z = 0.0
                        cv[fn] = {'x': x, 'y': y, 'z': z}
                    cv['text'] = str(vinyl.get('text', '') or '')
                    cv['color'] = int(vinyl.get('color', 0) or 0)
                    cv['packedData'] = int(vinyl.get('packedData', 0) or 0)
                    out.append(cv)
                clean[key] = out
            else:
                clean[key] = value
        elif key in ('CarID', 'dataVersion', 'flagID'):
            try:
                clean[key] = int(value)
            except:
                clean[key] = 0
        else:
            clean[key] = value
    return clean

def cpm1_encode_field_value_binary(name, value):
    if name == 'vectors':
        if not isinstance(value, list):
            value = []
        buf = struct.pack("<i", len(value))
        for vec in value:
            x = float(vec.get('x') or 0) if isinstance(vec, dict) else 0.0
            y = float(vec.get('y') or 0) if isinstance(vec, dict) else 0.0
            z = float(vec.get('z') or 0) if isinstance(vec, dict) else 0.0
            buf += struct.pack("<fff", x, y, z)
        return buf
    if name in ('floats', 'gears'):
        if not isinstance(value, list):
            value = []
        buf = struct.pack("<i", len(value))
        for v in value:
            try:
                f = float(v)
            except:
                f = 0.0
            buf += struct.pack("<f", f)
        return buf
    if name in ('typeToInstall', 'BoughtParts', 'fsoData', 'installedPoliceLights'):
        if not isinstance(value, list):
            value = []
        buf = struct.pack("<i", len(value))
        for v in value:
            try:
                iv = int(v)
            except:
                iv = 0
            buf += struct.pack("<i", iv)
        return buf
    if name == 'texts':
        if not isinstance(value, list):
            value = []
        buf = struct.pack("<i", len(value))
        for v in value:
            buf += cpm1_write_memorypack_string(str(v) if v is not None else '')
        return buf
    if name == 'Vynils':
        if not isinstance(value, dict) or not isinstance(value.get('allVynils'), list):
            return b""
        fc = int(value.get('_fieldCount', 2) or 2)
        parts = [bytes([fc & 0xFF])]
        if fc == 0:
            return b"".join(parts)
        parts.append(struct.pack("<i", len(value['allVynils'])))
        for vinyl in value['allVynils']:
            if not isinstance(vinyl, dict):
                parts.append(bytes([0]))
                continue
            vfc = int(vinyl.get('_fieldCount', 6) or 6)
            parts.append(bytes([vfc & 0xFF]))
            if vfc == 0:
                continue
            for fn in ('position', 'scaleRotation', 'iconPosition'):
                vec = vinyl.get(fn) if isinstance(vinyl.get(fn), dict) else {}
                x = float(vec.get('x') or 0)
                y = float(vec.get('y') or 0)
                z = float(vec.get('z') or 0)
                parts.append(struct.pack("<fff", x, y, z))
            parts.append(cpm1_write_memorypack_string(str(vinyl.get('text', '') or '')))
            parts.append(struct.pack("<I", int(vinyl.get('color', 0) or 0) & 0xFFFFFFFF))
            try:
                pd = int(vinyl.get('packedData', 0) or 0)
            except:
                pd = 0
            parts.append(struct.pack("<q", pd))
        if fc >= 2:
            carid = value.get('CarID')
            if carid is None and isinstance(value.get('_remainingHex'), str) and value['_remainingHex']:
                try:
                    hx = bytes.fromhex(value['_remainingHex'])
                    carid = struct.unpack_from("<i", hx, 0)[0]
                except:
                    carid = 0
            try:
                carid = int(carid) if carid is not None else 0
            except:
                carid = 0
            parts.append(struct.pack("<i", carid))
        return b"".join(parts)
    if name == 'WindowVinyls':
        if not isinstance(value, list):
            value = []
        parts = [struct.pack("<i", len(value))]
        for vinyl in value:
            if not isinstance(vinyl, dict):
                parts.append(bytes([0]))
                continue
            vfc = int(vinyl.get('_fieldCount', 6) or 6)
            parts.append(bytes([vfc & 0xFF]))
            if vfc == 0:
                continue
            for fn in ('position', 'scaleRotation', 'iconPosition'):
                vec = vinyl.get(fn) if isinstance(vinyl.get(fn), dict) else {}
                x = float(vec.get('x') or 0)
                y = float(vec.get('y') or 0)
                z = float(vec.get('z') or 0)
                parts.append(struct.pack("<fff", x, y, z))
            parts.append(cpm1_write_memorypack_string(str(vinyl.get('text', '') or '')))
            parts.append(struct.pack("<I", int(vinyl.get('color', 0) or 0) & 0xFFFFFFFF))
            try:
                pd = int(vinyl.get('packedData', 0) or 0)
            except:
                pd = 0
            parts.append(struct.pack("<q", pd))
        return b"".join(parts)
    return b""

def cpm1_encode_car_to_memorypack(car):
    fields = []
    for fid, name in CPM_FIELD_NAMES.items():
        if name in car and car[name] is not None:
            fields.append((fid, name, car[name]))
    fields.sort(key=lambda x: x[0])
    parts = [struct.pack("<i", len(fields))]
    for fid, name, value in fields:
        parts.append(struct.pack("<h", fid))
        if name in ('CarID', 'dataVersion', 'flagID'):
            try:
                iv = int(value)
            except:
                iv = 0
            parts.append(cpm1_write_memorypack_string(str(iv)))
        elif isinstance(value, str) and cpm1_looks_like_base64(value):
            parts.append(cpm1_write_memorypack_string(value))
        else:
            binv = cpm1_encode_field_value_binary(name, value)
            try:
                compressed = brotli.compress(binv, quality=4)
            except:
                compressed = brotli.compress(binv)
            parts.append(cpm1_write_memorypack_string(base64.b64encode(compressed).decode('ascii')))
    return b"".join(parts)

def cpm1_encrypt_car_for_save(car, uid):
    clean = cpm1_sanitize_car_for_encoding(car)
    key = make_xor_key(uid)
    mp = cpm1_encode_car_to_memorypack(clean)
    compressed = brotli.compress(mp, quality=4)
    encrypted = xor_bytes(compressed, key)
    return "__ver1__" + base64.b64encode(encrypted).decode('ascii')

def cpm1_fetch_cars_v2(token):
    try:
        resp = http_session.post(CPM_CARS_FETCH_URL, json={"data": ""},
                                 headers=cpm1_ios_headers(token), timeout=20)
        if resp.status_code < 200 or resp.status_code >= 300:
            return {"success": False, "error": f"HTTP {resp.status_code}",
                    "status": resp.status_code, "cars": []}
        parsed = resp.json() if resp.text else {}
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except:
                pass
        raw_result = None
        if isinstance(parsed, dict):
            if parsed.get("result") is not None:
                raw_result = parsed["result"]
            elif isinstance(parsed.get("data"), dict) and parsed["data"].get("result") is not None:
                raw_result = parsed["data"]["result"]
        if raw_result is None:
            return {"success": True, "cars": []}
        cars = []
        try:
            cars = json.loads(raw_result)
        except:
            m = re.search(r'\[\s*\{[\s\S]*\}\s*\]', str(raw_result))
            if m:
                try:
                    cars = json.loads(m.group(0))
                except:
                    pass
        return {"success": True, "cars": cars if isinstance(cars, list) else []}
    except Exception as e:
        return {"success": False, "error": str(e), "cars": []}

def cpm1_save_car_encrypted_v2(token, car, uid, retries=2):
    try:
        payload = cpm1_encrypt_car_for_save(car, uid)
    except Exception as e:
        return {"success": False, "error": f"encode:{str(e)[:80]}"}
    headers = cpm1_ios_headers(token)
    last = {"success": False, "error": "max_retries"}
    for attempt in range(1, retries + 1):
        try:
            resp = http_session.post(CPM_CARS_SAVE_URL, json={"data": payload},
                                     headers=headers, timeout=30)
            if resp.status_code < 300:
                return {"success": True, "status": resp.status_code, "data": resp.text}
            if resp.status_code in (401, 403):
                return {"success": False, "auth": True, "status": resp.status_code,
                        "error": f"HTTP {resp.status_code}"}
            last = {"success": False, "status": resp.status_code, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            last = {"success": False, "error": str(e)[:120]}
        if attempt < retries:
            time.sleep(min(1 * attempt, 3))
    return last

def cpm1_save_car_status(auth, fuid, car_entries):
    sparse = cpm1_entries_to_sparse(car_entries)
    gen_ids = ['' if v is None else str(v) for v in sparse["carGeneratedIDs"]]
    statuses = [0 if v is None else int(v) for v in sparse["carStatus"]]
    record = {"carIDnStatus": {"carGeneratedIDs": gen_ids, "carStatus": statuses}}
    try:
        ok, msg = nuker._send(auth, record, fuid, original=None, force_fields={"carIDnStatus"})
        return {"success": bool(ok), "message": msg}
    except Exception as e:
        return {"success": False, "message": str(e)[:120]}

def cpm1_verify_clone_v2(token, expected_car_ids):
    r = cpm1_fetch_cars_v2(token)
    if not r.get("success"):
        return {"success": False, "error": r.get("error"),
                "present": [], "missing": list(expected_car_ids)}
    present = set()
    for c in r.get("cars", []):
        try:
            present.add(int(c.get("CarID")))
        except:
            pass
    missing = [cid for cid in expected_car_ids if cid not in present]
    return {"success": len(missing) == 0, "present": list(present), "missing": missing}

def cpm1_clone_cars_core(tgt_email, tgt_password, src_cars_to_clone, src_uid=None,
                         tgt_token=None, tgt_uid=None, existing_tgt_cars=None,
                         progress_cb=None, verify=True):
    result = {
        "success": False, "ok": 0, "fail": 0, "total": len(src_cars_to_clone),
        "stage": "INIT", "failed": [], "verified": None,
        "tgt_token": tgt_token, "tgt_uid": tgt_uid
    }
    if not tgt_token or not tgt_uid:
        lr = nuker.login(tgt_email, tgt_password)
        if not lr.get("ok"):
            result["stage"] = "LOGIN"
            result["error"] = lr.get("message", "login_fail")
            return result
        tgt_token, tgt_uid = lr["auth"], lr["firebase_uid"]
    if existing_tgt_cars is None:
        r = cpm1_fetch_cars_v2(tgt_token)
        if not r.get("success") and r.get("status") in (401, 403):
            lr = nuker.login(tgt_email, tgt_password)
            if lr.get("ok"):
                tgt_token, tgt_uid = lr["auth"], lr["firebase_uid"]
                r = cpm1_fetch_cars_v2(tgt_token)
        if not r.get("success"):
            result["stage"] = "FETCH_TGT"
            result["error"] = r.get("error", "fetch_fail")
            return result
        existing_tgt_cars = r["cars"]
    result["tgt_token"] = tgt_token
    result["tgt_uid"] = tgt_uid
    rec = nuker.get_record(tgt_uid, tgt_email) or {}
    cpm_id = cpm1_resolve_cpm_id(rec)
    result["cpm_id"] = cpm_id
    prepared = []
    for car in src_cars_to_clone:
        try:
            c2 = json.loads(json.dumps(car))
            if src_uid:
                c2 = cpm1_replace_uid_in_value(c2, src_uid, tgt_uid)
            prepared.append(cpm1_prepare_car(c2, cpm_id))
        except Exception as e:
            result["failed"].append({"CarID": car.get("CarID"), "stage": "PREPARE",
                                     "error": str(e)[:120]})
    if not prepared:
        result["stage"] = "PREPARE"
        result["error"] = "no_prepared"
        return result
    merged = cpm1_merge_cars_by_id(existing_tgt_cars, prepared)
    entries = cpm1_build_car_entries(merged, cpm_id)
    sr = cpm1_save_car_status(tgt_token, tgt_uid, entries)
    if not sr.get("success"):
        lr = nuker.login(tgt_email, tgt_password)
        if lr.get("ok"):
            tgt_token, tgt_uid = lr["auth"], lr["firebase_uid"]
            result["tgt_token"] = tgt_token
            result["tgt_uid"] = tgt_uid
            sr = cpm1_save_car_status(tgt_token, tgt_uid, entries)
    if not sr.get("success"):
        result["stage"] = "STATUS_SAVE"
        result["error"] = sr.get("message", "status_fail")
        return result
    ok = 0
    total = len(prepared)
    for i, car in enumerate(prepared):
        sr = cpm1_save_car_encrypted_v2(tgt_token, car, tgt_uid, retries=2)
        if not sr.get("success") and sr.get("auth"):
            lr = nuker.login(tgt_email, tgt_password)
            if lr.get("ok"):
                tgt_token, tgt_uid = lr["auth"], lr["firebase_uid"]
                result["tgt_token"] = tgt_token
                result["tgt_uid"] = tgt_uid
                sr = cpm1_save_car_encrypted_v2(tgt_token, car, tgt_uid, retries=2)
        if sr.get("success"):
            ok += 1
        else:
            result["failed"].append({"CarID": car.get("CarID"), "stage": "CAR_SAVE",
                                     "error": sr.get("error", "unknown")})
        if progress_cb:
            try:
                progress_cb(i + 1, total)
            except:
                pass
        time.sleep(0.15)
    result["ok"] = ok
    result["fail"] = total - ok
    result["stage"] = "DONE"
    result["success"] = ok > 0
    if verify:
        try:
            v = cpm1_verify_clone_v2(tgt_token, [c.get("CarID") for c in prepared])
            result["verified"] = v
        except Exception as e:
            result["verified"] = {"success": False, "error": str(e)[:80]}
    return result

# ================================================================
#  BACKGROUND TASKS
# ================================================================
def background_inject_all_cars(chat_id, email, password, msg_id):
    TOKEN_COST = TOKEN_COSTS["unlock_all_cars"]
    try:
        web_uid = get_web_uid(chat_id)
        td = nuker.get_token_data(web_uid)
        tgt_email = (td.get("email") if td else None) or email
        tgt_pass = (td.get("password") if td else None) or password
        try:
            bot.edit_message_text(
                f"{get_premium_emoji('loading_progress')} <b>INJECTING CARS...</b>\n"
                f"Authenticating source...\n\n"
                f"{get_premium_emoji('car_injection')} Vehicles Settings",
                chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
            )
        except:
            pass
        s = nuker.login(*SOURCE_ACCOUNT)
        if not s.get("ok"):
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('cancel_failed_error')} Source account unreachable.\n\n"
                    f"{get_premium_emoji('car_injection')} Vehicles Settings",
                    chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
                )
            except:
                pass
            return
        fr = cpm1_fetch_cars_v2(s["auth"])
        src_cars = fr.get("cars", []) if fr.get("success") else []
        if not src_cars:
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('cancel_failed_error')} No cars fetched.\n\n"
                    f"{get_premium_emoji('car_injection')} Vehicles Settings",
                    chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
                )
            except:
                pass
            return
        last_edit = [0]

        def _prog(cur, tot):
            now = time.time()
            if now - last_edit[0] < 2.5 and cur != tot:
                return
            last_edit[0] = now
            pct = int(cur / max(1, tot) * 100)
            filled = int(pct / 5)
            bar = "█" * filled + "▒" * (20 - filled)
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('loading_progress')} <b>INJECTING CARS...</b>\n"
                    f"<code>{bar}</code> {pct}%\n({cur}/{tot})\n\n"
                    f"{get_premium_emoji('car_injection')} Vehicles Settings",
                    chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
                )
            except:
                pass
        res = cpm1_clone_cars_core(tgt_email, tgt_pass, src_cars, src_uid=s["firebase_uid"],
                                   progress_cb=_prog, verify=True)
        if res.get("ok", 0) > 0:
            deduct_tokens(chat_id, TOKEN_COST)
            v = res.get("verified") or {}
            vline = f"\n{get_premium_emoji('success_preserved')} Verified: {len(v.get('present', []))}" if v else ""
            msg = (
                f"{get_premium_emoji('success_preserved')} <b>CAR INJECTION COMPLETE</b>\n"
                f"Transferred: {res['ok']}/{res['total']}{vline}\n"
                f"🪙 Deducted: {TOKEN_COST} tokens\n"
                f"💎 Balance: {get_user_tokens(chat_id)}\n\n"
                f"{get_premium_emoji('car_injection')} Vehicles Settings"
            )
        else:
            msg = (
                f"{get_premium_emoji('cancel_failed_error')} <b>INJECTION FAILED</b>\n"
                f"Stage: {res.get('stage')}\n"
                f"Error: {html.escape(str(res.get('error',''))[:60])}\n"
                f"(No tokens deducted)\n\n"
                f"{get_premium_emoji('car_injection')} Vehicles Settings"
            )
        try:
            bot.edit_message_text(msg, chat_id, msg_id,
                                  reply_markup=create_premium_keyboard(), parse_mode="HTML")
        except:
            pass
    except Exception as e:
        try:
            bot.edit_message_text(
                f"{get_premium_emoji('cancel_failed_error')} Internal: {html.escape(str(e)[:60])}",
                chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
            )
        except:
            pass

def background_single_clone(chat_id, src_email, src_pass, tgt_email, tgt_pass, msg_id):
    TOKEN_COST = TOKEN_COSTS["clone_single"]
    try:
        if not is_admin(chat_id):
            cur = get_user_tokens(chat_id)
            if cur < TOKEN_COST:
                try:
                    bot.edit_message_text(
                        token_shortage_msg(chat_id, TOKEN_COST, cur) +
                        f"\n\n{get_premium_emoji('premium_hub')} Premium Hub",
                        chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
                    )
                except:
                    pass
                return
        try:
            bot.edit_message_text(
                f"{get_premium_emoji('loading_progress')} <b>CLONING...</b>\n"
                f"{get_premium_emoji('encryption')} Extracting source...\n\n"
                f"{get_premium_emoji('premium_hub')} Premium Hub",
                chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
            )
        except:
            pass
        s = nuker.login(src_email, src_pass)
        if not s.get("ok"):
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('cancel_failed_error')} <b>CLONE FAILED</b>\n"
                    f"Source login failed\n(No tokens deducted)\n\n"
                    f"{get_premium_emoji('premium_hub')} Premium Hub",
                    chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
                )
            except:
                pass
            return
        src_token = s["auth"]
        src_uid = s["firebase_uid"]
        nuker.load(src_uid, force=True)
        src_record = nuker.get_record(src_uid, src_email) or {}
        fr = cpm1_fetch_cars_v2(src_token)
        src_cars = fr.get("cars", []) if fr.get("success") else []
        if not src_cars:
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('cancel_failed_error')} <b>CLONE FAILED</b>\n"
                    f"No source cars\n(No tokens deducted)\n\n"
                    f"{get_premium_emoji('premium_hub')} Premium Hub",
                    chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
                )
            except:
                pass
            return
        t = nuker.login(tgt_email, tgt_pass)
        if not t.get("ok"):
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('cancel_failed_error')} <b>CLONE FAILED</b>\n"
                    f"Target login failed\n(No tokens deducted)\n\n"
                    f"{get_premium_emoji('premium_hub')} Premium Hub",
                    chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
                )
            except:
                pass
            return
        tgt_token = t["auth"]
        tgt_uid = t["firebase_uid"]
        nuker.load(tgt_uid, force=True)
        t_record = nuker.get_record(tgt_uid, tgt_email) or {}
        safe_keys = ['money', 'coin', 'floats', 'integers', 'animations', 'wheels',
                     'personEquipmentsMale', 'personEquipmentsFemale', 'boughtFsos', 'emojiPacks']
        for k in safe_keys:
            if k in src_record:
                t_record[k] = deepcopy(src_record[k])
        t_record['boughtPoliceSirens'] = []
        t_record['boughtPoliceLights'] = []
        safe_keys.extend(['boughtPoliceSirens', 'boughtPoliceLights'])
        try:
            nuker._send(tgt_token, t_record, tgt_uid, original=None, force_fields=set(safe_keys))
        except:
            pass
        last_edit = [0]

        def _prog(cur, tot):
            if tot == 0:
                tot = 1
            now = time.time()
            if now - last_edit[0] < 2.5 and cur != tot:
                return
            last_edit[0] = now
            pct = int(cur / tot * 100)
            filled = int(pct / 5)
            bar = "█" * filled + "▒" * (20 - filled)
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('loading_progress')} <b>CLONING...</b>\n"
                    f"<code>{bar}</code> {pct}%\n({cur}/{tot} Cars)\n\n"
                    f"{get_premium_emoji('premium_hub')} Premium Hub",
                    chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
                )
            except:
                pass
        res = cpm1_clone_cars_core(tgt_email, tgt_pass, src_cars, src_uid=src_uid,
                                   tgt_token=tgt_token, tgt_uid=tgt_uid,
                                   progress_cb=_prog, verify=True)
        if res.get("success"):
            deduct_tokens(chat_id, TOKEN_COST)
            v = res.get("verified") or {}
            vline = f"\n{get_premium_emoji('success_preserved')} Verified: {len(v.get('present', []))}" if v else ""
            fline = ""
            if res.get("failed"):
                lines = [f"• ID {f.get('CarID')} [{f.get('stage')}]: {html.escape(str(f.get('error',''))[:40])}"
                         for f in res["failed"][:10]]
                fline = f"\n{get_premium_emoji('warning')} Failed ({len(res['failed'])}):\n" + "\n".join(lines)
            msg = (
                f"{get_premium_emoji('success_preserved')} <b>CLONE COMPLETE</b>\n"
                f"┣━━━━━━━━━━━━━━━━━━┫\n"
                f"{get_premium_emoji('vehicles_cars_w124')} Cars: {res['ok']}/{res['total']}{vline}{fline}\n"
                f"🪙 Deducted: {TOKEN_COST} tokens\n"
                f"💎 Balance: {get_user_tokens(chat_id)}\n\n"
                f"{get_premium_emoji('premium_hub')} Premium Hub"
            )
        else:
            msg = (
                f"{get_premium_emoji('cancel_failed_error')} <b>CLONE FAILED</b>\n"
                f"┣━━━━━━━━━━━━━━━━━━┫\n"
                f"Stage: {res.get('stage','?')}\n"
                f"{html.escape(str(res.get('error','?'))[:80])}\n"
                f"(No tokens deducted)\n\n"
                f"{get_premium_emoji('premium_hub')} Premium Hub"
            )
        try:
            bot.edit_message_text(msg, chat_id, msg_id,
                                  reply_markup=create_premium_keyboard(), parse_mode="HTML")
        except:
            pass
    except Exception as e:
        try:
            bot.edit_message_text(
                f"{get_premium_emoji('cancel_failed_error')} Internal: {html.escape(str(e)[:80])}\n\n"
                f"{get_premium_emoji('premium_hub')} Premium Hub",
                chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
            )
        except:
            pass

def clone_task(src_record, src_cars, i, res_list, source_token, source_uid, progress_cb=None):
    t_email = f"markmwehehehe{random.randint(10000,99999)}@gmail.com"
    t_pass = f"markwhehehehe{random.randint(10000,99999)}"
    reg_ok = False
    for _ in range(3):
        try:
            r = http_session.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FK}",
                json={"email": t_email, "password": t_pass, "returnSecureToken": True},
                timeout=15
            )
            if "idToken" in r.text:
                reg_ok = True
                break
        except:
            pass
        time.sleep(0.5)
    if progress_cb:
        progress_cb(i, "registering")
    if not reg_ok:
        res_list.append(
            f"{get_premium_emoji('warning')} ID {i+1} FAILED: signup\n"
            f"{get_premium_emoji('email')} <code>{t_email}</code>\n"
            f"{get_premium_emoji('password')} <code>{t_pass}</code>"
        )
        if progress_cb:
            progress_cb(i, "done")
        return t_email, t_pass
    blank = {
        "Name": "Player", "money": 25000, "coin": 0,
        "localID": str(random.randint(1000000,9999999)).zfill(8),
        "allData": '{"cars":[]}', "floats": [], "integers": []
    }
    try:
        lr = nuker.login(t_email, t_pass)
        if lr.get("ok"):
            nuker._send(lr["auth"], blank, lr["firebase_uid"])
    except:
        pass
    cres = cpm1_clone_cars_core(t_email, t_pass, src_cars, src_uid=source_uid, verify=False)
    if cres.get("ok", 0) > 0:
        res_list.append(
            f"{get_premium_emoji('success_preserved')} ID {i+1} ({cres['ok']}/{cres['total']} cars)\n"
            f"{get_premium_emoji('email')} <code>{t_email}</code>\n"
            f"{get_premium_emoji('password')} <code>{t_pass}</code>"
        )
    else:
        res_list.append(
            f"{get_premium_emoji('warning')} ID {i+1} FAILED [{cres.get('stage')}]\n"
            f"{get_premium_emoji('email')} <code>{t_email}</code>\n"
            f"{get_premium_emoji('password')} <code>{t_pass}</code>"
        )
    if progress_cb:
        progress_cb(i, "done")
    return t_email, t_pass

def background_bulk_clone(chat_id, src_email, src_pass, count, msg_id, is_admin_user=False):
    if count <= 5:
        TOKEN_COST = TOKEN_COSTS["bulk_1_5"]
    else:
        TOKEN_COST = TOKEN_COSTS["bulk_6_10"]
    try:
        if not is_admin(chat_id):
            cur = get_user_tokens(chat_id)
            if cur < TOKEN_COST:
                try:
                    bot.edit_message_text(
                        token_shortage_msg(chat_id, TOKEN_COST, cur) +
                        f"\n📦 Bulk {count} accounts\n\n"
                        f"{get_premium_emoji('premium_hub')} Premium Hub",
                        chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
                    )
                except:
                    pass
                return
        try:
            bot.edit_message_text(
                f"{get_premium_emoji('bulk_clone')} <b>BULK CLONE STARTED</b>\n"
                f"┣━━━━━━━━━━━━━━━━━━┫\n"
                f"{get_premium_emoji('encryption')} Extracting Source Profile...\n\n"
                f"{get_premium_emoji('premium_hub')} Premium Hub",
                chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
            )
        except:
            pass
        s = nuker.login(src_email, src_pass)
        if not s.get("ok"):
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('cancel_failed_error')} <b>BULK CLONE FAILED</b>\n"
                    f"Source login failed\n(No tokens deducted)\n\n"
                    f"{get_premium_emoji('premium_hub')} Premium Hub",
                    chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
                )
            except:
                pass
            return
        src_token = s["auth"]
        src_uid = s["firebase_uid"]
        nuker.load(src_uid, force=True)
        src_record = nuker.get_record(src_uid, src_email) or {}
        fr = cpm1_fetch_cars_v2(src_token)
        cars = fr.get("cars", []) if fr.get("success") else []
        if not cars:
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('cancel_failed_error')} <b>BULK CLONE FAILED</b>\n"
                    f"No cars found\n(No tokens deducted)\n\n"
                    f"{get_premium_emoji('premium_hub')} Premium Hub",
                    chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML"
                )
            except:
                pass
            return
        res_list = []
        account_creds = []
        total_accounts = count
        done_accounts = [0]

        def update_bulk_progress(acc_idx, status):
            if status == "done":
                done_accounts[0] += 1
            pct = int(done_accounts[0] / max(1, total_accounts) * 100)
            progress_text = (
                f"{get_premium_emoji('loading_progress')} <b>BULK CLONE PROGRESS</b>\n"
                f"┣━━━━━━━━━━━━━━━━━━┫\n"
                f"{get_premium_emoji('create_account')} Accounts: {done_accounts[0]}/{total_accounts} ({pct}%)\n\n"
                f"{get_premium_emoji('premium_hub')} Premium Hub"
            )
            try:
                bot.edit_message_text(progress_text, chat_id, msg_id,
                                      reply_markup=create_premium_keyboard(), parse_mode="HTML")
            except:
                pass
        max_threads = min(count, 5)
        threads = []
        results_lock = threading.Lock()

        def worker(i):
            email, pw = clone_task(src_record, cars, i, res_list, src_token, src_uid,
                                   progress_cb=update_bulk_progress)
            with results_lock:
                account_creds.append((email, pw))

        for i in range(count):
            while len([t for t in threads if t.is_alive()]) >= max_threads:
                time.sleep(1)
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        successful = sum(1 for r in res_list if "✅" in r or "success_preserved" in r)
        if successful > 0 and not is_admin(chat_id):
            deduct_tokens(chat_id, TOKEN_COST)
        accounts_file = f"accounts_{random.randint(100,999)}.txt"
        try:
            with open(accounts_file, "w") as f:
                f.write("email:password\n")
                for email, pw in account_creds:
                    f.write(f"{email}:{pw}\n")
        except:
            pass
        if successful > 0:
            token_line = f"\n🪙 Deducted: {TOKEN_COST} tokens\n💎 Balance: {get_user_tokens(chat_id)}"
        else:
            token_line = "\n(No tokens deducted)"
        final_text = (
            f"{get_premium_emoji('bulk_clone')} <b>BULK CLONE REPORT</b>\n"
            f"┣━━━━━━━━━━━━━━━━━━┫\n\n" +
            "\n\n".join(sorted(res_list)) +
            f"{token_line}\n\n"
            f"{get_premium_emoji('source_account')} Saved: {accounts_file}\n\n"
            f"{get_premium_emoji('premium_hub')} Premium Hub"
        )
        try:
            bot.edit_message_text(final_text, chat_id, msg_id,
                                  reply_markup=create_premium_keyboard(), parse_mode="HTML")
            if os.path.exists(accounts_file):
                try:
                    with open(accounts_file, "rb") as f:
                        bot.send_document(chat_id, f)
                except:
                    pass
        except:
            pass
    except Exception as e:
        pass

def inject_car_by_id_thread(chat_id, msg_id, web_uid, car_id, car_name=""):
    TOKEN_COST = TOKEN_COSTS["unlock_by_id"]
    try:
        if not is_admin(chat_id):
            cur = get_user_tokens(chat_id)
            if cur < TOKEN_COST:
                try:
                    bot.edit_message_text(
                        token_shortage_msg(chat_id, TOKEN_COST, cur) +
                        f"\n\n{get_premium_emoji('unlocks_login')} Unlocks",
                        chat_id, msg_id, reply_markup=create_unlocks_keyboard(), parse_mode="HTML"
                    )
                except:
                    pass
                return
        try:
            bot.edit_message_text(
                f"{get_premium_emoji('loading_progress')} <b>UNLOCKING CAR ID {car_id}...</b>",
                chat_id, msg_id, reply_markup=create_unlocks_keyboard(), parse_mode="HTML"
            )
        except:
            pass
        td = nuker.get_token_data(web_uid)
        if not td:
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('cancel_failed_error')} Login required.\n\n"
                    f"{get_premium_emoji('unlocks_login')} Unlocks",
                    chat_id, msg_id, reply_markup=create_unlocks_keyboard(), parse_mode="HTML"
                )
            except:
                pass
            return
        tgt_email = td.get("email")
        tgt_pass = td.get("password")
        if not tgt_email or not tgt_pass:
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('cancel_failed_error')} Auth missing.\n\n"
                    f"{get_premium_emoji('unlocks_login')} Unlocks",
                    chat_id, msg_id, reply_markup=create_unlocks_keyboard(), parse_mode="HTML"
                )
            except:
                pass
            return
        s = nuker.login(*SOURCE_ACCOUNT)
        if not s.get("ok"):
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('cancel_failed_error')} Source unavailable.\n\n"
                    f"{get_premium_emoji('unlocks_login')} Unlocks",
                    chat_id, msg_id, reply_markup=create_unlocks_keyboard(), parse_mode="HTML"
                )
            except:
                pass
            return
        fr = cpm1_fetch_cars_v2(s["auth"])
        src_cars = fr.get("cars", []) if fr.get("success") else []
        target_car = None
        for c in src_cars:
            try:
                if int(c.get("CarID", 0)) == int(car_id):
                    target_car = c
                    break
            except:
                pass
        if not target_car:
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('cancel_failed_error')} Car ID {car_id} not in source.\n\n"
                    f"{get_premium_emoji('unlocks_login')} Unlocks",
                    chat_id, msg_id, reply_markup=create_unlocks_keyboard(), parse_mode="HTML"
                )
            except:
                pass
            return
        res = cpm1_clone_cars_core(tgt_email, tgt_pass, [target_car],
                                   src_uid=s["firebase_uid"], verify=False)
        if res.get("ok", 0) > 0:
            deduct_tokens(chat_id, TOKEN_COST)
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('success_preserved')} <b>CAR ID {car_id} {car_name} UNLOCKED</b>\n"
                    f"🪙 Deducted: {TOKEN_COST} tokens\n"
                    f"💎 Balance: {get_user_tokens(chat_id)}\n\n"
                    f"{get_premium_emoji('unlocks_login')} Unlocks",
                    chat_id, msg_id, reply_markup=create_unlocks_keyboard(), parse_mode="HTML"
                )
            except:
                pass
        else:
            err = html.escape(str(res.get("error", "unknown"))[:60])
            try:
                bot.edit_message_text(
                    f"{get_premium_emoji('cancel_failed_error')} Failed: {err}\n"
                    f"(No tokens deducted)\n\n"
                    f"{get_premium_emoji('unlocks_login')} Unlocks",
                    chat_id, msg_id, reply_markup=create_unlocks_keyboard(), parse_mode="HTML"
                )
            except:
                pass
    except:
        pass

# ================================================================
#  SESSION / STATE MANAGEMENT
# ================================================================
user_sessions, user_states = {}, {}

def get_web_uid(telegram_id):
    return int(str(telegram_id)[:12])

def get_role_badge(chat_id):
    if is_admin(chat_id):
        return f"{get_premium_emoji('overseer_panel')} Admin"
    if has_premium_access(chat_id):
        return f"{get_premium_emoji('premium_hub')} Premium User"
    if has_active_subscription(chat_id):
        return f"{get_premium_emoji('free_user')} Subscribed"
    return f"{get_premium_emoji('free_user')} Free User"

# ================================================================
#  KEYBOARDS
# ================================================================
def cancel_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(get_btn("cancel_failed_error", "Cancel", callback_data="menu_main"))
    return markup

def create_dashboard_keyboard(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(get_btn("account_info", "Account", callback_data="menu_account"),
               get_btn("economy_profile", "Economy", callback_data="menu_economy"))
    markup.row(get_btn("unlocks_login", "Unlocks", callback_data="menu_unlocks"))
    if has_premium_access(chat_id) or is_admin(chat_id):
        markup.row(get_btn("premium_hub", "Premium", callback_data="menu_premium"))
    markup.row(get_btn("coin", "Buy Tokens", callback_data="tok_stars_menu"),
               get_btn("info", "Info", callback_data="show_info"))
    markup.row(get_btn("premium_hub", "Subscribe", callback_data="subscribe_menu"),
               get_btn("stats_telemetry", "My Profile", callback_data="show_profile"))
    if is_admin(chat_id):
        markup.row(get_btn("overseer_panel", "OVERSEER PANEL", callback_data="admin_panel"))
    markup.row(get_btn("refresh", "Refresh", callback_data="refresh_account"),
               get_btn("back", "Logout", callback_data="logout"))
    return markup

def create_account_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(get_btn("info", "Info", callback_data="acc_info"),
               get_btn("set_name", "Set Name", callback_data="acc_name"))
    markup.row(get_btn("set_id", "Set ID", callback_data="acc_id"),
               get_btn("email", "Change Email", callback_data="acc_email"))
    markup.row(get_btn("password", "Change Pass", callback_data="acc_pass"))
    markup.add(get_btn("back", "Back", callback_data="menu_main"))
    return markup

def create_economy_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(get_btn("money", "Money 50M", callback_data="eco_money_max"),
               get_btn("coin", "Coins 500K", callback_data="eco_coins_max"))
    markup.row(get_btn("money", "Custom Money", callback_data="eco_money_cust"),
               get_btn("coin", "Custom Coins", callback_data="eco_coins_cust"))
    markup.row(get_btn("premium_hub", "King Rank", callback_data="eco_king"))
    markup.add(get_btn("back", "Back", callback_data="menu_main"))
    return markup

def create_unlocks_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(get_btn("vehicles_cars_w124", "Unlock W124 (ID 258)", callback_data="unl_w124"))
    markup.row(get_btn("unlock_camry_id", "Unlock Camry (ID 264)", callback_data="unl_camry"))
    markup.row(get_btn("w16_engine", "W16 Engine (20🪙)", callback_data="unl_w16"),
               get_btn("smoke", "Smoke (20🪙)", callback_data="unl_smoke"))
    markup.row(get_btn("max_fuel", "Max Fuel (20🪙)", callback_data="unl_fuel"),
               get_btn("no_damage", "No Damage (20🪙)", callback_data="unl_damage"))
    markup.row(get_btn("horns", "Horns (20🪙)", callback_data="unl_horns"),
               get_btn("animations", "Animations (20🪙)", callback_data="unl_anim"))
    markup.row(get_btn("all_houses", "All Houses (20🪙)", callback_data="unl_houses"),
               get_btn("wheels", "Wheels (20🪙)", callback_data="unl_wheels"))
    markup.row(get_btn("complete_all_levels", "Complete All Levels (20🪙)", callback_data="unl_levels"))
    markup.row(get_btn("all_clothes", "All Clothes (20🪙)", callback_data="unl_clothes"))
    markup.row(get_btn("ultimate_glitch", "ULTIMATE GLITCH (20🪙)", callback_data="unl_ultimate"))
    markup.add(get_btn("back", "Back", callback_data="menu_main"))
    return markup

def create_premium_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(get_btn("car_injection", "Unlock All Cars (75🪙)", callback_data="veh_unlock_all"),
               get_btn("vehicles_cars_w124", "Unlock By ID (30🪙)", callback_data="veh_unlock_single"))
    markup.row(get_btn("w16_engine", "Fix Account (20🪙)", callback_data="veh_fix"))
    markup.row(get_btn("group_unlock", "Clone Account (90🪙)", callback_data="prem_clone"))
    markup.row(get_btn("bulk_clone", "Bulk Clone (120-150🪙)", callback_data="prem_bulk_clone"))
    markup.add(get_btn("back", "Back", callback_data="menu_main"))
    return markup

def create_admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(get_btn("add_admin", "Add Admin", callback_data="admin_add_admin"),
               get_btn("remove_admin", "Remove Admin", callback_data="admin_rem_admin"))
    markup.row(get_btn("group_unlock", "View Admins", callback_data="admin_view_admins"))
    markup.row(get_btn("success_preserved", "Add Premium", callback_data="admin_add_prem"),
               get_btn("cancel_failed_error", "Revoke Premium", callback_data="admin_revoke"))
    markup.row(get_btn("stats_telemetry", "Stats", callback_data="admin_stats"),
               get_btn("broadcast_announcement", "Broadcast", callback_data="admin_broadcast"))
    markup.row(get_btn("bulk_clone", "Bulk Clone", callback_data="admin_bulk_clone"))
    markup.add(get_btn("back", "Back to Terminal", callback_data="menu_main"))
    return markup

def create_subscription_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(get_btn("premium_hub", "⭐ Pay with Stars", callback_data="sub_stars"))
    markup.row(get_btn("money", "💵 Pay with Money", callback_data="sub_money"))
    markup.add(get_btn("back", "Back", callback_data="menu_main"))
    return markup

def create_stars_plans_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.row(get_btn("free_user", "50⭐ = 1 Day (No Premium)", callback_data="stars_50"))
    markup.row(get_btn("premium_hub", "200⭐ = 1 Week + Premium", callback_data="stars_200"))
    markup.row(get_btn("premium_hub", "350⭐ = 1 Month + Premium", callback_data="stars_350"))
    markup.row(get_btn("ultimate_glitch", "550⭐ = Lifetime + Premium", callback_data="stars_550"))
    markup.add(get_btn("back", "Back", callback_data="subscribe_menu"))
    return markup

def create_money_plans_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.row(get_btn("free_user", "$2 (₱124) = 1.5 Days", callback_data="money_2"))
    markup.row(get_btn("free_user", "$4 (₱248) = 2.5 Days", callback_data="money_4"))
    markup.row(get_btn("premium_hub", "$6 (₱372) = 1 Week (2D Prem)", callback_data="money_6"))
    markup.row(get_btn("premium_hub", "$8 (₱496) = 2 Weeks (4D Prem)", callback_data="money_8"))
    markup.row(get_btn("premium_hub", "$10 (₱620) = 1 Month (3W Prem)", callback_data="money_10"))
    markup.row(get_btn("ultimate_glitch", "$30 (₱1,860) = Lifetime Prem", callback_data="money_30"))
    markup.add(get_btn("back", "Back", callback_data="subscribe_menu"))
    return markup

def create_token_packages_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.row(get_btn("coin", "19⭐ = 100 Tokens", callback_data="tok_s_19"))
    markup.row(get_btn("coin", "38⭐ = 150 Tokens", callback_data="tok_s_38"))
    markup.row(get_btn("coin", "75⭐ = 200 Tokens 👑", callback_data="tok_s_75"))
    markup.row(get_btn("coin", "113⭐ = 250 Tokens 👑", callback_data="tok_s_113"))
    markup.row(get_btn("coin", "150⭐ = 300 Tokens 👑", callback_data="tok_s_150"))
    markup.add(get_btn("back", "Back", callback_data="buytokens_menu"))
    return markup

def create_token_money_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.row(get_btn("coin", "$1.50 (₱93) = 150 Tokens", callback_data="tok_m_1.5"))
    markup.row(get_btn("coin", "$3 (₱186) = 200 Tokens 👑", callback_data="tok_m_3"))
    markup.row(get_btn("coin", "$4.50 (₱279) = 250 Tokens 👑", callback_data="tok_m_4.5"))
    markup.row(get_btn("coin", "$6 (₱372) = 300 Tokens 👑", callback_data="tok_m_6"))
    markup.row(get_btn("coin", "$7.50 (₱465) = 350 Tokens 👑", callback_data="tok_m_7.5"))
    markup.row(get_btn("coin", "$9 (₱558) = 400 Tokens 👑", callback_data="tok_m_9"))
    markup.row(get_btn("coin", "$19 (₱1,178) = Custom", callback_data="tok_m_custom"))
    markup.add(get_btn("back", "Back", callback_data="buytokens_menu"))
    return markup

# ================================================================
#  DASHBOARD
# ================================================================
def safe_send_dashboard(chat_id, custom_top_msg=None, force_refresh=False,
                       is_callback=False, message_id=None):
    try:
        session_data = user_sessions.get(chat_id, {})
        is_logged_in = session_data.get('cpm_logged_in', False)
        if not is_logged_in:
            msg = f"{get_premium_emoji('not_logged_in')} <b>Not logged in</b> — tap Login or Register to get started."
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.row(
                get_btn("unlocks_login", "Login", callback_data="init_login"),
                get_btn("create_account", "Register", callback_data="init_register")
            )
            markup.row(get_btn("info", "Info", callback_data="show_info"))
            if is_callback and message_id:
                try:
                    bot.edit_message_text(msg, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
                except:
                    bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="HTML")
            return
        web_uid = get_web_uid(chat_id)
        info = nuker.get_account_info(web_uid, force_refresh=force_refresh)
        if not info.get("ok"):
            user_sessions[chat_id]['cpm_logged_in'] = False
            msg = f"{get_premium_emoji('cancel_failed_error')} <b>Session Expired.</b> Please Login again."
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.row(
                get_btn("unlocks_login", "Login", callback_data="init_login"),
                get_btn("create_account", "Register", callback_data="init_register")
            )
            if is_callback and message_id:
                try:
                    bot.edit_message_text(msg, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
                except:
                    bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="HTML")
            else:
                bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="HTML")
            return
        role = get_role_badge(chat_id)
        name = html.escape(clean_str(info.get('name', 'Unknown')))
        tag = html.escape(clean_str(info.get('localID', 'Unknown')))
        email = html.escape(clean_str(info.get('email', 'Unknown')))
        cars_owned = info.get('cars', 0)
        tokens = get_user_tokens(chat_id)
        try:
            money_val = int(info.get('money') or 0)
        except:
            money_val = 0
        try:
            coin_val = int(info.get('coin') or 0)
        except:
            coin_val = 0
        text = (
            f"{get_premium_emoji('success_preserved')} <b>Logged in!</b>\n\n"
            f"{get_premium_emoji('account_info')} <b>Your Information</b>\n───────────────\n"
            f"{get_premium_emoji('access_granted')} Status: Access granted\n"
            f"{get_premium_emoji('set_id')} Telegram ID: <code>{chat_id}</code>\n"
            f"{get_premium_emoji('coin')} Tokens: <code>{tokens}</code>\n"
            f"{get_premium_emoji('role')} Role: {role}\n\n"
            f"{get_premium_emoji('cpm_dashboard')} <b>CPM DASHBOARD</b>\n───────────────\n"
            f"{get_premium_emoji('account_info')} Name: {name}\n"
            f"{get_premium_emoji('set_id')} ID: {tag}\n"
            f"{get_premium_emoji('money')} Money: {money_val:,}\n"
            f"{get_premium_emoji('coin')} Coins: {coin_val:,}\n"
            f"{get_premium_emoji('vehicles_cars_w124')} Cars owned: {cars_owned}\n"
            f"{get_premium_emoji('email')} {email}\n\n"
            f"{get_premium_emoji('choose_section')} Choose a section:"
        )
        if custom_top_msg:
            text = f"{get_premium_emoji('info')} <b>{html.escape(custom_top_msg)}</b>\n\n{text}"
        markup = create_dashboard_keyboard(chat_id)
        if is_callback and message_id:
            try:
                bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
            except:
                bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        pass

# ================================================================
#  WARNING / UNAUTHORIZED
# ================================================================
def warn_unauthorized_cpm1(chat_id, command_name, username=None):
    warnings_count = add_warning(chat_id)
    remaining = MAX_WARNINGS - warnings_count
    if warnings_count >= MAX_WARNINGS:
        msg = (
            f"{get_premium_emoji('cancel_failed_error')} <b>BANNED</b>\n\n"
            f"You have been banned after {MAX_WARNINGS} warnings.\n"
            f"Contact: {ADMIN_USERNAME}"
        )
        try:
            bot.send_message(ADMIN_ID,
                f"{get_premium_emoji('cancel_failed_error')} <b>USER AUTO-BANNED</b>\n"
                f"👤 @{username or 'Unknown'}\n"
                f"🆔 <code>{chat_id}</code>\n"
                f"Command: <code>{command_name}</code>",
                parse_mode="HTML")
        except:
            pass
    else:
        msg = (
            f"{get_premium_emoji('warning')} <b>WARNING {warnings_count}/{MAX_WARNINGS}</b>\n\n"
            f"You tried to use admin command: <code>{command_name}</code>\n"
            f"This is NOT allowed.\n\n"
            f"<b>{remaining} warning(s) remaining</b> before permanent ban."
        )
        try:
            bot.send_message(ADMIN_ID,
                f"{get_premium_emoji('warning')} <b>Unauthorized Command</b>\n"
                f"👤 @{username or 'Unknown'}\n"
                f"🆔 <code>{chat_id}</code>\n"
                f"Command: <code>{command_name}</code>\n"
                f"Warning: {warnings_count}/{MAX_WARNINGS}",
                parse_mode="HTML")
        except:
            pass
    try:
        bot.send_message(chat_id, msg, parse_mode="HTML")
    except:
        pass

# ================================================================
#  COMMAND HANDLERS
# ================================================================
@bot.message_handler(commands=['start', 'menu'])
def start(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        if chat_id in user_states:
            del user_states[chat_id]

        # ⚠️ BAN CHECK
        if is_blocked_by_ban(chat_id):
            send_ban_message(chat_id)
            return

        track_user(chat_id, message.from_user.username)
        if chat_id not in user_sessions:
            user_sessions[chat_id] = {'cpm_logged_in': False}
        elif 'cpm_logged_in' not in user_sessions[chat_id]:
            user_sessions[chat_id]['cpm_logged_in'] = False
        bot.send_message(
            chat_id,
            f"{get_premium_emoji('terminal_hybrid')} <b>MARKCPM1TOOLS TERMINAL</b> {get_premium_emoji('terminal_hybrid')}",
            reply_markup=types.ReplyKeyboardRemove(), parse_mode="HTML"
        )
        safe_send_dashboard(chat_id, force_refresh=False, is_callback=False)
    except:
        pass

@bot.message_handler(commands=['admin'])
def admin_command(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        if chat_id in user_states:
            del user_states[chat_id]

        # ⚠️ BAN CHECK
        if is_blocked_by_ban(chat_id):
            send_ban_message(chat_id)
            return

        if not is_admin(chat_id):
            warn_unauthorized_cpm1(chat_id, "/admin", message.from_user.username)
            return
        track_user(chat_id, message.from_user.username)
        bot.send_message(
            chat_id,
            f"{get_premium_emoji('overseer_panel')} <b>OVERSEER TERMINAL</b>",
            reply_markup=create_admin_keyboard(), parse_mode="HTML"
        )
    except:
        pass

@bot.message_handler(commands=['subscribe'])
def subscribe_command(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        if chat_id in user_states:
            del user_states[chat_id]

        if is_blocked_by_ban(chat_id):
            send_ban_message(chat_id)
            return

        track_user(chat_id, message.from_user.username)
        msg = (
            f"{get_premium_emoji('premium_hub')} <b>SUBSCRIPTION PLANS</b>\n"
            "━━━━━━━━━━━━━━━━\n"
            f"{get_premium_emoji('premium_hub')} <b>Premium Features:</b>\n"
            "• Unlock any car\n"
            "• Create single clone accounts (unlimited)\n"
            "• Create bulk clone accounts (up to 10 at a time)\n\n"
            f"{get_premium_emoji('warning')} <b>Note:</b>\n"
            "1 Day subscription has <b>NO premium access</b>.\n"
            "1 Week onwards includes premium features.\n\n"
            "Choose payment method:"
        )
        bot.send_message(chat_id, msg, reply_markup=create_subscription_keyboard(), parse_mode="HTML")
    except:
        pass

@bot.message_handler(commands=['buytokens'])
def buytokens_command(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass

        if is_blocked_by_ban(chat_id):
            send_ban_message(chat_id)
            return

        track_user(chat_id, message.from_user.username)
        current = get_user_tokens(chat_id)
        msg = (
            f"{get_premium_emoji('coin')} <b>BUY TOKENS</b> (25% OFF)\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🪙 Your Tokens: <code>{current}</code>\n\n"
            f"<b>Token Feature Costs:</b>\n"
            f"• Unlock by ID: 30 tokens\n"
            f"• Unlock All Cars: 75 tokens\n"
            f"• Clone Account: 90 tokens\n"
            f"• Bulk Clone (1-5): 120 tokens\n"
            f"• Bulk Clone (6-10): 150 tokens\n"
            f"• Other features: 20 tokens\n\n"
            f"👑 Buy 200+ tokens to unlock premium!\n\n"
            f"Choose payment method:"
        )
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(get_btn("premium_hub", "⭐ Buy with Stars", callback_data="tok_stars_menu"))
        keyboard.add(get_btn("money", "💵 Buy with Money", callback_data="tok_money_menu"))
        keyboard.add(get_btn("back", "Back", callback_data="menu_main"))
        bot.send_message(chat_id, msg, reply_markup=keyboard, parse_mode="HTML")
    except:
        pass

@bot.message_handler(commands=['info'])
def info_command(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass

        if is_blocked_by_ban(chat_id):
            send_ban_message(chat_id)
            return

        show_info(chat_id)
    except:
        pass

def show_info(chat_id, msg_id=None):
    msg = (
        f"{get_premium_emoji('info')} <b>MARK CPM1 TOOLS — INFO</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚡ <b>FEATURES</b>\n"
        f"├ Unlock cars (by ID or all)\n"
        f"├ Clone account (single)\n"
        f"├ Bulk clone (up to 10)\n"
        f"├ Money & coin modification\n"
        f"├ W16 Engine · Horns · No Damage\n"
        f"├ Animations · Wheels · Houses\n"
        f"├ Complete All Levels · Max Rank\n"
        f"└ All Clothes\n\n"
        f"👑 <b>PREMIUM ACCESS</b>\n"
        f"├ Unlock ANY car\n"
        f"├ Unlimited single clones\n"
        f"└ Bulk clone (up to 10 at once)\n\n"
        f"🪙 <b>TOKEN COSTS</b>\n"
        f"├ Unlock by ID ····· <b>30</b>\n"
        f"├ Unlock All Cars ·· <b>75</b>\n"
        f"├ Clone Account ···· <b>90</b>\n"
        f"├ Bulk Clone (1-5) · <b>120</b>\n"
        f"├ Bulk Clone (6-10) · <b>150</b>\n"
        f"└ Other features ··· <b>20</b>\n\n"
        f"💎 <b>SUBSCRIPTION PLANS</b>\n"
        f"<b>⭐ Stars:</b>\n"
        f"├ 50⭐  → 1 Day (no premium)\n"
        f"├ 200⭐ → 1 Week + Premium\n"
        f"├ 350⭐ → 1 Month + Premium\n"
        f"└ 550⭐ → Lifetime + Premium\n\n"
        f"<b>💵 Money:</b>\n"
        f"├ $2  (₱124)  → 1.5 Days\n"
        f"├ $4  (₱248)  → 2.5 Days\n"
        f"├ $6  (₱372)  → 1 Week (2D Prem)\n"
        f"├ $8  (₱496)  → 2 Weeks (4D Prem)\n"
        f"├ $10 (₱620)  → 1 Month (3W Prem)\n"
        f"└ $30 (₱1,860) → Lifetime Prem\n\n"
        f"👑 <b>TOKEN-BASED PREMIUM</b>\n"
        f"Buy <b>200+ tokens</b> → Premium auto-unlocks.\n"
        f"Ends when balance drops to <b>50 tokens or less</b>.\n\n"
        f"💳 <b>PAYMENT METHODS</b>\n"
        f"📱 PayMaya: <code>09281630511</code>\n"
        f"👤 MARK RYAN MANOGUID\n"
        f"💳 PayPal: <code>markryanmanoguid867@gmail.com</code>\n"
        f"📲 GCash→PayMaya (QR): DM {ADMIN_USERNAME}\n\n"
        f"💬 <b>Support:</b> {ADMIN_USERNAME}"
    )
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(get_btn("back", "Back", callback_data="menu_main"))
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=keyboard, parse_mode="HTML")
        except:
            bot.send_message(chat_id, msg, reply_markup=keyboard, parse_mode="HTML")
    else:
        bot.send_message(chat_id, msg, reply_markup=keyboard, parse_mode="HTML")

@bot.message_handler(commands=['profile'])
def profile_command(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass

        if is_blocked_by_ban(chat_id):
            send_ban_message(chat_id)
            return

        show_profile(chat_id)
    except:
        pass

def show_profile(chat_id, msg_id=None):
    tokens = get_user_tokens(chat_id)
    sub = get_user_subscription(chat_id)
    sub_text = "❌ None"
    prem_text = "❌ None"
    if sub:
        try:
            expiry = datetime.fromisoformat(sub["expiry"])
            days_left = (expiry - datetime.now()).days
            sub_text = f"✅ Active ({days_left} days left)" if days_left < 36500 else "✅ Lifetime"
        except:
            pass
        if sub.get("premium_expiry"):
            try:
                prem_exp = datetime.fromisoformat(sub["premium_expiry"])
                prem_days = (prem_exp - datetime.now()).days
                if prem_days >= 36500:
                    prem_text = "✅ Lifetime Premium"
                elif prem_days > 0:
                    prem_text = f"✅ Active ({prem_days} days left)"
                else:
                    prem_text = "❌ Expired"
            except:
                pass
    data = fb_get(f"cpm1_users/{chat_id}") or {}
    if data.get("premium_by_tokens") and tokens > PREMIUM_TOKEN_THRESHOLD:
        prem_text = f"✅ Token-Based (Balance: {tokens})"
    warnings = get_user_warnings(chat_id)
    banned = get_user_banned(chat_id)
    role = "👑 Admin" if is_admin(chat_id) else ("👑 Premium User" if has_premium_access(chat_id) else "🆓 Free User")
    if banned:
        role = "🚫 BANNED"
    msg = (
        f"{get_premium_emoji('account_info')} <b>YOUR PROFILE</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{chat_id}</code>\n"
        f"🎖️ Role: {role}\n"
        f"🪙 Tokens: <code>{tokens}</code>\n"
        f"📦 Subscription: {sub_text}\n"
        f"👑 Premium Access: {prem_text}\n"
        f"⚠️ Warnings: {warnings}/3\n"
    )
    if banned:
        msg += f"\n{get_premium_emoji('cancel_failed_error')} <b>YOU ARE BANNED</b>\nContact: {ADMIN_USERNAME}"
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.row(
        get_btn("coin", "Buy Tokens", callback_data="tok_stars_menu"),
        get_btn("premium_hub", "Subscribe", callback_data="subscribe_menu")
    )
    keyboard.add(get_btn("back", "Back", callback_data="menu_main"))
    if msg_id:
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=keyboard, parse_mode="HTML")
        except:
            bot.send_message(chat_id, msg, reply_markup=keyboard, parse_mode="HTML")
    else:
        bot.send_message(chat_id, msg, reply_markup=keyboard, parse_mode="HTML")

@bot.message_handler(commands=['ban'])
def ban_command(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        if not is_admin(chat_id):
            warn_unauthorized_cpm1(chat_id, "/ban", message.from_user.username)
            return
        args = message.text.split()
        if len(args) < 2:
            bot.send_message(chat_id, f"Format: <code>/ban user_id [reason]</code>", parse_mode="HTML")
            return
        target = int(args[1])
        reason = " ".join(args[2:]) if len(args) > 2 else "No reason provided"
        fb_patch(f"cpm1_users/{target}", {"banned": True, "banned_at": datetime.now().isoformat(), "ban_reason": reason})
        bot.send_message(chat_id, f"🚫 User <code>{target}</code> has been banned.\nReason: {reason}", parse_mode="HTML")
        try:
            bot.send_message(target,
                f"{get_premium_emoji('cancel_failed_error')} <b>YOU ARE BANNED</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"You have been banned from using this bot.\n"
                f"Reason: {reason}\n\n"
                f"Contact admin: {ADMIN_USERNAME}",
                parse_mode="HTML")
        except:
            pass
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)[:80]}", parse_mode="HTML")

@bot.message_handler(commands=['unban'])
def unban_command(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        if not is_admin(chat_id):
            warn_unauthorized_cpm1(chat_id, "/unban", message.from_user.username)
            return
        args = message.text.split()
        if len(args) != 2:
            bot.send_message(chat_id, f"Format: <code>/unban &lt;user_id&gt;</code>", parse_mode="HTML")
            return
        target = int(args[1])
        unban_user_cpm1(target)
        bot.send_message(chat_id, f"{get_premium_emoji('success_preserved')} User <code>{target}</code> unbanned.",
                         parse_mode="HTML")
        try:
            bot.send_message(target,
                f"{get_premium_emoji('success_preserved')} <b>YOU HAVE BEEN UNBANNED</b>\n\n"
                f"You can now use the bot again.\nUse /start to begin.",
                parse_mode="HTML")
        except:
            pass
    except:
        pass

@bot.message_handler(commands=['clearwarn'])
def clearwarn_command(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        if not is_admin(chat_id):
            return
        args = message.text.split()
        if len(args) != 2:
            bot.send_message(chat_id, f"Format: <code>/clearwarn &lt;user_id&gt;</code>", parse_mode="HTML")
            return
        target = int(args[1])
        fb_patch(f"cpm1_users/{target}", {"warnings": 0, "banned": False})
        bot.send_message(chat_id,
                         f"{get_premium_emoji('success_preserved')} Warnings cleared for <code>{target}</code>",
                         parse_mode="HTML")
    except:
        pass

@bot.message_handler(commands=['listwarned'])
def listwarned_command(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        if not is_admin(chat_id):
            return
        users_data = fb_get("cpm1_users") or {}
        msg = f"{get_premium_emoji('warning')} <b>WARNED/BANNED USERS</b>\n\n"
        warned, banned = [], []
        for uid, d in users_data.items():
            w = d.get("warnings", 0)
            if w > 0 or d.get("banned", False):
                info = f"<code>{uid}</code> - ⚠️ {w}/3"
                if d.get("banned", False):
                    banned.append(info)
                elif w > 0:
                    warned.append(info)
        if not warned and not banned:
            msg += "✅ No warned/banned users."
        else:
            if warned:
                msg += f"⚠️ <b>WARNED ({len(warned)}):</b>\n" + "\n".join(warned) + "\n\n"
            if banned:
                msg += f"🚫 <b>BANNED ({len(banned)}):</b>\n" + "\n".join(banned)
        bot.send_message(chat_id, msg, parse_mode="HTML")
    except:
        pass

@bot.message_handler(commands=['listpremium'])
def listpremium_command(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        if not is_admin(chat_id):
            warn_unauthorized_cpm1(chat_id, "/listpremium", message.from_user.username)
            return
        users_data = fb_get("cpm1_users") or {}
        active_sub, active_prem, lifetime, token_prem = [], [], [], []
        for uid, d in users_data.items():
            username = d.get("username", "Unknown")
            sub = d.get("subscription")
            if d.get("premium_by_tokens") and d.get("tokens", 0) > PREMIUM_TOKEN_THRESHOLD:
                token_prem.append(f"🪙 <b>@{username}</b> / <code>{uid}</code> — Balance: {d.get('tokens', 0)}")
            if not sub:
                continue
            try:
                expiry = sub.get("expiry")
                prem_exp = sub.get("premium_expiry")
                if expiry:
                    exp_dt = datetime.fromisoformat(expiry)
                    if exp_dt > datetime.now():
                        days = (exp_dt - datetime.now()).days
                        if days >= 36500:
                            lifetime.append(f"♾️ <b>@{username}</b> / <code>{uid}</code>")
                        else:
                            prem_days = 0
                            if prem_exp:
                                try:
                                    pe = datetime.fromisoformat(prem_exp)
                                    if pe > datetime.now():
                                        prem_days = (pe - datetime.now()).days
                                except:
                                    pass
                            if prem_days > 0:
                                active_prem.append(f"👑 <b>@{username}</b> / <code>{uid}</code> — Sub: {days}d | Prem: {prem_days}d")
                            else:
                                active_sub.append(f"📦 <b>@{username}</b> / <code>{uid}</code> — {days}d left (no prem)")
            except:
                pass
        msg = "👑 <b>PREMIUM / SUBSCRIPTION USERS</b>\n━━━━━━━━━━━━━━━━\n\n"
        if lifetime:
            msg += f"♾️ <b>LIFETIME ({len(lifetime)}):</b>\n" + "\n".join(lifetime) + "\n\n"
        if active_prem:
            msg += f"👑 <b>PREMIUM ACTIVE ({len(active_prem)}):</b>\n" + "\n".join(active_prem) + "\n\n"
        if active_sub:
            msg += f"📦 <b>SUBSCRIBED (no premium) ({len(active_sub)}):</b>\n" + "\n".join(active_sub) + "\n\n"
        if token_prem:
            msg += f"🪙 <b>TOKEN-BASED PREMIUM ({len(token_prem)}):</b>\n" + "\n".join(token_prem) + "\n\n"
        if not (lifetime or active_prem or active_sub or token_prem):
            msg += "✅ No active premium users."
        total = len(lifetime) + len(active_prem) + len(active_sub) + len(token_prem)
        msg += f"\n━━━━━━━━━━━━━━━━\n📊 Total Active: <b>{total}</b>"
        bot.send_message(chat_id, msg, parse_mode="HTML")
    except Exception as e:
        try:
            bot.send_message(message.chat.id, f"❌ Error: {str(e)[:80]}", parse_mode="HTML")
        except:
            pass

@bot.message_handler(commands=['addtokens'])
def admin_addtokens(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        if not is_admin(chat_id):
            warn_unauthorized_cpm1(chat_id, "/addtokens", message.from_user.username)
            return

        args = message.text.split()
        if len(args) < 3 or len(args) > 4:
            bot.send_message(
                chat_id,
                f"<b>Format:</b>\n"
                f"<code>/addtokens user_id amount</code> — tokens only\n"
                f"<code>/addtokens user_id amount premium</code> — tokens + token-based premium\n\n"
                f"<b>Examples:</b>\n"
                f"<code>/addtokens 123456789 100</code>\n"
                f"<code>/addtokens 123456789 500 premium</code>\n\n"
                f"<b>Note:</b> Premium auto-ends when balance drops to <b>{PREMIUM_TOKEN_THRESHOLD} tokens</b> or less.",
                parse_mode="HTML"
            )
            return

        target = int(args[1])
        amount = int(args[2])
        grant_premium = (len(args) == 4 and args[3].lower() == "premium")

        add_tokens(target, amount)
        new_balance = get_user_tokens(target)

        prem_line = ""
        if grant_premium:
            fb_patch(f"cpm1_users/{target}", {"premium_by_tokens": True})
            prem_line = (
                f"\n👑 Premium: <b>ENABLED (token-based)</b>\n"
                f"⚠️ Auto-ends when balance hits <b>{PREMIUM_TOKEN_THRESHOLD} tokens</b> or less."
            )

        bot.send_message(
            chat_id,
            f"{get_premium_emoji('success_preserved')} <b>UPDATED</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🆔 User: <code>{target}</code>\n"
            f"🪙 Tokens added: <code>+{amount}</code>\n"
            f"💎 New balance: <code>{new_balance}</code>"
            f"{prem_line}",
            parse_mode="HTML"
        )

        try:
            notify = (
                f"{get_premium_emoji('success_preserved')} <b>Your account has been updated!</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🪙 Tokens: <code>+{amount}</code>\n"
                f"💎 Balance: <code>{new_balance}</code>"
            )
            if grant_premium:
                notify += (
                    f"\n\n👑 <b>PREMIUM ACCESS GRANTED</b>\n"
                    f"Premium stays active while your balance is above <b>{PREMIUM_TOKEN_THRESHOLD} tokens</b>."
                )
            bot.send_message(target, notify, parse_mode="HTML")
        except:
            pass

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)[:80]}", parse_mode="HTML")

@bot.message_handler(commands=['removetoken'])
def admin_removetoken(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        if not is_admin(chat_id):
            warn_unauthorized_cpm1(chat_id, "/removetoken", message.from_user.username)
            return

        args = message.text.split()
        if len(args) != 3:
            bot.send_message(
                chat_id,
                f"<b>Format:</b>\n"
                f"<code>/removetoken user_id amount</code>\n\n"
                f"<b>Example:</b>\n"
                f"<code>/removetoken 123456789 100</code>",
                parse_mode="HTML"
            )
            return

        target = int(args[1])
        amount = int(args[2])

        if amount <= 0:
            bot.send_message(chat_id, "❌ Amount must be positive.", parse_mode="HTML")
            return

        old_balance = get_user_tokens(target)
        new_balance = remove_tokens(target, amount)

        premium_revoked = False
        try:
            data = fb_get(f"cpm1_users/{target}")
            if data and data.get("premium_by_tokens") and new_balance <= PREMIUM_TOKEN_THRESHOLD:
                fb_patch(f"cpm1_users/{target}", {"premium_by_tokens": False})
                premium_revoked = True
        except:
            pass

        prem_line = ""
        if premium_revoked:
            prem_line = f"\n👑 Premium: <b>REVOKED</b> (balance now below threshold)"

        bot.send_message(
            chat_id,
            f"{get_premium_emoji('success_preserved')} <b>TOKENS REMOVED</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🆔 User: <code>{target}</code>\n"
            f"🪙 Removed: <code>-{amount}</code>\n"
            f"💎 Old balance: <code>{old_balance}</code>\n"
            f"💎 New balance: <code>{new_balance}</code>"
            f"{prem_line}",
            parse_mode="HTML"
        )

        try:
            notify = (
                f"{get_premium_emoji('warning')} <b>TOKENS REMOVED</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🪙 Removed: <code>-{amount}</code>\n"
                f"💎 New balance: <code>{new_balance}</code>"
            )
            if premium_revoked:
                notify += (
                    f"\n\n👑 <b>Premium access has been removed</b>\n"
                    f"Your balance is now below <b>{PREMIUM_TOKEN_THRESHOLD} tokens</b>."
                )
            bot.send_message(target, notify, parse_mode="HTML")
        except:
            pass

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)[:80]}", parse_mode="HTML")

@bot.message_handler(commands=['addsubs'])
def admin_addsubs(message):
    try:
        chat_id = message.chat.id
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        if not is_admin(chat_id):
            return
        args = message.text.split()
        if len(args) < 3:
            bot.send_message(chat_id, f"Format: <code>/addsubs user_id days [premium_days]</code>",
                             parse_mode="HTML")
            return
        target = int(args[1])
        days = int(args[2])
        prem_days = int(args[3]) if len(args) > 3 else 0
        activate_subscription(target, days, prem_days)
        bot.send_message(chat_id,
                         f"{get_premium_emoji('success_preserved')} Subscription for <code>{target}</code> ({days}d, {prem_days}d premium)",
                         parse_mode="HTML")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)[:80]}", parse_mode="HTML")

# ================================================================
#  GENERIC TEXT HANDLER (STATES)
# ================================================================
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_all_messages(message):
    try:
        chat_id = message.chat.id
        text = message.text
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass

        if is_blocked_by_ban(chat_id):
            if text and text.startswith('/'):
                send_ban_message(chat_id)
            return

        track_user(chat_id, message.from_user.username)
        if not text or text.startswith('/'):
            return
        if chat_id in user_states:
            state = user_states[chat_id]
            if state.get('awaiting_add_admin'):
                del user_states[chat_id]
                msg_id = state.get('msg_id')
                if not is_admin(chat_id):
                    return
                try:
                    target_id = int(text.strip())
                    add_admin(target_id)
                    bot.delete_message(chat_id, msg_id)
                    bot.send_message(chat_id,
                                     f"{get_premium_emoji('success_preserved')} Admin: <code>{target_id}</code>",
                                     parse_mode="HTML")
                except:
                    try:
                        bot.edit_message_text(f"❌ Invalid ID.", chat_id, msg_id,
                                              reply_markup=cancel_keyboard(), parse_mode="HTML")
                    except:
                        pass
                return
            if state.get('awaiting_rem_admin'):
                del user_states[chat_id]
                msg_id = state.get('msg_id')
                if not is_admin(chat_id):
                    return
                try:
                    target_id = int(text.strip())
                    remove_admin(target_id)
                    bot.delete_message(chat_id, msg_id)
                    bot.send_message(chat_id,
                                     f"{get_premium_emoji('cancel_failed_error')} Admin removed: <code>{target_id}</code>",
                                     parse_mode="HTML")
                except:
                    pass
                return
            if state.get('awaiting_add_prem'):
                del user_states[chat_id]
                msg_id = state.get('msg_id')
                if not is_admin(chat_id):
                    return
                try:
                    parts = text.strip().split()
                    target_id = int(parts[0])
                    days = int(parts[1]) if len(parts) > 1 else 30
                    approve_premium(target_id, days)
                    bot.delete_message(chat_id, msg_id)
                    bot.send_message(chat_id,
                                     f"✅ Premium for <code>{target_id}</code> ({days}d)",
                                     parse_mode="HTML")
                except:
                    pass
                return
            if state.get('awaiting_revoke'):
                del user_states[chat_id]
                msg_id = state.get('msg_id')
                if not is_admin(chat_id):
                    return
                try:
                    target = int(text.strip())
                    revoke_premium(target)
                    revoke_subscription(target)
                    fb_patch(f"cpm1_users/{target}", {
                        "premium_by_tokens": False,
                        "subscription": None
                    })
                    bot.delete_message(chat_id, msg_id)
                    bot.send_message(chat_id,
                                     f"❌ <b>FULLY REVOKED</b>\n"
                                     f"━━━━━━━━━━━━━━━━\n"
                                     f"🆔 User: <code>{target}</code>\n"
                                     f"• Subscription cleared ✅\n"
                                     f"• Token-based premium cleared ✅",
                                     parse_mode="HTML")
                    try:
                        bot.send_message(target,
                            f"⚠️ <b>PREMIUM REVOKED</b>\n\n"
                            f"Your premium access has been removed by an admin.\n"
                            f"Contact: {ADMIN_USERNAME}",
                            parse_mode="HTML")
                    except:
                        pass
                except Exception as e:
                    bot.send_message(chat_id, f"❌ Error: {str(e)[:80]}", parse_mode="HTML")
                return
            if state.get('awaiting_broadcast'):
                del user_states[chat_id]
                msg_id = state.get('msg_id')
                if not is_admin(chat_id):
                    return
                users_data = fb_get("cpm1_users") or {}
                c = 0
                failed = 0
                for uid in users_data.keys():
                    try:
                        bot.send_message(int(uid),
                                         f"{get_premium_emoji('broadcast_announcement')} <b>ANNOUNCEMENT</b>\n\n{html.escape(text)}",
                                         parse_mode="HTML")
                        c += 1
                        time.sleep(0.05)
                    except:
                        failed += 1
                try:
                    bot.delete_message(chat_id, msg_id)
                    bot.send_message(chat_id,
                                     f"✅ <b>Broadcast Complete</b>\n\n📤 Sent: {c}\n❌ Failed: {failed}",
                                     parse_mode="HTML")
                except:
                    pass
                return
            if state.get('awaiting_cpm_login_email'):
                user_sessions[chat_id]['email'] = text.strip()
                msg_id = state.get('msg_id')
                user_states[chat_id] = {'awaiting_cpm_login_pass': True, 'msg_id': msg_id}
                try:
                    bot.edit_message_text(f"{get_premium_emoji('password')} Send password:",
                                          chat_id, msg_id, reply_markup=cancel_keyboard(), parse_mode="HTML")
                except:
                    pass
                return
            if state.get('awaiting_cpm_login_pass'):
                password = text.strip()
                email = user_sessions[chat_id].get('email', '')
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                try:
                    bot.edit_message_text(f"{get_premium_emoji('loading_progress')} Authenticating...",
                                          chat_id, msg_id, parse_mode="HTML")
                except:
                    pass
                try:
                    web_uid = get_web_uid(chat_id)
                    res = nuker.login(email, password)
                    if res and isinstance(res, dict) and res.get("ok"):
                        nuker.save_token(web_uid, res.get("auth", ""), email, password,
                                         res.get("refresh_token", ""), res.get("firebase_uid", ""))
                        user_sessions[chat_id].update({'cpm_logged_in': True, 'web_uid': web_uid})
                        safe_send_dashboard(chat_id, force_refresh=True, is_callback=True, message_id=msg_id)
                    else:
                        err = clean_str(res.get('message', 'Unknown') if isinstance(res, dict) else 'Network')
                        try:
                            bot.edit_message_text(f"❌ AUTH FAILED: {html.escape(err)}",
                                                  chat_id, msg_id, reply_markup=cancel_keyboard(), parse_mode="HTML")
                        except:
                            pass
                except:
                    try:
                        bot.edit_message_text(f"❌ Timeout.", chat_id, msg_id,
                                              reply_markup=cancel_keyboard(), parse_mode="HTML")
                    except:
                        pass
                return
            if state.get('awaiting_cpm_register_email'):
                user_sessions[chat_id]['reg_email'] = text.strip()
                msg_id = state.get('msg_id')
                user_states[chat_id] = {'awaiting_cpm_register_pass': True, 'msg_id': msg_id}
                try:
                    bot.edit_message_text(f"{get_premium_emoji('password')} Send password (min 6 chars):",
                                          chat_id, msg_id, reply_markup=cancel_keyboard(), parse_mode="HTML")
                except:
                    pass
                return
            if state.get('awaiting_cpm_register_pass'):
                password = text.strip()
                email = user_sessions[chat_id].get('reg_email', '')
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                try:
                    bot.edit_message_text(f"{get_premium_emoji('loading_progress')} Creating...",
                                          chat_id, msg_id, parse_mode="HTML")
                except:
                    pass
                try:
                    web_uid = get_web_uid(chat_id)
                    res = nuker.register(email, password)
                    if res and isinstance(res, dict) and res.get("ok"):
                        auth = res.get("auth", "")
                        fuid = res.get("firebase_uid", "")
                        blank_profile = {
                            "Name": "Player", "money": 25000, "coin": 0,
                            "localID": str(random.randint(1000000, 9999999)).zfill(8),
                            "allData": '{"cars":[]}', "floats": [], "integers": []
                        }
                        try:
                            nuker._send(auth, blank_profile, fuid)
                        except:
                            pass
                        nuker.save_token(web_uid, auth, email, password, res.get("refresh_token", ""), fuid)
                        user_sessions[chat_id].update({'cpm_logged_in': True, 'web_uid': web_uid})
                        safe_send_dashboard(chat_id, custom_top_msg="Account Created!",
                                            force_refresh=True, is_callback=True, message_id=msg_id)
                    else:
                        err = clean_str(res.get('message', 'Failed') if isinstance(res, dict) else 'Network')
                        try:
                            bot.edit_message_text(f"❌ {html.escape(err)}", chat_id, msg_id,
                                                  reply_markup=cancel_keyboard(), parse_mode="HTML")
                        except:
                            pass
                except:
                    try:
                        bot.edit_message_text(f"❌ Timeout.", chat_id, msg_id,
                                              reply_markup=cancel_keyboard(), parse_mode="HTML")
                    except:
                        pass
                return
            if state.get('awaiting_clone_source_email'):
                user_sessions[chat_id]['clone_src_email'] = text.strip()
                msg_id = state.get('msg_id')
                user_states[chat_id] = {'awaiting_clone_source_pass': True, 'msg_id': msg_id}
                try:
                    bot.edit_message_text(f"{get_premium_emoji('password')} Source password:",
                                          chat_id, msg_id, reply_markup=cancel_keyboard(), parse_mode="HTML")
                except:
                    pass
                return
            if state.get('awaiting_clone_source_pass'):
                user_sessions[chat_id]['clone_src_pass'] = text.strip()
                msg_id = state.get('msg_id')
                user_states[chat_id] = {'awaiting_clone_target_email': True, 'msg_id': msg_id}
                try:
                    bot.edit_message_text(f"{get_premium_emoji('email')} Target email:",
                                          chat_id, msg_id, reply_markup=cancel_keyboard(), parse_mode="HTML")
                except:
                    pass
                return
            if state.get('awaiting_clone_target_email'):
                user_sessions[chat_id]['clone_tgt_email'] = text.strip()
                msg_id = state.get('msg_id')
                user_states[chat_id] = {'awaiting_clone_target_pass': True, 'msg_id': msg_id}
                try:
                    bot.edit_message_text(f"{get_premium_emoji('password')} Target password:",
                                          chat_id, msg_id, reply_markup=cancel_keyboard(), parse_mode="HTML")
                except:
                    pass
                return
            if state.get('awaiting_clone_target_pass'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                tgt_pass = text.strip()
                src_email = user_sessions[chat_id].get('clone_src_email')
                src_pass = user_sessions[chat_id].get('clone_src_pass')
                tgt_email = user_sessions[chat_id].get('clone_tgt_email')
                threading.Thread(target=background_single_clone,
                                 args=(chat_id, src_email, src_pass, tgt_email, tgt_pass, msg_id)).start()
                return
            if state.get('awaiting_prem_bulk_source_email') or state.get('awaiting_admin_bulk_source_email'):
                user_sessions[chat_id]['bulk_source_email'] = text.strip()
                msg_id = state.get('msg_id')
                user_states[chat_id] = {'awaiting_prem_bulk_source_pass': True, 'msg_id': msg_id}
                try:
                    bot.edit_message_text(f"{get_premium_emoji('password')} Source password:",
                                          chat_id, msg_id, reply_markup=cancel_keyboard(), parse_mode="HTML")
                except:
                    pass
                return
            if state.get('awaiting_prem_bulk_source_pass') or state.get('awaiting_admin_bulk_source_pass'):
                user_sessions[chat_id]['bulk_source_pass'] = text.strip()
                msg_id = state.get('msg_id')
                user_states[chat_id] = {'awaiting_prem_bulk_count': True, 'msg_id': msg_id}
                try:
                    bot.edit_message_text(f"{get_premium_emoji('bulk_clone')} How many clones? (1-10):",
                                          chat_id, msg_id, reply_markup=cancel_keyboard(), parse_mode="HTML")
                except:
                    pass
                return
            if state.get('awaiting_prem_bulk_count') or state.get('awaiting_admin_bulk_count'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                try:
                    count = int(text.strip())
                    if not (1 <= count <= 10):
                        try:
                            bot.edit_message_text(f"❌ Limit 1-10", chat_id, msg_id,
                                                  reply_markup=cancel_keyboard(), parse_mode="HTML")
                        except:
                            pass
                        return
                    src_email = user_sessions[chat_id].get('bulk_source_email')
                    src_pass = user_sessions[chat_id].get('bulk_source_pass')
                    is_admin_user = is_admin(chat_id)
                    threading.Thread(target=background_bulk_clone,
                                     args=(chat_id, src_email, src_pass, count, msg_id, is_admin_user)).start()
                except:
                    pass
                return
            if state.get('awaiting_single_car_id'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                try:
                    car_id = int(text.strip())
                    web_uid = get_web_uid(chat_id)
                    try:
                        bot.edit_message_text(f"{get_premium_emoji('loading_progress')} Injecting Car {car_id}...",
                                              chat_id, msg_id, reply_markup=create_premium_keyboard(), parse_mode="HTML")
                    except:
                        pass
                    threading.Thread(target=inject_car_by_id_thread,
                                     args=(chat_id, msg_id, web_uid, car_id, "")).start()
                except:
                    pass
                return
            if state.get('awaiting_cpm1_email'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                nuker.change_email(user_sessions[chat_id].get('web_uid'), text.strip())
                safe_send_dashboard(chat_id, custom_top_msg="Email Changed!",
                                    force_refresh=True, is_callback=True, message_id=msg_id)
                return
            if state.get('awaiting_change_id'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                nuker.change_player_id(user_sessions[chat_id].get('web_uid'), text.strip().upper())
                safe_send_dashboard(chat_id, custom_top_msg="Tag Masked!",
                                    force_refresh=True, is_callback=True, message_id=msg_id)
                return
            if state.get('awaiting_change_name'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                nuker.change_player_name(user_sessions[chat_id].get('web_uid'), text.strip())
                safe_send_dashboard(chat_id, custom_top_msg="Name Changed!",
                                    force_refresh=True, is_callback=True, message_id=msg_id)
                return
            if state.get('awaiting_money'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                try:
                    nuker.set_money(user_sessions[chat_id].get('web_uid'), int(text.strip()))
                    safe_send_dashboard(chat_id, custom_top_msg="Money Applied!",
                                        force_refresh=True, is_callback=True, message_id=msg_id)
                except:
                    pass
                return
            if state.get('awaiting_coin'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                try:
                    nuker.set_coin(user_sessions[chat_id].get('web_uid'), int(text.strip()))
                    safe_send_dashboard(chat_id, custom_top_msg="Coins Applied!",
                                        force_refresh=True, is_callback=True, message_id=msg_id)
                except:
                    pass
                return
    except Exception as e:
        pass

# ================================================================
#  PLANS (MONEY / STARS / TOKENS)
# ================================================================
MONEY_PLANS = {
    "money_2": {"usd": 2, "days": 1.5, "premium_days": 0, "label": "1.5 Days (No Premium)"},
    "money_4": {"usd": 4, "days": 2.5, "premium_days": 0, "label": "2.5 Days (No Premium)"},
    "money_6": {"usd": 6, "days": 7, "premium_days": 2, "label": "1 Week (2 Days Premium)"},
    "money_8": {"usd": 8, "days": 14, "premium_days": 4, "label": "2 Weeks (4 Days Premium)"},
    "money_10": {"usd": 10, "days": 30, "premium_days": 21, "label": "1 Month (3 Weeks Premium)"},
    "money_30": {"usd": 30, "days": 36500, "premium_days": 36500, "label": "Lifetime Premium"},
}

STARS_PLANS = {
    "stars_50": {"stars": 50, "days": 1, "premium_days": 0, "label": "1 Day (No Premium)"},
    "stars_200": {"stars": 200, "days": 7, "premium_days": 7, "label": "1 Week + Premium"},
    "stars_350": {"stars": 350, "days": 30, "premium_days": 30, "label": "1 Month + Premium"},
    "stars_550": {"stars": 550, "days": 36500, "premium_days": 36500, "label": "Lifetime + Premium"},
}

TOKEN_STARS = {
    "tok_s_19": {"stars": 19, "tokens": 100},
    "tok_s_38": {"stars": 38, "tokens": 150},
    "tok_s_75": {"stars": 75, "tokens": 200},
    "tok_s_113": {"stars": 113, "tokens": 250},
    "tok_s_150": {"stars": 150, "tokens": 300},
}

# ================================================================
#  PHOTO HANDLER (PAYMENT SCREENSHOTS)
# ================================================================
@bot.message_handler(content_types=['photo'])
def photo_handler(message):
    chat_id = message.chat.id

    if is_blocked_by_ban(chat_id):
        send_ban_message(chat_id)
        return

    state = user_states.get(chat_id, {})
    if state.get('awaiting_payment_screenshot'):
        plan_key = state.get('plan')
        method = state.get('method', 'unknown')
        plan = MONEY_PLANS.get(plan_key, {})
        del user_states[chat_id]
        if not plan:
            return
        method_names = {"paymaya": "PayMaya", "paypal": "PayPal", "gcash": "GCash to PayMaya (QR)"}
        method_display = method_names.get(method, "Unknown")
        try:
            photo_id = message.photo[-1].file_id
            caption_text = message.caption or "No details provided"
            usd = plan['usd']
            php = usd * USD_TO_PHP
            group_msg = (
                f"📸 <b>New Payment Screenshot Received!</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"👤 User: @{message.from_user.username or 'Unknown'}\n"
                f"🆔 ID: <code>{chat_id}</code>\n"
                f"💳 Payment Method: <b>{method_display}</b>\n"
                f"📋 Plan: <b>{plan['label']}</b>\n"
                f"💵 Amount: <b>${usd} (₱{php:,.0f})</b>\n"
                f"📝 Details: {caption_text}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"⏳ Waiting for admin verification..."
            )
            keyboard = types.InlineKeyboardMarkup()
            keyboard.row(
                types.InlineKeyboardButton("✅ Confirm", callback_data=f"adm_conf_{chat_id}_{plan_key}"),
                types.InlineKeyboardButton("❌ Decline", callback_data=f"adm_dec_{chat_id}")
            )
            bot.send_photo(GROUP_LOG_ID, photo_id, caption=group_msg,
                           reply_markup=keyboard, parse_mode="HTML")
            bot.send_message(chat_id,
                             f"{get_premium_emoji('success_preserved')} <b>Screenshot Received!</b>\n\nThe admin will verify your payment.\n⏳ Please wait...",
                             parse_mode="HTML")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error: {html.escape(str(e)[:80])}", parse_mode="HTML")
        return

# ================================================================
#  CALLBACK HANDLER
# ================================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data
    user = call.from_user

    if is_blocked_by_ban(chat_id):
        try:
            bot.answer_callback_query(call.id, "🚫 You are banned from using this bot.", show_alert=True)
        except:
            pass
        return

    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    track_user(chat_id, call.from_user.username)
    silent_nav = ["menu_main", "init_login", "init_register", "logout", "refresh_account",
                  "menu_account", "menu_economy", "menu_unlocks", "menu_premium",
                  "acc_info", "acc_name", "acc_id", "acc_email", "acc_pass", "admin_bulk_clone",
                  "eco_money_cust", "eco_coins_cust", "veh_unlock_single", "veh_unlock_all",
                  "prem_bulk_clone", "prem_clone", "subscribe_menu", "sub_stars", "sub_money",
                  "tok_stars_menu", "tok_money_menu", "show_info", "show_profile", "buytokens_menu",
                  "admin_stats", "admin_panel", "admin_add_admin", "admin_rem_admin",
                  "admin_view_admins", "admin_add_prem", "admin_revoke", "admin_broadcast"]
    if data in silent_nav:
        try:
            bot.answer_callback_query(call.id)
        except:
            pass

    # ========== ADMIN STATS (FIXED — uses send_message) ==========
    if data == "admin_stats":
        if not is_admin(chat_id):
            return
        try:
            try:
                bot.answer_callback_query(call.id, "⏳ Loading stats...")
            except:
                pass

            users_data = fb_get("cpm1_users") or {}
            if not users_data:
                bot.send_message(chat_id, "❌ No users found.", parse_mode="HTML")
                return

            lines = []
            total_tokens = 0
            active_subs = 0
            active_premium = 0
            token_premium_count = 0
            MAX_DISPLAY = 30

            for idx, (uid, d) in enumerate(users_data.items()):
                username = d.get("username", "Unknown")
                tokens = d.get("tokens", 0)
                total_tokens += tokens
                sub = d.get("subscription")
                sub_status = "no active"
                prem_status = "no active"
                if d.get("premium_by_tokens") and tokens > PREMIUM_TOKEN_THRESHOLD:
                    prem_status = f"token-based ({tokens})"
                    token_premium_count += 1
                if sub and sub.get("expiry"):
                    try:
                        exp = datetime.fromisoformat(sub["expiry"])
                        if exp > datetime.now():
                            days = (exp - datetime.now()).days
                            sub_status = "lifetime" if days >= 36500 else f"{days}d left"
                            active_subs += 1
                    except:
                        pass
                if sub and sub.get("premium_expiry"):
                    try:
                        pexp = datetime.fromisoformat(sub["premium_expiry"])
                        if pexp > datetime.now():
                            pdays = (pexp - datetime.now()).days
                            prem_status = "lifetime" if pdays >= 36500 else f"{pdays}d left"
                            active_premium += 1
                    except:
                        pass
                banned_flag = " 🚫" if d.get("banned", False) else ""
                warn_flag = f" ⚠️{d.get('warnings', 0)}" if d.get("warnings", 0) > 0 else ""
                line = (f"<b>@{username}</b> / <code>{uid}</code>{banned_flag}{warn_flag}\n"
                        f"   🪙 {tokens:,} tokens\n"
                        f"   📦 Sub: {sub_status}\n"
                        f"   👑 Premium: {prem_status}")
                lines.append(line)
                if idx >= MAX_DISPLAY - 1:
                    break

            header = (
                f"📈 <b>BOT STATISTICS</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"👥 Total Users: <b>{len(users_data)}</b>\n"
                f"🪙 Total Tokens: <b>{total_tokens:,}</b>\n"
                f"📦 Active Subs: <b>{active_subs}</b>\n"
                f"👑 Active Premium: <b>{active_premium}</b>\n"
                f"🪙 Token-Based Premium: <b>{token_premium_count}</b>\n"
                f"🛡️ Admins: <b>{len(get_all_admins())}</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
            )

            try:
                bot.send_message(chat_id, header, parse_mode="HTML")
            except:
                pass

            if lines:
                display_lines = list(lines)
                if len(users_data) > MAX_DISPLAY:
                    display_lines.append(f"\n<i>...and {len(users_data) - MAX_DISPLAY} more users (not shown)</i>")

                current_chunk = ""
                for line in display_lines:
                    if len(current_chunk) + len(line) + 2 > 3500:
                        try:
                            bot.send_message(chat_id, current_chunk, parse_mode="HTML")
                        except:
                            pass
                        current_chunk = line
                    else:
                        current_chunk += ("\n\n" if current_chunk else "") + line
                if current_chunk:
                    try:
                        bot.send_message(chat_id, current_chunk, parse_mode="HTML")
                    except:
                        pass

        except Exception as e:
            try:
                bot.send_message(chat_id,
                                 f"❌ Stats error: <code>{html.escape(str(e)[:200])}</code>",
                                 parse_mode="HTML")
            except:
                pass
        return

    if data == "subscribe_menu":
        try:
            msg = (
                f"{get_premium_emoji('premium_hub')} <b>SUBSCRIPTION PLANS</b>\n\n"
                f"{get_premium_emoji('premium_hub')} <b>Premium Features:</b>\n"
                "• Unlock any car\n"
                "• Create single clone accounts (unlimited)\n"
                "• Create bulk clone accounts (up to 10 at a time)\n\n"
                f"{get_premium_emoji('warning')} <b>Note:</b>\n"
                "1 Day subscription has <b>NO premium access</b>.\n"
                "1 Week onwards includes premium features.\n\n"
                "Choose payment method:"
            )
            bot.edit_message_text(msg, chat_id, msg_id,
                                  reply_markup=create_subscription_keyboard(), parse_mode="HTML")
        except:
            pass
        return
    if data == "sub_stars":
        try:
            msg = (
                f"{get_premium_emoji('premium_hub')} <b>STARS SUBSCRIPTION</b>\n\n"
                "• 50⭐ = 1 Day (No Premium)\n"
                "• 200⭐ = 1 Week + Premium\n"
                "• 350⭐ = 1 Month + Premium\n"
                "• 550⭐ = Lifetime + Premium\n\n"
                "Select your package:"
            )
            bot.edit_message_text(msg, chat_id, msg_id,
                                  reply_markup=create_stars_plans_keyboard(), parse_mode="HTML")
        except:
            pass
        return
    if data == "sub_money":
        try:
            msg = (
                f"{get_premium_emoji('money')} <b>MONEY SUBSCRIPTION</b>\n\n"
                f"• $2 (₱124) = 1.5 Days (No Premium)\n"
                f"• $4 (₱248) = 2.5 Days (No Premium)\n"
                f"• $6 (₱372) = 1 Week (2D Premium)\n"
                f"• $8 (₱496) = 2 Weeks (4D Premium)\n"
                f"• $10 (₱620) = 1 Month (3W Premium)\n"
                f"• $30 (₱1,860) = Lifetime Premium\n\n"
                "Select your package:"
            )
            bot.edit_message_text(msg, chat_id, msg_id,
                                  reply_markup=create_money_plans_keyboard(), parse_mode="HTML")
        except:
            pass
        return
    if data in STARS_PLANS:
        plan = STARS_PLANS[data]
        try:
            bot.send_invoice(
                chat_id=chat_id,
                title=f"{plan['stars']}⭐ - {plan['label']}",
                description=f"Subscription: {plan['label']}",
                invoice_payload=f"cpm1_sub_{plan['stars']}_{plan['days']}_{plan['premium_days']}",
                provider_token="",
                currency="XTR",
                prices=[types.LabeledPrice(label=f"{plan['stars']} Stars", amount=plan['stars'])],
                start_parameter="stars_sub"
            )
        except Exception as e:
            try:
                bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)
            except:
                pass
        return
    if data in MONEY_PLANS:
        plan = MONEY_PLANS[data]
        usd = plan["usd"]
        php = usd * USD_TO_PHP
        msg = (
            f"{get_premium_emoji('money')} <b>PAYMENT DETAILS</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📦 Plan: {plan['label']}\n"
            f"💵 Amount: ${usd} (₱{php:,.0f})\n\n"
            f"💳 <b>Select payment method:</b>"
        )
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.row(types.InlineKeyboardButton("📱 PayMaya", callback_data=f"pm_paymaya_{data}"))
        keyboard.row(types.InlineKeyboardButton("💳 PayPal", callback_data=f"pm_paypal_{data}"))
        keyboard.row(types.InlineKeyboardButton("📲 GCash to PayMaya (QR)", callback_data=f"pm_gcash_{data}"))
        keyboard.add(get_btn("back", "Back", callback_data="sub_money"))
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=keyboard, parse_mode="HTML")
        except:
            pass
        return
    if data.startswith("pm_paymaya_") or data.startswith("pm_paypal_") or data.startswith("pm_gcash_"):
        parts = data.split("_", 2)
        method = parts[1]
        plan_key = parts[2] if len(parts) > 2 else ""
        plan = MONEY_PLANS.get(plan_key)
        if not plan:
            try:
                bot.answer_callback_query(call.id, "❌ Invalid plan", show_alert=True)
            except:
                pass
            return
        usd = plan["usd"]
        php = usd * USD_TO_PHP
        if method == "paymaya":
            msg = (
                f"📱 <b>PayMaya Payment</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📦 Plan: {plan['label']}\n"
                f"💵 Amount: ${usd} (₱{php:,.0f})\n\n"
                f"<b>Send payment to:</b>\n"
                f"📱 Number: <code>09281630511</code>\n"
                f"👤 Name: MARK RYAN MANOGUID\n\n"
                f"⚠️ After payment, tap the button below and send your screenshot."
            )
        elif method == "paypal":
            msg = (
                f"💳 <b>PayPal Payment</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📦 Plan: {plan['label']}\n"
                f"💵 Amount: ${usd}\n\n"
                f"<b>Send payment to:</b>\n"
                f"💳 Email: <code>markryanmanoguid867@gmail.com</code>\n\n"
                f"⚠️ After payment, tap the button below and send your screenshot."
            )
        else:
            msg = (
                f"📲 <b>GCash to PayMaya (QR)</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📦 Plan: {plan['label']}\n"
                f"💵 Amount: ${usd} (₱{php:,.0f})\n\n"
                f"<b>Please DM {ADMIN_USERNAME} for the QR code.</b>\n\n"
                f"⚠️ After payment, tap the button below and send your screenshot."
            )
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("✅ I have paid - Send Screenshot",
                                                callback_data=f"money_submit_{method}_{plan_key}"))
        keyboard.add(get_btn("back", "Back", callback_data="sub_money"))
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=keyboard, parse_mode="HTML")
        except:
            pass
        return
    if data.startswith("money_submit_"):
        raw = data.replace("money_submit_", "")
        parts = raw.split("_", 1)
        if len(parts) < 2:
            return
        method = parts[0]
        plan_key = parts[1]
        plan = MONEY_PLANS.get(plan_key)
        if not plan:
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "📸 <b>Please send your payment screenshot now.</b>",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_payment_screenshot': True, 'msg_id': msg.message_id,
                                'plan': plan_key, 'method': method}
        return
    if data.startswith("adm_conf_") or data.startswith("adm_dec_"):
        if not is_admin(call.from_user.id):
            try:
                bot.answer_callback_query(call.id, "❌ Admin only", show_alert=True)
            except:
                pass
            return
        if data.startswith("adm_conf_"):
            raw = data.replace("adm_conf_", "")
            parts = raw.split("_", 1)
            user_id = int(parts[0])
            plan_key = parts[1]
            plan = MONEY_PLANS.get(plan_key, {})
            if not plan:
                return
            activate_subscription(user_id, plan["days"], plan["premium_days"])
            try:
                bot.edit_message_caption(
                    caption=(f"{get_premium_emoji('success_preserved')} <b>PAYMENT CONFIRMED</b>\n"
                             f"━━━━━━━━━━━━━━━━\n"
                             f"🆔 User: <code>{user_id}</code>\n"
                             f"📦 Plan: {plan['label']}\n"
                             f"✅ Confirmed by Admin"),
                    chat_id=chat_id, message_id=msg_id, parse_mode="HTML"
                )
            except:
                pass
            try:
                expiry_str = (datetime.now() + timedelta(days=plan["days"])).strftime('%Y-%m-%d') if plan["days"] < 36500 else "Lifetime"
                prem_str = (datetime.now() + timedelta(days=plan["premium_days"])).strftime('%Y-%m-%d') if 0 < plan["premium_days"] < 36500 else ("Lifetime" if plan["premium_days"] >= 36500 else "No Premium")
                bot.send_message(user_id,
                    f"{get_premium_emoji('success_preserved')} <b>SUBSCRIPTION ACTIVATED!</b>\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"📦 Plan: {plan['label']}\n"
                    f"✅ Expires: {expiry_str}\n"
                    f"👑 Premium: {prem_str}\n\nEnjoy!",
                    parse_mode="HTML")
            except:
                pass
            try:
                bot.answer_callback_query(call.id, "✅ Confirmed!", show_alert=False)
            except:
                pass
        else:
            user_id = int(data.replace("adm_dec_", ""))
            try:
                bot.edit_message_caption(
                    caption=(f"{get_premium_emoji('cancel_failed_error')} <b>PAYMENT DECLINED</b>\n"
                             f"━━━━━━━━━━━━━━━━\n"
                             f"🆔 User: <code>{user_id}</code>\n"
                             f"❌ Declined by Admin"),
                    chat_id=chat_id, message_id=msg_id, parse_mode="HTML"
                )
            except:
                pass
            try:
                bot.send_message(user_id,
                                 f"{get_premium_emoji('cancel_failed_error')} <b>PAYMENT DECLINED</b>\n\nContact: {ADMIN_USERNAME}",
                                 parse_mode="HTML")
            except:
                pass
            try:
                bot.answer_callback_query(call.id, "❌ Declined", show_alert=False)
            except:
                pass
        return
    if data == "buytokens_menu":
        current = get_user_tokens(chat_id)
        msg = (
            f"{get_premium_emoji('coin')} <b>BUY TOKENS</b> (25% OFF)\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🪙 Your Tokens: <code>{current}</code>\n\nChoose payment method:"
        )
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(get_btn("premium_hub", "⭐ Buy with Stars", callback_data="tok_stars_menu"))
        keyboard.add(get_btn("money", "💵 Buy with Money", callback_data="tok_money_menu"))
        keyboard.add(get_btn("back", "Back", callback_data="menu_main"))
        try:
            bot.edit_message_text(msg, chat_id, msg_id, reply_markup=keyboard, parse_mode="HTML")
        except:
            pass
        return
    if data == "tok_stars_menu":
        try:
            bot.edit_message_text(f"{get_premium_emoji('coin')} <b>BUY TOKENS WITH STARS</b>\n\nSelect package:\n👑 = premium auto-unlock",
                                  chat_id, msg_id,
                                  reply_markup=create_token_packages_keyboard(), parse_mode="HTML")
        except:
            pass
        return
    if data == "tok_money_menu":
        try:
            bot.edit_message_text(
                f"{get_premium_emoji('coin')} <b>BUY TOKENS WITH MONEY</b>\n\nDM {ADMIN_USERNAME} to purchase.\n👑 = premium auto-unlock\n\nSelect package:",
                chat_id, msg_id,
                reply_markup=create_token_money_keyboard(), parse_mode="HTML")
        except:
            pass
        return
    if data in TOKEN_STARS:
        pkg = TOKEN_STARS[data]
        try:
            bot.send_invoice(
                chat_id=chat_id,
                title=f"{pkg['stars']}⭐ - {pkg['tokens']} Tokens",
                description=f"Buy {pkg['tokens']} tokens",
                invoice_payload=f"cpm1_tok_{pkg['stars']}_{pkg['tokens']}",
                provider_token="",
                currency="XTR",
                prices=[types.LabeledPrice(label=f"{pkg['stars']} Stars", amount=pkg['stars'])],
                start_parameter="tok_stars"
            )
        except Exception as e:
            try:
                bot.answer_callback_query(call.id, f"❌ {str(e)[:80]}", show_alert=True)
            except:
                pass
        return
    if data.startswith("tok_m_") and data != "tok_money_menu":
        key = data.replace("tok_m_", "")
        token_map = {"1.5": 150, "3": 200, "4.5": 250, "6": 300, "7.5": 350, "9": 400, "custom": 0}
        usd_map = {"1.5": 1.5, "3": 3, "4.5": 4.5, "6": 6, "7.5": 7.5, "9": 9, "custom": 19}
        tokens = token_map.get(key, 0)
        usd = usd_map.get(key, 0)
        try:
            bot.edit_message_text(
                f"{get_premium_emoji('money')} <b>TOKEN PURCHASE</b>\n"
                f"🪙 Tokens: {tokens if tokens > 0 else 'Custom'}\n"
                f"💵 Amount: ${usd} (₱{usd*USD_TO_PHP:,.0f})\n\nDM {ADMIN_USERNAME} to purchase.",
                chat_id, msg_id,
                reply_markup=types.InlineKeyboardMarkup().add(get_btn("back", "Back", callback_data="tok_money_menu")),
                parse_mode="HTML")
        except:
            pass
        return
    if data == "show_info":
        show_info(chat_id, msg_id)
        return
    if data == "show_profile":
        show_profile(chat_id, msg_id)
        return
    if data == "menu_main":
        if chat_id in user_states:
            del user_states[chat_id]
        return safe_send_dashboard(chat_id, force_refresh=False, is_callback=True, message_id=msg_id)
    if data == "init_login":
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"{get_premium_emoji('email')} Send your email to login:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_cpm_login_email': True, 'msg_id': msg.message_id}
        return
    if data == "init_register":
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"{get_premium_emoji('email')} Send new email:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_cpm_register_email': True, 'msg_id': msg.message_id}
        return
    if data == "logout":
        if chat_id in user_sessions:
            user_sessions[chat_id]['cpm_logged_in'] = False
        nuker.delete_token(get_web_uid(chat_id))
        return safe_send_dashboard(chat_id, force_refresh=False, is_callback=True, message_id=msg_id)
    if data == "refresh_account":
        return safe_send_dashboard(chat_id, custom_top_msg="Refreshed!",
                                   force_refresh=True, is_callback=True, message_id=msg_id)
    if data == "menu_account":
        try:
            bot.edit_message_text(f"{get_premium_emoji('account_info')} <b>Account Management</b>",
                                  chat_id, msg_id,
                                  reply_markup=create_account_keyboard(), parse_mode="HTML")
        except:
            pass
        return
    if data == "menu_economy":
        try:
            bot.edit_message_text(f"{get_premium_emoji('economy_profile')} <b>Economy</b>",
                                  chat_id, msg_id,
                                  reply_markup=create_economy_keyboard(), parse_mode="HTML")
        except:
            pass
        return
    if data == "menu_unlocks":
        try:
            bot.edit_message_text(f"{get_premium_emoji('unlocks_login')} <b>Unlocks</b>",
                                  chat_id, msg_id,
                                  reply_markup=create_unlocks_keyboard(), parse_mode="HTML")
        except:
            pass
        return
    if data == "menu_premium":
        if not has_premium_access(chat_id) and not is_admin(chat_id):
            try:
                bot.answer_callback_query(call.id, "❌ Premium required.", show_alert=True)
            except:
                pass
            return
        try:
            bot.edit_message_text(f"{get_premium_emoji('premium_hub')} <b>Premium Section</b>",
                                  chat_id, msg_id,
                                  reply_markup=create_premium_keyboard(), parse_mode="HTML")
        except:
            pass
        return
    if data == "acc_info":
        return safe_send_dashboard(chat_id, is_callback=True, message_id=msg_id)
    if data == "acc_name":
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"✏️ Enter new Name:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_change_name': True, 'msg_id': msg.message_id}
        return
    if data == "acc_id":
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"🆔 Enter new ID:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_change_id': True, 'msg_id': msg.message_id}
        return
    if data == "acc_email":
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"📧 Enter new Email:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_cpm1_email': True, 'msg_id': msg.message_id}
        return
    if data == "acc_pass":
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"🔒 Enter new Password:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_change_pass': True, 'msg_id': msg.message_id}
        return
    if data == "prem_clone":
        if not has_premium_access(chat_id) and not is_admin(chat_id):
            try:
                bot.answer_callback_query(call.id, "❌ Premium required.", show_alert=True)
            except:
                pass
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"📧 Send SOURCE email:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_clone_source_email': True, 'msg_id': msg.message_id}
        return
    if data == "admin_bulk_clone" or data == "prem_bulk_clone":
        if not is_admin(chat_id) and not has_premium_access(chat_id):
            try:
                bot.answer_callback_query(call.id, "❌ Premium required.", show_alert=True)
            except:
                pass
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"📧 Send SOURCE email:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_prem_bulk_source_email': True, 'msg_id': msg.message_id}
        return
    if data == "unl_w124":
        try:
            bot.answer_callback_query(call.id)
        except:
            pass
        web_uid = get_web_uid(chat_id)
        threading.Thread(target=inject_car_by_id_thread,
                         args=(chat_id, msg_id, web_uid, 258, "W124")).start()
        return
    if data == "unl_camry":
        try:
            bot.answer_callback_query(call.id)
        except:
            pass
        web_uid = get_web_uid(chat_id)
        threading.Thread(target=inject_car_by_id_thread,
                         args=(chat_id, msg_id, web_uid, 264, "Camry")).start()
        return

    web_uid = get_web_uid(chat_id)

    def exec_mod(call_obj, name, func, *args, token_cost=20):
        try:
            if not is_admin(chat_id):
                cur = get_user_tokens(chat_id)
                if cur < token_cost:
                    try:
                        bot.answer_callback_query(call_obj.id,
                            f"❌ Need {token_cost} tokens. You have {cur}.", show_alert=True)
                    except:
                        pass
                    return
            if data.startswith("eco_"):
                menu_text = f"{get_premium_emoji('economy_profile')} <b>Economy</b>"
                kb = create_economy_keyboard()
            elif data.startswith("veh_") or data == "unl_all_cars":
                menu_text = f"{get_premium_emoji('premium_hub')} <b>Premium</b>"
                kb = create_premium_keyboard()
            else:
                menu_text = f"{get_premium_emoji('unlocks_login')} <b>Unlocks</b>"
                kb = create_unlocks_keyboard()
            try:
                bot.edit_message_text(f"{get_premium_emoji('loading_progress')} Executing...\n\n{menu_text}",
                                      chat_id, msg_id, reply_markup=kb, parse_mode="HTML")
            except:
                pass
            if args:
                res = func(web_uid, *args)
            else:
                res = func(web_uid)
            if res and isinstance(res, dict) and res.get("ok"):
                deduct_tokens(chat_id, token_cost)
                final_text = (
                    f"{get_premium_emoji('success_preserved')} {html.escape(name)}\n"
                    f"🪙 -{token_cost} tokens\n"
                    f"💎 Balance: {get_user_tokens(chat_id)}\n\n{menu_text}"
                )
            else:
                err = clean_str(res.get("message", "Failed") if isinstance(res, dict) else "Timeout")
                final_text = f"{get_premium_emoji('cancel_failed_error')} {html.escape(err)}\n(No tokens deducted)\n\n{menu_text}"
            try:
                bot.edit_message_text(final_text, chat_id, msg_id, reply_markup=kb, parse_mode="HTML")
            except:
                pass
        except:
            pass

    if data == "eco_money_max":
        return exec_mod(call, "Money 50M", nuker.set_money, 50000000)
    if data == "eco_coins_max":
        return exec_mod(call, "Coins 500K", nuker.set_coin, 500000)
    if data == "eco_king":
        return exec_mod(call, "King Rank", nuker.set_rank)
    if data == "eco_money_cust":
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"💵 Enter money amount:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_money': True, 'msg_id': msg.message_id}
        return
    if data == "eco_coins_cust":
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"🪙 Enter coins amount:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_coin': True, 'msg_id': msg.message_id}
        return
    if data == "veh_fix":
        if not has_premium_access(chat_id) and not is_admin(chat_id):
            return
        return exec_mod(call, "Fix Account", nuker.fix_account)
    if data == "veh_unlock_all":
        if not has_premium_access(chat_id) and not is_admin(chat_id):
            return
        TOKEN_COST_ALL = TOKEN_COSTS["unlock_all_cars"]
        if not is_admin(chat_id):
            cur = get_user_tokens(chat_id)
            if cur < TOKEN_COST_ALL:
                try:
                    bot.answer_callback_query(call.id,
                        f"❌ Need {TOKEN_COST_ALL} tokens. You have {cur}.", show_alert=True)
                except:
                    pass
                return
        try:
            bot.edit_message_text(
                f"{get_premium_emoji('warning')} <b>WARNING: MASS INJECTION</b>\n"
                f"Inject all source cars?\n"
                f"🪙 Cost: {TOKEN_COST_ALL} tokens\nProceed?",
                chat_id, msg_id,
                reply_markup=types.InlineKeyboardMarkup().add(
                    get_btn("success_preserved", "YES, INJECT", callback_data="start_car_inject"),
                    get_btn("cancel_failed_error", "CANCEL", callback_data="menu_premium")
                ),
                parse_mode="HTML"
            )
        except:
            pass
        return
    if data == "start_car_inject":
        if not has_premium_access(chat_id) and not is_admin(chat_id):
            return
        TOKEN_COST = TOKEN_COSTS["unlock_all_cars"]
        if not is_admin(chat_id):
            cur = get_user_tokens(chat_id)
            if cur < TOKEN_COST:
                try:
                    bot.answer_callback_query(call.id, f"❌ Need {TOKEN_COST} tokens.", show_alert=True)
                except:
                    pass
                return
        td = nuker.get_token_data(get_web_uid(chat_id))
        em = td.get("email") if td else ""
        pw = td.get("password") if td else ""
        threading.Thread(target=background_inject_all_cars,
                         args=(chat_id, em, pw, msg_id)).start()
        return
    if data == "veh_unlock_single":
        if not has_premium_access(chat_id) and not is_admin(chat_id):
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"🚗 Enter Car ID:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_single_car_id': True, 'msg_id': msg.message_id}
        return
    if data == "unl_w16":
        return exec_mod(call, "W16", nuker.unlock_w16)
    if data == "unl_smoke":
        return exec_mod(call, "Smoke", nuker.unlock_smoke)
    if data == "unl_fuel":
        return exec_mod(call, "Fuel", nuker.unlimited_fuel)
    if data == "unl_damage":
        return exec_mod(call, "No Damage", nuker.disable_damage)
    if data == "unl_horns":
        return exec_mod(call, "Horns", nuker.unlock_horns)
    if data == "unl_anim":
        return exec_mod(call, "Animations", nuker.unlock_animations)
    if data == "unl_houses":
        return exec_mod(call, "Houses", nuker.unlock_houses)
    if data == "unl_wheels":
        return exec_mod(call, "Wheels", nuker.unlock_wheels)
    if data == "unl_levels":
        return exec_mod(call, "Levels", nuker.complete_all_levels)
    if data == "unl_clothes":
        return exec_mod(call, "Clothes", nuker.unlock_all_clothes)
    if data == "unl_ultimate":
        return exec_mod(call, "Ultimate", nuker.unlock_all_features)
    if data == "admin_panel":
        if not is_admin(chat_id):
            warn_unauthorized_cpm1(chat_id, "Admin Panel Button", user.username)
            return
        try:
            bot.edit_message_text(f"{get_premium_emoji('overseer_panel')} <b>OVERSEER TERMINAL</b>",
                                  chat_id, msg_id,
                                  reply_markup=create_admin_keyboard(), parse_mode="HTML")
        except:
            pass
        return
    if data == "admin_add_admin":
        if not is_admin(chat_id):
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"👤 Enter target ID:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_add_admin': True, 'msg_id': msg.message_id}
        return
    if data == "admin_rem_admin":
        if not is_admin(chat_id):
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"🗑️ Enter target ID:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_rem_admin': True, 'msg_id': msg.message_id}
        return
    if data == "admin_view_admins":
        if not is_admin(chat_id):
            return
        admins = get_all_admins()
        msg_text = f"👥 <b>ADMINS</b>\n\n" + "\n".join([f"<code>{uid}</code>" for uid in admins])
        try:
            bot.edit_message_text(msg_text, chat_id, msg_id,
                                  reply_markup=create_admin_keyboard(), parse_mode="HTML")
        except:
            pass
        return
    if data == "admin_add_prem":
        if not is_admin(chat_id):
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"✅ Enter: <code>user_id days</code>",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_add_prem': True, 'msg_id': msg.message_id}
        return
    if data == "admin_revoke":
        if not is_admin(chat_id):
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"❌ Enter target ID:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_revoke': True, 'msg_id': msg.message_id}
        return
    if data == "admin_broadcast":
        if not is_admin(chat_id):
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, f"📢 Enter broadcast message:",
                               reply_markup=cancel_keyboard(), parse_mode="HTML")
        user_states[chat_id] = {'awaiting_broadcast': True, 'msg_id': msg.message_id}
        return

# ================================================================
#  PAYMENT HANDLERS
# ================================================================
@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout(query):
    try:
        bot.answer_pre_checkout_query(query.id, ok=True)
    except:
        pass

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    try:
        chat_id = message.chat.id

        if is_blocked_by_ban(chat_id):
            send_ban_message(chat_id)
            return

        payload = message.successful_payment.invoice_payload
        parts = payload.split("_")
        if len(parts) >= 5 and parts[0] == "cpm1" and parts[1] == "sub":
            stars = int(parts[2])
            days = int(parts[3])
            prem_days = int(parts[4])
            activate_subscription(chat_id, days, prem_days)
            plan_map = {50: "1 Day (No Premium)", 200: "1 Week + Premium",
                        350: "1 Month + Premium", 550: "Lifetime + Premium"}
            plan_label = plan_map.get(stars, f"{stars}⭐")
            expiry_str = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d') if days < 36500 else "Lifetime"
            prem_str = (datetime.now() + timedelta(days=prem_days)).strftime('%Y-%m-%d') if 0 < prem_days < 36500 else ("Lifetime" if prem_days >= 36500 else "No Premium")
            bot.send_message(chat_id,
                f"{get_premium_emoji('success_preserved')} <b>PAYMENT SUCCESSFUL!</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📦 Plan: {plan_label}\n"
                f"✅ Expires: {expiry_str}\n"
                f"👑 Premium: {prem_str}\n\nEnjoy!",
                parse_mode="HTML")
            try:
                bot.send_message(ADMIN_ID,
                    f"✅ <b>NEW STARS PAYMENT</b>\n"
                    f"👤 @{message.from_user.username or 'Unknown'}\n"
                    f"🆔 <code>{chat_id}</code>\n"
                    f"⭐ {stars} Stars\n"
                    f"📦 {plan_label}",
                    parse_mode="HTML")
            except:
                pass
        elif len(parts) >= 4 and parts[0] == "cpm1" and parts[1] == "tok":
            stars = int(parts[2])
            tokens = int(parts[3])
            add_tokens(chat_id, tokens)
            new_balance = get_user_tokens(chat_id)

            premium_msg = ""
            if tokens >= PREMIUM_AUTO_UNLOCK_AMOUNT:
                fb_patch(f"cpm1_users/{chat_id}", {"premium_by_tokens": True})
                premium_msg = (
                    f"\n\n👑 <b>PREMIUM UNLOCKED!</b>\n"
                    f"Your purchase of <b>{tokens} tokens</b> activated premium access.\n"
                    f"Premium stays active while your balance is above <b>{PREMIUM_TOKEN_THRESHOLD} tokens</b>."
                )

            bot.send_message(chat_id,
                f"{get_premium_emoji('success_preserved')} <b>TOKENS ADDED!</b>\n\n"
                f"🪙 Added: <code>{tokens}</code>\n"
                f"💎 New Balance: <code>{new_balance}</code>"
                f"{premium_msg}",
                parse_mode="HTML")
    except:
        pass

# ================================================================
#  MAIN ENTRY POINT
# ================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("⚡ MARKCPM1TOOLS V25.0 - FINAL EDITION ⚡")
    print("=" * 60)
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)
