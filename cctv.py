import cv2
import flask
import time
import json
import multiprocessing
import pickle

import settings

app = flask.Flask(__name__,static_url_path='',static_folder='public')

import logging
log = logging.getLogger('werkzeug')
log.disable = True
app.logger.disabled = True
log.setLevel(logging.ERROR)

def loadFrame(camId,cam,mainQueue,modelQueue):
	import time
	cvCapture = cv2.VideoCapture(cam)
	cvCapture.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
	cvCapture.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
	fps = cvCapture.get(cv2.CAP_PROP_FPS)
	if fps > 0 and fps < 60:
		wt = 1 / fps
	else:
		wt = 1 / 30

	try:
		while True:
			st = time.time()
			if not cvCapture.isOpened():
				print("sss1 err")
				return
			success, frame = cvCapture.read()
			if not success:
				return
			if mainQueue.qsize() < 10:
				mainQueue.put(frame)
			if modelQueue.qsize() < 10:
				modelQueue.put((camId,frame))

			dt = time.time() - st
			if wt - dt > 0:
				time.sleep(wt - dt)
	finally:
		print("camera stop")
		return

def modelExec(imageQueue,resultQueue):
	import detectModel.YOLO
	import sounddevice
	import soundfile

	model = detectModel.YOLO.model

	result = {}

	data, sf = soundfile.read('notice.wav')

	lastPlayTime = {}
	lastLogTime = {}

	try:
		while True:
			camId,frame = imageQueue.get()
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			ret = model.eval(camId,frame)

			if camId not in result:
				result[camId] = []
			if len(result[camId]) > 14:
				result[camId].pop(0)
			result[camId].append(ret)

			count = 0
			for i in result[camId]:
				if i:
					count += 1
			if count > 13:
				curTime = int(time.time())
				if camId not in lastPlayTime or curTime - lastPlayTime[camId] > settings.noticeTerm:
					lastPlayTime[camId] = curTime
					sounddevice.default.device = settings.cctvList[camId]['speaker']
					sounddevice.play(data,sf)

				if (camId not in lastLogTime or curTime - lastLogTime[camId] > 2) and resultQueue.empty():
					lastLogTime[camId] = curTime
					resultQueue.put((camId,"danger dog detected"))
	finally:
		print("model stop")

cctvData = { 'cctvList': [],'mapPath':'/map' }

if settings.mapPath == 'navermap':
	cctvData['mapPath'] = 'navermap'
else:
	cctvData['mapPath'] = '/map'

cctvObject = []
mainImageQueueList = []
#modelImageQueueDict = {}
#resultQueueList = []

imageLoadProcessList = []
#modelProcessList = []
modelImageQueue = multiprocessing.Queue()
modelResultQueue = multiprocessing.Queue()
modelProcess = multiprocessing.Process(target=modelExec,args=(modelImageQueue,modelResultQueue))
modelProcess.start()

for i,cctv in enumerate(settings.cctvList):
	cctvData['cctvList'].append({
		'name':cctv['name'],
		'location':cctv['location'],
		'type':"image_stream",
		'targetPath':'/view?cctv=' + str(i),
	})

	mainImageQueue = multiprocessing.Queue()
	mainImageQueueList.append(mainImageQueue)
	imageLoadProcessList.append(multiprocessing.Process(target=loadFrame, args=(i,cctv['cam'],mainImageQueue,modelImageQueue)))

for p in imageLoadProcessList:
	p.start()

def genFrames(cctvId):
	while True:
		frame = mainImageQueueList[cctvId].get()
		while not mainImageQueueList[cctvId].empty():
			frame = mainImageQueueList[cctvId].get()
		ret, buffer = cv2.imencode('.jpg', frame)
		frame = buffer.tobytes()
		yield (b'--frame\r\n'
			   b'Content-Type: image/jpg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
	return app.send_static_file('viewer.html')

@app.route('/cctv.json')
def cctvJson():
	resp = flask.Response(json.dumps(cctvData))
	resp.headers['Content-Type'] = 'text/json'
	return resp

@app.route('/view')
def frameImage():
	cctvId = int(flask.request.args.get('cctv'))
	return flask.Response(genFrames(cctvId), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
	statusResult = {}
	while not modelResultQueue.empty():
		camId,result = modelResultQueue.get()
		if camId not in statusResult:
			statusResult[camId] = []
		statusResult[camId].append(result)

	resp = flask.Response(json.dumps(statusResult))
	resp.headers['Content-Type'] = 'text/json'
	return resp

@app.route('/map')
def map():
	return flask.send_file(settings.mapPath)

if __name__ == "__main__":
	app.run()
