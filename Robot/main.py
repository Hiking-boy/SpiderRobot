import time
import multiprocessing
import movementlibrary as ML
import pygame

from snow import snow
from imagecv import imagecv


if __name__ == '__main__':
    # target：指定执行的函数名
    # args:使用元组方式给指定任务传参
    # kwargs:使用字典方式给指定任务传参
    pygame.init()
    win = pygame.display.set_mode((1,1))

    print('Please wait for 10 seconds')
    ML.StandUp()
    print('I am Ready!')
    snow_process = multiprocessing.Process(target=snow,args=(0))
    imagecv_process = multiprocessing.Process(target=imagecv, args=(0))

    snow_process.start()
    imagecv_process.start()
