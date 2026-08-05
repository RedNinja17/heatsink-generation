# Imports
import os, h5py, numpy as np, phi.torch.flow as phi

# Variables
num_samples = 10000 # Number of SDF heatsinks to create
grid_shape = (64, 64, 64)
file_path = "sdf_sample.h5"

# Functions
def generateHeatsink(resolution=(64, 64, 64)):
    style = np.random.choice(["plate", "pin"])
    
    if style == "plate":
        num_fins = np.random.randint(4, 10)
        return generatePlate(resolution, num_fins)
    else:
        density = np.random.randint(3, 7)
        return generatePin(resolution, density)

def generatePlate(resolution=(64, 64, 64), num_fins=6):
    x = np.linspace(-1, 1, resolution[0])
    y = np.linspace(-1, 1, resolution[1])
    z = np.linspace(0, 1, resolution[2])
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    base_mask = Z < 0.1
    fin_pattern = np.sin(num_fins * np.pi * X)
    fin_mask = (fin_pattern > 0) & (Z < 0.9)
    solid_mask = fin_mask | base_mask
    return np.where(solid_mask, -0.1, 0.1).astype(np.float32)

def generatePin(resolution=(64, 64, 64), fin_density=5):
    x = np.linspace(-1, 1, resolution[0])
    y = np.linspace(-1, 1, resolution[1])
    z = np.linspace(0, 1, resolution[2])
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
    
    x_pattern = np.sin(fin_density * np.pi * X) > 0.2
    y_pattern = np.sin(fin_density * np.pi * Y) > 0.2
    
    base_mask = Z < 0.1
    pin_mask = x_pattern & y_pattern & (Z < 0.85)
    solid_mask = pin_mask | base_mask
    return np.where(solid_mask, -0.1, 0.1).astype(np.float32)

def runSim(sdf_grid, steps=200):
    res = phi.SpatialCoord(x=64, y=64, z=64)
    bounds = phi.Box(x=1, y=1, z=1)
    vel_extrap = phi.extrapolation.combine_sides(
        x=phi.extrapolation.BOUNDARY,
        y=phi.extrapolation.BOUNDARY,
        z=(phi.math.stack([0, 0, 1.0], phi.spatial('vector')), phi.extrapolation.ZERO)
    )
    obstacle = phi.CenteredGrid(sdf_grid < 0, phi.extrapolation.ZERO, bounds)
    velocity = phi.StaggeredGrid(0, extrapolation=vel_extrap, bounds=bounds, resolution=res)
    temperature= phi.CenteredGrid(20.0,extrapolation=phi.extrapolation.ZERO, bounds=bounds, resolution=res)
    
    for _ in range(steps):
        temperature = phi.advect.semi_lagrangian(temperature, velocity, dt=0.01)
        temperature = phi.diffuse.explicit(temperature, diffusivity=0.02, dt=0.01)
        temperature = phi.math.where(obstacle, 100.0, temperature)
        velocity, pressure = phi.fluid.make_incompressible(velocity, obstacle=obstacle)
    
    return pressure, temperature

def generatePressure(pressure_grid):
    p_inlet = phi.math.mean(pressure_grid.values[:, :, 1])
    p_outlet = phi.math.mean(pressure_grid.values[:, :, -2])
    
    pressure_drop = float(p_inlet - p_outlet)
    return np.array([pressure_drop], dtype=np.float32)

def generateThermal(temperature_grid):
    avg_outlet_temp = float(phi.math.mean(temperature_grid.values[:, :, -1]))
    return np.array([avg_outlet_temp], dtype=np.float32)

# RUNTIME
with h5py.File(file_path, "a") as f:
    if "sdfs" not in f: # new data set
        sdf_ds = f.create_dataset(
            "sdfs",
            shape=(num_samples, 1, *grid_shape),
            dtype="float32",
            chunks=(32, 1, *grid_shape),
            compression="gzip"
        )
        pressure_ds = f.create_dataset("pressure_drop", shape=(num_samples, 1), dtype="float32")
        thermal_ds = f.create_dataset("thermal_diss", shape=(num_samples, 1), dtype="float32")
        f.attrs["completed_count"] = 0
    else:
        sdf_ds = f["sdfs"]
        pressure_ds = f["pressure_drop"]
        thermal_ds = f["thermal_diss"]
        
    current_count = f.attrs.get("completed_count", 0)
    
    if current_count >= num_samples:
        print(f"Complete!")
    else:
        remaining = num_samples - current_count
        print(f"Found {current_count} samples.")
        for i in range(current_count, num_samples):
            sdf = generateHeatsink(resolution=(64, 64, 64))
            pressure, thermal = runSim(sdf, steps=200)
            
            sim_pressure = generatePressure(pressure)
            sim_thermal = generateThermal(thermal)
            
            sdf_ds[i] = np.expand_dims(sdf, axis=0)
            pressure_ds[i] = sim_pressure
            thermal_ds[i] = sim_thermal
            
            f.attrs["completed_count"] = i + 1
            
            if( i + 1) % 500 == 0 or (i + 1) == num_samples:
                print(f"Progress: {i + 1}/{num_samples} samples.")  
print("Done.")