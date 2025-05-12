import os
import sqlite3
import logging
from datetime import datetime
from core.app_block_using_driver import set_blocked_apps, get_all_blocked_apps, DB_PATH
from core.app_monitor import get_app_usage_today
from config.config import DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(DATA_DIR, "app_block_policy.log")
)
logger = logging.getLogger('app_block_policy')


def get_app_block_rules():
    """Get all app block rules from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT app_name, always_blocked, usage_limit_seconds, time_start, time_end, notes 
            FROM app_block_rules
        """)
        rules = cursor.fetchall()
        result = []

        for rule in rules:
            result.append({
                'app_name': rule[0],
                'always_blocked': bool(rule[1]),
                'usage_limit_seconds': rule[2],
                'time_start': rule[3],
                'time_end': rule[4],
                'notes': rule[5]
            })

        conn.close()
        return result
    except sqlite3.Error as e:
        logger.error(f"Database error while getting rules: {str(e)}")
        conn.close()
        return []


def add_app_block_rule(app_name, always_blocked=False, usage_limit_seconds=None,
                       time_start=None, time_end=None, notes=None):
    """Add or update a rule for blocking an app"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT OR REPLACE INTO app_block_rules 
            (app_name, always_blocked, usage_limit_seconds, time_start, time_end, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (app_name, always_blocked, usage_limit_seconds, time_start, time_end, notes))

        conn.commit()
        conn.close()

        evaluate_time_policies()

        return {
            "status": "success",
            "message": f"App block rule added for {app_name}"
        }
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        logger.error(f"Database error adding app block rule: {str(e)}")
        return {
            "status": "error",
            "message": f"Database error: {str(e)}"
        }


def remove_app_block_rule(app_name):
    """Remove a rule for a specific app"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM app_block_rules WHERE app_name = ?", (app_name,))

        conn.commit()
        conn.close()

        evaluate_time_policies()

        return {
            "status": "success",
            "message": f"App block rule removed for {app_name}"
        }
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        logger.error(f"Database error removing app block rule: {str(e)}")
        return {
            "status": "error",
            "message": f"Database error: {str(e)}"
        }


def is_app_time_blocked(app_name):
    """Check if an app is blocked based on current time"""
    rules = get_app_block_rules()

    for rule in rules:
        if rule['app_name'] == app_name and rule['time_start'] and rule['time_end']:
            current_time = datetime.now().time()

            try:
                start_time = datetime.strptime(
                    rule['time_start'], '%H:%M').time()
                end_time = datetime.strptime(rule['time_end'], '%H:%M').time()

                if start_time <= end_time:
                    if start_time <= current_time <= end_time:
                        return True
                else:
                    if current_time >= start_time or current_time <= end_time:
                        return True
            except ValueError:
                logger.error(f"Invalid time format for app {app_name}")

    return False


def is_app_usage_limited(app_name):
    """Check if an app has exceeded its usage limit"""
    rules = get_app_block_rules()

    for rule in rules:
        if rule['app_name'] == app_name and rule['usage_limit_seconds']:
            current_usage = get_app_usage_today(app_name)

            if current_usage >= rule['usage_limit_seconds']:
                return True

    return False


def evaluate_time_policies():
    """Evaluate all time-based policies and update blocked apps list"""
    try:
        logger.info("Evaluating time-based policies")

        currently_blocked = get_all_blocked_apps()

        rules = get_app_block_rules()
        apps_to_block = []

        for rule in rules:
            app_name = rule['app_name']

            if rule['always_blocked']:
                apps_to_block.append(app_name)
                continue

            print("Checking for time based block" + app_name)
            if is_app_time_blocked(app_name):
                apps_to_block.append(app_name)
                continue

            print("Checking for usage based block" + app_name)
            if is_app_usage_limited(app_name):
                apps_to_block.append(app_name)
                continue

        if set(apps_to_block) != set(currently_blocked):
            print(f"Updating blocked apps list: {apps_to_block}")
            set_blocked_apps(apps_to_block)

        return apps_to_block
    except Exception as e:
        logger.error(f"Error evaluating time policies: {str(e)}")
        return []


def get_formatted_app_rules():
    """Get all app rules formatted for display"""
    rules = get_app_block_rules()

    formatted_rules = []

    for rule in rules:
        app_name = rule['app_name']
        current_usage = get_app_usage_today(app_name)
        usage_limit = rule['usage_limit_seconds']

        time_restriction = "None"
        if rule['time_start'] and rule['time_end']:
            time_restriction = f"{rule['time_start']} to {rule['time_end']}"

        usage_restriction = "None"
        if usage_limit:
            remaining = max(0, usage_limit - current_usage)
            minutes, seconds = divmod(remaining, 60)
            hours, minutes = divmod(minutes, 60)

            usage_restriction = f"{hours}h {minutes}m remaining of {usage_limit//60} min limit"

        formatted_rules.append({
            'app_name': app_name,
            'always_blocked': rule['always_blocked'],
            'time_restriction': time_restriction,
            'usage_restriction': usage_restriction,
            'notes': rule['notes'] or ""
        })

    return formatted_rules

def init_app_block_db():
    """Initialize the SQLite database for app blocking"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_block_rules (
            app_name TEXT PRIMARY KEY,
            always_blocked BOOLEAN DEFAULT 0,
            usage_limit_seconds INTEGER DEFAULT NULL,
            time_start TEXT DEFAULT NULL,
            time_end TEXT DEFAULT NULL,
            notes TEXT DEFAULT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

init_app_block_db()