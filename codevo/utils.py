__author__ = 'lzp'

import numpy as np
from random import random

def sample(values, weights):
    bins = np.add.accumulate([w + 1 for w in weights])
    return values[np.digitize([random() * bins[-1]], bins)]
