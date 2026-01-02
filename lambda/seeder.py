import os
import json
import boto3
from botocore.exceptions import ClientError

DDB_TABLE = os.environ["DDB_TABLE"]
SECRET_ARN = os.environ.get("SECRET_ARN")  # optional, but good for consistency

dynamodb = boto3.resource("dynamodb")
secrets = boto3.client("secretsmanager")

def _get_demo_secret_metadata():
    if not SECRET_ARN:
        return {"retrieved": False, "reason": "SECRET_ARN env var not set"}
    try:
        resp = secrets.get_secret_value(SecretId=SECRET_ARN)
        secret_str = resp.get("SecretString", "{}")
        parsed = json.loads(secret_str) if secret_str else {}
        return {"retrieved": True, "keys_present": list(parsed.keys())[:5]}
    except ClientError as e:
        return {"retrieved": False, "error": str(e)}

def lambda_handler(event, context):
    print("Seeding DynamoDB table...")

    # Optional proof line (nice to have, not required)
    meta = _get_demo_secret_metadata()
    if meta.get("retrieved"):
        print("Secrets Manager: GetSecretValue succeeded (secret value not logged).")
        print(f"Secret JSON keys (sample): {meta.get('keys_present')}")
    else:
        print("Secrets Manager: demo secret retrieval skipped/failed.")
        print(f"Details: {meta}")

    table = dynamodb.Table(DDB_TABLE)

    items = [
        {"StudId": 100, "FirstName": "Harry", "LastName": "Styles", "Dept": "IT", "Age": 28},
        {"StudId": 200, "FirstName": "Sam", "LastName": "Billings", "Dept": "BE", "Age": 22},
        {"StudId": 300, "FirstName": "Pete", "LastName": "Davidson", "Dept": "EE", "Age": 25},
    ]

    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)

    return {"statusCode": 200, "body": f"Seeded {len(items)} items into {DDB_TABLE}"}
