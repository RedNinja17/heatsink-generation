# Author: trexhaydor
# Description: Basic script to convert SDF geometries into .stl format

from sdf import * 

base_length = 60     # X dimension
base_width = 40      # Y dimension
base_height = 5      # Z thickness

fin_height = 25
fin_width = 2
fin_spacing = 5
fin_length = 35

base = box(
    base_length,
    base_width,
    base_height
)


# Center the base around origin
base = base.translate(Z * (base_height / 2))


fins = []

num_fins = int(base_length / fin_spacing)

for i in range(num_fins):

    x = (
        -base_length / 2
        + i * fin_spacing
    )

    fin = box(
        fin_width,
        fin_length,
        fin_height
    )

    # Move fin above base
    fin = fin.translate(
        X * x
        + Z * (base_height + fin_height / 2)
    )

    fins.append(fin)

heatsink = base

for fin in fins:
    heatsink = heatsink | fin


heatsink.save(
    "heatsink_example_1.stl",
    samples=2**18
)