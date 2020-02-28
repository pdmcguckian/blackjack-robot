import pickle
import tensorflow as tf
import numpy as np

pickle_in = open("X.pickle","rb")
X = pickle.load(pickle_in)
pickle_in = open("y.pickle","rb")
y = pickle.load(pickle_in)

X = np.divide(X, 255.0)

x_train = X[:int(len(X)*0.3)]
y_train = y[:int(len(X)*0.3)]

x_test = X[int(len(X)*0.3):]
y_test = y[int(len(X)*0.3):]


x_train = tf.keras.utils.normalize(x_train, axis=1).reshape(x_train.shape[0], -1)
x_test = tf.keras.utils.normalize(x_test, axis=1).reshape(x_test.shape[0], -1)

model = tf.keras.models.Sequential()
model.add(tf.keras.layers.Dense(128, activation=tf.nn.relu, input_shape= x_train.shape[1:]))
model.add(tf.keras.layers.Dense(128, activation=tf.nn.relu))
model.add(tf.keras.layers.Dense(13, activation=tf.nn.softmax))

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])  

model.fit(x_train, y_train, epochs=12)

loss, acc = model.evaluate(x_test, y_test)
print(acc, loss)

model.save("/Users/patrickmcguckian/Desktop/model.h5")

converter = tf.lite.TFLiteConverter.from_keras_model_file("/Users/patrickmcguckian/Desktop/model.h5")
tflite_model = converter.convert()
open("/Users/patrickmcguckian/Desktop/converted_model.tflite", "wb").write(tflite_model)

