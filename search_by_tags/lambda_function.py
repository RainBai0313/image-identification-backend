import boto3
import json

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')


def lambda_handler(event, context):
    # specify your DynamoDB table name
    table = dynamodb.Table('detected_images')

    user_uuid = event['uuid']

    # get the required tags from the event
    required_tags = event['tags']

    # scan all the items in the table
    response = table.scan()
    items = response['Items']

    # initialize a list to store the URLs of the matching images
    matching_urls = []

    for tag in required_tags:
        # Remove items that don't have enough of this tag
        items = [item for item in items if item['tags'].count(tag['tag']) >= tag['count'] and item['uuid'] == user_uuid]

    # Generate signed URLs for each matching S3 object
    for item in items:
        bucket, key = s3UriToBucketAndKey(item['s3_url'])
        signed_url = generate_presigned_url(bucket, key)
        matching_urls.append(signed_url)

    if len(matching_urls) < 1:
        return {
            'statusCode': 404,
            'body': 'No matching images'
        }
    return {
        'statusCode': 200,
        'body': matching_urls
    }


# Convert s3 uri to bucket and key
def s3UriToBucketAndKey(s3Uri):
    parts = s3Uri.replace('s3://', '').split('/')
    bucket = parts.pop(0)
    key = "/".join(parts)
    return bucket, key


# Generate a presigned S3 URL
def generate_presigned_url(bucket, key):
    url = f"https://{bucket}.s3.amazonaws.com/{key}"
    return url
