from lab3_tools import *
from lab2_tools import *
from lab1_tools import *
from lab3_proto import *
from lab2_proto import *
from lab1_proto import *
from prondict import prondict
import os
import pdb
from sklearn.model_selection import train_test_split
from tqdm import tqdm
from sklearn.preprocessing import StandardScaler
from keras.utils import np_utils
import csv


def task(task):
    # ----- 4.1 -------
    if task=='4.1':
        phoneHMMs = np.load('lab2_models_all.npz')['phoneHMMs'].item()
        phones = sorted(phoneHMMs.keys())
        nstates = {phone: phoneHMMs[phone]['means'].shape[0] for phone in phones}
        stateList = [ph + '_' + str(id) for ph in phones for id in range(nstates[ph])]
        stateList.dump('statelist.dat')
        stateList = np.asarray(stateList)
        stateList.dump('statelist.dat')

     # ----- 4.2 -------
    stateList = np.load('statelist.dat')
    filename = 'tidigits/disc_4.1.1/tidigits/train/man/nw/z43a.wav'
    samples, samplingrate = loadAudio(filename)
    lmfcc = mfcc(samples)
    wordTrans = list(path2info(filename)[2])#sequence of digits (word level transcription)
    phoneTrans = words2phones(wordTrans, prondict)#phone level transcription
    utteranceHMM = concatHMMs(phoneHMMs, phoneTrans)
    stateTrans = [phone + '_' + str(stateid) for phone in phoneTrans
                  for stateid in range(nstates[phone])]
    viterbiStateTrans = forcedAlignment(lmfcc, utteranceHMM, stateTrans)
    # pdb.set_trace()
    frames2trans(viterbiStateTrans, outfilename='z43a.lab')

    if task == '4.3':
        traindata = []
        #for root, dirs, files in os.walk('tidigits/disc_4.1.1/tidigits/train'):
        for root, dirs, files in os.walk('tidigits/disc_4.2.1/tidigits/test'):
            for file in files:
                if file.endswith('.wav'):
                    filename = os.path.join(root, file)
                    samples, samplingrate = loadAudio(filename)
                    lmfcc_ = mfcc(samples, samplingrate=samplingrate)
                    mspec_ = mspec(samples, samplingrate=samplingrate)
                    wordTrans = list(path2info(filename)[2])
                    phoneTrans = words2phones(wordTrans, prondict)
                    utteranceHMM = concatHMMs(phoneHMMs, phoneTrans)
                    stateTrans = [phone + '_' + str(stateid) for phone in phoneTrans
                                  for stateid in range(nstates[phone])]
                    viterbiStateTrans = forcedAlignment(lmfcc, utteranceHMM, stateTrans)
                    targets = [stateList.index(s) for s in viterbiStateTrans]
                    traindata.append({'filename': filename, 'lmfcc': lmfcc_, 'mspec': mspec_, 'targets': targets})
        #np.savez('traindata.npz', traindata=traindata)
        np.savez('testdata.npz', traindata=traindata)


def splitdata(path='traindata.npz', percent=0.1):
    traindata = np.load(path)['traindata']
    trainset, validset = train_test_split(traindata, test_size=percent)
    np.savez('train_set.npz', traindata=trainset)
    np.savez('valid_set.npz', traindata=validset)


def acoustic(dataset, feature='lmfcc', datasetname='train'):
    if feature=='lmfcc':
        features = np.empty((1,91))
    elif feature=='mspec':
        features = np.empty((1, 280))
    elif feature == 'targets':
        features = np.empty(1)
    else:
        raise ValueError('No such feature!')

    for utterance in tqdm(dataset):
        lmfcc_ = utterance[feature]
        if feature == 'targets':
            lmfcc_feature = np.asarray(lmfcc_)
            features = np.hstack((features, lmfcc_feature))
        else:
            D = lmfcc_.shape[1] # 13 or 40
            N = lmfcc_.shape[0]
            lmfcc_feature = np.zeros((N, D*7))
            #lmfcc_ = np.vstack((lmfcc_[3], lmfcc_[2],lmfcc_[1], lmfcc_.reshape(1,-1)[0], lmfcc_[N-2], lmfcc_[N-3], lmfcc_[N-4]))
            lmfcc_ = np.concatenate((lmfcc_[3], lmfcc_[2],lmfcc_[1], lmfcc_.reshape(1,-1)[0], lmfcc_[N-2], lmfcc_[N-3], lmfcc_[N-4]), axis=0)#1*1937
            for i in range(N):
                lmfcc_feature[i] = lmfcc_[i*D:(i+7)*D]

            features = np.vstack((features, lmfcc_feature))

    filename = feature + '_' + datasetname + '_x.dat'
    features[1:].dump(filename)

    return features[1:]



if __name__ == '__main__':
    #task('4.3')
    #splitdata()
    # feature(lmfcc and mspec) extraction, TODO: NEED CHECK
    '''
    train_set = np.load('train_set.npz')['traindata']
    lmfcc_train_x = acoustic(train_set,feature='lmfcc')
    mspec_train_x = acoustic(train_set, feature='mspec')
    scaler_lmfcc = StandardScaler().fit(lmfcc_train_x)
    #mean_lmfcc = scaler_lmfcc.mean_
    #var_lmfcc = scaler_lmfcc.var_
    lmfcc_train_x = scaler_lmfcc.transform(lmfcc_train_x)
    lmfcc_train_x = lmfcc_train_x.astype('float32')
    lmfcc_train_x.dump('lmfcc_train_x.dat')

    scaler_mspec = StandardScaler().fit(mspec_train_x)
    mean_mspec = scaler_mspec.mean_
    var_mspec = scaler_mspec.var_
    mspec_train_x = scaler_mspec.transform(mspec_train_x)
    mspec_train_x = mspec_train_x.astype('float32')
    mspec_train_x.dump('mspec_train_x.dat')

    valid_set = np.load('valid_set.npz')['traindata']
    lmfcc_val_x = acoustic(valid_set, feature='lmfcc',datasetname='val')
    lmfcc_val_x = scaler_lmfcc.transform(lmfcc_val_x)
    lmfcc_val_x = lmfcc_val_x.astype('float32')
    lmfcc_val_x.dump('lmfcc_val_x.dat')

    mspec_val_x = acoustic(valid_set, feature='mspec', datasetname='val')
    mspec_val_x = scaler_mspec.transform(mspec_val_x)
    mspec_val_x = mspec_val_x.astype('float32')
    mspec_val_x.dump('mspec_val_x.dat')

    test_set = np.load('testdata.npz')['traindata']
    lmfcc_test_x = acoustic(test_set, feature='lmfcc', datasetname='test')
    lmfcc_test_x = scaler_lmfcc.transform(lmfcc_test_x)
    lmfcc_train_X = lmfcc_train_x.astype('float32')
    lmfcc_test_X.dump('lmfcc_test_X.dat')
    
    mspec_test_x = acoustic(test_set, feature='mspec', datasetname='test')
    mspec_test_X = scaler_mspec.transform(mspec_test_x)
    mspec_test_X = mspec_test_X.astype('float32')
    mspec_test_X.dump('mspec_test_X.dat')
    '''

    # process the targets
    valid_set = np.load('valid_set.npz')['traindata']
    valid_y = acoustic(valid_set, feature='targets', datasetname='val')
    StateList = np.load('statelist.dat')
    output_dim = len(StateList)#61
    valid_y = np_utils.to_categorical(valid_y, output_dim)#152751 * 61















