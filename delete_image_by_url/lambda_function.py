import boto3
import os

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    # Get the s3 url and uuid from the event
    s3_url = event['url']
    user_uuid = event['uuid']

    # Parse the bucket name and key from the url
    bucket = s3_url.split('/')[2]
    key = '/'.join(s3_url.split('/')[3:])

    # Delete the image from s3
    s3.delete_object(Bucket=bucket, Key=key)

    # specify your DynamoDB table name
    table = dynamodb.Table('detected_images')

    # Construct the primary key of the item to be deleted
    # Replace 'your_primary_key_attribute' with the name of your primary key attribute
    primary_key = {
        'uuid': user_uuid,
        's3_url': s3_url
    }

    # Delete the item from DynamoDB
    table.delete_item(Key=primary_key)

    return {
        'statusCode': 200,
        'body': 'Image deleted successfully'
    }