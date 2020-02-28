import numpy as np
import os
import cv2
from tqdm import tqdm
import random
import pickle

path = "/Users/patrickmcguckian/OneDrive - Imperial College London/GIZMO/NN Test Images"
ranks = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]

training_data = []

def prep_data():
    for rank in ranks: 

        full_path = os.path.join(path,rank)
        class_num = ranks.index(rank)

        for instance in tqdm(os.listdir(full_path)):

            img_array = cv2.imread(os.path.join(full_path,instance) ,cv2.IMREAD_GRAYSCALE)
            new_array = cv2.resize(img_array, (35, 55)) 
            training_data.append([new_array, class_num])

prep_data()

print(len(training_data))

random.shuffle(training_data)

X = []
y = []

for features,label in training_data:
    X.append(features)
    y.append(label)

X = np.array(X).reshape(-1, 35, 55, 1)

pickle_out = open("X.pickle","wb")
pickle.dump(X, pickle_out)
pickle_out.close()

pickle_out = open("y.pickle","wb")
pickle.dump(y, pickle_out)
pickle_out.close()