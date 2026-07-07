"""mac_ui.py — small helpers for native macOS dialogs via AppleScript."""

import subprocess


def _escape(text: str) -> str:
    return text.replace('\\', '\\\\').replace('"', '\\"')


def show_popup(title: str, message: str):
    """Show a simple OK dialog."""
    script = f'display dialog "{_escape(message)}" with title "{_escape(title)}" buttons {{"OK"}} default button "OK"'
    try:
        subprocess.run(['osascript', '-e', script], check=True)
    except Exception as e:
        print(f"Could not show popup: {e}")


def ask_yes_no(title: str, message: str, yes_label: str, no_label: str) -> bool:
    """Show a two-button dialog. Returns True if yes_label was chosen, False otherwise
    (including if the dialog was closed/escaped)."""
    script = (
        f'display dialog "{_escape(message)}" with title "{_escape(title)}" '
        f'buttons {{"{_escape(no_label)}", "{_escape(yes_label)}"}} '
        f'default button "{_escape(yes_label)}"'
    )
    try:
        result = subprocess.run(['osascript', '-e', script], check=True, capture_output=True, text=True)
        return f'button returned:{yes_label}' in result.stdout
    except subprocess.CalledProcessError:
        return False
