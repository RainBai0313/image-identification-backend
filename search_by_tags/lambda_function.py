import boto3
import json

dynamodb = boto3.resource('dynamodb')

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
        items = [item for item in items if item['tags'].count(tag['tag']) >= tag['count']]

    matching_urls.extend(item['s3_url'] for item in items)
    
    if len(matching_urls) < 1:
        return{
            'statusCode': 404,
            'body': 'No matching images'
        }
    return {
        'statusCode': 200,
        'body': matching_urls
    }