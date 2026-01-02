import os
import json
import boto3
from botocore.exceptions import ClientError

DDB_TABLE = os.environ["DDB_TABLE"]
SECRET_ARN = os.environ.get("SECRET_ARN")

dynamodb = boto3.resource("dynamodb")
secrets = boto3.client("secretsmanager")

def _get_demo_secret():
    if not SECRET_ARN:
        print("SECRET_ARN not set.")
        return False

    try:
        secrets.get_secret_value(SecretId=SECRET_ARN)
        print("Secret successfully retrieved at runtime (value not logged).")
        return True
    except ClientError as e:
        print(f"Secret retrieval failed: {e}")
        return False

def lambda_handler(event, context):
    print("---------------------------------------")
    print(" Secure Secret Retrieval Demo")
    print(" Owner: Nisha")
    print("---------------------------------------")

    secret_retrieved = _get_demo_secret()

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
        "secret_retrieved": secret_retrieved
    }
