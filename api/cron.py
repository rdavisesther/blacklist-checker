import os
import ipaddress
import dns.resolver
import dns.exception
import requests
from flask import Flask, jsonify

app = Flask(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ZEN_ZONE = "zen.spamhaus.org"
DBL_ZONE = "dbl.spamhaus.org"

# Spamhaus return codes used here:
# CSS in ZEN => 127.0.0.3
# ZEN includes SBL, CSS, XBL, PBL
# We treat known ZEN response codes conservatively.
ZEN_CODE_MAP = {
    "127.0.0.2": "SBL",
    "127.0.0.3": "CSS",
    "127.0.0.4": "XBL",
    "127.0.0.9": "SBL",
    "127.0.0.10": "PBL",
    "127.0.0.11": "PBL",
}

def read_list(file_path: str) -> list[str]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def is_ipv4(value: str) -> bool:
    try:
        return isinstance(ipaddress.ip_address(value), ipaddress.IPv4Address)
    except ValueError:
        return False

def is_domain(value: str) -> bool:
    if not value or len(value) > 253:
        return False
    parts = value.strip(".").split(".")
    if len(parts) < 2:
        return False
    for part in parts:
        if not part or len(part) > 63:
            return False
        if part.startswith("-") or part.endswith("-"):
            return False
    return True

def reverse_ipv4(ip: str) -> str:
    return ".".join(reversed(ip.split(".")))

def dns_a_lookup(name: str) -> list[str]:
    try:
        answers = dns.resolver.resolve(name, "A")
        return [r.to_text() for r in answers]
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout):
        return []

def check_ip_spamhaus(ip: str) -> dict:
    result = {"SBL": False, "CSS": False, "XBL": False, "PBL": False}

    if not is_ipv4(ip):
        return result

    query = f"{reverse_ipv4(ip)}.{ZEN_ZONE}"
    codes = dns_a_lookup(query)

    for code in codes:
        list_name = ZEN_CODE_MAP.get(code)
        if list_name:
            result[list_name] = True

    return result

def check_domain_dbl(domain: str) -> bool:
    if not is_domain(domain):
        return False

    query = f"{domain.strip('.').lower()}.{DBL_ZONE}"
    codes = dns_a_lookup(query)

    # Any valid A answer on DBL domain query means listed for our usage here.
    # Never use DBL for IP lookups.
    return len(codes) > 0

def build_result() -> str:
    ips = read_list("ips.txt")
    domains = read_list("domains.txt")

    counts = {
        "CSS": 0,
        "XBL": 0,
        "PBL": 0,
        "SBL": 0,
        "Clean": 0,
    }

    dbl_count = 0

    for ip in ips:
        if not is_ipv4(ip):
            continue

        res = check_ip_spamhaus(ip)
        listed = False

        for key in ["CSS", "XBL", "PBL", "SBL"]:
            if res[key]:
                counts[key] += 1
                listed = True

        if not listed:
            counts["Clean"] += 1

    for domain in domains:
        if check_domain_dbl(domain):
            dbl_count += 1

    return f"""🟤 CSS        : {counts['CSS']} Listed
🟠 XBL        : {counts['XBL']} Listed
🔵 PBL        : {counts['PBL']} Listed
🔴 SBL        : {counts['SBL']} Listed
✅ Clean      : {counts['Clean']}

━━━━━━━━━━━━━━
🌐 DOMAINS
━━━━━━━━━━━━━━
🌍 DBL        : {dbl_count} Listed"""

@app.route("/api/cron", methods=["GET"])
def run_cron():
    if not BOT_TOKEN or not CHAT_ID:
        return jsonify({
            "ok": False,
            "error": "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"
        }), 500

    text = build_result()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    res = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": text
        },
        timeout=30
    )

    try:
        response_json = res.json()
    except Exception:
        response_json = {"raw": res.text}

    return jsonify({
        "ok": res.ok,
        "status": res.status_code,
        "response": response_json
    }), (200 if res.ok else 500)
