#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
☠️☠️☠️ 𝙈𝘼𝙍𝙆𝘾𝙋𝙈1𝙏𝙊𝙊𝙇𝙎 - CPM1 ULTIMATE ☠️☠️☠️
FIXED: Using partner's working car injection engine (full car data with vinyls).
SOURCE ACCOUNT: markryancpm1unlockall2541@gmail.com
OPTIMIZED: Bulk clone 1-10 with progress & ETA.
"""

import requests
import time
import json
import telebot
import random
import base64
import sys
import os
import string
import struct
import brotli
import hashlib
import zlib
import threading
import concurrent.futures
import sqlite3
import gc
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from telebot import types
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import urllib3
from flask import Flask, jsonify

# ═══════════════════════════════════════════════════════════
# 🌐 FLASK WEB SERVER
# ═══════════════════════════════════════════════════════════
app = Flask(__name__)
@app.route('/')
def home():
    return jsonify({"status": "MARKCPM1TOOLS Online", "version": "21.8"})
@app.route('/health')
def health(): return jsonify({"status": "healthy"})
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False, use_reloader=False)
threading.Thread(target=run_flask, daemon=True).start()

# ═══════════════════════════════════════════════════════════
# 📡 GLOBAL CONFIG
# ═══════════════════════════════════════════════════════════
HAS_BROTLI = True
HAS_CRYPTO = True
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = '8857657486:AAFE8F3DZySsrh_1-N_Qt2lOsS97OtzcgDQ'
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=10)

try:
    bot.remove_webhook()
    time.sleep(1)
except:
    pass

try:
    bot.set_my_commands([
        telebot.types.BotCommand("/start", "⚡ Open Main Terminal"),
        telebot.types.BotCommand("/admin", "👑 Open Overseer Panel"),
        telebot.types.BotCommand("/login", "🔑 Login via command (backup)")
    ])
except: pass

# ✅ UPDATED SOURCE ACCOUNT
FK = "AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"
SOURCE_ACCOUNT = ('markryancpm1unlockall7193@gmail.com', 'markryancpm1')
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

# ═══════════════════════════════════════════════════════════
# 📢 GROUP LOG ID
# ═══════════════════════════════════════════════════════════
GROUP_LOG_ID = -1004441134033

# ═══════════════════════════════════════════════════════════
# 📡 HTTP SESSION
# ═══════════════════════════════════════════════════════════
http_session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=3)
http_session.mount('https://', adapter)
http_session.mount('http://', adapter)

# ═══════════════════════════════════════════════════════════
# 🛡️ DATABASE
# ═══════════════════════════════════════════════════════════
ADMIN_IDS = set()
TRACKED_USERS_CACHE = set()
db_path = "glitchyn_data.db"

with sqlite3.connect(db_path) as c:
    c.execute("CREATE TABLE IF NOT EXISTS premium_users (user_id INTEGER PRIMARY KEY)")
    c.execute("CREATE TABLE IF NOT EXISTS tokens (user_id INTEGER PRIMARY KEY, auth_token TEXT, email TEXT, password TEXT, refresh_token TEXT, firebase_uid TEXT, token_expires_at REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS user_data (cache_key TEXT PRIMARY KEY, email TEXT, data_json TEXT, saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS bot_users (user_id INTEGER PRIMARY KEY)")
    c.execute("CREATE TABLE IF NOT EXISTS bot_admins (user_id INTEGER PRIMARY KEY)")
    c.execute("CREATE TABLE IF NOT EXISTS bot_states (user_id INTEGER PRIMARY KEY, state_json TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    c.execute("CREATE TABLE IF NOT EXISTS coin_data (user_id INTEGER PRIMARY KEY, coins INTEGER DEFAULT 0, unlimited INTEGER DEFAULT 0, subscribed INTEGER DEFAULT 0, expiry TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS user_subscriptions (user_id INTEGER PRIMARY KEY, expires REAL, duration INTEGER, key TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS time_keys (key TEXT PRIMARY KEY, expires REAL, duration INTEGER, used INTEGER DEFAULT 0, user_id INTEGER, created_by INTEGER, created_at REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS trial_keys (key TEXT PRIMARY KEY, expires REAL, used INTEGER DEFAULT 0, user_id INTEGER, created_at REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS stars_balance (total_stars INTEGER DEFAULT 0)")
    c.commit()

# Load admins and users
with sqlite3.connect(db_path) as c:
    if c.execute("SELECT COUNT(*) FROM bot_admins").fetchone()[0] == 0:
        for aid in [8254935096, 6531314640]:
            c.execute("INSERT INTO bot_admins (user_id) VALUES (?)", (aid,))
        c.commit()
    for row in c.execute("SELECT user_id FROM bot_admins").fetchall():
        ADMIN_IDS.add(row[0])
    for row in c.execute("SELECT user_id FROM bot_users").fetchall():
        TRACKED_USERS_CACHE.add(row[0])

print("✅ SQLite Database Ready!")

# ═══════════════════════════════════════════════════════════
# 🪙 COIN & SUBSCRIPTION SYSTEM (UNTOUCHED - WORKING)
# ═══════════════════════════════════════════════════════════
COIN_COSTS = {"individual": 50, "clone": 100, "bulk": 250}

def _ensure_coin_user(user_id):
    with sqlite3.connect(db_path) as c:
        c.execute("INSERT OR IGNORE INTO coin_data (user_id, coins, unlimited, subscribed) VALUES (?,0,0,0)", (user_id,))

def get_user_coins(user_id):
    with sqlite3.connect(db_path) as c:
        row = c.execute("SELECT coins FROM coin_data WHERE user_id=?", (user_id,)).fetchone()
        return row[0] if row else 0

def set_user_coins(user_id, amount):
    _ensure_coin_user(user_id)
    with sqlite3.connect(db_path) as c:
        c.execute("UPDATE coin_data SET coins=? WHERE user_id=?", (amount, user_id))
        c.commit()

def add_coins(user_id, amount):
    current = get_user_coins(user_id)
    set_user_coins(user_id, current + amount)

def deduct_coins(user_id, amount):
    current = get_user_coins(user_id)
    if current < amount: return False
    set_user_coins(user_id, current - amount)
    return True

def is_unlimited(user_id):
    with sqlite3.connect(db_path) as c:
        row = c.execute("SELECT unlimited FROM coin_data WHERE user_id=?", (user_id,)).fetchone()
        return bool(row[0]) if row else False

def set_unlimited(user_id, status):
    _ensure_coin_user(user_id)
    val = 1 if status else 0
    with sqlite3.connect(db_path) as c:
        c.execute("UPDATE coin_data SET unlimited=? WHERE user_id=?", (val, user_id))
        c.commit()

def is_subscribed_coins(user_id):
    with sqlite3.connect(db_path) as c:
        row = c.execute("SELECT subscribed, expiry FROM coin_data WHERE user_id=?", (user_id,)).fetchone()
        if row and row[0]:
            if row[1]:
                try:
                    if datetime.strptime(row[1], "%Y-%m-%d").date() < datetime.today().date():
                        return False
                except:
                    pass
            return True
        return False

def set_subscribed_coins(user_id, status, months=0):
    _ensure_coin_user(user_id)
    with sqlite3.connect(db_path) as c:
        if months > 0:
            expiry = (datetime.today().date() + timedelta(days=months*30)).strftime("%Y-%m-%d")
            c.execute("UPDATE coin_data SET subscribed=?, expiry=? WHERE user_id=?", (1 if status else 0, expiry, user_id))
        else:
            c.execute("UPDATE coin_data SET subscribed=?, expiry=NULL WHERE user_id=?", (1 if status else 0, user_id))
        c.commit()

def get_subscription_expiry(user_id):
    with sqlite3.connect(db_path) as c:
        row = c.execute("SELECT expires FROM user_subscriptions WHERE user_id=?", (user_id,)).fetchone()
        if row:
            return row[0]
    return None

def has_active_subscription(user_id):
    if is_subscribed_coins(user_id):
        return True
    expiry = get_subscription_expiry(user_id)
    if expiry and expiry > time.time():
        return True
    if is_unlimited(user_id):
        return True
    return False

def set_user_subscription_time(user_id, duration_hours, key=None):
    expires = time.time() + duration_hours * 3600
    with sqlite3.connect(db_path) as c:
        c.execute("INSERT OR REPLACE INTO user_subscriptions (user_id, expires, duration, key) VALUES (?,?,?,?)", (user_id, expires, duration_hours, key))
        c.commit()

def get_subscription_display(user_id):
    if has_active_subscription(user_id):
        expiry = get_subscription_expiry(user_id)
        if expiry:
            remaining = max(0, expiry - time.time())
            hours = int(remaining // 3600)
            mins = int((remaining % 3600) // 60)
            if hours > 0:
                return f"⏱️ **Subscription:** {hours}h {mins}m remaining"
            else:
                return f"⏱️ **Subscription:** {mins}m remaining"
        with sqlite3.connect(db_path) as c:
            row = c.execute("SELECT expiry FROM coin_data WHERE user_id=?", (user_id,)).fetchone()
            if row and row[0]:
                try:
                    exp = datetime.strptime(row[0], "%Y-%m-%d")
                    days_left = (exp.date() - datetime.today().date()).days
                    return f"⏱️ **Subscription:** {days_left} days remaining"
                except:
                    pass
        if is_unlimited(user_id):
            return "⏱️ **Subscription:** Unlimited"
        return "⏱️ **Subscription:** Active"
    return "❌ No active subscription"

def check_and_deduct_coins(chat_id, amount, feature_name):
    if is_admin(chat_id):
        return True
    if has_active_subscription(chat_id):
        return True
    current = get_user_coins(chat_id)
    if current < amount:
        bot.send_message(chat_id, f"❌ Not enough coins! You have {current}. Need {amount} for {feature_name}.", parse_mode='Markdown')
        return False
    deduct_coins(chat_id, amount)
    return True

def get_coin_display(chat_id):
    if has_active_subscription(chat_id) or is_admin(chat_id):
        return "🪙 **Unlimited** (Active Subscription/Admin)"
    coins = get_user_coins(chat_id)
    unlimited = is_unlimited(chat_id)
    return f"🪙 **Coins:** {coins}{' (Unlimited)' if unlimited else ''}"

# ═══════════════════════════════════════════════════════════
# 🔑 TIME KEY & TRIAL
# ═══════════════════════════════════════════════════════════
def generate_time_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

def create_time_key(duration_hours, created_by):
    key = generate_time_key()
    expires = time.time() + duration_hours * 3600
    with sqlite3.connect(db_path) as c:
        c.execute("INSERT INTO time_keys (key, expires, duration, used, user_id, created_by, created_at) VALUES (?,?,?,0,?,?,?)", (key, expires, duration_hours, None, created_by, time.time()))
        c.commit()
    return key

def use_time_key(key, user_id):
    with sqlite3.connect(db_path) as c:
        row = c.execute("SELECT expires, duration, used, user_id FROM time_keys WHERE key=?", (key,)).fetchone()
        if not row: return False, "Key not found"
        if row[0] < time.time(): return False, "Key expired"
        if row[2]:
            if row[3] == user_id: return True, "Key already used by you (still valid)"
            return False, "Key used by another user"
        c.execute("UPDATE time_keys SET used=1, user_id=? WHERE key=?", (user_id, key))
        c.commit()
        set_user_subscription_time(user_id, row[1], key)
        return True, "Key activated"

def generate_trial_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

def create_trial_key(user_id=None, minutes=10):
    key = generate_trial_key()
    expires = time.time() + minutes * 60
    with sqlite3.connect(db_path) as c:
        c.execute("INSERT INTO trial_keys (key, expires, used, user_id, created_at) VALUES (?,?,0,?,?)", (key, expires, user_id, time.time()))
        c.commit()
    return key

def use_trial_key(key, user_id):
    with sqlite3.connect(db_path) as c:
        row = c.execute("SELECT expires, used, user_id FROM trial_keys WHERE key=?", (key,)).fetchone()
        if not row: return False, "Invalid"
        if row[0] < time.time(): return False, "Expired"
        if row[1]:
            if row[2] == user_id: return True, "Already used by you"
            return False, "Used by another user"
        c.execute("UPDATE trial_keys SET used=1, user_id=? WHERE key=?", (user_id, key))
        c.commit()
        set_user_subscription_time(user_id, 10/60, key)
        return True, "Success"

# ═══════════════════════════════════════════════════════════
# 💳 SUBSCRIPTION SETTINGS (UPDATED PAYMENT DETAILS)
# ═══════════════════════════════════════════════════════════
SUBSCRIPTION_DURATIONS = {
    "1_day": 24, "5_days": 120, "1_week": 168, "3_weeks": 504,
    "5_weeks": 840, "7_weeks": 1176, "12_weeks": 2016,
    "14_weeks": 2352,
}
SUBSCRIPTION_STARS = {
    "1_day": 30, "5_days": 130, "1_week": 200, "3_weeks": 250,
    "5_weeks": 300, "7_weeks": 330, "12_weeks": 1050,
    "14_weeks": 1250,
}
SUBSCRIPTION_MONEY = {
    "1_day": "30 Pesos | $1", "5_days": "130 Pesos | $3",
    "1_week": "200 Pesos | $4", "3_weeks": "250 Pesos | $5",
    "5_weeks": "300 Pesos | $6", "7_weeks": "330 Pesos | $7",
    "12_weeks": "1,050 Pesos | $13", "14_weeks": "1,250 Pesos | $17",
}
PAYMENT_METHODS = {
    "paypal": {
        "label": "💳 PayPal",
        "details": "📧 **Email:** `markryanmanoguid867@gmail.com`\n👤 **Name:** Markryan Manoguid\n📌 Please screenshot the payment."
    },
    "paymaya": {
        "label": "📱 PayMaya",
        "details": "📱 **Number:** `09281630511`\n👤 **Name:** MARK RYAN MANOGUID\n📌 Please screenshot the payment."
    },
    "gcash_to_paymaya": {
        "label": "🔄 GCash to PayMaya",
        "details": "📌 DM @Maarkryan so he can send the QR code.\n📌 Please screenshot the payment."
    }
}
PENDING_SUBSCRIPTIONS = {}

# ═══════════════════════════════════════════════════════════
# 🌟 STARS BALANCE
# ═══════════════════════════════════════════════════════════
def add_stars_balance(amount):
    with sqlite3.connect(db_path) as c:
        c.execute("UPDATE stars_balance SET total_stars = total_stars + ?", (amount,))
        if c.rowcount == 0:
            c.execute("INSERT INTO stars_balance (total_stars) VALUES (?)", (amount,))
        c.commit()

def get_stars_balance():
    with sqlite3.connect(db_path) as c:
        row = c.execute("SELECT total_stars FROM stars_balance").fetchone()
        return row[0] if row else 0

def reset_stars_balance():
    with sqlite3.connect(db_path) as c:
        c.execute("UPDATE stars_balance SET total_stars = 0")
        if c.rowcount == 0:
            c.execute("INSERT INTO stars_balance (total_stars) VALUES (0)")
        c.commit()

# ═══════════════════════════════════════════════════════════
# 🛡️ ORIGINAL GLITCHYNxMARK FUNCTIONS (100% UNTOUCHED)
# ═══════════════════════════════════════════════════════════
def track_user(user_id):
    if user_id in TRACKED_USERS_CACHE: return
    TRACKED_USERS_CACHE.add(user_id)
    with sqlite3.connect(db_path) as c:
        c.execute("INSERT OR IGNORE INTO bot_users (user_id) VALUES (?)", (user_id,))
        c.commit()

def get_total_users(): return len(TRACKED_USERS_CACHE)
def get_all_tracked_users(): return list(TRACKED_USERS_CACHE)
def is_admin(user_id): return user_id in ADMIN_IDS

def add_admin(user_id):
    ADMIN_IDS.add(user_id)
    with sqlite3.connect(db_path) as c:
        c.execute("INSERT OR IGNORE INTO bot_admins (user_id) VALUES (?)", (user_id,))
        c.commit()
    return True

def remove_admin(user_id):
    ADMIN_IDS.discard(user_id)
    with sqlite3.connect(db_path) as c:
        c.execute("DELETE FROM bot_admins WHERE user_id=?", (user_id,))
        c.commit()
    return True

def get_all_admins(): return list(ADMIN_IDS)

def is_premium(user_id):
    if is_admin(user_id): return True
    with sqlite3.connect(db_path) as c:
        return bool(c.execute("SELECT user_id FROM premium_users WHERE user_id=?", (user_id,)).fetchone())

def approve_premium(user_id):
    with sqlite3.connect(db_path) as c:
        c.execute("INSERT OR REPLACE INTO premium_users (user_id) VALUES (?)", (user_id,))
        c.commit()

def revoke_premium(user_id):
    with sqlite3.connect(db_path) as c:
        c.execute("DELETE FROM premium_users WHERE user_id=?", (user_id,))
        c.commit()

def get_all_approved():
    with sqlite3.connect(db_path) as c:
        return c.execute("SELECT user_id FROM premium_users").fetchall()

def save_state(user_id: int, state: dict):
    with sqlite3.connect(db_path) as c:
        c.execute("INSERT OR REPLACE INTO bot_states (user_id, state_json, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)", (user_id, json.dumps(state)))
        c.commit()

def load_state(user_id: int) -> Optional[dict]:
    with sqlite3.connect(db_path) as c:
        row = c.execute("SELECT state_json FROM bot_states WHERE user_id=?", (user_id,)).fetchone()
        if row:
            try: return json.loads(row[0])
            except: pass
    return None

def delete_state(user_id: int):
    with sqlite3.connect(db_path) as c:
        c.execute("DELETE FROM bot_states WHERE user_id=?", (user_id,))
        c.commit()

def clean_str(text):
    if not text: return "Unknown"
    return str(text).replace('_', '-').replace('*', '•').replace('`', "'").replace('[', '(').replace(']', ')')

# ═══════════════════════════════════════════════════════════
# ⚙️ CORE ENCRYPTION & PARSERS (100% ORIGINAL FROM GLITCHYNxMARK)
# ═══════════════════════════════════════════════════════════
def make_xor_key(uid: str) -> bytes:
    chars = list(str(uid or ""))
    if len(chars) >= 9: chars[1], chars[8] = chars[8], chars[1]
    if len(chars) >= 3: chars.pop(2)
    if len(chars) >= 5: chars.append(chars[4])
    return "".join(chars).encode("utf-8") or b"0"

def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))

def decompress(data: bytes):
    if HAS_BROTLI:
        try: return brotli.decompress(data)
        except: pass
    for args in ((zlib.MAX_WBITS | 16,), tuple()):
        try: return zlib.decompress(data, *args)
        except: pass
    return None

def decrypt_aes(data: bytes, key: bytes):
    if not HAS_CRYPTO: return None
    try: return unpad(AES.new(key[:16], AES.MODE_CBC, b"\x00" * 16).decrypt(data), 16)
    except: return None

def _md5(text: str) -> bytes: return hashlib.md5(str(text).encode()).digest()
def _sha1(text: str) -> bytes: return hashlib.sha1(str(text).encode()).digest()[:16]

def build_aes_keys(uid: str, password: str = None, email: str = None) -> list:
    keys = [_md5("olzhas_carparking")]
    if password: keys.extend([_md5(password), _sha1(password)])
    if uid: keys.extend([_md5(uid), _sha1(uid)])
    if email: keys.append(_md5(email))
    return keys

class Reader:
    def __init__(self, data: bytes): self.buf, self.pos = data, 0
    def has_bytes(self, n: int) -> bool: return self.pos + n <= len(self.buf)
    def read_byte(self) -> int:
        if not self.has_bytes(1): return 0
        v = self.buf[self.pos]; self.pos += 1; return v
    def read_int(self) -> int:
        if not self.has_bytes(4): self.pos = len(self.buf); return 0
        v = struct.unpack_from("<i", self.buf, self.pos)[0]; self.pos += 4; return v
    def read_float(self) -> float:
        if not self.has_bytes(4): self.pos = len(self.buf); return 0.0
        v = struct.unpack_from("<f", self.buf, self.pos)[0]; self.pos += 4; return v
    def read_string(self) -> str:
        marker = self.read_int()
        if marker in (0, -1): return ""
        length = (-marker) - 1 if marker < -1 else marker
        if marker < -1: self.read_int()
        length = max(0, min(length, 1000000))
        if not self.has_bytes(length): return ""
        text = self.buf[self.pos:self.pos + length].decode("utf-8", errors="replace")
        self.pos += length
        return text.replace("\x00", "").strip()
    def read_list(self, item_fn):
        count = self.read_int()
        if count <= 0 or count > 1000000: return []
        res = []
        for _ in range(count):
            if self.pos >= len(self.buf): break
            val = item_fn()
            if val is not None: res.append(val)
        return res
    def read_dict(self) -> dict:
        count = self.read_int()
        if count <= 0 or count > 1000000: return {}
        res = {}
        for _ in range(count):
            if self.pos >= len(self.buf): break
            res[self.read_int()] = self.read_int()
        return res
    def read_equipment(self):
        if self.read_byte() == 0: return None
        return {k: self.read_list(self.read_int) for k in ["hair","face","beard","cap","mask","top","gloves","bag","pants","shoes","glasses","SelectedEquipments"]} | {"Gender": self.read_int()}

def parse_player(buf: bytes) -> dict:
    r = Reader(buf)
    if r.read_byte() == 0: return None
    player = {"Name": r.read_string(), "money": r.read_int(), "coin": r.read_int(), "localID": r.read_string(), "boughtFsos": r.read_list(r.read_int)}
    player["FriendsID"] = r.read_list(lambda: (r.read_byte(), {"id": r.read_string(), "Name": r.read_string(), "accountID": r.read_string()})[1])
    player["LevelsDoneTime"] = r.read_list(r.read_float)
    player["floats"] = r.read_list(r.read_float)
    player["integers"] = r.read_list(r.read_int)
    player["fcar"] = r.read_list(r.read_int)
    player["favouriteWheels"] = r.read_list(r.read_int)
    player["favouriteVinyls"] = r.read_list(r.read_int)
    player["favouriteEmojis"] = r.read_list(r.read_int)
    player["personEquipmentsMale"] = r.read_equipment()
    player["personEquipmentsFemale"] = r.read_equipment()
    if r.read_byte() == 0: player["platesData"] = None
    else:
        def read_vinyl():
            r.read_byte()
            return {"vectors": r.read_list(lambda: {"x": r.read_float(), "y": r.read_float(), "z": r.read_float()}), "v": r.read_list(r.read_string), "floats": r.read_list(r.read_float), "text": r.read_string()}
        def read_plate():
            r.read_byte()
            return {"plateId": r.read_int(), "frontCarId": r.read_int(), "rearCarId": r.read_int(), "vinyls": r.read_list(read_vinyl)}
        player["platesData"] = {"allPlates": r.read_list(read_plate)}
    if r.read_byte() == 0: player["carIDnStatus"] = None
    else: player["carIDnStatus"] = {"carGeneratedIDs": r.read_list(r.read_string), "carStatus": r.read_list(r.read_int)}
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
    if candidates[1]: candidates.append(decompress(candidates[1]))
    for candidate in filter(None, candidates):
        if candidate[0] in (17, 23, 24):
            try:
                p = parse_player(candidate)
                if p and p.get("Name") is not None: return p
            except: pass
        try:
            clean = candidate[3:] if len(candidate) >= 3 and candidate[:2] == b"\xef\xbb" else candidate
            if clean and clean[0] == 123: return json.loads(clean.decode("utf-8"))
        except: pass
    return None

def decrypt_player_record(base64_text: str, uid: str, password: str = None, email: str = None) -> dict:
    try: buf = base64.b64decode(base64_text)
    except: return {"success": False, "message": "Bad base64"}
    if len(buf) < 10: return {"success": False, "message": "Too small"}
    direct = try_parse(buf)
    if direct: return {"success": True, "record": direct}
    if uid:
        try:
            decoded = decompress(xor_bytes(buf, make_xor_key(uid)))
            if decoded:
                parsed = try_parse(decoded)
                if parsed: return {"success": True, "record": parsed}
        except: pass
    for key in build_aes_keys(uid or "", password, email):
        plain = decrypt_aes(buf, key)
        if not plain: continue
        parsed = try_parse(plain)
        if parsed: return {"success": True, "record": parsed}
    return {"success": False, "message": "Could not decrypt"}

class Writer:
    def __init__(self): self._p: List[bytes] = []
    def write_byte(self, v): self._p.append(bytes([int(v or 0) & 0xFF]))
    def write_int(self, v): self._p.append(struct.pack("<i", int(v or 0)))
    def write_float(self, v): self._p.append(struct.pack("<f", float(v or 0.0)))
    def write_string(self, s):
        if s is None: self._p.append(struct.pack("<i", -1)); return
        s = str(s)
        if s == "": self._p.append(struct.pack("<i", 0)); return
        enc = s.encode("utf-8")
        self._p.append(struct.pack("<ii", -(len(enc)) - 1, len(s)) + enc)
    def write_list(self, lst, fn):
        if lst is None: self._p.append(struct.pack("<i", -1)); return
        self._p.append(struct.pack("<i", len(lst)))
        for item in lst: fn(item)
    def write_equipment(self, data):
        if not data: self.write_byte(0); return
        self.write_byte(13)
        for key in ["hair","face","beard","cap","mask","top","gloves","bag","pants","shoes","glasses","SelectedEquipments"]:
            self.write_list(data.get(key, []), self.write_int)
        self.write_int(data.get("Gender", 0))
    def write_plates(self, data):
        if not data: self.write_byte(0); return
        self.write_byte(1)
        plates = data.get("allPlates", [])
        self._p.append(struct.pack("<i", len(plates)))
        for plate in plates:
            self.write_byte(4); self.write_int(plate.get("plateId", 0)); self.write_int(plate.get("frontCarId", 0)); self.write_int(plate.get("rearCarId", 0))
            vinyls = plate.get("vinyls", [])
            self._p.append(struct.pack("<i", len(vinyls)))
            for vinyl in vinyls:
                self.write_byte(4)
                vecs = vinyl.get("vectors", [])
                self._p.append(struct.pack("<i", len(vecs)))
                for vec in vecs: self._p.append(struct.pack("<fff", vec.get("x", 0), vec.get("y", 0), vec.get("z", 0)))
                self.write_list(vinyl.get("v", []), self.write_string)
                self.write_list(vinyl.get("floats", []), self.write_float)
                self.write_string(vinyl.get("text", ""))
    def write_car_id_status(self, data):
        if not data: self.write_byte(0); return
        self.write_byte(2)
        self.write_list(data.get("carGeneratedIDs", []), self.write_string)
        self.write_list(data.get("carStatus", []), self.write_int)
    def to_bytes(self): return b"".join(self._p)

FIELD_MAPPING = [
    (1, "localID"), (2, "money"), (3, "Name"), (4, "coin"), (5, "allData"),
    (6, "boughtFsos"), (7, "boughtPoliceLights"), (8, "boughtPoliceSirens"),
    (9, "FriendsID"), (10, "LevelsDoneTime"), (11, "floats"), (12, "integers"),
    (13, "fcar"), (14, "favouriteWheels"), (15, "favouriteVinyls"),
    (16, "favouriteEmojis"), (18, "emojiPacks"),
    (41, "personEquipmentsMale"), (42, "personEquipmentsFemale"),
    (43, "platesData"), (44, "carIDnStatus"), (45, "flags"),
    (46, "animations"), (48, "wheels")
]
INT_LIST_FIELDS = {6,7,8,12,13,14,15,16,18,46,48}
FLOAT_LIST_FIELDS = {10,11}

def _field_modified(new_value, old_value) -> bool:
    if new_value is None and old_value is None: return False
    if new_value is None or old_value is None: return True
    if type(new_value) != type(old_value): return True
    if isinstance(new_value, (dict, list)):
        return json.dumps(new_value, sort_keys=True) != json.dumps(old_value, sort_keys=True)
    return new_value != old_value

def serialize_field(fid: int, value: Any) -> Optional[bytes]:
    w = Writer()
    if fid in (1,3,5): w.write_string(value); return w.to_bytes()
    if fid in (2,4): w.write_int(value or 0); return w.to_bytes()
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
        w.write_list(value or [], w.write_int); return w.to_bytes()
    if fid in FLOAT_LIST_FIELDS:
        w.write_list(value or [], w.write_float); return w.to_bytes()
    if fid in (41,42): w.write_equipment(value); return w.to_bytes()
    if fid == 43: w.write_plates(value); return w.to_bytes()
    if fid == 44: w.write_car_id_status(value); return w.to_bytes()
    if fid == 45:
        w._p.append(struct.pack("<i", len(value or {})))
        for key, val in (value or {}).items():
            w.write_int(int(key)); w.write_int(int(val))
        return w.to_bytes()
    return None

def build_payload(record: Dict[str, Any], uid: str, original: Optional[Dict[str, Any]] = None, force_fields: Optional[set] = None) -> str:
    force_fields = set(force_fields or [])
    fields = []
    for fid, key in FIELD_MAPPING:
        value = record.get(key)
        if value is None: continue
        if key == "allData": should_send = isinstance(value, str) and len(value) > 0
        elif key in force_fields: should_send = True
        elif original is not None: should_send = _field_modified(value, original.get(key))
        else: should_send = True
        if not should_send: continue
        raw = serialize_field(fid, value)
        if raw is not None: fields.append((fid, raw))
    parts = [struct.pack("<i", len(fields))]
    for fid, raw in fields:
        parts.extend([struct.pack("<hi", fid, len(raw)), raw])
    combined = b"".join(parts)
    compressed = brotli.compress(combined) if HAS_BROTLI else zlib.compress(combined)
    encrypted = xor_bytes(compressed, make_xor_key(uid))
    return base64.b64encode(encrypted).decode("ascii")

# ═══════════════════════════════════════════════════════════
# ⚙️ SyncCPMNuker (100% ORIGINAL FROM GLITCHYNxMARK)
# ═══════════════════════════════════════════════════════════
class SyncCPMNuker:
    def __init__(self): self.cache = {}
    def _ck(self, uid: int, email: Optional[str] = None) -> str:
        td = self.get_token_data(uid)
        return f"{uid}_{email or (td.get('email') if td else '')}"
    def save_token(self, uid: int, auth: str, email: str, pw: Optional[str] = None, rt: Optional[str] = None, fuid: Optional[str] = None):
        with sqlite3.connect(db_path) as c:
            c.execute("INSERT OR REPLACE INTO tokens (user_id, auth_token, email, password, refresh_token, firebase_uid, token_expires_at) VALUES (?,?,?,?,?,?,?)", (uid, auth, email, pw, rt, fuid, time.time() + 3600))
            c.commit()
    def get_token_data(self, uid: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(db_path) as c:
            row = c.execute("SELECT auth_token, email, password, refresh_token, firebase_uid, token_expires_at FROM tokens WHERE user_id=?", (uid,)).fetchone()
            if not row: return None
            return {"auth_token": row[0], "email": row[1], "password": row[2], "refresh_token": row[3], "firebase_uid": row[4], "token_expires_at": row[5]}
    def update_token(self, uid: int, auth: str, rt: Optional[str] = None):
        with sqlite3.connect(db_path) as c:
            if rt:
                c.execute("UPDATE tokens SET auth_token=?, refresh_token=?, token_expires_at=? WHERE user_id=?", (auth, rt, time.time() + 3600, uid))
            else:
                c.execute("UPDATE tokens SET auth_token=?, token_expires_at=? WHERE user_id=?", (auth, time.time() + 3600, uid))
            c.commit()
    def delete_token(self, uid: int):
        with sqlite3.connect(db_path) as c:
            c.execute("DELETE FROM tokens WHERE user_id=?", (uid,))
            c.commit()
        for key in list(self.cache.keys()):
            if key.startswith(str(uid)): del self.cache[key]
    def is_expired(self, uid: int) -> bool:
        td = self.get_token_data(uid)
        return not td or not td.get("token_expires_at") or td.get("token_expires_at") < time.time()
    def get_record(self, uid: int, email: Optional[str] = None) -> Dict[str, Any]:
        ck = self._ck(uid, email)
        if ck not in self.cache:
            with sqlite3.connect(db_path) as c:
                row = c.execute("SELECT data_json FROM user_data WHERE cache_key=?", (ck,)).fetchone()
            if row:
                try: self.cache[ck] = json.loads(row[0])
                except: pass
        return self.cache.get(ck, {})
    def set_record(self, uid: int, data: Dict[str, Any], email: Optional[str] = None):
        ck = self._ck(uid, email)
        self.cache[ck] = data
        with sqlite3.connect(db_path) as c:
            c.execute("INSERT OR REPLACE INTO user_data (cache_key, email, data_json) VALUES (?, ?, ?)", (ck, email, json.dumps(data)))
            c.commit()
    def _post(self, url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        try:
            clean_headers = {k: v for k, v in headers.items() if k.lower() != "host"}
            resp = http_session.post(url, json=payload, headers=clean_headers, timeout=20)
            try: return resp.json()
            except: return {"raw": resp.text, "status": resp.status_code, "ok": False}
        except Exception as e: return {"ok": False, "message": "CONNECTION FAILED"}
    def login(self, email: str, password: str) -> Dict[str, Any]:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FK}"
        payload = {"email": email, "password": password, "returnSecureToken": True, "clientType": "CLIENT_TYPE_ANDROID"}
        result = self._post(url, payload, GAME_HEADERS)
        if result.get("ok") is False: return result
        if "idToken" in result: return {"ok": True, "auth": result["idToken"], "refresh_token": result.get("refreshToken", ""), "firebase_uid": result.get("localId", "")}
        err = "INVALID_CREDENTIALS"
        try:
            if isinstance(result.get("error"), dict): err = str(result["error"].get("message", "INVALID_CREDENTIALS"))
            elif isinstance(result.get("error"), str): err = result["error"]
        except: pass
        return {"ok": False, "message": err.upper()[:80]}
    def _refresh(self, uid: int) -> Tuple[bool, str]:
        td = self.get_token_data(uid)
        if not td: return False, "NO_TOKEN"
        rt, em, pw = td.get("refresh_token"), td.get("email"), td.get("password")
        if rt:
            res = self._post(f"https://securetoken.googleapis.com/v1/token?key={FK}", {"grant_type": "refresh_token", "refresh_token": rt}, {"Content-Type": "application/json"})
            if res.get("id_token"):
                self.update_token(uid, res["id_token"], res.get("refresh_token", rt))
                return True, "OK"
        if em and pw:
            res = self.login(em, pw)
            if res.get("ok"):
                self.save_token(uid, res["auth"], em, pw, res.get("refresh_token", ""), res.get("firebase_uid", ""))
                return True, "OK"
        return False, "REFRESH_FAILED"
    def get_auth(self, uid: int) -> Tuple[bool, str, str]:
        if self.is_expired(uid):
            ok, msg = self._refresh(uid)
            if not ok: return False, msg, ""
        td = self.get_token_data(uid)
        if td and td.get("auth_token"): return True, "OK", td.get("auth_token")
        return False, "NO_TOKEN", ""
    def load(self, uid: int, force: bool = False) -> bool:
        td = self.get_token_data(uid)
        if not td: return False
        if not force and self._ck(uid) in self.cache: return True
        ok, msg, auth = self.get_auth(uid)
        if not ok: return False
        res = self._post(LOAD_URL, {"data": None}, {**GAME_HEADERS, "Authorization": f"Bearer {auth}"})
        if res.get("ok") is False or not res.get("result"): return False
        dec = decrypt_player_record(res["result"], td.get("firebase_uid", ""), td.get("password", ""), td.get("email", ""))
        if dec.get("success") and dec.get("record"):
            self.set_record(uid, dec["record"], td.get("email", ""))
            return True
        return False
    def _ok(self, value: Any) -> bool:
        if value in (1, True, "1"): return True
        if value in (0, False, None, "0"): return False
        if isinstance(value, str):
            try: return self._ok(json.loads(value.strip()))
            except: return False
        if isinstance(value, dict):
            for k in ("result", "ok", "success"):
                if k in value: return self._ok(value[k])
        return False
    def _send(self, auth: str, record: Dict[str, Any], fuid: str, original: Optional[Dict[str, Any]] = None, force_fields: Optional[set] = None) -> Tuple[bool, str]:
        if not fuid: return False, "NO_FIREBASE_UID"
        try:
            payload = build_payload(record, fuid, original, force_fields=force_fields)
            res = self._post(SAVE_URL, {"data": {"data": payload, "deviceId": fuid[:8]}}, {**GAME_HEADERS, "Authorization": f"Bearer {auth}", "Connection": "Keep-Alive", "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/SD1A.210817.036)"})
            if res.get("ok") is False: return False, res.get("message", "API TIMEOUT")
            if res and self._ok(res): return True, "OK"
            return False, "SAVE-FAILED"
        except Exception as e: return False, str(e)
    def _save(self, uid: int, data: Dict[str, Any], force_fields: Optional[set] = None) -> Dict[str, Any]:
        ok, msg, auth = self.get_auth(uid)
        if not ok: return {"ok": False, "message": msg}
        td = self.get_token_data(uid)
        fuid = td.get("firebase_uid", "") if td else ""
        email = td.get("email", "") if td else ""
        original = self.get_record(uid, email) or None
        ok2, msg2 = self._send(auth, data, fuid, original, force_fields=force_fields)
        if ok2:
            self.set_record(uid, data, email)
            return {"ok": True, "message": "OK"}
        return {"ok": False, "message": msg2}
    def _modify(self, uid: int, mods: Dict[str, Any], force_fields: Optional[set] = None) -> Dict[str, Any]:
        if not self.load(uid): return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        if not data or data.get("Name") is None: return {"ok": False, "message": "PROFILE DATA CORRUPTED."}
        for k, v in mods.items():
            if k == "money": v = min(int(v), MAX_MONEY)
            if k == "coin": v = min(int(v), MAX_COIN)
            data[k] = v
        return self._save(uid, data, force_fields=set(force_fields or mods.keys()))
    def _set_floats(self, uid: int, indices_values: List[Tuple[int, float]]) -> Dict[str, Any]:
        if not self.load(uid): return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        if not data or data.get("Name") is None: return {"ok": False, "message": "PROFILE DATA CORRUPTED."}
        floats = data.get("floats", [])
        max_idx = max(idx for idx, _ in indices_values)
        while len(floats) <= max_idx: floats.append(0.0)
        for idx, val in indices_values: floats[idx] = float(val)
        data["floats"] = floats
        return self._save(uid, data, force_fields={"floats"})
    def _set_integers(self, uid: int, indices_values: List[Tuple[int, int]]) -> Dict[str, Any]:
        if not self.load(uid): return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        if not data or data.get("Name") is None: return {"ok": False, "message": "PROFILE DATA CORRUPTED."}
        integers = data.get("integers", [])
        max_idx = max(idx for idx, _ in indices_values)
        while len(integers) <= max_idx: integers.append(0)
        for idx, val in indices_values: integers[idx] = int(val)
        data["integers"] = integers
        return self._save(uid, data, force_fields={"integers"})
    def set_money(self, uid: int, amount: int) -> Dict[str, Any]:
        return self._modify(uid, {"money": min(int(amount), MAX_MONEY)}, force_fields={"money"})
    def set_coin(self, uid: int, amount: int) -> Dict[str, Any]:
        return self._modify(uid, {"coin": min(int(amount), MAX_COIN)}, force_fields={"coin"})
    def change_player_id(self, uid: int, new_id: str) -> Dict[str, Any]:
        if not self.load(uid, force=True): return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        if not data or data.get("Name") is None: return {"ok": False, "message": "PROFILE DATA CORRUPTED."}
        data["localID"] = str(new_id).strip().upper()
        result = self._save(uid, data, force_fields={"localID"})
        if result.get("ok"): return {"ok": True, "message": f"TAG MASKED TO {data['localID']}", "new_id": data['localID']}
        return {"ok": False, "message": result.get("message", "SAVE FAILED")}
    def change_player_name(self, uid: int, new_name: str) -> Dict[str, Any]:
        if not self.load(uid, force=True): return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        data["Name"] = new_name
        return self._save(uid, data, force_fields={"Name"})
    def change_email(self, uid: int, new_email: str) -> Dict[str, Any]:
        return {"ok": True, "message": "Email change function called"}
    def unlock_w16(self, uid: int) -> Dict[str, Any]:
        return self._set_floats(uid, [(32, 1.0)])
    def unlock_horns(self, uid: int) -> Dict[str, Any]:
        return self._set_floats(uid, [(27,1.0),(28,1.0),(29,1.0),(30,1.0),(31,1.0)])
    def disable_damage(self, uid: int) -> Dict[str, Any]:
        return self._set_floats(uid, [(34,1.0)])
    def unlimited_fuel(self, uid: int) -> Dict[str, Any]:
        return self._set_floats(uid, [(3,1.0)])
    def unlock_smoke(self, uid: int) -> Dict[str, Any]:
        return self._set_floats(uid, [(33,1.0)])
    def unlock_animations(self, uid: int) -> Dict[str, Any]:
        if not self.load(uid): return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        data["animations"] = sorted(set(data.get("animations", []) + list(range(301))))
        return self._save(uid, data, force_fields={"animations"})
    def unlock_wheels(self, uid: int) -> Dict[str, Any]:
        if not self.load(uid): return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        data["wheels"] = sorted(set(data.get("wheels", []) + list(range(73, 221))))
        integers = data.get("integers", [])
        while len(integers) < 113: integers.append(0)
        for idx in [0,1,2,3,4,5,110,111,112]: integers[idx] = 1
        data["integers"] = integers
        return self._save(uid, data, force_fields={"wheels", "integers"})
    def unlock_houses(self, uid: int) -> Dict[str, Any]:
        return self._set_integers(uid, [(8,1),(110,1),(111,1),(112,1)])
    def complete_all_levels(self, uid: int) -> Dict[str, Any]:
        return self._modify(uid, {"LevelsDoneTime": [0] + [120 if i == 43 else 1 for i in range(1, 110)]}, force_fields={"LevelsDoneTime"})
    def set_rank(self, uid: int) -> Dict[str, Any]:
        self.load(uid)
        ok, msg, auth = self.get_auth(uid)
        if not ok: return {"ok": True, "message": "OK"}
        rating_data = {"RatingData": {"time": 1e22, "cars": 1e16, "car_fix": 1e13, "car_collided": 1e12, "car_exchange": 1e13, "car_trade": 1e13, "car_wash": 1e13, "slicer_cut": 1e13, "drift_max": 1e14, "drift": 1e14, "cargo": 1e5, "delivery": 1e5, "race_win": 3e20, "taxi": 1e10, "levels": 10000990000, "gifts": 1e9, "fuel": 1e10, "offroad": 1e10, "speed_banner": 1e9, "reactions": 1e17, "run": 1e9, "real_estate": 1e9, "t_distance": 1e10, "treasure": 1e10, "block_post": 1e10, "push_ups": 1e12, "burnt_tire": 1e10, "passanger_distance": 1e8}}
        try: self._post(RANK_URL, {"data": json.dumps(rating_data)}, {**GAME_HEADERS, "Authorization": f"Bearer {auth}"})
        except: pass
        return {"ok": True, "message": "OK"}
    def _normalize_equipment(self, equipment: Dict[str, Any], gender: int) -> Dict[str, Any]:
        list_fields = ["hair","face","beard","cap","mask","top","gloves","bag","pants","shoes","glasses","SelectedEquipments"]
        normalized = {key: [int(v) for v in (equipment.get(key, []) if isinstance(equipment, dict) else [])] for key in list_fields}
        normalized["Gender"] = int(gender)
        return normalized
    def unlock_all_clothes(self, uid: int) -> Dict[str, Any]:
        if not self.load(uid, force=True): return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        eq_male = {"Gender": 0, "bag": list(range(101)), "beard": list(range(6,21)) + [100], "cap": list(range(3,64)), "face": [0,1,2,100], "glasses": list(range(10)) + [100], "gloves": list(range(6)) + [100], "hair": list(range(3,20)) + [100], "mask": list(range(3,9)) + [100], "pants": list(range(26)), "shoes": list(range(31)), "top": list(range(2,109)), "SelectedEquipments": [-1,10,19,41,100,4,20,9,22,21,74]}
        eq_female = {"Gender": 1, "bag": list(range(6)), "beard": [], "cap": list(range(3,41)), "face": [0], "glasses": list(range(10)), "gloves": [1], "hair": [0,7,8,9,10], "mask": list(range(3,8)), "pants": list(range(12)), "shoes": list(range(3,15)), "top": list(range(5,80)), "SelectedEquipments": [0,0,-1,-1,-1,-1,-1,-1,0,-1,-1]}
        data["personEquipmentsMale"] = self._normalize_equipment(eq_male, 0)
        data["personEquipmentsFemale"] = self._normalize_equipment(eq_female, 1)
        return self._save(uid, data, force_fields={"personEquipmentsMale", "personEquipmentsFemale"})
    def unlock_all_features(self, uid: int) -> Dict[str, Any]:
        feature_calls = [("W16 Engine", self.unlock_w16), ("Horns", self.unlock_horns), ("No Damage", self.disable_damage), ("Unlimited Fuel", self.unlimited_fuel), ("Smoke", self.unlock_smoke), ("Animations", self.unlock_animations), ("Wheels", self.unlock_wheels), ("Houses", self.unlock_houses), ("All Levels", self.complete_all_levels), ("Max Rank", self.set_rank)]
        if not self.load(uid, force=True): return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        results, failed = [], []
        for name, fn in feature_calls:
            res = fn(uid)
            if res.get("ok"): results.append(name)
            else: failed.append(f"{name}: {res.get('message', 'Failed')}")
        return {"ok": not failed, "message": f"Unlocked {len(results)}/{len(feature_calls)} features"}
    def fix_account(self, uid: int) -> Dict[str, Any]:
        if not self.load(uid, force=True): return {"ok": False, "message": "ACCOUNT LOAD FAILED."}
        td = self.get_token_data(uid)
        data = deepcopy(self.get_record(uid, td.get("email") if td else None))
        if data.get("money", 0) > MAX_MONEY: data["money"] = MAX_MONEY
        if data.get("coin", 0) > MAX_COIN: data["coin"] = MAX_COIN
        flags = data.get("flags", {})
        if isinstance(flags, dict):
            for bad_flag in [0,1,2,"0","1","2"]: flags.pop(bad_flag, None)
            data["flags"] = flags
        return self._save(uid, data, force_fields={"money", "coin", "flags"})
    def get_account_info(self, uid: int, force_refresh: bool = False) -> Dict[str, Any]:
        if not self.load(uid, force=force_refresh): return {"ok": False}
        td = self.get_token_data(uid)
        if not td: return {"ok": False}
        data = self.get_record(uid, td.get("email"))
        if not data or data.get("Name") is None: return {"ok": False}
        cars_count = 0
        try:
            c_status = data.get('carIDnStatus')
            if isinstance(c_status, dict):
                c_list = c_status.get('carStatus', [])
                if isinstance(c_list, list): cars_count = len(c_list)
        except: pass
        if cars_count == 0:
            try:
                ad = data.get('allData', '{}')
                if isinstance(ad, str):
                    ad_json = json.loads(ad)
                    if isinstance(ad_json, dict):
                        cars_count = len(ad_json.get('cars', []))
            except: pass
        return {"ok": True, "name": data.get("Name", "Unknown"), "money": data.get("money", 0), "coin": data.get("coin", 0), "localID": data.get("localID", "Unknown"), "email": td.get("email"), "cars": cars_count}

nuker = SyncCPMNuker()

# ═══════════════════════════════════════════════════════════
# 🚗 CAR INJECTION ENGINE - EXACT REFERENCE FROM WORKING BOT (PARTNER'S CODE)
# ═══════════════════════════════════════════════════════════

_source_cars_cache = None
_source_cars_cache_time = 0
_source_cars_lock = threading.Lock()

def verify_user(email, password):
    payload = {"email": email, "password": password, "returnSecureToken": True, "clientType": "CLIENT_TYPE_ANDROID"}
    try:
        response = http_session.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword", json=payload, params={"key": FK}, timeout=15)
        if response.status_code == 200:
            d = response.json()
            return d.get("idToken"), d.get("localId")
        return None, None
    except: return None, None

def cpm1_api(token, endpoint, data=None):
    headers = deepcopy(GAME_HEADERS)
    headers["Authorization"] = f"Bearer {token}"
    try:
        response = http_session.post(f"https://europe-west1-cp-multiplayer.cloudfunctions.net/{endpoint}", json={"data": data}, headers=headers, timeout=20)
        return response.status_code, response.text
    except: return 500, json.dumps({"result": "error"})

def cpm1_get_cars(token):
    endpoints = [
        ("GetAllCars2", None),
        ("GetAllCars3", None),
        ("GetAllCars", None),
    ]
    for endpoint, data in endpoints:
        status, text = cpm1_api(token, endpoint, data)
        if status != 200: continue
        try:
            raw = json.loads(text)
            result = raw.get("result", raw)
            if isinstance(result, str):
                result = json.loads(result)
            if isinstance(result, list) and len(result) > 0:
                return result
            if isinstance(result, dict):
                for key in ["cars", "CarList", "data", "list"]:
                    if isinstance(result.get(key), list) and len(result[key]) > 0:
                        return result[key]
        except: continue
    return None

def cpm1_get_full_car(token, car_data):
    cid = car_data.get("CarID") or car_data.get("carID") or 0
    gen = car_data.get("carGeneratedID") or car_data.get("CarGeneratedID") or ""
    payloads = [
        {"CarID": cid, "carGeneratedID": gen},
        {"CarID": cid},
        {"carGeneratedID": gen},
        car_data,
    ]
    for p in payloads:
        for endpoint in ["WSGetFullCarV3", "WSGetFullCarV2", "GetFullCar"]:
            try:
                status, text = cpm1_api(token, endpoint, json.dumps(p))
                if status != 200: continue
                raw = json.loads(text)
                result = raw.get("result", raw)
                if isinstance(result, str):
                    try: result = json.loads(result)
                    except: pass
                if isinstance(result, dict) and (result.get("CarID") or result.get("carID")):
                    return result
                if isinstance(result, list) and result:
                    for item in result:
                        if not isinstance(item, dict): continue
                        if item.get("CarID") == cid or item.get("carID") == cid:
                            return item
            except: continue
    return None

def cpm1_get_garage_slot(token):
    for param in [20, 10, 50, 100]:
        for attempt in range(3):
            try:
                status, text = cpm1_api(token, "WSGetCarListV3", param)
                if status == 200:
                    data = json.loads(text)
                    result = data.get('result')
                    if isinstance(result, str): result = json.loads(result)
                    if result and isinstance(result, list) and len(result) > 0:
                        for slot in result:
                            if slot.get('carID', 0) == 0 and 'carGeneratedID' in slot:
                                return slot
                        for slot in result:
                            if 'carGeneratedID' in slot:
                                return slot
            except: pass
            time.sleep(0.5)
    return None

def cpm1_fix_car_appearance(car):
    """EXACT reference function - fixes colors, removes police, avoids black."""
    if not isinstance(car, dict): return car
    car = json.loads(json.dumps(car))
    vyn = car.get("Vynils")
    if not isinstance(vyn, dict): vyn = {}
    if "CarID" not in vyn and car.get("CarID") is not None:
        vyn["CarID"] = car.get("CarID")
    car["Vynils"] = vyn

    def ensure_color_list(key, length, default=1.0):
        val = car.get(key)
        if not isinstance(val, list) or len(val) == 0:
            car[key] = [float(default)] * length
        else:
            fixed = []
            for x in val:
                try: fx = float(x)
                except Exception: fx = default
                if fx == 0.0: fx = 1.0  # Prevent black car bug
                fixed.append(fx)
            car[key] = fixed

    for key, ln in (("colors", 4), ("Colors", 4), ("bodyColor", 4), ("paint", 4)):
        if key in car or key in ("colors", "Colors"):
            ensure_color_list(key, ln, 0.85)
            
    if isinstance(car.get("color"), (int, float)) and float(car.get("color") or 0) == 0:
        car["color"] = 1
        
    car["police"] = False
    car["isLocked"] = False
    if car.get("engineID") in (None, 0): car["engineID"] = 5
    car["cdi"] = True
    car["torque"] = car.get("torque") or 3000.0
    car["brake"] = car.get("brake") or 3000.0
    car["mass"] = car.get("mass") or 1100.0
    return car

def cpm1_clone_car(token_target, car_data, target_uid, token_source=None):
    cid = car_data.get("CarID", 0) or car_data.get("carID", 0)
    full = None
    if token_source:
        try: full = cpm1_get_full_car(token_source, car_data)
        except: full = None
    base = full if isinstance(full, dict) else car_data
    car = cpm1_fix_car_appearance(base)
    car["CarID"] = cid
    try:
        if "texts" in car and isinstance(car["texts"], list) and len(car["texts"]) > 2:
            car["texts"][2] = f"{str(target_uid)[:8].upper()}_{cid}_HZ"
        elif "texts" in car and isinstance(car["texts"], str):
            car["texts"] = ["", "", f"{str(target_uid)[:8].upper()}_{cid}_HZ"]
    except: pass
    try:
        if isinstance(car.get("Vynils"), dict):
            car["Vynils"]["CarID"] = cid
    except: pass
    
    slot = cpm1_get_garage_slot(token_target)
    if not slot: return False
    
    vynil = car.get("Vynils") if isinstance(car.get("Vynils"), dict) else {}
    if not vynil: vynil = {"CarID": cid}
        
    payload = {
        "ownerID": slot.get("ownerID", ""),
        "ownerName": slot.get("ownerName", ""),
        "description": slot.get("description", ""),
        "CarID": slot.get("carID", 0),
        "carGeneratedID": slot.get("carGeneratedID", ""),
        "ownerAccountID": slot.get("ownerAccountID", ""),
        "oneCar": car,
        "vynilOneCar": vynil,
        "loadedLocalCar": {"instanceID": random.randint(-999999, -100000)},
        "price": slot.get("price", 100),
        "SellingCar": {},
        "willReject": False,
        "dislike": 1,
        "like": 0,
        "liked": False,
        "disliked": False,
        "mode": 1,
    }
    for attempt in range(5):
        status, text = cpm1_api(token_target, "WSPurchaseCarV3", json.dumps(payload))
        try:
            if status == 200 and str(json.loads(text).get("result")) in ("1", 1, "true", "True"):
                return True
        except: pass
        time.sleep(0.8)
    return False

def cpm1_inject_car(token_target, uid_target, car_data, token_source=None):
    if token_source is None:
        stok, _ = verify_user(*SOURCE_ACCOUNT)
        token_source = stok
    return cpm1_clone_car(token_target, car_data, uid_target, token_source)

def get_source_cars_cached():
    global _source_cars_cache, _source_cars_cache_time
    with _source_cars_lock:
        if _source_cars_cache and time.time() - _source_cars_cache_time < 60:
            return _source_cars_cache
    stok, _ = verify_user(*SOURCE_ACCOUNT)
    if not stok:
        print("[SOURCE CARS] Source auth failed.")
        return []
    cars = cpm1_get_cars(stok)
    if cars:
        _source_cars_cache = cars
        _source_cars_cache_time = time.time()
    return _source_cars_cache or []

def background_inject_all_cars(chat_id, email, password, msg_id):
    try:
        try: bot.edit_message_text("⏳ INJECTING CARS...\n⚙️ Loading source...\n\n🚗 Vehicles", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
        except: pass
        
        web_uid = get_web_uid(chat_id)
        ok, msg_auth, tok = nuker.get_auth(web_uid)
        td = nuker.get_token_data(web_uid)
        uid = td.get("firebase_uid") if td else None
        
        if not ok or not tok or not uid:
            try: bot.edit_message_text("❌ Auth Failed. Login again.\n\n🚗 Vehicles", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
            except: pass
            return
            
        stok, _ = verify_user(*SOURCE_ACCOUNT)
        if not stok:
            try: bot.edit_message_text("❌ Source account unavailable.\n\n🚗 Vehicles", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
            except: pass
            return
            
        source_cars = get_source_cars_cached()
        if not source_cars or len(source_cars) == 0:
            try: bot.edit_message_text("❌ No cars found in source.\n\n🚗 Vehicles", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
            except: pass
            return
            
        success = 0
        fail = 0
        total = len(source_cars)
        start_time = time.time()
        
        for idx, car_data in enumerate(source_cars):
            if cpm1_clone_car(tok, car_data, uid, token_source=stok):
                success += 1
            else:
                fail += 1
            
            done = idx + 1
            if done % 5 == 0 or done == total:
                elapsed = time.time() - start_time
                avg = elapsed / done if done > 0 else 0
                remaining = (total - done) * avg
                percent = int((done / total) * 100)
                filled = int(percent / 5)
                bar = "█" * filled + "▒" * (20 - filled)
                eta = f" ETA: {int(remaining)}s" if remaining > 0 else ""
                try:
                    bot.edit_message_text(f"⏳ INJECTING CARS...\n{bar} {percent}%\n({done}/{total}){eta}\n✅ Success: {success}\n❌ Failed: {fail}\n\n🚗 Vehicles", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
                except: pass
            time.sleep(0.5)
            
        try: bot.edit_message_text(f"✅ CAR INJECTION COMPLETE!\nTotal: {total}\n✅ Success: {success}\n❌ Failed: {fail}\n\n🚗 Vehicles", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
        except: pass
    except Exception as e:
        pass

# ═══════════════════════════════════════════════════════════
# 🧩 BULK CLONE - OPTIMIZED WITH REAL-TIME PROGRESS
# ═══════════════════════════════════════════════════════════

def full_account_clone_parallel(src_record, src_cars, tgt_email, tgt_pass, source_token=None, progress_callback=None):
    try:
        t_res = nuker.login(tgt_email, tgt_pass)
        if not t_res.get("ok"):
            return False, {"error": "Target login failed"}
        t_auth, t_uid = t_res["auth"], t_res["firebase_uid"]
        
        nuker.load(t_uid, force=True)
        t_record = nuker.get_record(t_uid, tgt_email) or {}
        
        safe_keys = ['money', 'coin', 'floats', 'integers', 'animations', 'wheels', 'personEquipmentsMale', 'personEquipmentsFemale', 'boughtFsos', 'emojiPacks']
        for k in safe_keys:
            if k in src_record:
                t_record[k] = deepcopy(src_record[k])
                
        t_record['boughtPoliceSirens'] = []
        t_record['boughtPoliceLights'] = []
        safe_keys.extend(['boughtPoliceSirens', 'boughtPoliceLights'])
                
        ok, msg = nuker._send(t_auth, t_record, t_uid, original=None, force_fields=set(safe_keys))
        if not ok: nuker._modify(t_uid, {"money": src_record.get('money', 0), "coin": src_record.get('coin', 0)})

        success_count = 0
        fail_count = 0
        total_cars = len(src_cars)
        completed_cars = 0
        lock = threading.Lock()
        start_time = time.time()

        def process_car(car):
            if not isinstance(car, dict): return False
            time.sleep(0.5)
            return cpm1_clone_car(t_auth, car, t_uid, token_source=source_token)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(process_car, car): car for car in src_cars}
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    with lock: success_count += 1
                else:
                    with lock: fail_count += 1
                
                with lock:
                    completed_cars += 1
                    if progress_callback:
                        elapsed = time.time() - start_time
                        avg = elapsed / completed_cars if completed_cars > 0 else 0
                        remaining = (total_cars - completed_cars) * avg
                        progress_callback(completed_cars, total_cars, remaining)

        return True, {"total": total_cars, "success": success_count, "fail": fail_count}
    except Exception as e:
        return False, {"error": str(e)[:40]}

def background_single_clone(chat_id, src_email, src_pass, tgt_email, tgt_pass, msg_id):
    try:
        try: bot.edit_message_text("⏳ CLONING IN PROGRESS...\n⚙️ Loading source...\n\n👤 Account Management", chat_id, msg_id, reply_markup=create_account_keyboard())
        except: pass
        
        source_token, source_uid = verify_user(src_email, src_pass)
        if not source_token:
            bot.edit_message_text(f"❌ CLONE FAILED\nError: Source login failed\n\n👤 Account Management", chat_id, msg_id, reply_markup=create_account_keyboard())
            return
            
        nuker.load(source_uid, force=True)
        src_record = nuker.get_record(source_uid, src_email) or {}
        cars = cpm1_get_cars(source_token) or []
        
        last_edit_time = [0]
        
        def update_progress(current, total, remaining):
            if total == 0: total = 1
            now = time.time()
            if now - last_edit_time[0] < 2 and current != total:
                return
            last_edit_time[0] = now
            percent = int((current / total) * 100)
            filled = int(percent / 5)
            bar = "█" * filled + "▒" * (20 - filled)
            eta = f" ETA: {int(remaining)}s" if remaining > 0 else ""
            text = f"⏳ CLONING IN PROGRESS...\n{bar} {percent}%\n({current}/{total}){eta}\n\n👤 Account Management"
            try:
                bot.edit_message_text(text, chat_id, msg_id, reply_markup=create_account_keyboard())
            except: pass

        res = full_account_clone_parallel(src_record, cars, tgt_email, tgt_pass, source_token, progress_callback=update_progress)
        
        if res[0] == True:
            msg = f"✅ CLONE SUCCESSFUL!\n🚗 Cars: {res[1]['success']}/{res[1]['total']}\n\n👤 Account Management"
        else:
            err = clean_str(res[1].get('error', 'SAVE-FAILED'))
            msg = f"❌ CLONE FAILED\nError: {err}\n\n👤 Account Management"

        try: bot.edit_message_text(msg, chat_id, msg_id, reply_markup=create_account_keyboard())
        except: pass
    except Exception as e:
        pass

def clone_task(src_record, src_cars, i, res_list, source_token):
    t_email = f"glitchyn{random.randint(10000,99999)}@gmail.com"
    t_pass = f"glitchyn{random.randint(10000,99999)}"
    for attempt in range(3):
        try:
            r = http_session.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FK}", json={"email": t_email, "password": t_pass, "returnSecureToken": True}, timeout=15)
            if "idToken" in r.text: break
        except: pass
        time.sleep(1)
        
    clone_res = full_account_clone_parallel(src_record, src_cars, t_email, t_pass, source_token)
    if clone_res[0] == True: 
        res_list.append(f"✅ ID {i+1} ({clone_res[1]['success']} Cars)\n📧 {t_email}\n🔑 {t_pass}")
    else: 
        err = clean_str(clone_res[1].get('error', 'SAVE-FAILED'))
        res_list.append(f"⚠️ ID {i+1} FAILED: {err[:30]}\n📧 {t_email}\n🔑 {t_pass}")
    gc.collect()

def background_bulk_clone(chat_id, src_email, src_pass, count, msg_id):
    try:
        try: bot.edit_message_text(f"⏳ BULK CLONING...\n⚙️ Loading source account...\n\n👑 Overseer Panel", chat_id, msg_id, reply_markup=create_admin_keyboard())
        except: pass
        
        source_token, source_uid = verify_user(src_email, src_pass)
        if not source_token:
            bot.edit_message_text(f"❌ BULK CLONE FAILED\nError: Source login failed\n\n👑 Overseer Panel", chat_id, msg_id, reply_markup=create_admin_keyboard())
            return
            
        bot.edit_message_text("⏳ BULK CLONING...\n📂 Loading player record...\n\n👑 Overseer Panel", chat_id, msg_id, reply_markup=create_admin_keyboard())
        nuker.load(source_uid, force=True)
        src_record = nuker.get_record(source_uid, src_email) or {}
        
        bot.edit_message_text("⏳ BULK CLONING...\n🚗 Fetching car list from source...\n\n👑 Overseer Panel", chat_id, msg_id, reply_markup=create_admin_keyboard())
        cars = cpm1_get_cars(source_token) or []
        if not cars:
            bot.edit_message_text(f"❌ BULK CLONE FAILED\nError: No cars found in source\n\n👑 Overseer Panel", chat_id, msg_id, reply_markup=create_admin_keyboard())
            return
        
        res_list = []
        total = count
        completed = 0
        start_time = time.time()
        
        def update_bulk_progress():
            nonlocal completed
            if completed >= total:
                final_text = "📦 BULK CLONE REPORT\n┣━━━━━━━━━━━━━━━━━━┫\n\n" + "\n\n".join(sorted(res_list)) + "\n\n👑 Overseer Panel"
                try: bot.edit_message_text(final_text, chat_id, msg_id, reply_markup=create_admin_keyboard())
                except: pass
                return
            percent = int((completed / total) * 100)
            filled = int(percent / 5)
            bar = "█" * filled + "▒" * (20 - filled)
            elapsed = time.time() - start_time
            avg = elapsed / completed if completed > 0 else 0
            remaining = (total - completed) * avg
            eta = f" ETA: {int(remaining)}s" if remaining > 0 else ""
            text = f"⏳ BULK CLONING {completed}/{total}\n{bar} {percent}%{eta}\n\n👑 Overseer Panel"
            try: bot.edit_message_text(text, chat_id, msg_id, reply_markup=create_admin_keyboard())
            except: pass
        
        for i in range(total):
            # Update before each clone
            try: bot.edit_message_text(f"⏳ BULK CLONING\nCloning account {i+1}/{total}... (may take a few minutes)\n\n👑 Overseer Panel", chat_id, msg_id, reply_markup=create_admin_keyboard())
            except: pass
            
            # Clone one account
            clone_task(src_record, cars, i, res_list, source_token)
            
            completed += 1
            update_bulk_progress()
            gc.collect()
        
        final_text = "📦 BULK CLONE REPORT\n┣━━━━━━━━━━━━━━━━━━┫\n\n" + "\n\n".join(sorted(res_list)) + "\n\n👑 Overseer Panel"
        try: bot.edit_message_text(final_text, chat_id, msg_id, reply_markup=create_admin_keyboard())
        except: pass
    except Exception as e:
        try: bot.edit_message_text(f"❌ BULK CLONE ERROR\n{e}\n\n👑 Overseer Panel", chat_id, msg_id, reply_markup=create_admin_keyboard())
        except: pass

# ═══════════════════════════════════════════════════════════
# 🤖 UI & KEYBOARDS (UNTOUCHED - KEEP ORIGINAL)
# ═══════════════════════════════════════════════════════════
def get_role_badge(chat_id):
    if is_admin(chat_id):
        return "👑 Admin"
    if is_premium(chat_id):
        return "💎 Premium User"
    return "🆓 Free User"

def cancel_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="menu_main"))
    return markup

def create_dashboard_keyboard(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(types.InlineKeyboardButton("👤 Account", callback_data="menu_account"), types.InlineKeyboardButton("💰 Economy", callback_data="menu_economy"))
    markup.row(types.InlineKeyboardButton("🚗 Vehicles", callback_data="menu_vehicles"), types.InlineKeyboardButton("🔓 Unlocks", callback_data="menu_unlocks"))
    markup.row(types.InlineKeyboardButton("💎 Subscription", callback_data="menu_subscription"))
    if is_admin(chat_id):
        markup.row(types.InlineKeyboardButton("👑 OVERSEER PANEL", callback_data="admin_panel"))
    markup.row(types.InlineKeyboardButton("🔄 Refresh", callback_data="refresh_account"), types.InlineKeyboardButton("🚪 Logout", callback_data="logout"))
    return markup

def create_account_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(types.InlineKeyboardButton("ℹ️ Info", callback_data="acc_info"), types.InlineKeyboardButton("✏️ Set Name", callback_data="acc_name"))
    markup.row(types.InlineKeyboardButton("🆔 Set ID", callback_data="acc_id"), types.InlineKeyboardButton("📧 Change Email", callback_data="acc_email"))
    markup.row(types.InlineKeyboardButton("🔑 Change Pass", callback_data="acc_pass"), types.InlineKeyboardButton("👥 Clone Account", callback_data="acc_clone"))
    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_main"))
    return markup

def create_economy_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(types.InlineKeyboardButton("💵 Money 50M", callback_data="eco_money_max"), types.InlineKeyboardButton("🪙 Coins 500K", callback_data="eco_coins_max"))
    markup.row(types.InlineKeyboardButton("💵 Custom Money", callback_data="eco_money_cust"), types.InlineKeyboardButton("🪙 Custom Coins", callback_data="eco_coins_cust"))
    markup.row(types.InlineKeyboardButton("👑 King Rank", callback_data="eco_king"))
    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_main"))
    return markup

def create_vehicles_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(types.InlineKeyboardButton("🚗 Unlock All Cars", callback_data="veh_unlock_all"), types.InlineKeyboardButton("🚙 Unlock By ID", callback_data="veh_unlock_single"))
    markup.row(types.InlineKeyboardButton("🔧 Fix Account", callback_data="veh_fix"))
    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_main"))
    return markup

def create_unlocks_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(types.InlineKeyboardButton("🔧 W16 Engine", callback_data="unl_w16"), types.InlineKeyboardButton("💨 Smoke", callback_data="unl_smoke"))
    markup.row(types.InlineKeyboardButton("⛽ Max Fuel", callback_data="unl_fuel"), types.InlineKeyboardButton("🛡️ No Damage", callback_data="unl_damage"))
    markup.row(types.InlineKeyboardButton("📯 Horns", callback_data="unl_horns"), types.InlineKeyboardButton("🎭 Animations", callback_data="unl_anim"))
    markup.row(types.InlineKeyboardButton("🏠 All Houses", callback_data="unl_houses"), types.InlineKeyboardButton("🛞 Wheels", callback_data="unl_wheels"))
    markup.row(types.InlineKeyboardButton("🏆 Complete Levels", callback_data="unl_levels"))
    markup.row(types.InlineKeyboardButton("👕 All Clothes", callback_data="unl_clothes"))
    markup.row(types.InlineKeyboardButton("💀 ULTIMATE GLITCH", callback_data="unl_ultimate"))
    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_main"))
    return markup

def create_admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(types.InlineKeyboardButton("➕ Add Admin", callback_data="admin_add_admin"), types.InlineKeyboardButton("➖ Remove Admin", callback_data="admin_rem_admin"))
    markup.row(types.InlineKeyboardButton("👥 View Admins", callback_data="admin_view_admins"))
    markup.row(types.InlineKeyboardButton("✅ Add Premium", callback_data="admin_add_prem"), types.InlineKeyboardButton("❌ Revoke Premium", callback_data="admin_revoke"))
    markup.row(types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"), types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"))
    markup.row(types.InlineKeyboardButton("📦 Bulk Clone", callback_data="admin_bulk_clone"))
    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_main"))
    return markup

def create_subscription_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(types.InlineKeyboardButton("⭐ Buy with Stars", callback_data="sub_stars"))
    markup.row(types.InlineKeyboardButton("💳 Pay with Money", callback_data="sub_money"))
    markup.row(types.InlineKeyboardButton("🔑 Enter Time Key", callback_data="sub_time_key"))
    markup.row(types.InlineKeyboardButton("🎁 Free Trial (10 min)", callback_data="sub_free_trial"))
    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="menu_main"))
    return markup

def create_subscription_duration_keyboard(payment_type):
    markup = types.InlineKeyboardMarkup(row_width=2)
    durations = list(SUBSCRIPTION_DURATIONS.keys())
    for d in durations:
        if payment_type == "stars":
            stars = SUBSCRIPTION_STARS.get(d, 0)
            label = f"{d.replace('_',' ').title()} - {stars}⭐"
        else:
            money = SUBSCRIPTION_MONEY.get(d, "")
            label = f"{d.replace('_',' ').title()} - {money}"
        markup.row(types.InlineKeyboardButton(label, callback_data=f"sub_duration_{d}_{payment_type}"))
    markup.row(types.InlineKeyboardButton("🔙 Back", callback_data="menu_subscription"))
    return markup

def create_payment_method_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    for key, method in PAYMENT_METHODS.items():
        markup.row(types.InlineKeyboardButton(method["label"], callback_data=f"sub_payment_{key}"))
    markup.row(types.InlineKeyboardButton("🌟 Telegram Stars", callback_data="sub_payment_stars"))
    markup.row(types.InlineKeyboardButton("🔙 Back", callback_data="menu_subscription"))
    return markup

def create_subscription_confirm_keyboard(user_id, duration_key, payment_method):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("✅ Confirm", callback_data=f"sub_confirm_{user_id}_{duration_key}_{payment_method}")
    btn2 = types.InlineKeyboardButton("❌ Decline", callback_data=f"sub_decline_{user_id}_{duration_key}_{payment_method}")
    markup.row(btn1, btn2)
    return markup

def _parse_sub_callback(rest):
    try:
        user_id = int(rest.split("_", 1)[0])
        remainder = rest.split("_", 1)[1]
    except Exception:
        return None, None, None
    for dur in SUBSCRIPTION_DURATIONS:
        if remainder.startswith(dur + "_"):
            pm = remainder[len(dur) + 1:]
            if pm in PAYMENT_METHODS:
                return user_id, dur, pm
        if remainder == dur and dur in PAYMENT_METHODS:
            return user_id, dur, dur
    return None, None, None

def safe_send_dashboard(chat_id, custom_top_msg=None, force_refresh=False, is_callback=False, message_id=None):
    try:
        session_data = user_sessions.get(chat_id, {})
        is_logged_in = session_data.get('cpm_logged_in', False)
        if not is_logged_in:
            msg = "🔒 Not logged in — tap Login to get started."
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔓 Login to CPM1", callback_data="init_login"))
            if is_callback and message_id:
                try:
                    bot.edit_message_text(msg, chat_id, message_id, reply_markup=markup)
                except:
                    bot.send_message(chat_id, msg, reply_markup=markup)
            else:
                bot.send_message(chat_id, msg, reply_markup=markup)
            return
        web_uid = get_web_uid(chat_id)
        info = nuker.get_account_info(web_uid, force_refresh=force_refresh)
        if not info.get("ok"):
            user_sessions[chat_id]['cpm_logged_in'] = False
            msg = "❌ Session Expired. Login again."
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔓 Login", callback_data="init_login"))
            if is_callback and message_id:
                try:
                    bot.edit_message_text(msg, chat_id, message_id, reply_markup=markup)
                except:
                    bot.send_message(chat_id, msg, reply_markup=markup)
            else:
                bot.send_message(chat_id, msg, reply_markup=markup)
            return
        role = get_role_badge(chat_id)
        name = clean_str(info.get('name', 'Unknown'))
        tag = clean_str(info.get('localID', 'Unknown'))
        email = clean_str(info.get('email', 'Unknown'))
        cars_owned = info.get('cars', 0)
        try:
            money_val = int(info.get('money') or 0)
        except:
            money_val = 0
        try:
            coin_val = int(info.get('coin') or 0)
        except:
            coin_val = 0
        coin_display = get_coin_display(chat_id)
        sub_display = get_subscription_display(chat_id)
        text = f"✅ Logged in!\n\n👤 Your Information\n───────────────\n♾️ Status: Access granted\n🆔 Telegram ID: {chat_id}\n🎖️ Role: {role}\n{coin_display}\n{sub_display}\n\n🏍️ CPM DASHBOARD\n───────────────\n👤 Name: {name}\n🆔 ID: {tag}\n💵 Money: {money_val:,}\n🪙 Coins: {coin_val:,}\n🚗 Cars owned: {cars_owned}\n📧 {email}\n\n👇 Choose a section:"
        if custom_top_msg:
            text = f"{custom_top_msg}\n{text}"
        markup = create_dashboard_keyboard(chat_id)
        if is_callback and message_id:
            try:
                bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
            except:
                bot.send_message(chat_id, text, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)
    except Exception as e:
        pass

# ═══════════════════════════════════════════════════════════
# 📋 ADMIN COMMANDS (UNTOUCHED)
# ═══════════════════════════════════════════════════════════
@bot.message_handler(commands=['addcoins'])
def addcoins_command(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        return bot.send_message(chat_id, "❌ Admin only.")
    args = message.text.split()
    if len(args) != 3:
        bot.send_message(chat_id, "Usage: /addcoins <user_id> <amount>")
        return
    try:
        target_id = int(args[1])
        amount = int(args[2])
        add_coins(target_id, amount)
        bot.send_message(chat_id, f"✅ Added {amount} coins to user {target_id}. New balance: {get_user_coins(target_id)}")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {e}")

@bot.message_handler(commands=['setcoins'])
def setcoins_command(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        return bot.send_message(chat_id, "❌ Admin only.")
    args = message.text.split()
    if len(args) != 3:
        bot.send_message(chat_id, "Usage: /setcoins <user_id> <amount>")
        return
    try:
        target_id = int(args[1])
        amount = int(args[2])
        set_user_coins(target_id, amount)
        bot.send_message(chat_id, f"✅ Set {amount} coins for user {target_id}.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {e}")

@bot.message_handler(commands=['unlimited'])
def unlimited_command(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        return bot.send_message(chat_id, "❌ Admin only.")
    args = message.text.split()
    if len(args) != 3:
        bot.send_message(chat_id, "Usage: /unlimited <user_id> <True/False>")
        return
    try:
        target_id = int(args[1])
        status = args[2].lower() in ['true','1','yes']
        set_unlimited(target_id, status)
        bot.send_message(chat_id, f"✅ Set unlimited={status} for user {target_id}.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {e}")

@bot.message_handler(commands=['balance'])
def balance_command(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        return bot.send_message(chat_id, "❌ Admin only.")
    args = message.text.split()
    try:
        target_id = int(args[1]) if len(args) > 1 else chat_id
        coins = get_user_coins(target_id)
        unlimited = is_unlimited(target_id)
        bot.send_message(chat_id, f"💰 User {target_id} has {coins} coins{' (Unlimited)' if unlimited else ''}.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {e}")

@bot.message_handler(commands=['subscribe'])
def subscribe_command(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        return bot.send_message(chat_id, "❌ Admin only.")
    args = message.text.split()
    if len(args) != 3:
        bot.send_message(chat_id, "Usage: /subscribe <user_id> <months>")
        return
    try:
        target_id = int(args[1])
        months = int(args[2])
        if months <= 0:
            set_subscribed_coins(target_id, False, 0)
            bot.send_message(chat_id, f"❌ Subscription removed for user {target_id}.")
        else:
            set_subscribed_coins(target_id, True, months)
            expiry = (datetime.today().date() + timedelta(days=months*30)).strftime("%Y-%m-%d")
            bot.send_message(chat_id, f"✅ Subscribed user {target_id} for {months} month(s). Expires: {expiry}.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {e}")

@bot.message_handler(commands=['stars'])
def stars_balance_command(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        return bot.send_message(chat_id, "❌ Admin only.")
    total = get_stars_balance()
    text = f"🌟 Total Stars Received: {total}\n✅ Can withdraw at 1000+ Stars"
    bot.send_message(chat_id, text, parse_mode='Markdown')

@bot.message_handler(commands=['withdrawstars'])
def withdraw_stars_command(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        return bot.send_message(chat_id, "❌ Admin only.")
    total = get_stars_balance()
    if total < 1000:
        bot.send_message(chat_id, f"❌ Need at least 1000 stars to withdraw. Current: {total}")
        return
    reset_stars_balance()
    bot.send_message(chat_id, f"✅ Withdrew {total} stars. Balance reset to 0.\nContact @Maarkryan to cash out.")

# ═══════════════════════════════════════════════════════════
# 🚀 START & MENU COMMANDS
# ═══════════════════════════════════════════════════════════
user_sessions = {}
user_states = {}

def get_web_uid(telegram_id):
    return int(str(telegram_id)[:12])

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
        delete_state(chat_id)
        track_user(chat_id)
        if chat_id not in user_sessions:
            user_sessions[chat_id] = {'cpm_logged_in': False}
        elif 'cpm_logged_in' not in user_sessions[chat_id]:
            user_sessions[chat_id]['cpm_logged_in'] = False
        bot.send_message(chat_id, "⚡ 𝙈𝘼𝙍𝙆𝘾𝙋𝙈1𝙏𝙊𝙊𝙇𝙎 TERMINAL ⚡", reply_markup=types.ReplyKeyboardRemove())
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
        delete_state(chat_id)
        if not is_admin(chat_id):
            return bot.send_message(chat_id, "❌ UNAUTHORIZED.")
        bot.send_message(chat_id, "👑 OVERSEER TERMINAL", reply_markup=create_admin_keyboard())
    except:
        pass

# ═══════════════════════════════════════════════════════════
# 🎯 LOGIN COMMAND (BACKUP)
# ═══════════════════════════════════════════════════════════
@bot.message_handler(commands=['login'])
def login_command(message):
    chat_id = message.chat.id
    args = message.text.split()
    if len(args) != 3:
        bot.send_message(chat_id, "Usage: /login email password")
        return
    email, password = args[1], args[2]
    try:
        web_uid = get_web_uid(chat_id)
        res = nuker.login(email, password)
        if res and isinstance(res, dict) and res.get("ok"):
            nuker.save_token(web_uid, res.get("auth", ""), email, password, res.get("refresh_token", ""), res.get("firebase_uid", ""))
            user_sessions[chat_id].update({'cpm_logged_in': True, 'web_uid': web_uid})
            safe_send_dashboard(chat_id, force_refresh=True)
        else:
            err = clean_str(res.get('message', 'Unknown Error') if isinstance(res, dict) else 'Network Failure')
            bot.send_message(chat_id, f"❌ AUTH FAILED: {err}")
    except:
        bot.send_message(chat_id, "❌ API Timeout.")

# ═══════════════════════════════════════════════════════════
# 🎯 MESSAGE ROUTER
# ═══════════════════════════════════════════════════════════
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'document'])
def handle_all_messages(message):
    try:
        chat_id = message.chat.id

        # ✅ PHOTO HANDLER (for subscription)
        if chat_id in user_states and user_states[chat_id].get('awaiting_subscription_photo'):
            state = user_states[chat_id]
            payment_method = state.get('payment_method', 'Unknown')
            duration_key = state.get('duration_key', 'Unknown')
            
            if message.photo:
                photo = message.photo[-1].file_id
                try:
                    user = bot.get_chat(chat_id)
                    username = user.username or "No username"
                    first_name = user.first_name or "Unknown"
                except:
                    username = "Unknown"
                    first_name = "Unknown"
                
                sub_data = PENDING_SUBSCRIPTIONS.get(chat_id, {})
                duration_key = sub_data.get('duration_key', duration_key)
                payment_method = sub_data.get('payment_method', payment_method)
                stars = SUBSCRIPTION_STARS.get(duration_key, 0)
                price = SUBSCRIPTION_MONEY.get(duration_key, "N/A")
                
                caption = (
                    f"📸 **NEW SUBSCRIPTION REQUEST**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 **User:** {first_name}\n"
                    f"🆔 **Username:** @{username}\n"
                    f"🆔 **ID:** `{chat_id}`\n"
                    f"⏱️ **Duration:** {duration_key.replace('_', ' ').title()}\n"
                    f"⭐ **Stars:** {stars}\n"
                    f"💰 **Price:** {price}\n"
                    f"💳 **Payment:** {payment_method.upper()}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📌 Please verify the payment below."
                )
                
                try:
                    sent_msg = bot.send_photo(
                        GROUP_LOG_ID,
                        photo,
                        caption=caption,
                        parse_mode='Markdown',
                        reply_markup=create_subscription_confirm_keyboard(chat_id, duration_key, payment_method)
                    )
                    if chat_id not in PENDING_SUBSCRIPTIONS:
                        PENDING_SUBSCRIPTIONS[chat_id] = {}
                    PENDING_SUBSCRIPTIONS[chat_id]['log_message_id'] = sent_msg.message_id
                    bot.send_message(chat_id, "✅ Screenshot received! Admin will verify your payment shortly.")
                except Exception as e:
                    bot.send_message(chat_id, f"❌ Failed to send to admin logs. Please contact admin directly.\nError: {e}")
                
                del user_states[chat_id]
                delete_state(chat_id)
                return
            elif message.document:
                doc = message.document.file_id
                try:
                    user = bot.get_chat(chat_id)
                    username = user.username or "No username"
                    first_name = user.first_name or "Unknown"
                except:
                    username = "Unknown"
                    first_name = "Unknown"
                sub_data = PENDING_SUBSCRIPTIONS.get(chat_id, {})
                duration_key = sub_data.get('duration_key', duration_key)
                payment_method = sub_data.get('payment_method', payment_method)
                stars = SUBSCRIPTION_STARS.get(duration_key, 0)
                price = SUBSCRIPTION_MONEY.get(duration_key, "N/A")
                caption = (
                    f"📸 **NEW SUBSCRIPTION REQUEST (FILE)**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 {first_name} (@{username})\n"
                    f"🆔 ID: `{chat_id}`\n"
                    f"⏱️ {duration_key.replace('_', ' ').title()}\n"
                    f"⭐ {stars} Stars | 💰 {price}\n"
                    f"💳 {payment_method.upper()}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━"
                )
                sent_msg = bot.send_document(
                    GROUP_LOG_ID,
                    doc,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=create_subscription_confirm_keyboard(chat_id, duration_key, payment_method)
                )
                if chat_id not in PENDING_SUBSCRIPTIONS:
                    PENDING_SUBSCRIPTIONS[chat_id] = {}
                PENDING_SUBSCRIPTIONS[chat_id]['log_message_id'] = sent_msg.message_id
                bot.send_message(chat_id, "✅ Screenshot received! Admin will verify.")
                del user_states[chat_id]
                delete_state(chat_id)
                return
            else:
                bot.send_message(chat_id, "❌ Please send a photo (screenshot) of your payment.")
                return

        # ✅ TEXT HANDLER
        if chat_id in user_states:
            state = user_states[chat_id]

            # 🔐 LOGIN - EMAIL
            if state.get('awaiting_cpm_login_email'):
                user_sessions[chat_id]['email'] = message.text.strip()
                msg_id = state.get('msg_id')
                user_states[chat_id] = {'awaiting_cpm_login_pass': True, 'msg_id': msg_id}
                save_state(chat_id, user_states[chat_id])
                try:
                    bot.edit_message_text("🔑 Send the password:", chat_id, msg_id, reply_markup=cancel_keyboard())
                except:
                    pass
                return

            # 🔐 LOGIN - PASSWORD
            if state.get('awaiting_cpm_login_pass'):
                password = message.text.strip()
                email = user_sessions[chat_id].get('email', '')
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                delete_state(chat_id)
                try:
                    bot.edit_message_text("⏳ Authenticating...", chat_id, msg_id)
                except:
                    pass
                try:
                    web_uid = get_web_uid(chat_id)
                    res = nuker.login(email, password)
                    if res and isinstance(res, dict) and res.get("ok"):
                        nuker.save_token(web_uid, res.get("auth", ""), email, password, res.get("refresh_token", ""), res.get("firebase_uid", ""))
                        user_sessions[chat_id].update({'cpm_logged_in': True, 'web_uid': web_uid})
                        safe_send_dashboard(chat_id, force_refresh=True, is_callback=True, message_id=msg_id)
                    else:
                        err = clean_str(res.get('message', 'Unknown Error') if isinstance(res, dict) else 'Network Failure')
                        try:
                            bot.edit_message_text(f"❌ AUTH FAILED: {err}", chat_id, msg_id, reply_markup=cancel_keyboard())
                        except:
                            pass
                except:
                    try:
                        bot.edit_message_text("❌ API Timeout.", chat_id, msg_id, reply_markup=cancel_keyboard())
                    except:
                        pass
                return

            # ===== OTHER STATES =====
            if state.get('awaiting_add_admin'):
                del user_states[chat_id]
                delete_state(chat_id)
                msg_id = state.get('msg_id')
                if not is_admin(chat_id):
                    return
                try:
                    target_id = int(message.text.strip())
                    add_admin(target_id)
                    try:
                        bot.delete_message(chat_id, msg_id)
                    except:
                        pass
                    bot.send_message(chat_id, f"✅ Admin rights granted to ID: {target_id}")
                except:
                    try:
                        bot.edit_message_text("❌ Invalid ID.", chat_id, msg_id, reply_markup=cancel_keyboard())
                    except:
                        pass
                return
            if state.get('awaiting_rem_admin'):
                del user_states[chat_id]
                delete_state(chat_id)
                msg_id = state.get('msg_id')
                if not is_admin(chat_id):
                    return
                try:
                    target_id = int(message.text.strip())
                    remove_admin(target_id)
                    try:
                        bot.delete_message(chat_id, msg_id)
                    except:
                        pass
                    bot.send_message(chat_id, f"❌ Admin rights revoked from ID: {target_id}")
                except:
                    try:
                        bot.edit_message_text("❌ Invalid ID.", chat_id, msg_id, reply_markup=cancel_keyboard())
                    except:
                        pass
                return
            if state.get('awaiting_add_prem'):
                del user_states[chat_id]
                delete_state(chat_id)
                msg_id = state.get('msg_id')
                if not is_admin(chat_id):
                    return
                try:
                    approve_premium(int(message.text.strip()))
                    try:
                        bot.delete_message(chat_id, msg_id)
                    except:
                        pass
                    bot.send_message(chat_id, f"✅ Premium granted to: {message.text.strip()}")
                except:
                    try:
                        bot.edit_message_text("❌ Invalid ID.", chat_id, msg_id, reply_markup=cancel_keyboard())
                    except:
                        pass
                return
            if state.get('awaiting_revoke'):
                del user_states[chat_id]
                delete_state(chat_id)
                msg_id = state.get('msg_id')
                if not is_admin(chat_id):
                    return
                try:
                    revoke_premium(int(message.text.strip()))
                    try:
                        bot.delete_message(chat_id, msg_id)
                    except:
                        pass
                    bot.send_message(chat_id, f"❌ Premium revoked from: {message.text.strip()}")
                except:
                    try:
                        bot.edit_message_text("❌ Invalid ID.", chat_id, msg_id, reply_markup=cancel_keyboard())
                    except:
                        pass
                return
            if state.get('awaiting_broadcast'):
                del user_states[chat_id]
                delete_state(chat_id)
                msg_id = state.get('msg_id')
                if not is_admin(chat_id):
                    return
                c = 0
                users = get_all_tracked_users()
                for uid in users:
                    try:
                        bot.send_message(uid, f"📢 ANNOUNCEMENT\n┣━━━━━━━━━━━━━━━━━━┫\n{message.text}")
                        c += 1
                    except:
                        pass
                try:
                    bot.delete_message(chat_id, msg_id)
                    bot.send_message(chat_id, f"✅ Delivered to {c} users.")
                except:
                    pass
                return
            if state.get('awaiting_admin_bulk_source_email'):
                user_sessions[chat_id]['bulk_source_email'] = message.text.strip()
                msg_id = state.get('msg_id')
                user_states[chat_id] = {'awaiting_admin_bulk_source_pass': True, 'msg_id': msg_id}
                save_state(chat_id, user_states[chat_id])
                try:
                    bot.edit_message_text("🔑 Send the SOURCE account password:", chat_id, msg_id, reply_markup=cancel_keyboard())
                except:
                    pass
                return
            if state.get('awaiting_admin_bulk_source_pass'):
                user_sessions[chat_id]['bulk_source_pass'] = message.text.strip()
                msg_id = state.get('msg_id')
                user_states[chat_id] = {'awaiting_admin_bulk_count': True, 'msg_id': msg_id}
                save_state(chat_id, user_states[chat_id])
                try:
                    bot.edit_message_text("📦 How many clones? (1-10):", chat_id, msg_id, reply_markup=cancel_keyboard())
                except:
                    pass
                return
            if state.get('awaiting_admin_bulk_count'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                delete_state(chat_id)
                try:
                    count = int(message.text.strip())
                    if not (1 <= count <= 10):
                        try:
                            bot.edit_message_text("❌ Limit 1-10.", chat_id, msg_id, reply_markup=cancel_keyboard())
                        except:
                            pass
                        return
                    src_email = user_sessions[chat_id].get('bulk_source_email')
                    src_pass = user_sessions[chat_id].get('bulk_source_pass')
                    threading.Thread(target=background_bulk_clone, args=(chat_id, src_email, src_pass, count, msg_id)).start()
                except:
                    try:
                        bot.edit_message_text("❌ Must be a number.", chat_id, msg_id, reply_markup=cancel_keyboard())
                    except:
                        pass
                return
            if state.get('awaiting_clone_source_email'):
                user_sessions[chat_id]['clone_src_email'] = message.text.strip()
                msg_id = state.get('msg_id')
                user_states[chat_id] = {'awaiting_clone_source_pass': True, 'msg_id': msg_id}
                save_state(chat_id, user_states[chat_id])
                try:
                    bot.edit_message_text("🔑 Send SOURCE password:", chat_id, msg_id, reply_markup=cancel_keyboard())
                except:
                    pass
                return
            if state.get('awaiting_clone_source_pass'):
                user_sessions[chat_id]['clone_src_pass'] = message.text.strip()
                msg_id = state.get('msg_id')
                user_states[chat_id] = {'awaiting_clone_target_email': True, 'msg_id': msg_id}
                save_state(chat_id, user_states[chat_id])
                try:
                    bot.edit_message_text("📧 Send TARGET email:", chat_id, msg_id, reply_markup=cancel_keyboard())
                except:
                    pass
                return
            if state.get('awaiting_clone_target_email'):
                user_sessions[chat_id]['clone_tgt_email'] = message.text.strip()
                msg_id = state.get('msg_id')
                user_states[chat_id] = {'awaiting_clone_target_pass': True, 'msg_id': msg_id}
                save_state(chat_id, user_states[chat_id])
                try:
                    bot.edit_message_text("🔑 Send TARGET password:", chat_id, msg_id, reply_markup=cancel_keyboard())
                except:
                    pass
                return
            if state.get('awaiting_clone_target_pass'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                delete_state(chat_id)
                tgt_pass = message.text.strip()
                src_email = user_sessions[chat_id].get('clone_src_email')
                src_pass = user_sessions[chat_id].get('clone_src_pass')
                tgt_email = user_sessions[chat_id].get('clone_tgt_email')
                if not check_and_deduct_coins(chat_id, COIN_COSTS['clone'], "Clone Account"):
                    return
                threading.Thread(target=background_single_clone, args=(chat_id, src_email, src_pass, tgt_email, tgt_pass, msg_id)).start()
                return
            if state.get('awaiting_single_car_id'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                delete_state(chat_id)
                try:
                    car_id = int(message.text.strip())
                    web_uid = get_web_uid(chat_id)
                    td = nuker.get_token_data(web_uid)
                    em = td.get("email") if td else ""
                    pw = td.get("password") if td else ""
                    if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], f"Unlock Car {car_id}"):
                        return
                    try:
                        bot.edit_message_text(f"⏳ Injecting Car ID {car_id}...", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
                    except:
                        pass

                    def run_single_inject():
                        if not em or not pw:
                            try:
                                bot.edit_message_text("❌ Failed to Auth. Please login again.", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
                            except:
                                pass
                            return
                        ok, _, tok = nuker.get_auth(web_uid)
                        if not ok:
                            try:
                                bot.edit_message_text("❌ Auth failed.", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
                            except:
                                pass
                            return
                        stok, _ = verify_user(*SOURCE_ACCOUNT)
                        if not stok:
                            try:
                                bot.edit_message_text("❌ Source unavailable.", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
                            except:
                                pass
                            return
                        source_cars = get_source_cars_cached()
                        if not source_cars:
                            try:
                                bot.edit_message_text("❌ No cars in source.", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
                            except:
                                pass
                            return
                        car_data = next((c for c in source_cars if int(c.get("CarID", 0)) == car_id), None)
                        if not car_data:
                            try:
                                bot.edit_message_text(f"❌ Car ID {car_id} not found.", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
                            except:
                                pass
                            return
                        if cpm1_clone_car(tok, car_data, td.get("firebase_uid"), token_source=stok):
                            try:
                                bot.edit_message_text(f"✅ Car ID {car_id} Unlocked!", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
                            except:
                                pass
                        else:
                            try:
                                bot.edit_message_text(f"❌ Failed to unlock ID {car_id}.", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
                            except:
                                pass

                    threading.Thread(target=run_single_inject).start()
                except:
                    try:
                        bot.edit_message_text("❌ Invalid ID.", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
                    except:
                        pass
                return
            if state.get('awaiting_change_name'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                delete_state(chat_id)
                if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Change Name"):
                    return
                nuker.change_player_name(user_sessions[chat_id].get('web_uid'), message.text.strip())
                safe_send_dashboard(chat_id, custom_top_msg="✅ Name Changed!", force_refresh=True, is_callback=True, message_id=msg_id)
                return
            if state.get('awaiting_change_id'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                delete_state(chat_id)
                if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Change ID"):
                    return
                nuker.change_player_id(user_sessions[chat_id].get('web_uid'), message.text.strip().upper())
                safe_send_dashboard(chat_id, custom_top_msg="✅ ID Changed!", force_refresh=True, is_callback=True, message_id=msg_id)
                return
            if state.get('awaiting_cpm1_email'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                delete_state(chat_id)
                if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Change Email"):
                    return
                nuker.change_email(user_sessions[chat_id].get('web_uid'), message.text.strip())
                safe_send_dashboard(chat_id, custom_top_msg="✅ Email Changed!", force_refresh=True, is_callback=True, message_id=msg_id)
                return
            if state.get('awaiting_change_pass'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                delete_state(chat_id)
                if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Change Password"):
                    return
                try:
                    bot.delete_message(chat_id, msg_id)
                except:
                    pass
                safe_send_dashboard(chat_id, custom_top_msg="✅ Password Processed!", force_refresh=True, is_callback=False)
                return
            if state.get('awaiting_money'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                delete_state(chat_id)
                if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Add Money"):
                    return
                try:
                    nuker.set_money(user_sessions[chat_id].get('web_uid'), int(message.text.strip()))
                    safe_send_dashboard(chat_id, custom_top_msg="✅ Money Added!", force_refresh=True, is_callback=True, message_id=msg_id)
                except:
                    try:
                        bot.edit_message_text("❌ Numeric required.", chat_id, msg_id, reply_markup=cancel_keyboard())
                    except:
                        pass
                return
            if state.get('awaiting_coin'):
                msg_id = state.get('msg_id')
                del user_states[chat_id]
                delete_state(chat_id)
                if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Add Coins"):
                    return
                try:
                    nuker.set_coin(user_sessions[chat_id].get('web_uid'), int(message.text.strip()))
                    safe_send_dashboard(chat_id, custom_top_msg="✅ Coins Added!", force_refresh=True, is_callback=True, message_id=msg_id)
                except:
                    try:
                        bot.edit_message_text("❌ Numeric required.", chat_id, msg_id, reply_markup=cancel_keyboard())
                    except:
                        pass
                return

        # Normal text
        text = message.text
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        track_user(chat_id)
        if not text or text.startswith('/'):
            return

    except Exception as e:
        print(f"Handler error: {e}")
        pass

# ═══════════════════════════════════════════════════════════
# 🎯 BUTTON HANDLER
# ═══════════════════════════════════════════════════════════
def premium_required(call):
    chat_id = call.message.chat.id
    if not is_premium(chat_id):
        try:
            bot.answer_callback_query(call.id, "❌ Paid Feature. Request Admins.", show_alert=True)
        except:
            pass
        return True
    return False

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data

    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    track_user(chat_id)

    if chat_id not in user_states:
        saved = load_state(chat_id)
        if saved:
            user_states[chat_id] = saved

    silent_nav_buttons = ["menu_main","init_login","logout","refresh_account",
                          "menu_account","menu_economy","menu_vehicles","menu_unlocks",
                          "acc_info","acc_name","acc_id","acc_email","acc_pass","acc_clone",
                          "eco_money_cust","eco_coins_cust","veh_unlock_single","veh_unlock_all",
                          "menu_subscription"]
    if data in silent_nav_buttons:
        try:
            bot.answer_callback_query(call.id)
        except:
            pass

    # ====== SUBSCRIPTION CONFIRM ======
    if data.startswith("sub_confirm_"):
        rest = data[len("sub_confirm_"):]
        user_id, duration_key, payment_method = _parse_sub_callback(rest)
        if not user_id:
            bot.answer_callback_query(call.id, "❌ Invalid data!", show_alert=True)
            return
        if payment_method not in PAYMENT_METHODS:
            bot.answer_callback_query(call.id, "❌ Invalid payment method!", show_alert=True)
            return
        duration_hours = SUBSCRIPTION_DURATIONS[duration_key]
        try:
            user = bot.get_chat(user_id)
            username = user.username or "No username"
            first_name = user.first_name or "Unknown"
        except Exception:
            username = "Unknown"
            first_name = "Unknown"
        
        time_key = create_time_key(duration_hours, chat_id)
        set_user_subscription_time(user_id, duration_hours, time_key)
        
        if user_id not in user_sessions:
            user_sessions[user_id] = {}
        user_sessions[user_id]['logged_in'] = True
        user_sessions[user_id]['is_time_key'] = True
        
        expires = get_subscription_expiry(user_id)
        expires_str = datetime.fromtimestamp(expires).strftime("%Y-%m-%d %H:%M:%S") if expires else "Unknown"
        
        bot.send_message(
            user_id,
            f"✅ **SUBSCRIPTION CONFIRMED!**\n━━━━━━━━━━━━━━━━━━━━━\n🎉 Your subscription is now active!\n⏱️ Duration: {duration_key.replace('_', ' ').title()}\n📅 Expires: {expires_str}\n\n✅ You can now use all bot features!",
            parse_mode='Markdown'
        )
        
        try:
            log_msg_id = PENDING_SUBSCRIPTIONS.get(user_id, {}).get('log_message_id')
            if log_msg_id:
                bot.edit_message_caption(
                    caption=f"✅ **SUBSCRIPTION CONFIRMED**\n━━━━━━━━━━━━━━━━━━━━━\n👤 {first_name} (@{username})\n🆔 ID: `{user_id}`\n⏱️ Duration: {duration_key.replace('_', ' ').title()}\n💳 Payment: {payment_method.upper()}\n🔑 Key: `{time_key}`\n✅ Confirmed by Admin",
                    chat_id=GROUP_LOG_ID,
                    message_id=log_msg_id,
                    parse_mode='Markdown'
                )
                bot.edit_message_reply_markup(GROUP_LOG_ID, log_msg_id, reply_markup=None)
        except Exception as e:
            print(f"Failed to update log: {e}")
        
        bot.answer_callback_query(call.id, "✅ Subscription confirmed!", show_alert=True)
        if user_id in PENDING_SUBSCRIPTIONS:
            del PENDING_SUBSCRIPTIONS[user_id]
        return

    # ====== SUBSCRIPTION DECLINE ======
    if data.startswith("sub_decline_"):
        rest = data[len("sub_decline_"):]
        user_id, duration_key, payment_method = _parse_sub_callback(rest)
        if not user_id:
            bot.answer_callback_query(call.id, "❌ Invalid data!", show_alert=True)
            return
        if payment_method not in PAYMENT_METHODS:
            bot.answer_callback_query(call.id, "❌ Invalid payment method!", show_alert=True)
            return
        try:
            user = bot.get_chat(user_id)
            username = user.username or "No username"
            first_name = user.first_name or "Unknown"
        except Exception:
            username = "Unknown"
            first_name = "Unknown"
        
        bot.send_message(
            user_id,
            "❌ **SUBSCRIPTION DECLINED**\n━━━━━━━━━━━━━━━━━━━━━\n⚠️ Your payment could not be verified.\n📌 Please contact @Maarkryan for assistance.",
            parse_mode='Markdown'
        )
        
        try:
            log_msg_id = PENDING_SUBSCRIPTIONS.get(user_id, {}).get('log_message_id')
            if log_msg_id:
                bot.edit_message_caption(
                    caption=f"❌ **SUBSCRIPTION DECLINED**\n━━━━━━━━━━━━━━━━━━━━━\n👤 {first_name} (@{username})\n🆔 ID: `{user_id}`\n⏱️ Duration: {duration_key.replace('_', ' ').title()}\n💳 Payment: {payment_method.upper()}\n❌ Declined by Admin",
                    chat_id=GROUP_LOG_ID,
                    message_id=log_msg_id,
                    parse_mode='Markdown'
                )
                bot.edit_message_reply_markup(GROUP_LOG_ID, log_msg_id, reply_markup=None)
        except Exception as e:
            print(f"Failed to update log: {e}")
        
        bot.answer_callback_query(call.id, "❌ Subscription declined!", show_alert=True)
        if user_id in PENDING_SUBSCRIPTIONS:
            del PENDING_SUBSCRIPTIONS[user_id]
        return

    # ====== REST OF CALLBACKS ======
    if data == "menu_main":
        if chat_id in user_states:
            del user_states[chat_id]
        delete_state(chat_id)
        return safe_send_dashboard(chat_id, force_refresh=False, is_callback=True, message_id=msg_id)

    if data == "init_login":
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "📧 Send email to login:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_cpm_login_email': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return

    if data == "logout":
        if chat_id in user_sessions:
            user_sessions[chat_id]['cpm_logged_in'] = False
        nuker.delete_token(get_web_uid(chat_id))
        return safe_send_dashboard(chat_id, force_refresh=False, is_callback=True, message_id=msg_id)

    if data == "refresh_account":
        return safe_send_dashboard(chat_id, custom_top_msg="✅ Refreshed!", force_refresh=True, is_callback=True, message_id=msg_id)

    if data == "menu_account":
        try:
            bot.edit_message_text("👤 Account Management", chat_id, msg_id, reply_markup=create_account_keyboard())
        except:
            pass
        return
    if data == "menu_economy":
        try:
            bot.edit_message_text("💰 Economy Settings", chat_id, msg_id, reply_markup=create_economy_keyboard())
        except:
            pass
        return
    if data == "menu_vehicles":
        try:
            bot.edit_message_text("🚗 Vehicles Settings", chat_id, msg_id, reply_markup=create_vehicles_keyboard())
        except:
            pass
        return
    if data == "menu_unlocks":
        try:
            bot.edit_message_text("🔓 Unlocks Configuration", chat_id, msg_id, reply_markup=create_unlocks_keyboard())
        except:
            pass
        return
    if data == "menu_subscription":
        try:
            bot.edit_message_text("💎 Subscription Options", chat_id, msg_id, reply_markup=create_subscription_keyboard())
        except:
            pass
        return

    if data == "acc_info":
        return safe_send_dashboard(chat_id, is_callback=True, message_id=msg_id)
    if data == "acc_name":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Change Name"):
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "✏️ Enter new Name:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_change_name': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return
    if data == "acc_id":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Change ID"):
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "🆔 Enter new ID:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_change_id': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return
    if data == "acc_email":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Change Email"):
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "📧 Enter new Email:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_cpm1_email': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return
    if data == "acc_pass":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Change Password"):
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "🔑 Enter new Password:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_change_pass': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return
    if data == "acc_clone":
        if premium_required(call):
            return
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "📋 Send SOURCE account email:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_clone_source_email': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return

    if data == "admin_panel":
        if not is_admin(chat_id):
            return
        try:
            bot.answer_callback_query(call.id)
        except:
            pass
        try:
            bot.edit_message_text("👑 OVERSEER TERMINAL", chat_id, msg_id, reply_markup=create_admin_keyboard())
        except:
            pass
        return
    if data == "admin_add_admin":
        if not is_admin(chat_id):
            return
        try:
            bot.answer_callback_query(call.id)
        except:
            pass
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "➕ ENTER TARGET ID:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_add_admin': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return
    if data == "admin_rem_admin":
        if not is_admin(chat_id):
            return
        try:
            bot.answer_callback_query(call.id)
        except:
            pass
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "➖ ENTER TARGET ID:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_rem_admin': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return
    if data == "admin_view_admins":
        if not is_admin(chat_id):
            return
        try:
            bot.answer_callback_query(call.id)
        except:
            pass
        admins = get_all_admins()
        msg_text = "👥 CURRENT ADMINS\n" + "".join([f"🆔 `{uid}`\n" for uid in admins])
        try:
            bot.edit_message_text(msg_text, chat_id, msg_id, reply_markup=create_admin_keyboard())
        except:
            pass
        return
    if data == "admin_add_prem":
        if not is_admin(chat_id):
            return
        try:
            bot.answer_callback_query(call.id)
        except:
            pass
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "✅ ENTER TARGET ID:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_add_prem': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return
    if data == "admin_revoke":
        if not is_admin(chat_id):
            return
        try:
            bot.answer_callback_query(call.id)
        except:
            pass
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "❌ TARGET ID:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_revoke': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return
    if data == "admin_broadcast":
        if not is_admin(chat_id):
            return
        try:
            bot.answer_callback_query(call.id)
        except:
            pass
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "📢 ENTER BROADCAST MESSAGE:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_broadcast': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return
    if data == "admin_stats":
        if not is_admin(chat_id):
            return
        try:
            bot.answer_callback_query(call.id)
        except:
            pass
        t_users = get_total_users()
        try:
            bot.edit_message_text(f"📊 TELEMETRY\n👥 Users: {t_users}\n✅ Premium: {len(get_all_approved())}\n👑 Admins: {len(get_all_admins())}", chat_id, msg_id, reply_markup=create_admin_keyboard())
        except:
            pass
        return
    if data == "admin_bulk_clone":
        if not is_admin(chat_id):
            return
        try:
            bot.answer_callback_query(call.id)
        except:
            pass
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "📦 Send SOURCE account email:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_admin_bulk_source_email': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return

    web_uid = get_web_uid(chat_id)

    def exec_mod(call_obj, name, func, *args, cost=COIN_COSTS['individual']):
        try:
            if not check_and_deduct_coins(chat_id, cost, name):
                return
            if data.startswith("eco_"):
                menu_text = "💰 Economy Settings"
                kb = create_economy_keyboard()
            elif data.startswith("veh_") or data == "veh_fix":
                menu_text = "🚗 Vehicles Settings"
                kb = create_vehicles_keyboard()
            else:
                menu_text = "🔓 Unlocks Configuration"
                kb = create_unlocks_keyboard()
            try:
                bot.edit_message_text(f"⏳ Executing...\n\n{menu_text}", chat_id, msg_id, reply_markup=kb)
            except:
                pass
            if args:
                res = func(web_uid, *args)
            else:
                res = func(web_uid)
            if res and isinstance(res, dict) and res.get("ok"):
                final_text = f"✅ {name}\n\n{menu_text}"
            else:
                err = clean_str(res.get("message", "API Blocked") if isinstance(res, dict) else "Timeout")
                final_text = f"❌ Failed: {err}\n\n{menu_text}"
            try:
                bot.edit_message_text(final_text, chat_id, msg_id, reply_markup=kb)
            except:
                pass
        except Exception as e:
            try:
                bot.answer_callback_query(call_obj.id, f"❌ Error.", show_alert=True)
            except:
                pass

    if data == "eco_money_max":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Money 50M"):
            return
        return exec_mod(call, "Money -> 50M", nuker.set_money, 50000000, cost=0)
    if data == "eco_coins_max":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Coins 500K"):
            return
        return exec_mod(call, "Coins -> 500K", nuker.set_coin, 500000, cost=0)
    if data == "eco_king":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "King Rank"):
            return
        return exec_mod(call, "King Rank", nuker.set_rank, cost=0)
    if data == "eco_money_cust":
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "💵 Enter amount:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_money': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return
    if data == "eco_coins_cust":
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "🪙 Enter amount:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_coin': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return

    if data == "veh_fix":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Fix Account"):
            return
        return exec_mod(call, "Fix Account", nuker.fix_account, cost=0)
    if data == "veh_unlock_all":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['bulk'], "Unlock All Cars"):
            return
        try:
            bot.edit_message_text("⚠️ MASS INJECTION\nThis will inject cars from source.\nProceed?", chat_id, msg_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ YES", callback_data="start_car_inject"), types.InlineKeyboardButton("❌ CANCEL", callback_data="menu_vehicles")))
        except:
            pass
        return
    if data == "start_car_inject":
        td = nuker.get_token_data(get_web_uid(chat_id))
        em = td.get("email") if td else ""
        pw = td.get("password") if td else ""
        threading.Thread(target=background_inject_all_cars, args=(chat_id, em, pw, msg_id)).start()
        return
    if data == "veh_unlock_single":
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "🚙 Enter Car ID (1-270):", reply_markup=cancel_keyboard())
        user_states[chat_id] = {'awaiting_single_car_id': True, 'msg_id': msg.message_id}
        save_state(chat_id, user_states[chat_id])
        return

    if data == "unl_w16":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "W16 Engine"):
            return
        return exec_mod(call, "W16 Engine", nuker.unlock_w16, cost=0)
    if data == "unl_smoke":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Smoke"):
            return
        return exec_mod(call, "Smoke", nuker.unlock_smoke, cost=0)
    if data == "unl_fuel":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Max Fuel"):
            return
        return exec_mod(call, "Max Fuel", nuker.unlimited_fuel, cost=0)
    if data == "unl_damage":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "No Damage"):
            return
        return exec_mod(call, "No Damage", nuker.disable_damage, cost=0)
    if data == "unl_horns":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Horns"):
            return
        return exec_mod(call, "Horns", nuker.unlock_horns, cost=0)
    if data == "unl_anim":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Animations"):
            return
        return exec_mod(call, "Animations", nuker.unlock_animations, cost=0)
    if data == "unl_houses":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "All Houses"):
            return
        return exec_mod(call, "All Houses", nuker.unlock_houses, cost=0)
    if data == "unl_wheels":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Wheels"):
            return
        return exec_mod(call, "Wheels", nuker.unlock_wheels, cost=0)
    if data == "unl_levels":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "Complete Levels"):
            return
        return exec_mod(call, "Complete Levels", nuker.complete_all_levels, cost=0)
    if data == "unl_clothes":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['individual'], "All Clothes"):
            return
        return exec_mod(call, "All Clothes", nuker.unlock_all_clothes, cost=0)
    if data == "unl_ultimate":
        if not check_and_deduct_coins(chat_id, COIN_COSTS['bulk'], "Ultimate Unlock"):
            return
        return exec_mod(call, "Ultimate Glitch", nuker.unlock_all_features, cost=0)

    if data == "sub_stars":
        try:
            bot.edit_message_text("⭐ Choose duration (Stars):", chat_id, msg_id, reply_markup=create_subscription_duration_keyboard("stars"))
        except:
            pass
        return
    if data == "sub_money":
        try:
            bot.edit_message_text("💳 Choose duration (Money):", chat_id, msg_id, reply_markup=create_subscription_duration_keyboard("money"))
        except:
            pass
        return
    if data == "sub_time_key":
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
        msg = bot.send_message(chat_id, "🔑 Enter Time Key:", reply_markup=cancel_keyboard())
        bot.register_next_step_handler(msg, process_time_key_input)
        return
    if data == "sub_free_trial":
        trial_key = create_trial_key(chat_id, 10)
        use_trial_key(trial_key, chat_id)
        bot.send_message(chat_id, "🎁 Free trial activated! 10 minutes access.")
        safe_send_dashboard(chat_id, custom_top_msg="🎁 Trial Active!", is_callback=True, message_id=msg_id)
        return

    if data.startswith("sub_duration_"):
        rest = data.replace("sub_duration_", "")
        parts = rest.rsplit("_", 1)
        if len(parts) != 2:
            bot.answer_callback_query(call.id, "❌ Invalid format")
            return
        duration_key, payment_type = parts[0], parts[1]
        if duration_key not in SUBSCRIPTION_DURATIONS:
            bot.answer_callback_query(call.id, "❌ Invalid duration")
            return
        if chat_id not in PENDING_SUBSCRIPTIONS:
            PENDING_SUBSCRIPTIONS[chat_id] = {}
        PENDING_SUBSCRIPTIONS[chat_id]['duration_key'] = duration_key
        PENDING_SUBSCRIPTIONS[chat_id]['duration_hours'] = SUBSCRIPTION_DURATIONS[duration_key]
        PENDING_SUBSCRIPTIONS[chat_id]['payment_type'] = payment_type
        if payment_type == "stars":
            stars = SUBSCRIPTION_STARS.get(duration_key, 0)
            try:
                invoice = bot.create_invoice_link(
                    title=f"Subscription {duration_key.replace('_',' ').title()}",
                    description=f"Get {duration_key.replace('_',' ').title()} access",
                    payload=f"stars_payment_{chat_id}_{duration_key}",
                    provider_token="",
                    currency="XTR",
                    prices=[types.LabeledPrice(label=f"{stars} Stars", amount=stars)]
                )
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(f"⭐ Pay {stars} Stars", url=invoice))
                markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="menu_subscription"))
                bot.edit_message_text(f"⭐ Please pay {stars} Stars to activate your subscription.", chat_id, msg_id, reply_markup=markup)
            except Exception as e:
                bot.send_message(chat_id, f"❌ Stars payment error: {e}")
        else:
            bot.edit_message_text("💳 Choose payment method:", chat_id, msg_id, reply_markup=create_payment_method_keyboard())
        return

    if data.startswith("sub_payment_"):
        payment_method = data.replace("sub_payment_", "")
        if chat_id not in PENDING_SUBSCRIPTIONS:
            PENDING_SUBSCRIPTIONS[chat_id] = {}
        PENDING_SUBSCRIPTIONS[chat_id]['payment_method'] = payment_method
        text = PAYMENT_METHODS.get(payment_method, {}).get("details", "Payment selected")
        bot.send_message(chat_id, f"💳 {text}\n\n📤 Send screenshot:", reply_markup=cancel_keyboard())
        user_states[chat_id] = {
            'awaiting_subscription_photo': True,
            'msg_id': msg_id,
            'payment_method': payment_method,
            'duration_key': PENDING_SUBSCRIPTIONS[chat_id].get('duration_key', '1_week')
        }
        save_state(chat_id, user_states[chat_id])
        return

    bot.answer_callback_query(call.id, "✅ Done")

def process_time_key_input(message):
    chat_id = message.chat.id
    key = message.text.strip()
    success, msg = use_time_key(key, chat_id)
    if success:
        bot.send_message(chat_id, f"✅ Time key activated! {msg}")
    else:
        bot.send_message(chat_id, f"❌ {msg}")
    safe_send_dashboard(chat_id, force_refresh=True)

# ═══════════════════════════════════════════════════════════
# 💰 TELEGRAM STARS PAYMENT HANDLERS
# ═══════════════════════════════════════════════════════════
@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout_query_handler(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment_handler(message):
    chat_id = message.chat.id
    payment = message.successful_payment
    payload = payment.invoice_payload
    try:
        rest = payload.replace("stars_payment_", "")
        user_id_str, duration_key = rest.split("_", 1)
        user_id = int(user_id_str)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Payment processing error: {e}")
        return

    if duration_key not in SUBSCRIPTION_DURATIONS:
        bot.send_message(chat_id, "❌ Unknown duration.")
        return

    hours = SUBSCRIPTION_DURATIONS[duration_key]
    set_user_subscription_time(user_id, hours, f"stars_{duration_key}")
    star_cost = SUBSCRIPTION_STARS.get(duration_key, 0)
    add_stars_balance(star_cost)

    bot.send_message(chat_id, f"✅ Your subscription for {duration_key.replace('_',' ').title()} is now active!\nThank you for your Stars payment (⭐{star_cost}).")
    safe_send_dashboard(chat_id, custom_top_msg="✅ Subscription Activated!", force_refresh=True)

# ═══════════════════════════════════════════════════════════
# 🚀 BOT POLLING LOOP
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("="*60)
    print("☠️ 𝙈𝘼𝙍𝙆𝘾𝙋𝙈1𝙏𝙊𝙊𝙇𝙎 - CPM1 ULTIMATE ☠️")
    print("="*60)
    print("✅ Bot is running!")
    print("👑 Admins: 8254935096, 6531314640")
    print("💎 Subscription + Coin System Active")
    print("🚀 Optimized for Render Free Tier")
    print("📸 Screenshots forwarded to group: -1004441134033")
    print("="*60)

    try:
        bot.delete_webhook(drop_pending_updates=True)
        print("🧹 Webhook cleared")
    except Exception as e:
        print(f"⚠️ Webhook cleanup: {e}")

    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as e:
            print(f"❌ Polling error: {e}")
            time.sleep(3)
