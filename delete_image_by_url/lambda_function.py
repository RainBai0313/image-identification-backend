import boto3
import urllib
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('detected_images')

def convert_url(url):
    s3_url = url.replace("https://", "s3://").replace(".s3.amazonaws.com/images", "/images")
    return s3_url

def delete_image(url):
    try:
        bucket_name = "assignment2group6bucket"
        object_key = url.replace("https://assignment2group6bucket.s3.amazonaws.com/", "")
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        return True
    except ClientError as e:
        print(e)
        return False

def lambda_handler(event, context):
    # Extract data from the event object.
    url = event['url']
    uuid = event['uuid']

    # Convert URL to S3 URL.
    s3_url = convert_url(url)

    try:
        response = table.get_item(
            Key={
                's3_url': s3_url,
                'uuid': uuid
            }
        )

        if 'Item' in response:
            item = response['Item']
            table.delete_item(
                Key={
                    's3_url': s3_url,
                    'uuid': uuid
                }
            )

            # Delete the image from S3 bucket
            if delete_image(url):
                return {
                    'statusCode': 200,
                    'body': "Delete successful."
                }
            else:
                return {
                    'statusCode': 500,
                    'body': "Error deleting image from S3 bucket."
                }
        else:
            return {
                'statusCode': 404,
                'body': "URL not found in the table.",
                'url': s3_url
            }
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': f"Error: {e.response['Error']['Message']}"
        }
