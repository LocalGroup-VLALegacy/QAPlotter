
import numpy as np

def load_spwdict(filename):
    '''
    Load in the SPW dictionary from the pipeline saved as a numpy
    file.
    '''
    return np.load(filename, allow_pickle=True).item()
