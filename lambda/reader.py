import os
import json
import boto3
from botocore.exceptions import ClientError

DDB_TABLE = os.environ["DDB_TABLE"]
SECRET_ARN = os.environ.get("SECRET_ARN")  # required for screenshot proof

dynamodb = boto3.resource("dynamodb")
secrets = boto3.client("secretsmanager")


def _get_demo_secret():
    """
    Retrieve a demo JSON secret from Secrets Manager.
    We only log metadata for proof. We do NOT print the secret.
    """
    if not SECRET_ARN:
        print("SECRET_ARN is not set. Skipping secret retrieval.")
        return None

    try:
        resp = secrets.get_secret_value(SecretId=SECRET_ARN)

        # Proof lines for your screenshot (safe to show)
        print("Secrets Manager retrieval: SUCCESS")
        print(f"SecretId used: {SECRET_ARN}")
        print(f"Secret VersionId: {resp.get('VersionId', 'n/a')}")

        secret_str = resp.get("SecretString", "{}")
        return json.loads(secret_str)

    except ClientError as e:
        print("Secrets Manager retrieval: FAILED")
        print(f"Error: {e}")
        raise


def lambda_handler(event, context):
    print("---------------------------------------")
    print(" Secure Secret Retrieval Demo")
    print(" Owner: Nisha")
    print("---------------------------------------")

    # 1) Prove secret retrieval
    demo_secret = _get_demo_secret()
    if isinstance(demo_secret, dict):
        print("Demo secret retrieved (keys only):", list(demo_secret.keys()))

    # 2) Prove DynamoDB still works without hardcoded creds
    table = dynamodb.Table(DDB_TABLE)
    resp = table.scan()

    print("------------ STUDENT DETAILS -----------")
    for item in resp.get("Items", []):
        print("Student Id       :", item.get("StudId"))
        print("Student Name     :", item.get("FirstName"), item.get("LastName"))
        print("Department       :", item.get("Dept"))
        print("Age              :", item.get("Age"))
        print("---------------------------------------")

    print("Invocation completed successfully.")
    return {
        "statusCode": 200,
        "owner": "Nisha",
        "records_returned": len(resp.get("Items", [])),
        "secret_retrieved": True if demo_secret else False
    }
