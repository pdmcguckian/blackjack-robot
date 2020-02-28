import cv2
import numpy as np
import time

class CardDetection():
    def __init__(self):
    
        self.stream = cv2.VideoCapture(1)
        time.sleep(1)
        
        self.count = 0
        while self.count < 500:
            self.prep_frame()
            self.isolate_card()
            self.transform_card()
            self.locate_number()
            cv2.imshow('Frame', self.frame)
            cv2.imshow('number', self.num_thresh)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            self.count += 1

            print(self.count)

        self.stream.release()
        cv2.destroyAllWindows()
    
    def prep_frame(self):
    #Image Converted to Grayscare, Blurred & Thresholded

        #Grayscaling
        self.ret, self.frame = self.stream.read()
        self.gray = cv2.cvtColor(self.frame,cv2.COLOR_BGR2GRAY)

        #Blurring
        self.blur = cv2.GaussianBlur(self.gray,(5,5),0)

        #Thresholding
        self.retval, self.threshold = cv2.threshold(self.blur, 100, 255, cv2.THRESH_BINARY)
    
    def isolate_card(self):
    #Image is Contoured with smaller contours being removed and cropped around card
        
        #Finding contours in frame
        self.contours, self._ = cv2.findContours(self.threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            
        self.threshold_min = 90000
        self.cnts = []
        for cnt in self.contours:        
            self.area = cv2.contourArea(cnt)         
            if self.area > self.threshold_min:            
                self.cnts.append(cnt)


        self.c = min(self.cnts, key=cv2.contourArea)

        cv2.drawContours(self.frame, self.c, -1, (0, 255, 0), 3)

        # Find perimeter of card and use it to approximate corner points
        self.perimeter = cv2.arcLength(self.c,True)
        self.approx = cv2.approxPolyDP(self.c,0.01*self.perimeter,True)
        self.points = np.float32(self.approx)

        # Find width and height of card's bounding rectangle
        self.x,self.y,self.w,self.h = cv2.boundingRect(self.c)

        # Find center point of card by taking x and y average of the four corners.
        self.average = np.sum(self.points, axis=0)/len(self.points)


    def transform_card(self):
    #Corner points transform card into a 200x300 flat perspective image
        
        self.temp_rect = np.zeros((4,2), dtype = "float32")
    
        self.s = np.sum(self.points, axis = 2)

        self.tl = self.points[np.argmin(self.s)]
        self.br = self.points[np.argmax(self.s)]

        self.diff = np.diff(self.points, axis = -1)
        self.tr = self.points[np.argmin(self.diff)]
        self.bl = self.points[np.argmax(self.diff)]

        # create an array listing points in order of [top left, top right, bottom right, bottom left]
        if self.w <= 0.8*self.h: # If card is vertically oriented
            self.temp_rect[0] = self.tl
            self.temp_rect[1] = self.tr
            self.temp_rect[2] = self.br
            self.temp_rect[3] = self.bl

        if self.w >= 1.2*self.h: # If card is horizontally oriented
            self.temp_rect[0] = self.bl
            self.temp_rect[1] = self.tl
            self.temp_rect[2] = self.tr
            self.temp_rect[3] = self.br
        
        if self.w > 0.8*self.h and self.w < 1.2*self.h: #If the card is at an angle
            if self.points[1][0][1] <= self.points[3][0][1]: #card is tilted to the left.
                self.temp_rect[0] = self.points[1][0] # Top left
                self.temp_rect[1] = self.points[0][0] # Top right
                self.temp_rect[2] = self.points[3][0] # Bottom right
                self.temp_rect[3] = self.points[2][0] # Bottom left


            if self.points[1][0][1] > self.points[3][0][1]: #card is tilted to the right.
                self.temp_rect[0] = self.points[0][0] # Top left
                self.temp_rect[1] = self.points[3][0] # Top right
                self.temp_rect[2] = self.points[2][0] # Bottom right
                self.temp_rect[3] = self.points[1][0] # Bottom left
                
            
        self.maxWidth = 200
        self.maxHeight = 300

        # Create destination array, calculate perspective transform matrix, and transform image
        self.dst = np.array([[0,0],[self.maxWidth-1,0],[self.maxWidth-1,self.maxHeight-1],[0, self.maxHeight-1]], np.float32)
        self.matrix = cv2.getPerspectiveTransform(self.temp_rect,self.dst)
        self.warp = cv2.warpPerspective(self.frame, self.matrix, (self.maxWidth, self.maxHeight))
        self.warpGray = cv2.cvtColor(self.warp, cv2.COLOR_BGR2GRAY)


    def locate_number(self):
    #Corner of image where number is located is isolated and zoomed in by a factor of 4 and prepared

        self.num_area = self.warpGray[0:55,0:35]

        #Blurring
        self.num_blur = cv2.GaussianBlur(self.num_area,(5,5),0)

        #Thresholding
        self.retval, self.num_thresh = cv2.threshold(self.num_blur, 180, 255, cv2.THRESH_BINARY)

        cv2.imwrite('/Users/patrickmcguckian/Documents/NN Test Images/13/' + str(self.count+1500) +'.jpg', self.num_thresh)


test = CardDetection()