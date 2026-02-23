# ═══════════════════════════════════════════════════════
#  VERIFICATION BOT — WEBSITE API  (Flask + pymongo sync)
#
#  Auth: pass API_SECRET via any one of:
#    Header : X-API-Secret: your_secret
#    Query  : ?secret=your_secret
#    JSON   : { "secret": "your_secret", ... }
# ═══════════════════════════════════════════════════════

from flask import Flask, request, jsonify
from config import API_SECRET, PORT
from database.database import (
    sync_global_stats,
    sync_verify_code,
    sync_check_code,
    sync_revoke_code,
)

app = Flask(__name__)


def _auth_ok() -> bool:
    secret = (
        request.headers.get("X-API-Secret")
        or request.args.get("secret")
        or (request.get_json(silent=True) or {}).get("secret", "")
        or request.form.get("secret", "")
    )
    return secret == API_SECRET


def _err(msg: str, code: int = 400):
    return jsonify({"ok": False, "error": msg}), code


def _body() -> dict:
    return request.get_json(silent=True) or {}


def _get_ip() -> str:
    """Get real client IP, accounting for proxies (Render, Cloudflare, etc.)"""
    return (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP", "")
        or request.remote_addr
        or "unknown"
    )


@app.route("/")
def index():
    return jsonify({
        "service": "Telegram Verification Bot API",
        "endpoints": {
            "GET|POST /telegram-verify?action=status":  "Global stats",
            "POST     /telegram-verify?action=verify":  "Verify code + register device",
            "POST     /telegram-verify?action=check":   "Check code (no device registration)",
            "POST     /telegram-verify?action=revoke":  "Admin: revoke a code",
        },
        "auth": "X-API-Secret header  OR  ?secret=  OR  JSON body 'secret' field",
    })


@app.route("/health")
def health():
    return jsonify({"ok": True, "status": "running"})


@app.route("/telegram-verify", methods=["GET", "POST"])
def telegram_verify():
    if not _auth_ok():
        return _err("Unauthorised — invalid or missing API secret", 401)

    action = (
        request.args.get("action")
        or _body().get("action", "")
        or request.form.get("action", "")
    )

    # ── STATUS ───────────────────────────────────────────
    if action == "status":
        stats = sync_global_stats()
        return jsonify({"ok": True, **stats})
        # Response:
        # { "ok": true, "active_codes": 5, "max_concurrent": 2,
        #   "can_generate": true, "total_used": 47, "active_users": [123, 456] }

    # ── VERIFY ───────────────────────────────────────────
    elif action == "verify":
        body      = _body()
        code      = (request.args.get("code")      or body.get("code",      "")).strip()
        device_id = (request.args.get("device_id") or body.get("device_id", "")).strip()
        ip        = _get_ip()

        if not code:
            return _err("Missing required field: 'code'")
        if not device_id:
            return _err("Missing required field: 'device_id'")

        result = sync_verify_code(code, device_id, ip=ip)
        return jsonify({"ok": result["valid"], **result})
        # Success:  { "ok": true,  "valid": true,  "telegram_id": 123, "devices_used": 1, "devices_max": 2 }
        # Invalid:  { "ok": false, "valid": false, "reason": "Code not found or no longer active" }
        # Too many: { "ok": false, "valid": false, "reason": "Maximum 2 devices...", "devices_used": 2 }

    # ── CHECK ────────────────────────────────────────────
    elif action == "check":
        body = _body()
        code = (request.args.get("code") or body.get("code", "")).strip()

        if not code:
            return _err("Missing required field: 'code'")

        result = sync_check_code(code)
        return jsonify({"ok": result["valid"], **result})
        # { "ok": true, "valid": true, "telegram_id": 123, "devices_used": 1, "devices_remaining": 1 }

    # ── REVOKE (admin) ───────────────────────────────────
    elif action == "revoke":
        body        = _body()
        code        = (request.args.get("code")        or body.get("code",        "")).strip()
        telegram_id = (request.args.get("telegram_id") or body.get("telegram_id"))

        if not code and not telegram_id:
            return _err("Provide either 'code' or 'telegram_id'")

        sync_revoke_code(
            code=code or None,
            telegram_id=int(telegram_id) if telegram_id else None,
        )
        return jsonify({"ok": True, "message": "Code(s) revoked successfully"})

    else:
        return _err("Unknown action. Valid: status | verify | check | revoke")


def start_api():
    """Called from main.py in a background thread."""
    app.run(host="0.0.0.0", port=PORT, use_reloader=False, threaded=True)
