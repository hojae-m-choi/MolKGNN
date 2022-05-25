import argparse
import numpy as np
import os.path as osp
from evaluation import calculate_ppv, calculate_logAUC, sigmoid
from sklearn.metrics import confusion_matrix

dataset = '488997'
model = 'bcl'
cutoff = 0.7

if model == 'bcl':
	bcl_dir = '../examples/bcl/20_models/results/'
	file_name = f'{dataset}.RSR.1_32_005_025/independent0-4_monitoring0-4_number0.gz.txt'
	default_input_file = osp.join(bcl_dir, file_name) 
elif model == 'kgnn':
	kgnn_dir = '../experiments/'

	default_input_file = ''

parser = argparse.ArgumentParser()
parser.add_argument('--predicted_file', type=str, default=default_input_file)

args = parser.parse_args()

sc_list = []
label_list = []
with open(args.predicted_file, 'r') as in_file:
	for line in in_file:
		components = line.split(',')
		pred_sc = float(components[0])
		label = int(components[1][0])
		sc_list.append(pred_sc)
		label_list.append(label)
		# print(f'pred_sc:{pred_sc} label:{label}')
sc_list = np.array(sc_list)
label_list = np.array(label_list)

predicted_prob = sigmoid(sc_list) # Convert to range [0,1]
predicted_y = np.where(predicted_prob > cutoff, 1, 0) # Convert to binary

tn, fp, fn, tp = confusion_matrix(label_list, predicted_y, labels=[0, 1]).ravel()

active_y = len(np.where(label_list==1)[0])
inactive_y = len(label_list) - active_y
total_y = len(label_list)

predicted_active = len(np.where(predicted_y==1)[0])
predicted_inactive = len(np.where(predicted_y==0)[0])

print(f'==== Dataset Info ====')
print(f'Looking at dataset {dataset} for {model}:') 
print(f'There are {active_y} actives, {inactive_y} inactives, totaling {total_y} molecules')
print(f'Active ratio:{active_y/total_y*100:0.2f}%')
print(f'==== Prediction ====')
print(f'There are {predicted_active} predicted actives, {predicted_inactive} predicted inactives')
print(f'There are {tp} TP, {fp} FP, {tn} TN, {fn} FN')
print(f'==== Metrics ====')
logAUC = calculate_logAUC(label_list, sc_list)
print(f'logAUC:{logAUC:0.2f}')
ppv = calculate_ppv(label_list, sc_list, cutoff=cutoff)
print(f'ppv:{ppv:0.5f}')



