# -*- coding: utf-8 -*-
"""okculuk_lstm.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/16-0CKR7aq_AH66bD17PDcUDK1PSPy98X
"""

from google.colab import drive
drive.mount('/content/drive')

!nvidia-smi

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pdb
import pickle
from sklearn.metrics import f1_score
from sklearn.metrics import confusion_matrix
import pywt

from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import Dense, RepeatVector, TimeDistributed, Flatten, LSTM, Bidirectional, Dropout, BatchNormalization, Conv2D, Activation, MaxPooling2D, Flatten
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.losses import mse
from tensorflow.keras.optimizers import Adam, RMSprop, Adagrad
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import load_model
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras import regularizers
from tensorflow.keras.initializers import glorot_normal
from pandas import DataFrame as df
import scipy.io

#window size is 1 second (125 points)
WIN_LEN = 212 # 1696/ 212 = 8 tane kaydırma.

#amount of points to slide forward for next window
WIN_SLIDE = 5

#at least 75% of the indices within a given window should be within the valid indices
#TODO: is this a good threshold? the lower this number is, it could affect performance quite a bit
MIN_VALID_PERC = 0.9

#define the frequencies for the cwt
wavelet = 'morl'
scales = np.arange(2,64)  #this corresponds to ~1.5Hz - 50Hz
wavelet_freqs = pywt.scale2frequency(wavelet, scales)*125

import os
os.listdir('/content/drive/MyDrive/okculuk')

myDict = scipy.io.loadmat('/content/drive/MyDrive/okculuk/myCell.mat')
T=myDict['myCell']
myCell=pd.DataFrame.from_dict(myDict['myCell'])
myCell.drop([0], axis=0, inplace=True)
myCell.columns = ['record_name', 'ch1', 'qrs_ch1']
myCell.head()

myCell.describe()

arr=myCell['record_name'].to_numpy()

myCell=myCell.applymap(func= np.ravel)
myCell.head()
myCell=myCell.applymap(func= np.ravel)
myCell.head()
myCell.describe()

def get_windows(row, channel):
    

    #check if there is no data here
    if row[channel] is None: return []

    #set up the data and labels
    #coefficients = row['cwt_'+channel]
    data = row[channel]
    N = 1701
    QRS_labels = row['qrs_'+channel]
    #valid_inds = row['inds_to_keep_'+channel]

    windows = []
    #now loop through windows of length WIN_LEN and generate windows with labels

    for i in range(0, N-WIN_LEN, WIN_SLIDE):
        #get the current window indices
        tmp_inds = range(i,i+WIN_LEN)

        #confirm that at least 90% of the points are within the valid indices
       # if sum(np.isin(tmp_inds, valid_inds))/WIN_LEN < MIN_VALID_PERC: continue

        #grab the data for this window
       # tmp_win = coefficients[:,tmp_inds]
        tmp_labels = QRS_labels[tmp_inds]
        tmp_data = data[tmp_inds]

        #plot
       # power = (abs(tmp_win))**2
        #levels = [0.0625, 0.125, 0.25, 0.5, 1, 2, 4, 8]
        #contourlevels = np.log2(levels)
        
        #if i == 5000:
          
            #plt.tight_layout()
            #plt.savefig('cwt/%s_%s.png' % (record_name, channel), dpi=125)
            #plt.show()
            #plt.close()#
        

        #add to list
        tmp_dict = { 'label': tmp_labels, 'data': tmp_data}
        windows.append(tmp_dict)

    return windows

#window the data
windows_ch1 = myCell.apply(func=get_windows, channel='ch1', axis=1)
windows_ch1 = pd.DataFrame(windows_ch1)
windows_ch1 = pd.DataFrame([item for sublist in windows_ch1.values for item in sublist[0]])

#take the first 90% as training and the last 10% as testing
train_ch1 = windows_ch1.iloc[0:int(len(windows_ch1)*0.9)]
test_ch1 = windows_ch1.iloc[int(len(windows_ch1)*0.9)+1:]


#save as separate files
train_ch1.to_pickle('/content/drive/MyDrive/okculuk/train.pkl', protocol=4)
test_ch1.to_pickle('/content/drive/MyDrive/okculuk/test.pkl', protocol=4)

plt.figure()
plt.plot(myCell['ch1'][55])
plt.plot(myCell['qrs_ch1'][55])

data_train = pd.read_pickle('/content/drive/MyDrive/okculuk/train.pkl')
X_train = np.array([np.reshape(x, (WIN_LEN,1)) for x in data_train['data'].values])
X_train = np.expand_dims(X_train,3)
y_train = np.array([y for y in data_train['label'].values])
y_train = to_categorical(np.expand_dims(y_train, axis=2))

data_test = pd.read_pickle('/content/drive/MyDrive/okculuk/test.pkl')
X_test = np.array([np.reshape(x, (WIN_LEN,1)) for x in data_test['data'].values])
X_test = np.expand_dims(X_test,3)
y_test = np.array([y for y in data_test['label'].values])
y_test = to_categorical(np.expand_dims(y_test, axis=2))
#data_test = np.array([data for data in data_test['data'].values])

#first CNN
model = Sequential()
model.add(Conv2D(filters=32, kernel_size=5, padding='same', input_shape=X_train.shape[1:]))
model.add(Activation('relu'))
model.add(BatchNormalization())
#model.add(MaxPooling2D(pool_size=(1, 4)))
model.add(Dropout(0.25))

#second CNN
model.add(Conv2D(filters=32, kernel_size=5, padding='same'))
model.add(Activation('relu'))
model.add(BatchNormalization())
#model.add(MaxPooling2D(pool_size=(1, 4)))
model.add(Dropout(0.25))

#first LSTM. note that we need to do a timedistributed flatten as a transition from CNN to LSTM
model.add(TimeDistributed(Flatten()))
model.add(Bidirectional(LSTM(units=100, return_sequences=True, dropout=0.25)))

#second LSTM. note that we need to do a timedistributed flatten as a transition from CNN to LSTM
model.add(Bidirectional(LSTM(units=50, return_sequences=True, dropout=0.25)))

#dense layer
model.add(TimeDistributed(Dense(5, activation='relu')))
model.add(BatchNormalization())
model.add(Dropout(0.25))

#activation layer
model.add(TimeDistributed(Dense(2, activation='softmax')))

#compile model
model.compile(
    loss='categorical_crossentropy',
    optimizer=Adam(),
    metrics=['accuracy'],
)

model.summary()

VAL_SPLIT = 0.30 #percentage for validation split during training
BATCH_SIZE = 32  #batch size
EPOCHS = 30      #number of epochs

do_training = True

if do_training:
    #monitor validation loss for early stopping
    early_stop = EarlyStopping(monitor='val_loss', min_delta=0.001, patience=25)

    history = model.fit(
      X_train,
      y_train,
      batch_size=BATCH_SIZE,
      epochs=EPOCHS,
      verbose=1,
      callbacks=[early_stop],
      shuffle=True,
      validation_split=VAL_SPLIT,
    )
    
    history = history.history
    model.save('/content/drive/MyDrive/okculuk/model.h5')
    pickle.dump(history, open('/content/drive/MyDrive/okculuk/history.pkl', 'wb'))

else:
    model = load_model('/content/drive/MyDrive/okculuk/model.h5')
    history = pickle.load(open('/content/drive/MyDrive/okculuk/history.pkl', 'rb'))

plt.figure(figsize=(10,6))
plt.plot(history['accuracy'], '*-')
plt.plot(history['val_accuracy'], '*-')
plt.title('Model accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.tight_layout()
plt.show()
plt.close()

# Plot training & validation loss values
plt.figure(figsize=(10,6))
plt.plot(history['loss'], '*-')
plt.plot(history['val_loss'], '*-')
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.tight_layout()
plt.show()
plt.close()

def roc(predictions, true):
    predictions = predictions.flatten()
    true = true.flatten()

    thresh_vals = [i/25 for i in range(26)]
    results = []
    for thresh in thresh_vals:
        tmp_predictions = (predictions < thresh).astype(int)
        f1 = f1_score(true, tmp_predictions)
        tn, fp, fn, tp = confusion_matrix(true, tmp_predictions).ravel()
        tpr = tp/(tp+fn)
        fpr = fp/(tn+fp)
        acc = (tp+tn)/(tn+fp+fn+tp)

        tmp_dict = {'f1': f1, 'acc': acc, 'tpr': tpr, 'fpr': fpr, 'thresh': thresh}
        results.append(tmp_dict)


    results = pd.DataFrame(results)
    results = results.sort_values(by='thresh', ascending=False)

    plt.figure(figsize=(10,6))
    plt.plot(results['fpr'], results['tpr'], '*-')
    plt.xlabel('FPR')
    plt.ylabel('TPR')
    plt.title('ROC')
    plt.show()

    results = results.sort_values(by='f1', ascending=False)
    final_thresh = results.head(1)['thresh'].values[0]

    return results, final_thresh

def invert_encoded_classes(encoded_classes):
  classes = []
  for row in encoded_classes:
      for i in range(0, encoded_classes.shape[1]):
        if row[i] == 1:
          classes.append(i)

  return np.asarray(classes).T

#predict outputs for training inputs
predictions = model.predict(X_train)

#since this is a binary classifier, just take the first column of probabilities

#calculate the probability threshold to optimize f1 score
# results, thresh = roc(predictions, y_train)

results, thresh = roc(predictions, y_train)

predictions.shape

ind=1865
plt.figure()
plt.plot(X_train[ind].ravel())
plt.plot(invert_encoded_classes(y_train[ind]))

veri_total=list()
veri_sonuc_total=list()

for k in range(0,53):
  veri=list()
  veri_sonuc=list()

  for i in range(k*298+k,(k+1)*298+1):
    if i==0:
      for j in range(212):
        veri.append(X_train[i][j])
        veri_sonuc.append(y_train[i][j])

    else:
      for j in range(207,212):
          veri.append(X_train[i][j])
          veri_sonuc.append(y_train[i][j]) 


  veri=np.asarray(veri)
  veri_sonuc=np.asarray(veri_sonuc)

  veri_total.append(veri)
  veri_sonuc_total.append(veri_sonuc)

ind=5
plt.figure()
plt.plot(veri_total[ind].ravel())
plt.plot(invert_encoded_classes(veri_sonuc_total[ind]))

predictions_r = np.round(predictions)
i_labels = []
for i in range(0, predictions.shape[0]):
  i_labels.append(invert_encoded_classes(predictions_r[i]))

i_labels = np.asarray(i_labels)

i_true_labels = []
for i in range(0, y_train.shape[0]):
  i_true_labels.append(invert_encoded_classes(y_train[i]))

i_true_labels = np.asarray(i_true_labels)

veri_labels_total=list()
veri_true_labels_total=list()

for k in range(0,53):
  veri_labels=list()
  veri_true_labels=list()

  for i in range(k*298+k,(k+1)*298+1):
    if i==0:
      for j in range(212):
        veri_labels.append(i_labels[i][j])
        veri_true_labels.append(i_true_labels[i][j])

    else:
      for j in range(207,212):
          veri_labels.append(i_labels[i][j])
          veri_true_labels.append(i_true_labels[i][j]) 


  veri_labels=np.asarray(veri_labels)
  veri_true_labels=np.asarray(veri_true_labels)

  veri_labels_total.append(veri_labels)
  veri_true_labels_total.append(veri_true_labels)

ind=12
plt.figure()
plt.plot(veri_total[ind].ravel())
plt.plot(invert_encoded_classes(veri_sonuc_total[ind]))
plt.plot(veri_labels_total[ind].ravel())



"""**BURADA KALDIM, SONRASI DENEME SADECE**"""









pred_input = X_train[0:32, :, :, :]
pred = model.predict(pred_input)
pred_input = pred_input.reshape((32*212,))

predictions_z = np.round(pred)
i_labels2 = []
for i in range(0, pred.shape[0]):
  i_labels2.append(invert_encoded_classes(predictions_z[i]))

i_labels2 = np.asarray(i_labels2)
i_labels2 = i_labels2.reshape((32*212,))

i_true_labels2 = []
for i in range(0, 32):
  i_true_labels2.append(invert_encoded_classes(y_train[i]))

i_true_labels2 = np.asarray(i_true_labels2)
i_true_labels2 = i_true_labels2.reshape((32*212,))

plt.figure()
plt.plot(pred_input)
plt.plot(i_labels2)
plt.plot(i_true_labels2)
plt.legend(['Xtrain', 'True', 'Predicted'])

#predict outputs for test inputs
predictions = model.predict(X_test)



#since this is a binary classifier, just take the first column of probabilities
predictions1 = predictions[:,:,0]

#threshold the probabilities
predictions1 = np.array([(p>thresh).astype(int) for p in predictions1])

#plot some random results
inds = np.array(range(len(predictions1)))
np.random.shuffle(inds)
for i in inds[0:5]:
    y_labels = y_test1[i]
    predictions1_tmp = 1-predictions1[i]
    data = X_test[i].ravel()



    plt.figure(figsize=(10,6))
    plt.plot(np.array(range(len(data)))/125, data, label='Data')
    plt.plot(np.array(range(len(data)))/125, y_labels, label='Label')
    plt.plot(np.array(range(len(data)))/125, predictions_tmp, label='Prediction')
    plt.legend(loc=1)
    plt.ylabel('Hz')
    plt.xlabel('Time (seconds)')
    plt.tight_layout()
    plt.show()
    plt.close()

#flatten
predictions1 = 1-predictions.flatten()
X_train1 = X_train.flatten()

#calculate various metrics
f1 = f1_score(X_train1, predictions1)
tn, fp, fn, tp = confusion_matrix(X_train1, predictions1).ravel()
tpr = tp/(tp+fn)
fpr = fp/(tn+fp)
acc = (tp+tn)/(tn+fp+fn+tp)

tmp_dict = {'f1': f1, 'acc': acc, 'tpr': tpr, 'fpr': fpr, 'thresh': thresh}
pd.DataFrame([tmp_dict])

