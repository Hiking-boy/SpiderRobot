# 导入系统库
import sys
import time

from picamera import PiCamera

import movementlibrary as ML
import cv2
import matplotlib.pyplot as plt
import numpy as np
import math
from PIL import Image
import pygame

camera = PiCamera()
camera.rotation = 180
# 导入自定义库
from tools import region_of_interest, detect_line, make_points, average_lines, display_line,average_slope_intercept,compute_steer,take_photo

# 创建并设置视频捕获对象
# cap = cv2.VideoCapture(0)
# print("摄像头是否已经打开 ？ {}".format(cap.isOpened()))
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # 设置图像宽度
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)  # 设置图像高度
i=0
pygame.init()
win = pygame.display.set_mode((1,1))

print('Please wait for 10 seconds')
ML.StandUp()
print('I am Ready!')
# 循环控制
p=1
while True:

    # 读取图像
    camera.start_preview(fullscreen=False, window=(200, 5, 960, 540))
    time.sleep(1)
    camera.capture('/home/pi/Robot/images/image' + str(p) + '.jpg')
    # ret, frame = cap.read()
    # if not ret:
    #     print("图像获取失败，请检查")
    #     #break
    #     sys.exit()
    frame = cv2.imread('/home/pi/Robot/images/image'+str(p)+'.jpg')
   # frame = np.rot90(frame,k=2)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # height, width, _ = frame.shape
    # hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 黄色区域检测
    lower_blue = np.array([30, 30, 30])
    upper_blue = np.array([45, 255, 255])
    yellow_mask = cv2.inRange(hsv, lower_blue, upper_blue)

    #cv2.imwrite('yellow_mask.jpg',yellow_mask)

    # 黄色线边缘提取
    yellow_edge = cv2.Canny(yellow_mask, 200, 400)

    #cv2.imwrite('yellow_edge.jpg', yellow_edge)

    # 橙色线感兴趣区域提取
    orange_roi = region_of_interest(yellow_edge)
    #cv2.imwrite('orange_roi.jpg', orange_roi)

    # 橙色线段检测
    orange_lines = detect_line(orange_roi)
    print('orange_lines=',orange_lines)
    lane_lines = average_slope_intercept(frame, orange_lines)
    orange_show = display_line(frame,lane_lines)
   # cv2.imwrite('/home/pi/Robot/orange_show%02d.jpg' % i for i in range(10),orange_show)
    #计算转向角
    line_num, steer_angle = compute_steer(lane_lines, frame)
    if line_num == 0:
        print('异常')
    print("\r 当前转向角度steer: %s    " % (steer_angle))
    take_photo(steer_angle, orange_show, i)
    #ML.CCW()
    # ML.CCW(int(abs(-1.2 * 45)))
    # time.sleep(0.5)
    # for i in range(2):
    # ML.Forward()
    # sys.exit()
    if steer_angle > 0.3333 and steer_angle < 1.2222:
        ML.CW(int(steer_angle*45))
        time.sleep(0.5)
        ML.Forward()
       # ML.Forward()
        print('右转')
    elif steer_angle >=1.2222:
        ML.CW(55)
        time.sleep(0.5)
        ML.Forward()
        # time.sleep(0.5)
        # ML.CW(int((steer_angle-1.2222)*45))
        print('急右转')
    elif steer_angle < -0.3333 and steer_angle >-1.2222:
        ML.CCW(int(abs(steer_angle*45)))
        time.sleep(0.5)
        ML.Forward()
      #  ML.Forward()
        print('左转')
    elif steer_angle <=-1.2222:
        ML.CCW(55)
        time.sleep(0.5)
        ML.Forward()
        # time.sleep(0.5)
        # ML.CCW(int((abs(-1.2222-steer_angle))*45))
        print('急左转')
    elif steer_angle < 0.3333 and steer_angle > -0.3333:
        ML.Forward()
        print('直走')


  #  for j in range(5):
  #  ML.Forward()
  #  sys.exit()
    time.sleep(3)
# cv2.imshow('yellow_show',orange_show)
# cv2.waitKey(0)
# # 白色线段检测
# white_lines = detect_line(white_roi)
# white_lane = average_lines(frame, white_lines, direction='right')
# white_show = display_line(frame, white_lane, line_color=(255, 0, 0))

# cv2.imshow('white_show',white_show)
# cv2.waitKey(0)
# # 计算转向角
# x_offset = 0
# y_offset = 0
# if len(yellow_lane) > 0 and len(white_lane) > 0:  # 检测到2条线
#     _, _, left_x2, _ = yellow_lane[0][0]
#     _, _, right_x2, _ = white_lane[0][0]
#     mid = int(width / 2)
#     x_offset = (left_x2 + right_x2) / 2 - mid
#     y_offset = int(height / 2)
# elif len(yellow_lane) > 0 and len(yellow_lane[0]) == 1:  # 只检测到黄色行道线
#     x1, _, x2, _ = yellow_lane[0][0]
#     x_offset = x2 - x1
#     y_offset = int(height / 2)
# elif len(white_lane) > 0 and len(white_lane[0]) == 1:  # 只检测到白色行道线
#     x1, _, x2, _ = white_lane[0][0]
#     x_offset = x2 - x1
#     y_offset = int(height / 2)
# else:  # 一条线都没检测到
#     print('检测不到行道线，退出程序')
#
#
# angle_to_mid_radian = math.atan(x_offset / y_offset)
# angle_to_mid_deg = int(angle_to_mid_radian * 180.0 / math.pi)
# steering_angle = angle_to_mid_deg / 45.0
# print("steering_angle是:",steering_angle)

    # # 执行动作
    # obv, reward, done, info = env.step(action)
    #
    # # 重新获取图像
    # frame = cv2.cvtColor(obv, cv2.COLOR_RGB2BGR)

    # # 运行完以后重置当前场景
    # obv = env.reset()


# if __name__ == '__main__':
#     '''
#     主函数入口
#     '''
#     main()