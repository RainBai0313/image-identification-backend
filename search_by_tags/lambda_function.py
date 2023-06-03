import boto3
import json

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    # specify your DynamoDB table name
    table = dynamodb.Table('detected_images')
    
    user_uuid = event['uuid']

    # get the required tags from the event
    required_tags = event['tags']
    required_tags_set = set(tag['tag'] for tag in required_tags)

    # scan all the items in the table
    response = table.scan()
    items = response['Items']

    # initialize a list to store the URLs of the matching images
    matching_urls = []

    # check each item to see if it has all the required tags
    for item in items:
        # make a set of the tags in this item
        item_tags_set = set(tag['S'] for tag in item['tags'])

        # if all the required tags are in this item's tags, add the item's URL to the list of matching URLs
        if required_tags_set.issubset(item_tags_set):
            matching_urls.append(item['s3_url'])

    return {
        'statusCode': 200,
        'body': json.dumps(matching_urls)
    }