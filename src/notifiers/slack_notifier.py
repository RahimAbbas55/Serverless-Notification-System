import os
import logging
import json
import urllib.request
import urllib.error

# Define the logger for this module
logger = logging.getLogger(__name__)

# Dictionary for our level styles
LEVEL_STYLES = {
    "info" : {
        "color" : "#2a78d6" , "emoji" : ":information_source:"    
    },
    "warning" : {
        "color" : "#eda100" , "emoji" : ":warning:"     
    },
    "error" : {
        "color" : "#e34948" , "emoji" : ":x:" 
    },
    "critical" : {
        "color" : "#501313" , "emoji" : ":rotating_light:"     
    }
}

# 
def send_slack(message: str , level: str = "info" , subject: str | None = None ) -> dict:
    webhook_url = os.environ["SLACK_WEBHOOK_URL"]
    style = LEVEL_STYLES.get(level , LEVEL_STYLES["info"])
    '''
        Slack uses a system called Block Kit to structure messages. 
        Each block is a dictionary that defines a specific type of content, 
        such as text, images, or buttons. The blocks are then combined into a list to create the final message payload.
    '''
    blocks = [
        {
            "type" : "header",
            "text" : {"type": "plain_text", "text": subject or f"{level.upper()} Alert", "emoji": True}
        },
        {
            "type" : "section",
            "text" : {"type": "mrkdwn", "text": f"{style['emoji']} *{level.upper()}*  {subject or ''}"}
        },
        {
            "type" : "section",
            "text" : {"type" : "mrkdwn" , "text" : message}
        },
        {
            "type" : "divider",
        }
    ]
    # HTTP request to send the message to Slack
    payload = json.dumps(
        {
            "attachments": [
                {
                    "color": style["color"],
                    "blocks": blocks
                }
            ]
        }
    )
    req = urllib.request.Request(
        webhook_url,
        data = payload.encode("utf-8"),
        headers = {
            "Content-Type" : "application/json"    
        },
        method = "POST"
    )
    # Sending & handling the request
    try:
        with urllib.request.urlopen(req , timeout=5) as resp:
            body = resp.read().decode("utf-8")
            if body == "ok":
                return { "success" : True }
            return { "success" : False , "error" : body }
    except urllib.error.HTTPError as e:
        return {"success": False, "error": f"HTTP {e.code}: {e.read().decode()}"}
    except urllib.error.URLError as e:
        return { "success" : False , "error" : str(e.reason)}