## Constants for the ZBP model

#Gravity
g = 9.81   # m/s

#Dry air
cp  = 1005.7 # J/K/kg
Rd  = 287.04 # J/K/kg

#Water vapor
cpv = 1870.0 # J/K/kg
Rv  = 461.5  # J/K/kg

#Liquid water
cpl = 4190.0 # J/K/kg

#Solid water
cpi = 2106.0 # J/K/kg


#Reference values

#Freezing temperature
T0 = 273.15 # K

#Temperature at which all condensate is ice
T_ice = 233.15 # K

#reference pressures
p00 = 100000  # Pa
e0  = 611.2   # Pa   This is the saturation vapor pressure at T0


#Latent heats at reference Temperature
Lv0 = 2501000.0     # J/kg
Ls0 = 2834000.0     # J/kg

# Derived thermodynamic constants
# Changing these will make the thermodynamics inconsistent
cv  = cp-Rd 
cvv = cpv-Rv 
eps = Rd/Rv 

#### Spectrual plume constants

P0 = 3 ## mm day-1
E = 0.15