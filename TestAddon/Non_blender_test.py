
import os
from gerber import PCB

GERBER_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'gerbers'))
# Create a new PCB instance
pcb = PCB.from_directory(GERBER_FOLDER)

layer = pcb.layers[0]
print('bounds: ',layer.bounds[0])