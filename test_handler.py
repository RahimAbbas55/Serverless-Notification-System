from src.handler import lambda_handler

event = {
    'body': '{"channel": "slack", "message": "Handler is working!", "level": "info"}'
}

result = lambda_handler(event, {})
print(result)