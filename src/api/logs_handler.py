import os
import json
import logging
import boto3
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def logs_handler(event, context):
    try:
        logs_client = boto3.client(
            "logs",
            region_name=os.environ.get("AWS_REGION", "us-east-1")
        )

        log_group = "/aws/lambda/Serverless-Notifier"
        limit = 20

        # Fetch the 5 most recent log streams
        streams_response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy="LastEventTime",
            descending=True,
            limit=5
        )
        streams = streams_response.get("logStreams", [])

        all_events = []

        # Loop through each stream and collect log events
        for stream in streams:
            stream_name = stream["logStreamName"]

            events_response = logs_client.get_log_events(
                logGroupName=log_group,
                logStreamName=stream_name,
                startFromHead=False,
                limit=10
            )

            for event in events_response.get("events", []):
                message = event["message"].strip()

                # Skip AWS internal lines — only keep our logger lines
                if message.startswith("START") or \
                   message.startswith("END") or \
                   message.startswith("REPORT") or \
                   message.startswith("INIT"):
                    continue

                # Convert millisecond timestamp to readable string
                timestamp = datetime.fromtimestamp(
                    event["timestamp"] / 1000,
                    tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M:%S UTC")

                all_events.append({
                    "timestamp": timestamp,
                    "message": message,
                    "stream": stream_name
                })

        # Sort newest first and return top 20
        all_events.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": True,
                "logs": all_events[:limit]
            })
        }

    except Exception as e:
        logger.exception("Failed to fetch logs")
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"success": False, "error": str(e)})
        }