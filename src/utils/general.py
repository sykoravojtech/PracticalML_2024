import os
import random

import torch
import numpy as np

def free_subnet(subnet):
    for p in subnet.parameters():
        p.requires_grad = False

def set_deterministic(seed=42):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = True