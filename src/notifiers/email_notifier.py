import os
import logging
import boto3        # Python package for AWS services
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Dictionary for our level styles
LEVEL_STYLES = {
    "info" : {
        "bg" : "#e6f1fb",
        "text" : "#185fa5",
        "label" : "INFO"
    },
    "warning" : {
        "bg" : "#faeeda",
        "text" : "#854f0b",
        "label" : "WARNING"
    },
    "critical" : {
        "bg" : "#501313",
        "text" : "#fcebeb",
        "label" : "CRITICAL"
    },
    "error" : {
        "bg" : "#fcebeb",
        "text" : "#a32d2d",
        "label" : "ERROR"
    }   
}

# Function to send an email
def send_email(recipient: str , subject: str , message: str , level: str = "info") -> dict:
    sender = os.environ["SES_SENDER_EMAIL"]
    region = os.environ.get("AWS_REGION" , "us-east-1")
    client = boto3.client("ses" , region_name = region)
    color = LEVEL_STYLES.get(level , LEVEL_STYLES["info"])
    # Building the plain-text version
    text_body = f"[{color["label"]}] {subject}\n\n{message}"
    # Building the HTML version
    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:24px;">
      <div style="max-width:560px;margin:auto;background:#fff;border-radius:8px;border:1px solid #e0e0e0;overflow:hidden;">
        <div style="padding:16px 24px;background:{color['bg']};">
          <span style="font-size:12px;font-weight:600;color:{color['text']};text-transform:uppercase;">{color['label']}</span>
          <h2 style="margin:8px 0 0;color:#0b0b0b;font-size:18px;">{subject}</h2>
        </div>
        <div style="padding:24px;color:#333;font-size:15px;line-height:1.6;">{message}</div>
        <div style="padding:12px 24px;background:#f9f9f9;border-top:1px solid #e0e0e0;font-size:12px;color:#888;">
          Sent by your AWS Serverless Notification System
        </div>
      </div>
    </body></html>
    """
    
    # Sending the email via AWS SES
    try:
        response = client.send_email(
            Source = sender,
            Destination = {
                "ToAddresses" : [recipient]
            },
            Message = {
                "Subject" : {
                    "Data" : f"[{color["label"]}] {subject}" , 
                    "Charset" : "utf-8"
                },
                "Body" : {
                    "Text" : {
                        "Data" : text_body ,
                        "Charset" : "utf-8"    
                    },
                    "Html" : {
                        "Data" : html_body ,
                        "Charset" : "utf-8"   
                    },
                }
            },
        )
        return {
            "success" : True,
            "message_id" : response["MessageId"]
        }
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        logger.error(f"SES Error: [{code}] - {msg}")
        return {
            "success" : False,
            "error" : f"{code} - {msg}"
        }