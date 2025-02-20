import numpy as np
import torch
import sys
import os

################################## ASSEMBLY OF THE DATASET ##################################

ref, test = 35, 100 # INSERT THE NUMBER FOR THE REFERENCE AND TEST SNAPSHOTS

timesteps = np.genfromtxt("../ITHACAoutput/NUMPYsnapshots/timesteps.txt")
Ns = timesteps.size

f = []
x = []
y = []

for j in range(Ns):

    snap_name = "../ITHACAoutput/NUMPYsnapshots/{:d}.npy".format(j)
    X = np.load(snap_name)

    f.append(X[:,0])
    x.append(X[:,1])
    y.append(X[:,2])

Nh = X[:,0].size

f = torch.tensor(np.array(f), requires_grad=True).T
x = torch.tensor(np.array(x), requires_grad=True).T
y = torch.tensor(np.array(y), requires_grad=True).T
# f.shape = x.shape = y.shape = torch.Size([Nh, Ns])

f_ref = f[:,ref].clone().float().reshape(-1, 1) 
x_ref = x[:,ref].clone().float().reshape(-1, 1)
y_ref = y[:,ref].clone().float().reshape(-1, 1) 
# f_ref.shape = x_ref.shape = y_ref.shape = torch.Size([Nh, 1])

# np.savetxt("reference_snapshot", f_ref,newline='\n')

################################## TRAINING ##################################

script_dir = os.path.dirname(__file__)
res_dir = os.path.join(script_dir, 'Results/')
os.makedirs(res_dir, exist_ok=True)

from interp_net import InterpNet

interpolate = InterpNet()

if os.path.exists('./TrainedModels/InterpNet.pt'):

 	trained_interpolation = torch.load('./TrainedModels/InterpNet.pt')
 	
else:

	input_ref = interpolate.build_input(x_ref, y_ref)
	interpolate.train(input_ref, f_ref)
	trained_interpolation = torch.load('./TrainedModels/InterpNet.pt')

from shift_net import ShiftNet

shift = ShiftNet(ref, test)
shift.train(x, y, timesteps, f)

print('####### Loading trained model parameters #######\n\n')
trained_shift = torch.load('./TrainedModels/ShiftNet.pt')

################################## GENERALIZATION ##################################

X = np.zeros((Nh, Ns))
counter = 0
print('####### Preparing for generalization #######\n')
for snap_x, snap_y, t, snap_f in zip(x.T, y.T, timesteps, f.T):

	output = trained_shift.forward(shift.build_input(snap_x, snap_y, t))

	shift_x = (output[:, 0]).reshape(-1, 1)
	shift_y = (output[:, 1]).reshape(-1, 1)

	shifted_x = snap_x.reshape(-1,1) - shift_x 
	shifted_y = snap_y.reshape(-1,1) - shift_y 

	shifted_coordinates = interpolate.build_input(shifted_x, shifted_y)

	shifted_f = trained_interpolation.forward(shifted_coordinates.float())
	snapshot = shifted_f.flatten().detach().numpy()

	X[:, counter] = snapshot
	counter += 1

print('####### Generalization complete #######\n\n')
np.save("../ITHACAoutput/NUMPYsnapshots/shifted_snapshot_matrix", X)
print('####### Shifted snapshot matrix exported succesfully #######\n')
