__author__ = 'lzp'

import numpy as np
from random import random


def sample(weighted_values):
    bins = np.add.accumulate([weight for value, weight in weighted_values])
    selected_index = np.digitize([random() * bins[-1]], bins)
    return weighted_values[int(selected_index)][0]
