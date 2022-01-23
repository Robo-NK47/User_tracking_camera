import cv2
import numpy as np
import serial
import time
import struct


def load_yolo():
    net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]

    layers_names = net.getLayerNames()
    output_layers = [layers_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    colors = np.random.uniform(0, 255, size=(len(classes), 3))
    return net, classes, colors, output_layers


def start_webcam():
    cap = cv2.VideoCapture(0)
    return cap


def display_blob(blob):
    for b in blob:
        for n, imgb in enumerate(b):
            cv2.imshow(str(n), imgb)


def detect_objects(img, net, outputLayers):
    blob = cv2.dnn.blobFromImage(img, scalefactor=0.00392, size=(320, 320), mean=(0, 0, 0), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward(outputLayers)
    return blob, outputs


def get_box_dimensions(outputs, height, width):
    boxes = []
    confs = []
    class_ids = []
    for output in outputs:
        for detect in output:
            scores = detect[5:]
            class_id = np.argmax(scores)
            conf = scores[class_id]
            if conf > 0.3:
                center_x = int(detect[0] * width)
                center_y = int(detect[1] * height)
                w = int(detect[2] * width)
                h = int(detect[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confs.append(float(conf))
                class_ids.append(class_id)
    return boxes, confs, class_ids


def draw_labels(boxes, confs, colors, class_ids, classes, img, center):
    indexes = cv2.dnn.NMSBoxes(boxes, confs, 0.5, 0.4)
    locations = {}
    color = (255, 0, 0)
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            object_center_position = np.array([int(x + (w * 0.5)), int(y + (h * 0.5))])
            label = str(classes[class_ids[i]])
            if label == 'Person':
                # colors[i]
                # cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
                # cv2.putText(img, f'{label} #{i}', (x, y - 5), font, 1, color, 1)
                cv2.putText(img, 'Nadav', object_center_position, font, 2, (255, 255, 255), 2)
                locations[f'{label}{i}'] = object_center_position
    return img, locations


def extract_arduino_numerical_data(raw_data):
    raw_data = str(raw_data)
    new_data = ''
    for character in raw_data:
        if character.isdigit() or character == '-':
            new_data += character
    return new_data


if __name__ == '__main__':
    font = cv2.FONT_HERSHEY_PLAIN
    model, classes, colors, output_layers = load_yolo()
    cap = start_webcam()
    webcam_counter = 0
    frame_check_rate = 1
    gap = 40  # the 'OK' distance in pixels for the frame center to be off the person center
    arduino_refresh_time_interval = 1  # time in seconds between arduino readjusts itself
    arduino_edge_position = 60
    last_updated = time.time()

    _, frame = cap.read()
    height, width, channels = frame.shape
    shape_center = np.array([int(width * 0.5), int(height * 0.5)])

    rectangle1 = (int(width * 0.5) + gap, int(height * 0.5) + gap)
    rectangle2 = (int(width * 0.5) - gap, int(height * 0.5) - gap)

    ard = serial.Serial('COM4', 9600)

    ######################## Initial positions ########################
    arduino_horizontal_position = 90  # int(extract_arduino_numerical_data(ard.readline()))
    arduino_vertical_position = 45
    horizontal_position = 0
    vertical_position = 0
    horizontal_movement, vertical_movement = 'None', 'None'
    ###################################################################

    while True:
        loop_start_time = time.time()
        _, frame = cap.read()
        if webcam_counter % frame_check_rate == 0:
            cv2.rectangle(frame, rectangle1, rectangle2, (0, 0, 0), 2)
            blob, outputs = detect_objects(frame, model, output_layers)
            boxes, confs, class_ids = get_box_dimensions(outputs, height, width)
            frame, objects_locations = draw_labels(boxes, confs, colors, class_ids, classes, frame, shape_center)
            webcam_counter = 0

        cv2.imshow("Webcam feed", frame)

        if len(list(objects_locations.keys())) > 0:
            horizontal_position = objects_locations[list(objects_locations.keys())[0]][0]
            vertical_position = objects_locations[list(objects_locations.keys())[0]][1]

        horizon_condition = (horizontal_position - gap > shape_center[0] or horizontal_position + gap < shape_center[0])
        vertical_condition = (vertical_position - gap > shape_center[1] or vertical_position + gap < shape_center[1])
        geometric_condition = horizon_condition or vertical_condition

        if geometric_condition and len(list(objects_locations.keys())) > 0:
            if horizon_condition:
                if horizontal_position + gap < shape_center[0]:
                    arduino_horizontal_position += 1
                    horizontal_movement = 'Left'

                if horizontal_position - gap > shape_center[0]:
                    arduino_horizontal_position -= 1
                    horizontal_movement = 'Right'

            if vertical_condition:
                if vertical_position + gap < shape_center[1]:
                    arduino_vertical_position += 1
                    vertical_movement = 'Up'

                if vertical_position - gap > shape_center[1]:
                    arduino_vertical_position -= 1
                    vertical_movement = 'Down'

            print(f'({horizontal_movement, vertical_movement})')
            if last_updated + arduino_refresh_time_interval < loop_start_time:
                ard.write(struct.pack('>BB', arduino_horizontal_position, arduino_vertical_position))
                # ard.write(bytes(str(arduino_current_position), 'utf-8'))
                last_updated = loop_start_time
                print(f"Arduino sent angles: {arduino_horizontal_position},{arduino_vertical_position}")

            if arduino_horizontal_position <= 0:
                arduino_horizontal_position = 0

            if arduino_horizontal_position >= 180:
                arduino_horizontal_position = 180

            if arduino_vertical_position <= 0:
                arduino_vertical_position = 0

            if arduino_vertical_position >= 90:
                arduino_vertical_position = 90

        webcam_counter += 1
        # print(horizontal_position, shape_center[0], arduino_current_position)

        key = cv2.waitKey(2)
        if key == 'q':
            ard.write(bytes('90'), 'utf-8')
            ard.close()
            break
    cap.release()
    ard.close()
    cv2.destroyAllWindows()
