import cv2
import numpy as np
import math
from time import time, strftime, localtime
import base64


def region_of_interest(edges):
    '''
    提取感兴趣区域（截取下半部分）
    '''
    height, width = edges.shape
    mask = np.zeros_like(edges)
    polygon = np.array([[
        # (0, height * 1 / 2),
        # (width, height * 1 / 2),
        # (width, height),
        # (0, height),
        (0, 0),
        (width, 0),
        (width, height * 1 / 2),
        (0, height * 1 / 2),
    ]], np.int32)

    cv2.fillPoly(mask, polygon, 255)
    cropped_edges = cv2.bitwise_and(edges, mask)
    return cropped_edges


def detect_line(edges):
    '''
    基于霍夫变换的直线检测
    '''
    rho = 1  # 距离精度：1像素
    angle = np.pi / 180  #角度精度：1度
    min_thr = 10  #最少投票数
    lines = cv2.HoughLinesP(edges,
                            rho,
                            angle,
                            min_thr,
                            np.array([]),
                            minLineLength=8,
                            maxLineGap=8)
    return lines


def average_lines(frame, lines, direction='left'):
    '''
    小线段聚类
    '''
    lane_lines = []
    if lines is None:
        print(direction + '没有检测到线段')
        return lane_lines
    height, width, _ = frame.shape
    fits = []

    for line in lines:
        for x1, y1, x2, y2 in line:
            if x1 == x2:
                continue
            # 计算拟合直线
            fit = np.polyfit((x1, x2), (y1, y2), 1)
            slope = fit[0]
            intercept = fit[1]
            if direction == 'left' and slope < 0:
                fits.append((slope, intercept))
            elif direction == 'right' and slope > 0:
                fits.append((slope, intercept))
    if len(fits) > 0:
        fit_average = np.average(fits, axis=0)
        lane_lines.append(make_points(frame, fit_average))
    return lane_lines

def make_points(frame, line):
    '''
    根据直线斜率和截距计算线段起始坐标
    '''
    height, width, _ = frame.shape
    slope, intercept = line
    y1 = height
    y2 = int(y1 * 1 / 2)
    x1 = max(-width, min(2 * width, int((y1 - intercept) / slope)))
    x2 = max(-width, min(2 * width, int((y2 - intercept) / slope)))
    return [[x1, y1, x2, y2]]

def display_line(frame, lines, line_color=(0, 0, 255), line_width=2):
    '''
    在原图上展示线段
    '''
    line_img = np.zeros_like(frame)
    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                cv2.line(line_img, (x1, y1), (x2, y2), line_color, line_width)
    line_img = cv2.addWeighted(frame, 0.8, line_img, 1, 1)
    return line_img

def average_slope_intercept(frame, line_segments):
    """
    汇聚所有线段成1段或2段
    如果所有线段斜率  slopes < 0: 只检测到左边行道线
    如果所有线段斜率  slopes > 0: 只检测到右边行道线
    """
    lane_lines = []
    if line_segments is None:
        print('没有检测到线段')
        return lane_lines

    height, width, _ = frame.shape
    left_fit = []
    right_fit = []

    boundary = 1 / 3
    left_region_boundary = width * (1 - boundary)  # 左行道线应该位于整个图像的左2/3部分
    right_region_boundary = width * boundary  # 右行道线应该位于整个图像的右1/3部分

    for line_segment in line_segments:
        for x1, y1, x2, y2 in line_segment:
            if x1 == x2:  # 忽略垂直线（没有斜率）
                continue
            fit = np.polyfit((x1, x2), (y1, y2), 1)
            slope = fit[0]
            intercept = fit[1]
            if slope < -math.tan(25):
                if x1 < left_region_boundary and x2 < left_region_boundary:
                    left_fit.append((slope, intercept))
            elif slope > math.tan(25):
                if x1 > right_region_boundary and x2 > right_region_boundary:
                    right_fit.append((slope, intercept))

    if len(left_fit) > 0:
        left_fit_average = np.average(left_fit, axis=0)
        lane_lines.append(make_points(frame, left_fit_average))

    if len(right_fit) > 0:
        right_fit_average = np.average(right_fit, axis=0)

        lane_lines.append(make_points(frame, right_fit_average))

    return lane_lines


def compute_steer(lane_lines, frame):
    height, width, _ = frame.shape
    x_offset = 0
    y_offset = 0
    line_num = 0
    steering_angle = 0
    if len(lane_lines) == 2:  # 检测到2条行道线
        _, _, left_x2, _ = lane_lines[0][0]
        _, _, right_x2, _ = lane_lines[1][0]
        mid = int(width / 2)
        x_offset = (left_x2 + right_x2) / 2 - mid
        y_offset = int(height / 2)
        line_num = 2
        print('检测到2条线')
    elif len(lane_lines) == 1:  # 检测到1条行道线
        x1, _, x2, _ = lane_lines[0][0]
        x_offset = int((x2 - x1) / 1.0)
        y_offset = int(height / 2.0)
        line_num = 1
        print('检测到1条线')
    else:
        print('检测失败')
        return 0, 0

    angle_to_mid_radian = math.atan(
        x_offset / y_offset)  # angle (in radian) to center vertical line
    angle_to_mid_deg = int(angle_to_mid_radian * 180.0 /
                         math.pi)  # angle (in degrees) to center vertical line

    steering_angle = angle_to_mid_deg / 45.0
    return line_num, steering_angle

def take_photo(steer_angle, frame, pic_index):
    '''
    采集照片和对应的转向值
    '''
    _time = strftime('%Y-%m-%d-%H-%M-%S', localtime(time()))
    name = '%s' % _time
    img_path = "/home/pi/Robot/results/" + name + '_photo' + str(pic_index) + '_' + str(steer_angle) + '.jpg'
    cv2.imwrite(img_path, frame)
