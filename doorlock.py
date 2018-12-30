import RPi.GPIO as GPIO
import pigpio
import os, sys, struct
import thread
from time import sleep
from firebase import firebase
import urllib2

global flag
flag = False

global passwd
passwd = ""

GPIO.setmode(GPIO.BCM)

relayPin = 14
GPIO.setup(relayPin, GPIO.OUT)

greenDoorPin = 2
redDoorPin = 3

redPinL = 17
greenPin = 27
redPinR = 22

GPIO.setup(greenDoorPin, GPIO.OUT)
GPIO.setup(redDoorPin, GPIO.OUT)
GPIO.setup(redPinL, GPIO.OUT)
GPIO.setup(greenPin, GPIO.OUT)
GPIO.setup(redPinR, GPIO.OUT)


def is_connected():
    try:
        urllib2.urlopen('http://216.58.192.142', timeout=1)
        return True
    except urllib2.URLError as err: 
        return False


def setupFirebase():
    global firebase1
    firebase1 = firebase.FirebaseApplication('https://magneticdoorlockcontroller.firebaseio.com', None)
    flag = firebase1.get('/control1', '/input')

if flag:
    GPIO.output(relayPin, GPIO.LOW)
    GPIO.output(greenDoorPin, GPIO.HIGH)
    GPIO.output(redDoorPin, GPIO.LOW)
else:
    GPIO.output(relayPin, GPIO.HIGH)
    GPIO.output(greenDoorPin, GPIO.LOW)
    GPIO.output(redDoorPin, GPIO.HIGH)


def updatePiInfo():
    global flag
    global firebase1
    try:
        doorIsUnlocked = firebase1.get('/control1', '/input')
        if doorIsUnlocked == flag:
            if doorIsUnlocked:
                print("Door is unlocked")
                print("Press Enter to change mode...")
                GPIO.output(greenDoorPin, GPIO.HIGH)
                GPIO.output(redDoorPin, GPIO.LOW)

            else:
                print("Door is locked")
                print("Press Enter to change mode...")
                GPIO.output(greenDoorPin, GPIO.LOW)
                GPIO.output(redDoorPin, GPIO.HIGH)

        else:
            if flag:
                lockDoor()
            else:
                unlockDoor()

            flag = doorIsUnlocked
    except:
        start()
        

def unlockDoor():
    GPIO.output(relayPin, GPIO.LOW)
    GPIO.output(greenDoorPin, GPIO.HIGH)
    GPIO.output(redDoorPin, GPIO.LOW)
    global flag
    flag = False


def lockDoor():
    GPIO.output(relayPin, GPIO.HIGH)
    GPIO.output(greenDoorPin, GPIO.LOW)
    GPIO.output(redDoorPin, GPIO.HIGH)
    global flag
    flag = True


def input_thread(L):
    raw_input()
    L.append(None)


def read_numpad_input(num):
    infile_path = "/dev/input/event3"

    # long int, long int, unsigned short, unsigned short, unsigned int
    FORMAT = 'llHHI'
    EVENT_SIZE = struct.calcsize(FORMAT)

    # open file in binary mode
    in_file = open(infile_path, "rb")

    event = in_file.read(EVENT_SIZE)

    while event:
        (tv_sec, tv_usec, type, code, value) = struct.unpack(FORMAT, event)

        if type != 0 or code != 0 or value != 0:
            if type == 4 and code == 4:
                if num == 0:
                    if value == 458841:
                        in_file.close()
                        return "1"
                    
                    elif value == 458842:
                        in_file.close()
                        return "2"
                    
                    else:
                        return "3"

                elif num == 1:
                    if value == 458840:
                        in_file.close()
                        global passwd
                        temp = ""
                        for i in range(len(passwd)):
                            if (i != 0 and i%2 == 0):
                                temp += passwd[i]
                        passwd = ""
                        print(temp)
                        return temp
                    else:
                        num_str = str(value % 10)
                        print("coba: " + num_str)
                        global passwd
                        passwd += num_str

                else:
                    return 0
        else:
            print()
            # nothing

        event = in_file.read(EVENT_SIZE)

    in_file.close()


def start():
    print("Choose Mode")
    GPIO.output(redPinL, GPIO.LOW)
    GPIO.output(greenPin, GPIO.HIGH)
    GPIO.output(redPinR, GPIO.LOW)

    var = read_numpad_input(0)
    
    if var == "1":
        print("Numpad Mode")
        # Numpad mode, red led 1 on
        GPIO.output(redPinL, GPIO.HIGH)
        GPIO.output(greenPin, GPIO.LOW)
        GPIO.output(redPinR, GPIO.LOW)

        password = read_numpad_input(1)

        if password == "80085":
            unlockDoor()

            GPIO.output(redDoorPin, GPIO.LOW)
            GPIO.output(greenDoorPin, GPIO.HIGH)
            
            # Locking door in 5 seconds
            for x in range(1, 6):
                GPIO.output(redPinL, GPIO.HIGH)
                sleep(1)
                GPIO.output(redPinL, GPIO.LOW)
                sleep(1)
            
            lockDoor()
            start()
        else:
            # Wrong password
            for x in range(1,3):
                GPIO.output(redPinL, GPIO.HIGH)
                GPIO.output(greenPin, GPIO.HIGH)
                sleep(1)
                GPIO.output(redPinL, GPIO.LOW)
                GPIO.output(greenPin, GPIO.LOW)
                sleep(1)

            start()

    elif var == "2":
        print("App Mode")
        if is_connected():
            print("Internet is up!")
            L = []
            thread.start_new_thread(input_thread, (L,))

            # App mode, green led on
            GPIO.output(redPinL, GPIO.LOW)
            GPIO.output(greenPin, GPIO.LOW)
            GPIO.output(redPinR, GPIO.HIGH)

            while True:
                if L:
                    print("exiting app mode")
                    lockDoor()
                    break
                updatePiInfo()
                sleep(1)

            # Exiting app mode
            for x in range(1,3):
                GPIO.output(redPinR, GPIO.HIGH)
                sleep(1)
                GPIO.output(redPinR, GPIO.LOW)
                sleep(1)

            start()
        else:
            print("No internet connection, please enter 1 for Numpad Mode")
            # No internet
            for x in range(1,3):
                GPIO.output(greenPin, GPIO.HIGH)
                GPIO.output(redPinR, GPIO.HIGH)
                print("Nyala")
                sleep(1)
                print("Mati")
                GPIO.output(greenPin, GPIO.LOW)
                GPIO.output(redPinR, GPIO.LOW)
                sleep(1)

            start()

    else:
        # Wrong command
        for x in range(1, 3):
            GPIO.output(greenPin, GPIO.HIGH)
            sleep(1)
            GPIO.output(greenPin, GPIO.LOW)
            sleep(1)

        start()


if is_connected():
    print("Internet is up!")
    setupFirebase()
    start()
else:
    print("No internet connection, please enter 1 for Numpad Mode")
    # No internet
    for x in range(1,3):
        GPIO.output(greenPin, GPIO.HIGH)
        GPIO.output(redPinR, GPIO.HIGH)
        print("Nyala")
        sleep(1)
        print("Mati")
        GPIO.output(greenPin, GPIO.LOW)
        GPIO.output(redPinR, GPIO.LOW)
        sleep(1)

    start()
