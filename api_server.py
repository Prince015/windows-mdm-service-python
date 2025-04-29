from flask import Flask, jsonify, request
import logging

from core.screenshot import capture_screenshot
from core.system_control import lock_workstation, shutdown_system, get_battery_status
from core.usb_control import set_usb_state, is_usb_enabled
from core.host_modifier import block_websites, unblock_websites, read_blocked_websites
from core.app_management import block_and_limit_apps, get_installed_apps
from core.heartbeat import send_heartbeat
from core.app_block_using_driver import block_apps, unblock_apps, get_all_blocked_apps, unblock_all_apps
from core.app_monitor import get_all_app_usage_today
from core.app_block_policy import add_app_block_rule, remove_app_block_rule

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.route("/lock", methods=["POST"])
def api_lock():
    lock_workstation()
    return jsonify({"status": "locked"})


@app.route("/shutdown", methods=["POST"])
def api_shutdown():
    shutdown_system()
    return jsonify({"status": "shutdown initiated"})


@app.route("/screenshot", methods=["GET"])
def api_screenshot():
    path = capture_screenshot()
    return jsonify({"screenshot_path": path})


@app.route("/battery", methods=["GET"])
def api_battery():
    return jsonify(get_battery_status())


@app.route("/todays_usage", methods=["GET"])
def api_todays_all_app_usage():
    return jsonify(get_all_app_usage_today())


@app.route("/usb", methods=["POST"])
def api_usb():
    action = request.json.get("enable", True)
    set_usb_state(action)
    return jsonify({"usb_enabled": action})


@app.route("/usb/status", methods=["GET"])
def api_usb_status():
    status = is_usb_enabled()
    return jsonify({"usb_enabled": status})


@app.route("/block_websites", methods=["GET"])
def api_list_blocked_websites():
    websites = read_blocked_websites()
    return jsonify({"websites": websites})


@app.route("/block_websites", methods=["POST"])
def api_block_websites():
    data = request.get_json()
    websites = data.get("websites", [])
    block_websites(websites)
    return jsonify({"status": "websites blocked", "websites": websites})


@app.route("/unblock_websites", methods=["POST"])
def api_unblock_websites():
    data = request.get_json()
    websites = data.get("websites", [])
    unblock_websites(websites)
    return jsonify({"status": "websites unblocked", "websites": websites})


@app.route("/apps/enforce", methods=["POST"])
def api_enforce_apps():
    block_and_limit_apps()
    return jsonify({"status": "app rules enforced"})


@app.route("/installed_app", methods=["GET"])
def installed_app():
    apps = get_installed_apps()
    return jsonify({"data": apps})


@app.route("/heartbeat", methods=["POST"])
def api_heartbeat():
    send_heartbeat()
    return jsonify({"status": "heartbeat logged"})


@app.route("/block-apps", methods=["POST"])
def api_block_apps():
    """Block specific applications"""
    data = request.get_json()
    apps = data.get("apps", [])

    if not apps:
        return jsonify({"status": "error", "message": "No applications specified"}), 400

    res = block_apps(apps)
    return jsonify(res)


@app.route("/unblock-apps", methods=["POST"])
def api_unblock_apps():
    """Unblock specific applications"""
    data = request.get_json()
    apps = data.get("apps", [])

    if not apps:
        return jsonify({"status": "error", "message": "No applications specified"}), 400

    res = unblock_apps(apps)
    return jsonify(res)


@app.route("/get-blocked-apps", methods=["GET"])
def api_get_blocked_apps():
    """Get list of all currently blocked applications"""
    blocked_apps = get_all_blocked_apps()
    return jsonify({
        "status": "success",
        "blocked_apps": blocked_apps,
        "count": len(blocked_apps)
    })


@app.route("/unblock-all", methods=["POST"])
def api_unblock_all_apps():
    """Unblock all applications"""
    res = unblock_all_apps()
    return jsonify(res)


@app.route("/add_app_block_rule", methods=["POST"])
def api_add_app_block_rule():
    """Add or update a block rule for an app"""
    data = request.get_json()

    app_name = data.get("app_name")
    always_blocked = data.get("always_blocked", False)
    usage_limit_seconds = data.get("usage_limit_seconds")
    time_start = data.get("time_start")  # Expected as "HH:MM"
    time_end = data.get("time_end")      # Expected as "HH:MM"
    notes = data.get("notes")

    if not app_name:
        return jsonify({"status": "error", "message": "Missing app_name"}), 400

    if not (
        always_blocked or
        usage_limit_seconds or
        (time_start and time_end)
    ):
        return jsonify({
            "status": "error",
            "message": "Must provide at least one of: always_blocked, usage_limit_seconds, or time_start and time_end"
        }), 400

    if (time_start and not time_end) or (time_end and not time_start):
        return jsonify({
            "status": "error",
            "message": "Both time_start and time_end must be provided if one is given"
        }), 400

    res = add_app_block_rule(
        app_name=app_name,
        always_blocked=bool(always_blocked),
        usage_limit_seconds=usage_limit_seconds,
        time_start=time_start,
        time_end=time_end,
        notes=notes
    )
    return jsonify(res)


@app.route("/remove_app_block_rule", methods=["POST"])
def api_remove_app_block_rule():
    """Remove a block rule for an app"""
    data = request.get_json()
    app_name = data.get("app_name")

    if not app_name:
        return jsonify({"status": "error", "message": "Missing app_name"}), 400

    res = remove_app_block_rule(app_name)
    return jsonify(res)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
