import boto3
import base64

s3 = boto3.client('s3')


def lambda_handler(event, context):
    # assuming the image is sent as base64 in the request body
    image = base64.b64decode(event['body'])

    # get the username from the request's authorizer context
    user = event['requestContext']['authorizer']['claims']['cognito:username']

    # construct the s3 key using the username and current timestamp
    s3_key = f"{user}/{int(time.time())}.jpg"

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
