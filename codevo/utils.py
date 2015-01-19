__author__ = 'lzp'

import numpy as np
from random import random

def sample(values, weights):
    bins = np.add.accumulate(weights)
    selected_index = np.digitize([random() * bins[-1]], bins)
    return values[selected_index]
