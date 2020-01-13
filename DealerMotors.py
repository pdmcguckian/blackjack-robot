###
# ARTOPS: a Blackjack playing robot
# Created by Oliver Colebourne & Patrick McGuckian
# 11.12.2019
###

#After looking online for a suitable motor library for the Raspberry Pi to run our Nema17 Stepper from the TB6612fng motor driver we were unsuccessful
#Therefore we created one and this also allowed us to make it specific for our use.
#We also combined it with our DC motor control from the Raspberry Pi
#This file is imported by the main.py file and allows control of the Dealer Stepper and also the Dealer DC motor

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

class DealerStepper():
    def __init__(self, pins=[29,13,31,37]):
        self.pins = pins
        self.steps = [
            [1,0,0,0], #defining half step sequence
            [1,1,0,0],
            [0,1,0,0],
            [0,1,1,0],
            [0,0,1,0],
            [0,0,1,1],
            [0,0,0,1],
            [1,0,0,1],
            ]
        self.position = 0
        #0 is shuffler, 1 is player side, 2 is dealer side
        for pin in self.pins: #setup pins
            GPIO.setup(pin, GPIO.OUT, initial=0)

    def runStepper(self, direction, turnvalue, unit='turns', delay=0.001): #unit in 'degrees' or default 'turns', delay default 0.001, direction 0 is clockwise, 1 is anticlockwise 
        #General stepper run code
        if unit=='turns': #default
            X = (turnvalue*360/8)/0.9 #Nema17 has 1.8 degree step, using half step so 0.9 degree 
        elif unit=='degrees':
            X = (turnvalue/8)/0.9
        else:
            raise TypeError('Invalid unit type')
        X = int(round(X,0))

        #direction controls - work by traversing the half step sequence in opposite ways
        if direction == 0:
            for i in range(X):
                for j in range(8):
                    for k in range(4):
                        GPIO.output(self.pins[k],self.steps[j][k])
                    time.sleep(delay)
        elif direction == 1:
            for i in range(X):
                for j in range(8):
                    for k in range(4):
                        GPIO.output(self.pins[k],self.steps[7-j][k])
                    time.sleep(delay)
        for pin in self.pins: #setup pins
            GPIO.setup(pin, GPIO.OUT, initial=0)

    def gotoShuffler(self):
        #by using positions the code can be used both as a check and a control. 
        #means the stepper won't accidently deal cards in the wrong place or move into the walls.
        if self.position == 0: #from shuffler
            print('already there')
            pass
        elif self.position == 1: #from player side
            print('moving Dealer')
            self.runStepper(1, 2.3) #2.3 rotations anticlockwise
            self.position = 0
        elif self.position == 2: #from dealer side
            print('moving Dealer')
            self.runStepper(1, 4.4) #3 rotations anticlockwise
            self.position = 0
        print('at Shuffler')
    def gotoPlayerSide(self):
        if self.position == 0: #from shuffler
            print('moving Dealer')
            self.runStepper(0, 2.3) #2.3 rotations clockwise
            self.position = 1
        elif self.position == 1: #from player side
            print('already there')
            pass
        elif self.position == 2: #from dealer side
            print('moving Dealer')
            self.runStepper(1, 2.1) #2.1 rotations anticlockwise
            self.position = 1
        print('at Player side')
    def gotoDealerSide(self):
        if self.position == 0: #from shuffler
            print('moving Dealer')
            self.runStepper(0, 4.4) #4.4 rotations clockwise
            self.position = 2
        elif self.position == 1: #from player side
            print('moving Dealer')
            self.runStepper(0, 2.1) #2.1 rotations clockwise
            self.position = 2
        elif self.position == 2: #from dealer side
            print('already there')
            pass
        print('at Dealer side')

class DealerDC():
    def __init__(self, pins=[40,38,36,32], frequency=500):
        self.pins = pins
        for pin in self.pins: #set pins as output
            GPIO.setup(pin, GPIO.OUT) 
        for pin in self.pins[:2]: #set motor pins to 0 initially
            GPIO.output(pin, 0)
        GPIO.output(self.pins[3],1) #pull standby pin to high
        self.pwm=GPIO.PWM(self.pins[2],frequency) #setup pwm
        
    def runMotor(self, speed, runtime, direction=True): #pins in list [Ai1, Ai2, PWM, STBY]
        #general DC run code
        if direction:
            GPIO.output(self.pins[0],1) #direction 1
            GPIO.output(self.pins[1],0)
        else:
            GPIO.output(self.pins[0],0) #direction 2
            GPIO.output(self.pins[1],1) 
        self.pwm.start(speed)
        time.sleep(runtime) #wait
        self.pwm.stop() #stop pwm

    def dealOneCard(self):
        print('dealing one card')
        self.runMotor(75,.25) #push one card out
        time.sleep(0.1)
        self.runMotor(70,.4,0) #pull cards back

    def dealWholePack(self):
        print('dealing remaining pack')
        self.runMotor(60,4) #deal all remaining cards in pack
        time.sleep(3)
        self.runMotor(60,4.5)
    
    def pullBack(self):
        print('pulling back cards')
        self.runMotor(70,.4,0) #pull back cards in Dealer, used after shuffle
