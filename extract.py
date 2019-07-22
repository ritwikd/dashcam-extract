import cv2
import os
import re
import numpy as np
import pytesseract

speed_reg = re.compile('^[0-9]* MPH+')
lat_reg = re.compile('^N[0-9]{2}\.[0-9]{6}')
long_reg = re.compile('^W[0-9]{3}\.[0-9]{6}')

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# BLUR AREA
# FROM (0, 955) to (625, 1080)

# SPEED/GPS TEXT
# FROM (52, 77) to (560, 108)

# Read the video from specified path
cam = cv2.VideoCapture("C:\\Users\\ritzy\\Videos\\2019_0720_133105_806.mp4")

try:

    # creating a folder named data
    if not os.path.exists('data'):
        os.makedirs('data')

    # if not created then raise error
except OSError:
    print('Error: Creating directory of data')

# frame
currentframe = 1

prev_data = []
prev_updated = 0

fourcc = cv2.VideoWriter_fourcc(*'XVID')
video = cv2.VideoWriter('output.avi',fourcc, 60.0, (1920, 1080))

extracted_info = []

while currentframe < 60:
    ret, frame = cam.read()
    frame_info = []

    if ret:
        # if video is still left continue creating images
        name = './data/frame' + str(currentframe) + '.jpg'
        name_extrac_pre = './data/frame' + str(currentframe) + '-extract-pre.jpg'
        name_ocr = './data/frame' + str(currentframe) + '-dashtext.jpg'
        # print('Creating...' + name)
        # writing the extracted images
        extract_pre_frame = frame[955:1080, 0:625]
        blur_frame = frame[480:600, 220:660]
        blur_frame_2 = frame[480:600, 1020:1460]
        blurred_overlay = cv2.GaussianBlur(blur_frame, (101, 101), 10)
        blurred_overlay_2 = cv2.GaussianBlur(blur_frame_2, (101, 101), 10)
        ocr_frame = (extract_pre_frame[77:108, 52:560])
        out = (255 - cv2.addWeighted(ocr_frame, 1.3, ocr_frame, 0, -60))
        out[out > 127] = 255
        out[out <= 127] = 0
        h, w = out.shape[0:2]
        base_size = h + 20, w + 20, 3
        # make a 3 channel image for base which is slightly larger than target img
        base = np.zeros(base_size, dtype=np.uint8)
        cv2.rectangle(base, (0, 0), (w + 20, h + 20), (255, 255, 255), 30)  # really thick white rectangle
        base[10:h + 10, 10:w + 10] = out  # this works
        # cv2.imwrite(name, frame)
        # cv2.imwrite(name_extrac_pre, extract_pre_frame)
        # cv2.imwrite(name_ocr, base)

        dash_text = pytesseract.image_to_string(base)

        print('\n'*80)

        if dash_text != '':
            try:

                dash_split = dash_text.split('W')

                speed = dash_split[0].replace('O', '0')
                latlong = 'W' + dash_split[1].replace(' ', '')

                latitude = 'N' + latlong.split('N')[1]
                longitude = latlong.split('N')[0]
                if longitude[-1] == '.': longitude = longitude[:-1]

                speed_match = speed_reg.search(speed)
                lat_match = lat_reg.search(latitude)
                long_match =  long_reg.search(longitude)

                if speed_match and lat_match and long_match:
                    frame_info = [speed, latitude, longitude]
                    print(f'Frame {currentframe:06d} - Speed: {speed} Latitude: {latitude} Longitude: {longitude}')
                    # print(repr(dash_text))
                    # print(repr(latlong))

                    prev_data = frame_info
                    prev_updated = currentframe
                else:
                    print(f'Frame {currentframe:06d} - Malformed data detected. Using data from Frame {prev_updated}')
                    print(speed, speed_match, latitude, lat_match, longitude, long_match)
                    print(repr(dash_text))
                    frame_info = prev_data
            except:
                print(f'Frame {currentframe:06d} - Data parse error. Using data from Frame {prev_updated}')
                frame_info = prev_data
        else:
            print(f'Frame {currentframe:06d} - No data. Using data from Frame {prev_updated}')
            frame_info = prev_data
        font = cv2.FONT_HERSHEY_SIMPLEX
        bottomLeftCornerOfText = (75, 85)
        fontScale = 2.5
        fontColor = (255, 255, 255)
        lineType = 2

        cv2.putText(blurred_overlay, speed,
                    bottomLeftCornerOfText,
                    font,
                    fontScale,
                    fontColor,
                    lineType)
        extracted_info.append(frame_info)
        frame[960:1080, 0:440] = blurred_overlay
        video.write(frame)
        currentframe += 1
    else:
        break

video.release()

# Release all space and windows once done
cam.release()
cv2.destroyAllWindows()
