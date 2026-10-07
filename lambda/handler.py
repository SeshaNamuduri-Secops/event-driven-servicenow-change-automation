import json
import os
import boto3
import urllib.request
import urllib.error
import base64
import urllib.parse

secrets_client = boto3.client("secretsmanager")


def get_secret():
    response = secrets_client.get_secret_value(
        SecretId=os.environ["SERVICENOW_SECRET_NAME"]
    )
    return json.loads(response["SecretString"])


def validate_event(event):
    required = [
        "event_id",
        "source",
        "environment",
        "change_type",
        "short_description",
        "description"
    ]

    missing = [field for field in required if not event.get(field)]

    if missing:
        raise ValueError(
            f"Missing required fields: {', '.join(missing)}"
        )


def classify_change(event):
    environment = event["environment"].lower()
    change_type = event["change_type"].lower()

    if change_type in ["emergency", "critical"]:
        return "critical", "emergency"

    if environment == "production":
        return "high", "normal"

    if environment in ["staging", "uat", "pre-production"]:
        return "medium", "normal"

    return "low", "standard"


def auth_headers(username, password):
    credentials = f"{username}:{password}".encode("utf-8")
    encoded = base64.b64encode(credentials).decode("utf-8")

    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded}"
    }


def find_existing_change(secret, event_id):
    instance_url = secret["instance_url"].rstrip("/")
    username = secret["username"]
    password = secret["password"]

    query = urllib.parse.urlencode({
        "sysparm_query": f"correlation_id={event_id}",
        "sysparm_limit": "1"
    })

    request = urllib.request.Request(
        f"{instance_url}/api/now/table/change_request?{query}",
        method="GET",
        headers=auth_headers(username, password)
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))

    results = data.get("result", [])

    return results[0] if results else None


def create_change_request(secret, event):
    instance_url = secret["instance_url"].rstrip("/")
    username = secret["username"]
    password = secret["password"]

    risk_level, recommended_type = classify_change(event)

    payload = {
        "short_description": event["short_description"],
        "description": (
            f"{event['description']}\n\n"
            f"Automation Source: {event['source']}\n"
            f"Event ID: {event['event_id']}\n"
            f"Environment: {event['environment']}\n"
            f"Risk Level: {risk_level}\n"
            f"Recommended Change Type: {recommended_type}"
        ),
        "comments": (
            "Created automatically by Event-Driven "
            "ServiceNow Change Automation."
        ),
        "correlation_id": event["event_id"]
    }

    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        f"{instance_url}/api/now/table/change_request",
        data=body,
        method="POST",
        headers=auth_headers(username, password)
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def lambda_handler(event, context):
    try:
        print(f"Received event: {json.dumps(event)}")

        validate_event(event)

        secret = get_secret()

        existing = find_existing_change(
            secret,
            event["event_id"]
        )

        if existing:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Duplicate event detected; existing Change Request returned",
                    "change_number": existing.get("number"),
                    "sys_id": existing.get("sys_id"),
                    "event_id": event["event_id"],
                    "duplicate": True
                })
            }

        result = create_change_request(secret, event)

        change = result.get("result", {})

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "ServiceNow Change Request created successfully",
                "change_number": change.get("number"),
                "sys_id": change.get("sys_id"),
                "event_id": event["event_id"],
                "duplicate": False
            })
        }

    except ValueError as error:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": str(error)
            })
        }

    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8")

        print(f"ServiceNow HTTP error: {error.code}")
        print(details)

        return {
            "statusCode": error.code,
            "body": json.dumps({
                "error": "ServiceNow API request failed",
                "details": details
            })
        }

    except Exception as error:
        print(f"Lambda error: {str(error)}")

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal automation error",
                "details": str(error)
            })
        }
