import boto3
import base64
import os

s3 = boto3.client('s3')


def lambda_handler(event, context):

    image = base64.b64decode(event['body'])

    # assuming the uuid is sent in the event
    user_uuid = event['uuid']

    # construct the s3 key using the username, uuid, and current timestamp
    s3_key = os.path.join("images", user_uuid, f"{event['path']}.jpg")

    # upload the image to the s3 bucket
    s3.put_object(
        Bucket="assignment2group6bucket",
        Key=s3_key,
        Body=image,
        ContentType='image/jpeg'
    )

    return {
        "statusCode": 200,
        "body": "Image uploaded successfully"
    }
