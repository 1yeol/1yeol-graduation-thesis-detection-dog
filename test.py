import detectModel.YOLO
import cv2
import time

#cvCapture = cv2.VideoCapture(0)
img = cv2.imread("../bull.jpg",cv2.IMREAD_COLOR)
#cvCapture.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
#cvCapture.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
#fps = cvCapture.get(cv2.CAP_PROP_FPS)
ret = detectModel.YOLO.model.eval(0,img)

#if fps > 0 and fps < 60:
#	wt = 1 / fps
#else:
#	wt = 1 / 30

#while True:
#	st = time.time()
#	if not cvCapture.isOpened():
#		print("cam Closed")
#		break
#	success, frame = cvCapture.read()
#	if not success:
#		break
#
#	ret = detectModel.YOLO.model.eval(0,frame)
#
#	dt = time.time() - st
#	if wt - dt > 0:
#		time.sleep(wt - dt)
