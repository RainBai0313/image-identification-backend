import base64
import boto3
import cv2
import json
import numpy as np
import os
import time
from botocore.exceptions import NoCredentialsError
from boto3.dynamodb.conditions import Key
from decimal import Decimal

# configure S3 client and DynamoDB resource
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# specify your DynamoDB table name
table = dynamodb.Table('detected_images')

# construct the argument parse and parse the arguments
confthres = 0.3
nmsthres = 0.1
yolo_path = "/opt/yolo_tiny_configs"


def get_labels(labels_path):
    lpath = os.path.sep.join([yolo_path, labels_path])
    LABELS = open(lpath).read().strip().split("\n")
    return LABELS


def get_weights(weights_path):
    weightsPath = os.path.sep.join([yolo_path, weights_path])
    return weightsPath


def get_config(config_path):
    configPath = os.path.sep.join([yolo_path, config_path])
    return configPath


def load_model(configpath, weightspath):
    net = cv2.dnn.readNetFromDarknet(configpath, weightspath)
    return net


def get_image_from_s3(bucket, key):
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        image_bytes = response['Body'].read()
        return image_bytes
    except NoCredentialsError:
        print('No credentials to access S3')
    except Exception as e:
        print(e)
        return None


def do_prediction(image, net, LABELS):
    (H, W) = image.shape[:2]
    # determine only the *output* layer names that we need from YOLO
    ln = net.getLayerNames()
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

    # construct a blob from the input image and then perform a forward
    # pass of the YOLO object detector, giving us our bounding boxes and
    # associated probabilities
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
                                 swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    # print(layerOutputs)
    end = time.time()

    # show timing information on YOLO
    print("[INFO] YOLO took {:.6f} seconds".format(end - start))

    # initialize our lists of detected bounding boxes, confidences, and
    # class IDs, respectively
    boxes = []
    confidences = []
    classIDs = []

    # loop over each of the layer outputs
    for output in layerOutputs:
        # loop over each of the detections
        for detection in output:
            # extract the class ID and confidence (i.e., probability) of
            # the current object detection
            scores = detection[5:]
            # print(scores)
            classID = np.argmax(scores)
            # print(classID)
            confidence = scores[classID]

            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if confidence > confthres:
                # scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                # use the center (x, y)-coordinates to derive the top and
                # and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # update our list of bounding box coordinates, confidences,
                # and class IDs
                boxes.append([x, y, int(width), int(height)])

                confidences.append(float(confidence))
                classIDs.append(classID)

    # apply non-maxima suppression to suppress weak, overlapping bounding boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, confthres,
                            nmsthres)

    # TODO Prepare the output as required to the assignment specification
    # ensure at least one detection exists
    detected_result = []
    if len(idxs) > 0:
        for i in idxs.flatten():
            accuracy = Decimal(str(confidences[i]))  # Convert float to Decimal
            detected_result.append(
                LABELS[classIDs[i]]
            )
            print("detected item:{}, accuracy:{}, X:{}, Y:{}, width:{}, height:{}".format(LABELS[classIDs[i]],
                                                                                          accuracy,
                                                                                          boxes[i][0],
                                                                                          boxes[i][1],
                                                                                          boxes[i][2],
                                                                                          boxes[i][3]))
    return detected_result


def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    user_uuid = event['Records'][0]['s3']['object']['key'].split('/')[1]  # This is the new line for getting UUID
    key = event['Records'][0]['s3']['object']['key']

    # load model
    labelsPath = "coco.names"
    cfgpath = "yolov3-tiny.cfg"
    wpath = "yolov3-tiny.weights"
    Labels = get_labels(labelsPath)
    CFG = get_config(cfgpath)
    Weights = get_weights(wpath)
    net = load_model(CFG, Weights)

    # get image from S3
    image_bytes = get_image_from_s3(bucket, key)

    # decode image
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

    # do prediction
    detected_result = do_prediction(image, net, Labels)

    # store result into DynamoDB
    # Here you can decide what to do with the user_uuid. For instance, you can store it together with the tags.
    table.put_item(Item={'s3_url': 's3://' + bucket + '/' + key, 'tags': detected_result, 'uuid': user_uuid})

    return {
        'statusCode': 200,
        'body': json.dumps('Image processed successfully!')
    }
