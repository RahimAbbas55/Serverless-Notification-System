import json
import logging
from src.router import route_notification
from src.validators import validate_webhook_payload

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def lambda_handler(event , context):
    try: 
        body = event.get("body" , {})
        if isinstance(body , str):
            payload = json.loads(body)
        else:
            payload = body
        
        logger.info(f"Recieved payload: {json.dumps(payload)}")
        errors = validate_webhook_payload(payload)
        if errors:
            return _response(400 , {
                "errors" : "Invalid payload",
                "details" : errors
            })
        results = route_notification(payload)
        return _response(200 , {
                "status" : "sent",
                "results" : results
        })
    except json.JSONDecodeError as e:
          return _response(400, {"error": "Request body must be valid JSON"})
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return _response(500, {"error": "Internal server error"})

def _response(status_code: int , body: dict) -> dict:
    return{
        "statusCode" : status_code,
        "headers" : {
            "Content-Type" : "application/json"
        },
        "body" : json.dumps(body)
    }