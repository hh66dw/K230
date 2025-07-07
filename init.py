import time
import os
import sys

from media.sensor import *
from media.display import *
from media.media import *
from time import ticks_ms
from machine import FPIOA
from machine import Pin
from machine import UART

#--------------------------------------------------------------------------

# 程序操作是否最简
ease = False

# 1024*768
photo_width  = 320
photo_height = 320

#--------------------------------------------------------------------------

# 退出

def camera_exit():
    if isinstance(sensor,Sensor):
        sensor.stop()
    Display.deinit()
    os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
    time.sleep_ms(100)
    MediaManager.deinit()


#--------------------------------------------------------------------------

# 反馈程序

def frame_check(img,clock):
    try:
        if ease == False:
            img.draw_string_advanced(50,50,80,"fps:{}".format(clock.fps()),color = (255,0,0))

    except Exception as e:
        if f"{e}" != "IDE interrupt":
            print(f"{e} --- frame_check")
        else:
            raise("IDE interrupt")


#--------------------------------------------------------------------------

# 简化调用

def draw_line(img, point1:list, point2:list,thickness = 10, color = (255,0,0)):
    try:
        img.draw_line(point1[0],point1[1],point2[0],point2[1],color =color,thickness = thickness)
    except Exception as e:
        if f"{e}" != "IDE interrupt":
            print(f"{e} --- draw_line")
        else:
            raise("IDE interrupt")



def draw_rect(img, point_leftup:list, width, height, thickness = 4, color = (255,0,0)):
    try:
        img.draw_rectangle(point_leftup[0],point_leftup[1],width,height,color =color,thickness = thickness,fill = False)
    except Exception as e:
        if f"{e}" != "IDE interrupt":
            print(f"{e} --- draw_rect")
        else:
            raise("IDE interrupt")



def draw_circle(img, point:list, r, thickness = 4, color = (255,0,0)):
    try:
        img.draw_circle(point[0],point[1],r,color =color,thickness = thickness,fill = False)
    except Exception as e:
        if f"{e}" != "IDE interrupt":
            print(f"{e} --- draw_circle")
        else:
            raise("IDE interrupt")



def find_lines(img,multipe = 1,distance_error=15,angle_error=15,length = 200,roi=(0,0,photo_width,photo_height)):
    try:
        roi = (roi[0]//multipe,roi[1]//multipe,roi[2]//multipe,roi[3]//multipe)

        img_deal = img.to_rgb565(copy=True)
        img_deal.midpoint_pool(multipe,multipe)
        lines = img_deal.find_line_segments(roi,distance_error,angle_error)

        back_lines = []
        for line in lines:
            if line.length() > length:
                back_lines.append(line)

                if ease == False:
                    img.draw_line(line.x1()*multipe,line.y1()*multipe,line.x2()*multipe,line.y2()*multipe,color=(255,0,0),thickness = 4)
        return back_lines

    except Exception as e :
        if f"{e}" != "IDE interrupt":
            print(f"{e} --- find_lines")
        else:
            raise("IDE interrupt")



def find_circles(img,deal = None, threshold=3000, roi=(0,0,photo_width,photo_height)):
    try:
        if deal == None:
            img_deal = img
        elif len(deal) == 2:
            img_deal = img.to_grayscale(copy = True)
            img_deal = img_deal.binary([deal])
        else:
            raise("deal just {gray(len-2)}")

        circles = img_deal.find_circles(threshold = threshold,roi = roi)

        if ease == False:
            for circle in circles:
                img.draw_circle(circle.circle(), color=(255, 0, 0), thickness=3)

        return circles
    except Exception as e :
        if f"{e}" != "IDE interrupt":
            print(f"{e} --- find_circles")
        else:
            raise("IDE interrupt")



def find_rects(img,deal = None, threshold=5000, roi=(0,0,photo_width,photo_height)):
    try:
        rects_corner = []

        if deal == None:
            img_deal = img
        elif len(deal) == 2:
            img_deal = img.to_grayscale(copy = True)
            img_deal = img_deal.binary([deal])
        else:
            raise("deal just {gray(len-2)}")

        rects = img_deal.find_rects(threshold = threshold,roi = roi)

        for rect in rects:
            rect_conner = rect.corners()
            rects_corner.append(rect_conner)

            if ease == False:
                draw_line(img,rect_conner[0],rect_conner[1])
                draw_line(img,rect_conner[1],rect_conner[2])
                draw_line(img,rect_conner[2],rect_conner[3])
                draw_line(img,rect_conner[3],rect_conner[0])

        return rects_corner
    except Exception as e :
        if f"{e}" != "IDE interrupt":
            print(f"{e} --- find_rects")
        else:
            raise("IDE interrupt")



def find_blobs(img,deal = None,invert = False,x_stride = 5,y_stride = 5, threshold=3000, roi=(0,0,photo_width,photo_height)):
    try:
        if len(deal) == 6:
            blobs = img.find_blobs([deal],invert,roi,x_stride = x_stride,y_stride = y_stride, pixels_threshold = threshold,margin = True)
        else:
            raise("deal just {LAB(len-6)}")

        if ease == False:
            for blob in blobs:
                img.draw_rectangle(blob.x(),blob.y(),blob.w(),blob.h(),color = (255,0,0),thickness = 4,fill = False)

        return blobs

    except Exception as e :
        if f"{e}" != "IDE interrupt":
            print(f"{e} --- find_blobs")
        else:
            raise("IDE interrupt")



#--------------------------------------------------------------------------

# UART

uart2 = None

def UART2_Init():
    fpioa = FPIOA()
    #fpioa.help()
    fpioa.set_function(11,FPIOA.UART2_TXD)
    fpioa.set_function(12,FPIOA.UART2_RXD)

    uart2 = UART(UART.UART2,115200)


#--------------------------------------------------------------------------

# 主程序
sensor = None

try:
    #UART2_Init()

    sensor = Sensor(width = photo_width,height = photo_height)
    sensor.reset()

    sensor.set_framesize(width = photo_width,height = photo_height)
    sensor.set_pixformat(Sensor.RGB565)

    Display.init(Display.LT9611,to_ide = True)

    MediaManager.init()

    sensor.run()

    clock = time.clock()

    while True:
        clock.tick()

        os.exitpoint()
        img = sensor.snapshot(chn = CAM_CHN_ID_0)

        a = find_circles(img)
        print(a)

        frame_check(img,clock)
        if (photo_width != 1920) or (photo_height != 1080):
            img.compressed_for_ide()
        Display.show_image(img)

except KeyboardInterrupt as e:
    print("用户停止:",e)
except BaseException as e:
    if (f"{e}" != "exceptions must derive from BaseException") and (f"{e}" != "IDE interrupt"):
        print(f"异常:{e}")
finally:
    camera_exit()


