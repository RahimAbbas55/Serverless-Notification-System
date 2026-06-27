import json
import logging
from src.validators import validate_webhook_payload
from src.router import route_notification

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

'''
    Function triggered by SQS. This function will processes each request in batches.
    If a message fails, SQS will retry the message up to 3 times before sending it to DLQ
'''
def sqs_handler(event , context):
    print()
    records = event.get('Records' , [])
    logger.info(f"Received {len(records)} records from SQS")
    # Start tracking the failed request
    failed = []
    for record in records:
        message_id = record.get("messageId" , "unknown")
        try:
            payload = json.loads(record["body"])
            logger.info(f"Processing message : {message_id} with payload: {payload}")
            # Validating the payload
            errors = validate_webhook_payload(payload)
            if errors:
                logger.error(f"Invalid payload in messsage {message_id} : {errors}")
                continue
            # Routing the notifications to the correct handler
            results = route_notification(payload)
            logger.info(f"Message {message_id} , results: {results}")
            any_failed = any(not r.get("success") for r in results.values())
            if any_failed:
                raise Exception(f"One or more channels failed : {results}")
        except json.JSONDecodeError as e:
            logger.error(f"Message {message_id} has invalid JSON")
            continue
        except Exception as e:
            logger.error(f"Message {message_id} failed. Error: {e}")
            failed.append({
                "itemIdentifier" : message_id
            })
    
    if failed:
        return {
            "batchItemFailures" : failed
        }