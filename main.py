import time
import serial


arduino_refresh_time_interval = 1
arduino_edge_position = 60
last_updated = time.time()
ard = serial.Serial('COM4', 9600)

######################## Initial positions ########################
arduino_current_position = 0  # int(extract_arduino_numerical_data(ard.readline()))
horizontal_position = 0
vertical_position = 0
shape_center = (0, 0)
###################################################################

while True:
    loop_start_time = time.time()

    objects_locations = (x, y)

    if horizontal_position != shape_center[0]:
        if horizontal_position < shape_center[0]:
            arduino_current_position += 1
            print('left')

        if horizontal_position > shape_center[0]:
            arduino_current_position -= 1
            print('right')

        if last_updated + arduino_refresh_time_interval < loop_start_time:
            ard.write(bytes(str(arduino_current_position), 'utf-8'))
            last_updated = loop_start_time
            print(f"Position update has been sent to arduino - horizontal position: {horizontal_position}, "
                  f"shape center: {shape_center[0]}, arduino current position: {arduino_current_position}")
