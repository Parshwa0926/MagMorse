from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
from datetime import datetime
import datetime as dt
import csv
import matplotlib.pyplot as plt
import numpy as np
from mbientlab.warble import BleScanner

savedataname1 = "sensorData.txt"

with open(savedataname1, "w") as file:
    file.write("")

class State:
    # init
    def __init__(self, device):
        self.device = device
        self.samples = 0
        self.start_time = datetime.now()
        self.magCallback1 = FnVoid_VoidP_DataP(self.mag_data_handler1)
        self.magData1 = []
        self.timeData1 = []


    # mag callback
    def mag_data_handler1(self, ctx, data):
        mag = parse_value(data)
        elapsed_time = datetime.now()
        #elapsed_time = (datetime.now() - self.start_time).total_seconds()
        self.timeData1.append(elapsed_time)
        #print("Mag data 1: ", mag)
        self.magData1.append(mag)
        #print("Length of magData1: ", len(self.magData1))
        self.samples += 1

        with open(savedataname1, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([mag.x, mag.y, mag.z, elapsed_time])


states = []

# #BleScanner.set_handler()
BleScanner.start()
sleep(5)
BleScanner.stop()

# connect
for mac in ["DA:7D:AE:7C:A4:04"]:
    d = MetaWear(mac)
    d.connect()
    #time = float(input("Enter estimated time of communication: "))
    print("Connected to %s over %s" % (d.address, "USB" if d.usb.is_connected else "BLE"))
    print("Wait 1 second before starting the communication and 1 second between each letter")
    print("Please give about one second between letters and each dot is equivalent to 1sec ( . = 1 sec) & each dash is equivalent to around 3 seconds ( - = 3 seconds)")
    states.append(State(d))

# configure
for s in states:
    print("Configuring device")
    libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
    sleep(1.5)

    # setup mag
    libmetawear.mbl_mw_mag_bmm150_stop(s.device.board)
    #libmetawear.mbl_mw_mag_bmm150_configure(s.device.board, 1, 1, MagBmm150Odr._30Hz)
    libmetawear.mbl_mw_mag_bmm150_set_preset(s.device.board, MagBmm150Preset.HIGH_ACCURACY)
    # get mag and subscribe
    mag = libmetawear.mbl_mw_mag_bmm150_get_b_field_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_subscribe(mag, None, s.magCallback1)

    # start mag
    libmetawear.mbl_mw_mag_bmm150_enable_b_field_sampling(s.device.board)
    libmetawear.mbl_mw_mag_bmm150_start(s.device.board)

# sleep
sleep(15.0)

# stop
for s in states:
    libmetawear.mbl_mw_mag_bmm150_stop(s.device.board)
    libmetawear.mbl_mw_mag_bmm150_disable_b_field_sampling(s.device.board)

    mag = libmetawear.mbl_mw_mag_bmm150_get_b_field_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_unsubscribe(mag)
    libmetawear.mbl_mw_debug_disconnect(s.device.board)

# read data from file
with open(savedataname1, mode='r') as file:
    reader = csv.reader(file)
    magData1 = list(reader)


# convert data to numpy arrays
magData1all = np.array(magData1)

# convert mag data to float
magData1 = magData1all[:, 0:3].astype(float)

# convert time to float
time1 = magData1all[:, 3]

datetime_objs1 = [dt.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f") for dt_str in time1]
floats_time1 = [(dt_obj - dt.datetime(1970, 1, 1)).total_seconds() for dt_obj in datetime_objs1]

#print(floats_time1)
#print(floats_time2)

# subtract first time from all times
start = floats_time1[0]
floats_time1 = [floats_time1[i] - start for i in range(len(floats_time1))]

#print(floats_time1)
#print(floats_time2)

# print(floats_time1)
# print(floats_time2)
# print(magData1)

# create figure and subplots
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)

# plot data on subplots
#ax1.plot(floats_time1, magData1[:, 0]-magData1[0, 0], label='x')
#ax1.plot(floats_time1, magData1[:, 1]-magData1[0, 1], label='y')
ax1.plot(floats_time1, magData1[:, 2]-magData1[0, 2], label='z')
ax1.set_title('Device 1')
#ax1.set_ylim([-150, 150])
ax1.legend()


# set axis labels
fig.text(0.5, 0.04, 'Time (s)', ha='center')
fig.text(0.04, 0.5, 'Magnetic Field (uT)', va='center', rotation='vertical')

# show plot
plt.show()

#translation of data
import statistics
from scipy.stats import trim_mean

with open('sensorData.txt', 'r') as file:
  data = file.read()

def listZValues(data):
  zValues = []
  for line in data.splitlines():
    zValues.append(float(line.split(',')[2]))
  return zValues

def listSensorTimings(data):
  sensorTimes = []
  for line in data.splitlines():
    sensorTimes.append(str(line.split(' ')[1]))
  return sensorTimes

# CHANGE THRESHOLD HERE
defaultThreshold = trim_mean(listZValues(data), proportiontocut=0.15) # Currently at about 48.2424
# (The trimmed mean is just a special version of the mean that is more resistant to outliers. Read more on Wikipedia if you'd like.)

def subtractTimes(time1, time2):
  time1Seconds = float(time1.split(':')[0]) * 3600 + float(time1.split(':')[1]) * 60 + float(time1.split(":")[2])
  time2Seconds = float(time2.split(':')[0]) * 3600 + float(time2.split(':')[1]) * 60 + float(time2.split(':')[2])
  return round(time2Seconds - time1Seconds, 6)

timeIntervals = []
def findMorseIntervals(zValues, sensorTimes, threshold=defaultThreshold, gapBetweenPress=0.5, showTimes=False):
  morseIntervals = []
  currentMorseInterval = []
  currentSpaceInterval = []
  firstValIndex = 0
  firstSpaceIndex = 0

  for i in range(len(zValues)):
    val = zValues[i]
    currentTime = sensorTimes[i]

    if val <= threshold:
      currentMorseInterval.append(val)
      if len(currentMorseInterval) == 1:
        firstValIndex = i

    elif val > threshold and len(currentMorseInterval) > 0:
      initialTime = sensorTimes[firstValIndex]
      timeDiff = subtractTimes(initialTime, currentTime)
      if showTimes: print("pressed  for", "{:.6f}".format(timeDiff), " seconds")
      if timeDiff >= gapBetweenPress:
        morseIntervals.append(currentMorseInterval)
        timeIntervals.append(timeDiff)
      currentMorseInterval = []


    if val > threshold:
      currentSpaceInterval.append(val)
      if len(currentSpaceInterval) == 1:
        firstSpaceIndex = i

    elif val <= threshold and len(currentSpaceInterval) > 0:
      initialTime = sensorTimes[firstSpaceIndex]
      timeDiff = subtractTimes(initialTime, currentTime)
      if showTimes: print("released for", "{:.6f}".format(timeDiff), " seconds")
      if timeDiff >= gapBetweenPress:
        morseIntervals.append(currentSpaceInterval)
        timeIntervals.append(timeDiff)
      currentSpaceInterval = []


  if len(currentMorseInterval) > 0:
    initialTime = sensorTimes[firstValIndex]
    currentTime = sensorTimes[-1]
    timeDiff = subtractTimes(initialTime, currentTime)
    if showTimes: print("pressed  for", "{:.6f}".format(timeDiff), " seconds")

    if timeDiff >= gapBetweenPress:
      morseIntervals.append(currentMorseInterval)
      timeIntervals.append(timeDiff)

  if len(currentSpaceInterval) > 0:
    initialTime = sensorTimes[firstSpaceIndex]
    currentTime = sensorTimes[-1]
    timeDiff = subtractTimes(initialTime, currentTime)
    if showTimes: print("released for", "{:.6f}".format(timeDiff), " seconds")

    if timeDiff >= gapBetweenPress:
      morseIntervals.append(currentSpaceInterval)
      timeIntervals.append(timeDiff)

  return morseIntervals

def convertIntervalsToMorse(morseIntervals, threshold=defaultThreshold):
  morseSequence = ""
  for i in range(len(morseIntervals)):
    interval = morseIntervals[i]
    timeOfInterval = timeIntervals[i]
    if timeOfInterval < 1.5:
      if all(zValue <= threshold for zValue in interval):
        morseSequence += "."
    else:
      if all(zValue <= threshold for zValue in interval):
        morseSequence += "-"
      elif all(zValue > threshold for zValue in interval):
        morseSequence += " "

  return morseSequence.strip()

def convertMorseToEnglish(morseSequence):
  morseDict = {
      '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D',
      '.': 'E', '..-.': 'F', '--.': 'G', '....': 'H',
      '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
      '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P',
      '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
      '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
      '-.--': 'Y', '--..': 'Z',
      '-----': '0', '.----': '1', '..---': '2', '...--': '3',
      '....-': '4', '.....': '5', '-....': '6', '--...': '7',
      '---..': '8', '----.': '9',
      '--..--': ',', '.-.-.-': '.', '..--..': '?', '-..-.': '/'
  }

  words = morseSequence.split('   ')
  englishMessage = ''

  for word in words:
      letters = word.split(' ')
      for letter in letters:
          if letter in morseDict:
            englishMessage += morseDict[letter]
          else:
            englishMessage += '<?>' # '<?>' for unknown characters
      englishMessage += ' '

  return englishMessage.strip()

# TESTING:

#print(data)
zValues = listZValues(data)
sensorTimes = listSensorTimings(data)
morseIntervals = findMorseIntervals(zValues, sensorTimes)
morseSequence = convertIntervalsToMorse(morseIntervals)
englishMessage = convertMorseToEnglish(morseSequence)

print(morseSequence) # Prints the morse code
print(englishMessage) # Prints the translated English

#print(statistics.mean(listZValues(data)))
#print(trim_mean(listZValues(data), proportiontocut=0.15))
import pyttsx3

def convert_to_speech():
  text_to_speak = englishMessage # HERE: ENTER TEXT TO CONVERT
  engine = pyttsx3.init()
  engine.setProperty("rate", 150)  # Speed of speech
  engine.say(text_to_speak)
  engine.runAndWait()

convert_to_speech()


