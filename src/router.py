import logging
from src.notifiers.email_notifier import send_email
from src.notifiers.slack_notifier import send_slack

logger = logging.getLogger(__name__)

# Function to route the notifications to correct channel
def route_notification(payload: dict) -> dict:
    channel = payload.get("channel")
    channels = [channel] if isinstance(channel , str) else channel
    results = {}
    for ch in channels:
        try:
            if ch == "email":
                result = send_email(
                    recipient=payload["recipient"],
                    subject=payload["subject"],
                    message=payload["message"],
                    level=payload.get("level" , "info")
                    )
            elif ch == "slack":
                result = send_slack(
                    message=payload["message"],
                    level=payload.get("level" , "info"),
                    subject=payload.get("subject")
                )
            else:
                result = {
                    "success" : False,
                    "error" : f"Unknown channel: {ch}"
                }
            results[ch] = result
        except Exception as e:
            logger.exception(f"Error sending notification to {ch} : {e}")
            results[ch] = {
                "success" : False,
                "error" : str(e)
            }
    return results