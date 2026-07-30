from sdf import *
import pyvista as pv
pv.global_theme.allow_empty_mesh = True #Allows empty meshes to be plotted

NAME = "heatsinkmk1"

#SAMPLES = 2**20 
STEP = 0.2

#Base dimensions
LENGTH = 17.0    # mm
WIDTH = 17.0       # mm
THICKNESS = 3.0     # mm

#Fin DimensionsI
FIN_QUANITY = 7
FIN_THICKNESS = 1.2
FIN_HEIGHT = 6.0
FIN_SPACING = (LENGTH - (FIN_QUANITY * FIN_THICKNESS)) / (FIN_QUANITY - 1) #mm


#===================DESIGN BOX===================


f = box((LENGTH, WIDTH, THICKNESS)) #Centered at (0,0,0)

fin = box((FIN_THICKNESS, WIDTH, FIN_HEIGHT)) 

z_offset = THICKNESS / 2 + FIN_HEIGHT / 2 #Offset to place fins on top of base

start_x = -LENGTH / 2 + FIN_THICKNESS / 2  

for i in range(FIN_QUANITY):
    x_offset = start_x+ i * (FIN_THICKNESS + FIN_SPACING) #Offset to place fins along base

    fin_postioned = fin.translate((x_offset, 0, z_offset)) #Translate fin to correct position
    f = f | fin_postioned #Add fin to base


#===================SAVE, READ, & PLOT DESIGN===================#

f.save(NAME + ".stl", STEP, sparse=False) # Used step instead of sample

mesh = pv.read(NAME + ".stl")
p = pv.Plotter()

p.add_mesh(mesh, color="lightgray", show_edges=False)
p.show()
