import numpy as np
import gdspy as gp
import os,sys

def ClearCurrentLib():
    # clear the current library
    kk=list(gp.current_library.cells.keys())
    for key in kk:
        gp.current_library.remove(key)
    return True

def GetSubcellNames(root):
    
    cell_names = [root.name]

    if root == None:
        return []

    def get_cell_names(root):
        if root.references == []:
            return
        for cell in root.references:
            if cell.ref_cell.name in cell_names:
                continue
            cell_names.append(cell.ref_cell.name)
            get_cell_names(cell.ref_cell)

    get_cell_names(root)

    return cell_names

