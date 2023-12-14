import cctvModel
import torch
import tensorflow as tf
import numpy as np
import cv2

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
	try:
		for gpu in gpus:
			tf.config.experimental.set_memory_growth(gpu, True)
			logical_gpus = tf.config.experimental.list_logical_devices('GPU')
			print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
	except RuntimeError as e:
		print(e)


class YOLO(cctvModel.CCTVModel):
	def __init__(self):
		#self.model = torch.hub.load("ultralytics/yolov5", 'yolov5s')
		self.model = torch.hub.load('yolov5','custom', path='best.pt',force_reload=True,source='local')
		self.sampleFrameCount = 30
		self.recentFrames = {}

		self.dog_breed_model = tf.keras.models.load_model('dog_detection.h5')

		print("breed model loaded")

	def eval(self, camId, image):
		result = self.model(image)
		labels = result.xyxyn[0].cpu()[:,-1].numpy().astype(int)
		detect = result.xyxyn[0].cpu().numpy() 
		result = []
		for target in detect:
			size = 0
			point = (0,0)
			if target[4] > 0.7:
				print("dog detected")
				size = (target[2] - target[0]) * (target[3] - target[1])
				point = ((target[2] + target[0]) / 2,(target[3] - target[1]) / 2)

				h,w,c = image.shape
				xStart = int(target[0] * w) - 1
				if xStart < 0:
					xStart = 0
				xEnd = int(target[2] * w) - 1
				if xEnd < 0:
					xEnd = 0
				yStart = int(target[1] * h) - 1
				if yStart < 0:
					yStart = 0
				yEnd = int(target[3] * h) - 1
				if yEnd < 0:
					yEnd = 0
				breed_image = image[yStart:yEnd,xStart:xEnd]

				breed_image = cv2.resize(breed_image,dsize=(331,331),interpolation=cv2.INTER_AREA)
				breed_image = np.expand_dims(breed_image, axis = 0)
				breed_image = breed_image / 255

				ret = self.dog_breed_model.predict(breed_image)
				argmax = np.argmax(ret)
				classes = ['affenpinscher', 'afghan_hound', 'african_hunting_dog', 'airedale', 'american_staffordshire_terrier', 'appenzeller', 'australian_terrier', 'basenji', 'basset', 'beagle', 'bedlington_terrier', 'bernese_mountain_dog', 'black-and-tan_coonhound', 'blenheim_spaniel', 'bloodhound', 'bluetick', 'border_collie', 'border_terrier', 'borzoi', 'boston_bull', 'bouvier_des_flandres', 'boxer', 'brabancon_griffon', 'briard', 'brittany_spaniel', 'bull_mastiff', 'cairn', 'cardigan', 'chesapeake_bay_retriever', 'chihuahua', 'chow', 'clumber', 'cocker_spaniel', 'collie', 'curly-coated_retriever', 'dandie_dinmont', 'dhole', 'dingo', 'doberman', 'english_foxhound', 'english_setter', 'english_springer', 'entlebucher', 'eskimo_dog', 'flat-coated_retriever', 'french_bulldog', 'german_shepherd', 'german_short-haired_pointer', 'giant_schnauzer', 'golden_retriever', 'gordon_setter', 'great_dane', 'great_pyrenees', 'greater_swiss_mountain_dog', 'groenendael', 'ibizan_hound', 'irish_setter', 'irish_terrier', 'irish_water_spaniel', 'irish_wolfhound', 'italian_greyhound', 'japanese_spaniel', 'keeshond', 'kelpie', 'kerry_blue_terrier', 'komondor', 'kuvasz', 'labrador_retriever', 'lakeland_terrier', 'leonberg', 'lhasa', 'malamute', 'malinois', 'maltese_dog', 'mexican_hairless', 'miniature_pinscher', 'miniature_poodle', 'miniature_schnauzer', 'newfoundland', 'norfolk_terrier', 'norwegian_elkhound', 'norwich_terrier', 'old_english_sheepdog', 'otterhound', 'papillon', 'pekinese', 'pembroke', 'pomeranian', 'pug', 'redbone', 'rhodesian_ridgeback', 'rottweiler', 'saint_bernard', 'saluki', 'samoyed', 'schipperke', 'scotch_terrier', 'scottish_deerhound', 'sealyham_terrier', 'shetland_sheepdog', 'shih-tzu', 'siberian_husky', 'silky_terrier', 'soft-coated_wheaten_terrier', 'staffordshire_bullterrier', 'standard_poodle', 'standard_schnauzer', 'sussex_spaniel', 'tibetan_mastiff', 'tibetan_terrier', 'toy_poodle', 'toy_terrier', 'vizsla', 'walker_hound', 'weimaraner', 'welsh_springer_spaniel', 'west_highland_white_terrier', 'whippet', 'wire-haired_fox_terrier', 'yorkshire_terrier']

				#print(classes[argmax],xEnd - xStart,yEnd - yStart)
				#for i,v in enumerate(ret[0]):
				#	if v > 0.4:
				#		print(classes[i],v)
				if classes[argmax] in ['american_staffordshire_terrier', 'boston_bull','bull_mastiff','french_bulldog','rottweiler','staffordshire_bullterrier']:
					return True
			else:
				continue
			#result.append({'type':target[5],'size':size,'point':point})
		return False

model = YOLO()
