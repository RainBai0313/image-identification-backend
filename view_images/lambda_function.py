import boto3
import json

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')


def lambda_handler(event, context):
    # specify your DynamoDB table name
    table = dynamodb.Table('detected_images')

    user_uuid = event['uuid']

    # scan all the items in the table
    response = table.scan()
    items = response['Items']

    # initialize a list to store the URLs of the matching images
    matching_urls = []

    # Generate signed URLs for each matching S3 object
    for item in items:
        if item['uuid'] == user_uuid:
            bucket, key = s3UriToBucketAndKey(item['s3_url'])
            signed_url = generate_presigned_url(bucket, key)
            matching_urls.append(signed_url + "::" + ', '.join(map(str, item['tags'])))

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
