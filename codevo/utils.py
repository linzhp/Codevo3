__author__ = 'lzp'

import numpy as np
from random import random

def sample(values, weights):
    bins = np.add.accumulate(weights)
    return values[np.digitize([random() * bins[-1]], bins)][0]
