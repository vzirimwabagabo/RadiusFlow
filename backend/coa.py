"""
CoA (Change of Authorization) — sends RADIUS Disconnect-Request packets
to MikroTik/NAS devices using the system's `radclient` utility.
This terminates active user sessions in real time.
"""
import subprocess
import logging

logger = logging.getLogger("radiusflow.coa")


def disconnect_user(nas_ip: str, nas_secret: str, username: str, session_id: str, nas_port: int = 3799) -> bool:
    """
    Send a CoA Disconnect-Request to the NAS for a given user session.
    Uses radclient (ships with FreeRADIUS) — no extra Python deps required.
    """
    attributes = f'User-Name="{username}",Acct-Session-Id="{session_id}"'
    cmd = [
        "radclient",
        "-r", "1",     # retry once
        "-t", "5",     # 5 second timeout
        f"{nas_ip}:{nas_port}",
        "disconnect",
        nas_secret,
    ]
    try:
        result = subprocess.run(
            cmd, input=attributes, capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            logger.info(f"CoA disconnect sent to {username} on {nas_ip}")
            return True
        logger.error(f"radclient failed: {result.stderr}")
        return False
    except FileNotFoundError:
        logger.error("radclient not found — is FreeRADIUS installed?")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"radclient timed out for {nas_ip}")
        return False