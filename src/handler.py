import os
import json
import logging
import boto3
from src.router import route_notification
from src.validators import validate_webhook_payload
from src.api.logs_handler import logs_handler
from src.api.dlq_handler import get_dlq_messages, replay_dlq_message

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # Detect if this is an SQS event
    if event.get("Records") and event["Records"][0].get("eventSource") == "aws:sqs":
        from src.sqs_handler import sqs_handler
        return sqs_handler(event, context)

    # Get request path and method
    path = event.get("rawPath", "/")
    method = event.get("requestContext", {}).get("http", {}).get("method", "POST")

    # Route to correct handler based on path and method
    if path == "/logs" and method == "GET":
        return logs_handler(event, context)
    elif path == "/dlq" and method == "GET":
        return get_dlq_messages(event, context)
    elif path == "/dlq/replay" and method == "POST":
        return replay_dlq_message(event, context)

    # Default — handle as notification request
    try:
        body = event.get("body", {})
        if isinstance(body, str):
            payload = json.loads(body)
        else:
            payload = body

        logger.info(f"Recieved payload: {json.dumps(payload)}")

        errors = validate_webhook_payload(payload)
        if errors:
            return _response(400, {
                "errors": "Invalid payload",
                "details": errors
            })

        results = route_notification(payload)

        any_failed = any(
            not (r.get("success") if isinstance(r, dict) else False)
            for r in results.values()
        )

        if any_failed:
            queue_result = send_to_sqs(payload)
            return _response(202, {
                "status": "queued_for_retry",
                "results": results,
                "queue": queue_result
            })

        return _response(200, {
            "status": "sent",
            "results": results
        })

    except json.JSONDecodeError:
        return _response(400, {"error": "Request body must be valid JSON"})
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return _response(500, {"error": "Internal server error"})


# Helper function for the main lambda_handler to format the response
def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }


# Helper function to send messages to SQS
def send_to_sqs(payload: dict) -> dict:
    try:
        queue_url = os.environ["SQS_QUEUE_URL"]
        sqs_client = boto3.client("sqs", region_name=os.environ.get("AWS_REGION", "us-east-1"))

        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(payload)
        )

        message_id = response["MessageId"]
        logger.info(f"Message sent to SQS queue. Message ID : {message_id}")

        return {
            "queued": True,
            "message_id": message_id
        }

    except Exception as e:
        logger.error(f"Failed to send payload to SQS queue")
        return {
            "queued": False,
            "error": str(e)
        }