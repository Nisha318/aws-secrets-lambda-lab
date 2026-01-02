import os
import json
import boto3
from botocore.exceptions import ClientError

DDB_TABLE = os.environ["DDB_TABLE"]
SECRET_ARN = os.environ.get("SECRET_ARN")  # required for the "secret retrieval" proof

dynamodb = boto3.resource("dynamodb")
secrets = boto3.client("secretsmanager")

def _get_demo_secret_metadata():
    """
    Retrieve the secret at runtime and return safe metadata only.
    We do NOT print the secret value.
    """
    if not SECRET_ARN:
        return {"retrieved": False, "reason": "SECRET_ARN env var not set"}

    try:
        resp = secrets.get_secret_value(SecretId=SECRET_ARN)
        secret_str = resp.get("SecretString", "{}")

        # Parse just to prove it is valid JSON, but don't print it
        parsed = json.loads(secret_str) if secret_str else {}

        return {
            "retrieved": True,
            "secret_id": resp.get("ARN") or SECRET_ARN,
            "keys_present": list(parsed.keys())[:5]  # safe: prints only key names
        }

    except ClientError as e:
        return {"retrieved": False, "error": str(e)}

def lambda_handler(event, context):
    print("---------------------------------------")
    print("Secure Secret Retrieval Demo")
    print("Owner: Nisha")
    print("---------------------------------------")

    # This is the key evidence line for Screenshot Set 1
    secret_meta = _get_demo_secret_metadata()
    if secret_meta.get("retrieved"):
        print("Secrets Manager: GetSecretValue succeeded (secret value not logged).")
        print(f"Secret reference: {secret_meta.get('secret_id')}")
        print(f"Secret JSON keys (sample): {secret_meta.get('keys_present')}")
    else:
        print("Secrets Manager: GetSecretValue failed or not configured.")
        print(f"Details: {secret_meta}")

    # DynamoDB validation
    table = dynamodb.Table(DDB_TABLE)
    resp = table.scan()

    print("------------ STUDENT DETAILS -----------")
    for item in resp.get("Items", []):
        print(f"Student Id       : {item.get('StudId')}")
        print(f"Student Name     : {item.get('FirstName')} {item.get('LastName')}")
        print(f"Department       : {item.get('Dept')}")
        print(f"Age              : {item.get('Age')}")
        print("---------------------------------------")

    print("Invocation completed successfully.")
    return {
        "statusCode": 200,
        "owner": "Nisha",
        "secret_retrieved": bool(secret_meta.get("retrieved")),
        "records_returned": len(resp.get("Items", []))
    }
