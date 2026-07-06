import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
from src.router import route_notification

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def handle_dlq_message(event , context):
    try:
        sqs = boto3.client(
            'sqs',
            region_name = os.environ.get("AWS_REGION" , "us-east-1")
        )
        dlq_url = os.environ.get("SQS_QUEUE_URL")
        response = sqs.receive_message(
            QueueUrl=dlq_url,
            MaxNumberOfMessages=10,
            MessageSystemAttributeNames=["All"],
            MessageAttributeNames=["All"],
            VisibilityTimeout=30
        )
        messages = response.get("Messages", [])
        formatted = []
        for msg in messages:
            body = json.loads(msg["Body"])
            formatted.append({
                "messageId": msg["MessageId"],
                "receiptHandle": msg["ReceiptHandle"],
                "payload": body,
                "receivedCount": msg.get("Attributes", {}).get("ApproximateReceiveCount", "unknown")
            })
        return {
            'StatusCode' : 200,
            "headers" : {
                "Content-Tyep" : "application/json",
                "Access-Control-Allow-Origin" : "*"     
            },
            "body" : json.dumps({
                "success" : True,
                "messages" : formatted
            })
        }
    except Exception as e:
        logger.exception("Failed to fetch DLQ messages")
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"success": False, "error": str(e)})
        }

# Function to replay messages from DLQ
def replay_dlq_message(event , context):
    try:
        body = event.get("body" , {})
        if isinstance(body , str):
            date = json.loads(body)
        else:
            data = body
        receipt_handle = data.get("receiptHandle")
        payload = data.get("payload")
        if not receipt_handle or not payload:
            return {
                "statusCode": 400,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({
                    "success": False,
                    "error": "receiptHandle and payload are required"
                })
            }
        logger.info(f"Replaying payload: {json.dumps(payload)}")
        results = route_notification(payload)

        any_failed = any(
            not (r.get("success") if isinstance(r, dict) else False)
            for r in results.values()
        )

        if any_failed:
            return {
                "statusCode": 200,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({
                    "success": False,
                    "error": "Replay failed — notification still failing",
                    "results": results
                })
            }
        sqs = boto3.client(
            "sqs",
            region_name=os.environ.get("AWS_REGION", "us-east-1")
        )
        dlq_url = os.environ["DLQ_URL"]

        sqs.delete_message(
            QueueUrl=dlq_url,
            ReceiptHandle=receipt_handle
        )

        logger.info("Message successfully replayed and deleted from DLQ")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": True,
                "message": "Notification replayed successfully",
                "results": results
            })
        }

    except Exception as e:
        logger.exception("Failed to replay DLQ message")
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"success": False, "error": str(e)})
        }