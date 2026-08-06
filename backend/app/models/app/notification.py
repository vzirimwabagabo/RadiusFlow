from dataclasses import dataclass


@dataclass
class Notification:
    recipient: str
    message: str
    channel: str = "sms"
