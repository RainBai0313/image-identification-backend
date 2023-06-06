import boto3
import urllib
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('detected_images')

def convert_url(url):
    s3_url = url.replace("https://", "s3://").replace(".s3.amazonaws.com/images", "/images")
    return s3_url

def lambda_handler(event, context):
    # Extract data from the event object.
    url = event['url']
    type = event['type']
    tags = event['tags']

    # Convert URL to S3 URL.
    s3_url = convert_url(url)

    try:
        response = table.get_item(
            Key={
                's3_url': s3_url,
                'uuid': event['uuid']
            }
        )

        if 'Item' in response:
            item = response['Item']

            for new_tag in tags:
                tag_name = new_tag['tag']
                count = new_tag['count']

                if type == 1: # Add tags
                    item['tags'].extend([tag_name]*count)
                else: # Remove tags
                    while count > 0 and tag_name in item['tags']:
                        item['tags'].remove(tag_name)
                        count -= 1

            table.put_item(Item=item)

            return {
                'statusCode': 200,
                'body': "Update successful."
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