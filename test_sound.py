import sounddevice
import soundfile
import time

data,sf = soundfile.read('notice.wav')
sounddevice.play(data,sf)
