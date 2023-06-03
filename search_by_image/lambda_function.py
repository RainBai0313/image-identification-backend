import base64
import boto3
import cv2
import json
import numpy as np
import os
import time
import base64
from botocore.exceptions import NoCredentialsError
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from collections import Counter

# construct the argument parse and parse the arguments
confthres = 0.3
nmsthres = 0.1
yolo_path = "/opt/yolo_tiny_configs"

dynamodb = boto3.resource('dynamodb')


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
     # specify your DynamoDB table name
    table = dynamodb.Table('detected_images')
    
    image_bytes = base64.b64decode(event['body'])
    user_uuid = event['uuid']
    
     # scan all the items in the table
    response = table.scan()
    items = response['Items']

    # load model
    labelsPath = "coco.names"
    cfgpath = "yolov3-tiny.cfg"
    wpath = "yolov3-tiny.weights"
    Labels = get_labels(labelsPath)
    CFG = get_config(cfgpath)
    Weights = get_weights(wpath)
    net = load_model(CFG, Weights)


    # decode image
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

    # do prediction
    detected_result = do_prediction(image, net, Labels)
    
    result = Counter(detected_result)
    
    tags = list(result.keys())
    
    matching_urls = []
    
    for tag in tags:
        # Remove items that don't have enough of this tag
        items = [item for item in items if item['tags'].count(tag) >= result[tag]]

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