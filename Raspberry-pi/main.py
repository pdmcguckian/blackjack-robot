###
# ARTOPS: a Blackjack playing robot
# Created by Oliver Colebourne & Patrick McGuckian
# 11.12.2019
###

#The main gameplay file
#Running this file runs the entire robot
#This code is based around the PyQT5 GUI control

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QMessageBox, QMainWindow, QShortcut
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import pyqtSlot, QRunnable, QThreadPool
import time
import serial
from mainwindow import *
import sys
import os

import RPi.GPIO as GPIO
import DealerMotors as DM
import CardDetection as CD
GPIO.setmode(GPIO.BOARD) #rpi gpio setup (.board referencing so using pin numbers)
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP) #button pin
GPIO.setup(7, GPIO.OUT) #button LED

class Worker(QRunnable): #MULTITHREADING WORKER: this was needed so that controlling the motors or triggering delays doesn't use the main GUI thread causing the UI to hang
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        self.fn(*self.args, **self.kwargs)

class Main(QMainWindow): #MAIN WINDOW
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.dealerStep = DM.DealerStepper() #setup motors
        self.dealerDC = DM.DealerDC()
        self.display(0)
        

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.ui.page1label1.setText("ARTOPS: Blackjack")

        self.ui.page3hitButton.clicked.connect(lambda: self.roundMainTrigger(0)) #setup the UI button functions
        self.ui.page3stickButton.clicked.connect(lambda: self.roundMainTrigger(1))
        self.ui.page7statsButton.clicked.connect(lambda: self.statisticsPage())
        self.ui.page7resetButton.clicked.connect(lambda: self.resetTrigger())
        self.ui.page8resetButton.clicked.connect(lambda: self.resetTrigger())
        self.ui.pageErrorButton1.clicked.connect(lambda: self.resetTrigger())
        self.shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        self.shortcut.activated.connect(self.exitApp)
        self.shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.shortcut.activated.connect(self.resetTrigger)
        
        self.showFullScreen()
        self.initialise()

    def initialise(self):
        #Ran at start of each game - resets variables and text
        self.playerScore,self.dealerScore,self.playerCards,self.dealerCards = 0,0,0,0
        self.playerCardList = []
        self.dealerCardList = []
        self.playerCamera = 0
        self.dealerCamera = 2
        self.roundNum = 0
        self.ui.page2label1.setText("Shuffling and dealing...")
        self.display(0)
        worker = Worker(self.waitForStart) 
        self.threadpool.start(worker)
        

    def waitForStart(self):
        #wait for button press to start
        GPIO.output(7, 1) #button LED on
        while True:
            button_state = GPIO.input(15)
            if button_state == False:
                print('Button Pressed...')
                GPIO.output(7, 0) #button LED off
                return self.shuffle() 
                
    def shuffle(self): #gui side shuffle
        self.display(1)
        self.shuffleComplete = False
        # Pass the function to execute
        worker = Worker(self.shuffleThread) 
        self.threadpool.start(worker)
        

    def shuffleThread(self): 
        #multithreaded shuffle
        #Connect to Arduino
        ser = serial.Serial('/dev/ttyACM0',9600, timeout = 0.1)
        time.sleep(1)
        ser.flushInput()

        #Send Request to Shuffle Cards
        ser.write(b'1')
        print('Shuffling')

        #Wait until Confirmation (handshake)
        self.shuffleComplete = False
        while self.shuffleComplete == False:
            data = ser.readline()
            if data:
                print('Shuffled')
                self.shuffleComplete = True
        self.dealerDC.pullBack() #pull in the cards
        self.startingDeal()


    def startingDeal(self): 
        #deal first two cards and read them for both sides
        self.dealerStep.gotoPlayerSide()
        self.dealCard('playerSide') #deal two cards
        self.ui.page2label1.setText("Please take your cards")
        self.dealerStep.gotoDealerSide()
        self.dealCard('dealerSide')
        #set #'My first card was a ...' text on hit/stick page
        if self.dealerCardList[0] == 1:
            self.ui.page3label2.setText('Ace')
        elif self.dealerCardList[0] == 11:
            self.ui.page3label2.setText('Jack')
        elif self.dealerCardList[0] == 12:
            self.ui.page3label2.setText('Queen')
        elif self.dealerCardList[0] == 13:
            self.ui.page3label2.setText('King')
        else:
            self.ui.page3label2.setText(str(self.dealerCardList[0]))

        worker = Worker(self.dealerStep.gotoPlayerSide)
        self.threadpool.start(worker)
        self.display(2)


    def dealCard(self,X): 
        #general single card and read method.
        worker = Worker(self.dealerDC.dealOneCard)
        self.threadpool.start(worker)

        if X == 'playerSide': #card detection for playerside card deal
            try:
                openCV = CD.CardDetection(self.playerCamera)
            except:
                self.dealCard(X)
            if openCV.card_rank > 10:
                self.playerScore += 10 #if the card is a jack queen or king add ten to the score
            else:
                self.playerScore += openCV.card_rank
            self.playerCards += 1
            self.playerCardList.append(openCV.card_rank)
            if self.playerCards<2: #if its the first round call the read card function again
                self.dealCard(X)
            print(self.playerCardList)
            
        elif X == 'dealerSide': #card detection for dealerside card deal
            try:
                openCV = CD.CardDetection(self.dealerCamera)
            except:
                self.dealCard(X)
            if openCV.card_rank > 10:
                self.dealerScore += 10
            else:
                self.dealerScore += openCV.card_rank
            self.dealerCards += 1
            self.dealerCardList.append(openCV.card_rank)
            if self.dealerCards<2:
                self.dealCard(X)
            print(self.dealerCardList)
    
    def errorPage(self): 
        #general error trigger
        self.display(8)

    def roundMainTrigger(self, playerAction): 
        #GUI side main round trigger
        self.ui.page4label2.setText('???')
        self.display(3)
        self.playerAction = playerAction
        worker = Worker(self.roundMain)
        self.threadpool.start(worker)

    def roundMain(self): 
        #main round method
        print('round main')
        #playerAction 0 is hit, 1 is stick
        self.roundNum += 1
        if self.playerAction == 0:
            self.dealerStep.gotoPlayerSide()
            self.dealCard('playerSide')
        self.dealerStep.gotoDealerSide()
        
        decision = self.decision(self.dealerCardList) #run decision method on dealers current cards
        if decision == 0:
            self.ui.page4label2.setText('HIT!')
            self.dealCard('dealerSide')
        elif decision == 1:
            self.ui.page4label2.setText('STICK!')
            time.sleep(1)
        self.dealerStep.gotoPlayerSide()
        if self.playerAction == 1 and decision == 1: #if both players choose to stick
            self.display(4)
            time.sleep(4)
            return self.finishGame()
        elif self.playerScore > 21 or self.dealerScore > 21: #if either player has gone bust
            return self.finishGame()
        else:
            return self.display(2) #return to hit or stick page

    def decision(self,cards):  
        #Dealer decision method
        if cards == []:
            return 1
        total_val = 340 #total value of all cards
        score = 0
        for i in cards: 
            if i > 10: #score calculator left from previous file
                i = 10
            score += i
            print(score)
        total_val -= score 
        prediction = total_val/(52-len(cards)) #find the average remaining card score
        if score + prediction <= 21:
            return 0 #hit
        else:
            return 1 #stick
        
    def finishGame(self):
        self.calculateScore() 
        os.getcwd
        f = open("running_total.txt", 'r+')  #reading then updating running_total txt file for total games won
        self.dealerTotal = int(f.readline()) 
        self.dealerTotal += self.dealerResult
        self.playerTotal = int(f.readline())
        self.playerTotal += self.playerResult
        f.truncate(0)
        f.seek(0,0)
        f.write(str(self.dealerTotal))
        f.write('\n' + str(self.playerTotal))
        f.close()
        self.ui.page8label3.setText(str(self.dealerTotal)) #setup results page
        self.ui.page8label5.setText(str(self.playerTotal))
        print(self.playerCardList, self.dealerCardList)
        self.display(5)


    def calculateScore(self): 
        #calculte the player and dealers score and find the winner. Update the gui 
        if self.dealerScore >21:
            self.dealerScore = 0
            self.ui.page7label3.setText('BUST')
        else:
            self.ui.page7label3.setText(str(self.dealerScore))
        
        if self.playerScore >21:
            self.playerScore = 0
            self.ui.page7label5.setText('BUST')
        else:
            self.ui.page7label5.setText(str(self.playerScore))
        if self.dealerScore > self.playerScore:
            self.dealerResult = 1
            self.playerResult = 0
            self.ui.page7label6.setText('I Win!')
        elif self.playerScore > self.dealerScore:
            self.dealerResult = 0
            self.playerResult = 1
            self.ui.page7label6.setText('You Win!')
        else:
            self.dealerResult = 0
            self.playerResult = 0
            self.ui.page7label6.setText('Draw!')
        return

    def statisticsPage(self): 
        #stats page control
        print("stats")
        self.display(6)
    
    def resetTrigger(self):
        #reset gui trigger
        print("PLAY AGAIN")
        self.display(7) #display collect cards message
        worker = Worker(self.reset)
        self.threadpool.start(worker)


    def reset(self): 
        #reset game for playing again
        self.dealerStep.gotoPlayerSide() #deal remaining pack onto player side
        self.dealerDC.dealWholePack()
        time.sleep(10)
        self.dealerStep.gotoShuffler()
        self.initialise()

    def display(self,i):
        #display the chosen stacked widget ie the page of the gui
        print('setting index', i)
        self.ui.stackedWidget.setCurrentIndex(i)


    @pyqtSlot()
    def exitApp(self):
        #exit method
        self.dealerStep.gotoShuffler
        GPIO.cleanup()
        sys.exit()

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Main()
    window.show()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
    sys.exit(app.exec_())