import numpy as np
import gdspy as gp
import os,sys

def ClearCurrentLib():
    # clear the current library
    kk=list(gp.current_library.cells.keys())
    for key in kk:
        gp.current_library.remove(key)
    return True
