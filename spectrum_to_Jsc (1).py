"""
Demo script to interpolate spectral data.
- Alastair Buckley <alastair.buckley@sheffield.ac.uk>
- First Authored: 2020-06-24
"""

from datetime import datetime
import pandas as pd
import numpy as np
import scipy
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

def interpolate_wl_spectrum(start_wl, end_wl, step_wl, input_spectrum):
    """
    Takes a csv spectrum file (input spectrum) with one row header and two columns (columns are "wavelength" in nm and "power") and interpolates with fixed "step_wl"
    wl stands for wavelength. x is wavelength axis and y is power axis. 
    a cubic spline is chosen
    The interpolation function operates on independent x and y 1D arrays so the first thing to do is split the data frame into these arrays by deleting the other column from the data frame. They then need converting to a 1D array using ".ravel()"
    Then the new x variable can be defined as int_x by taking a equal step from the start wavelength "start_wl" to the end wavelength "end_wl". 
    A function "f" is fitted using the spline method for all x and y.
    Then a new set of y (int_y) are created using the new x values (int_x) and the function "f"
    Finally the new x and y values (int_x, int_y) are added to a new dataframe "df"
    I have no idea why "axis=-1" is needed!
    """
    #converting to matrix
    conv_spectrum = input_spectrum.values
    #converting matrix columns to 1d array
    x = np.delete(conv_spectrum,[1],axis=1)
    y = np.delete(conv_spectrum,[0],axis=1)
    #converting to 1D array
    x = x.ravel()
    y = y.ravel()
    int_x = np.linspace(start_wl, end_wl, (end_wl-start_wl+1))
    f = interp1d(x, y, kind='cubic')
    int_y = f(int_x)
    df = pd.DataFrame(np.stack((int_x, int_y), axis=-1))
    return df
    

def main():
    AM15_spectrum = pd.read_csv('AM15_G_raw.csv', sep = ',' , header = 1)
    eqe_spectrum = pd.read_csv('eqe_spectrum.csv', sep = ',' , header = 1)
    
    start_wl = 300
    end_wl = 2000
    step_wl = end_wl-start_wl
    
    #following code interpolates the AM1.5 spectrum to 1nm spacing. for some reason i need to add another index "A". but i don't really know why!
    AM15int = interpolate_wl_spectrum(start_wl=start_wl, end_wl=end_wl, step_wl=step_wl, input_spectrum = AM15_spectrum)
    AM15int['A'] = list(range(len(AM15int.index)))
    AM15int.plot.scatter(x=0, y=1)
    plt.show()
    
    #following code interpolates EQE spectrum - exactly as with AM1.5
    EQEint = interpolate_wl_spectrum(start_wl=start_wl, end_wl=end_wl, step_wl=step_wl, input_spectrum = eqe_spectrum)
    EQEint['A'] = list(range(len(EQEint)))
    EQEint.plot.scatter(x=0, y=1)
    plt.show()
    
    #it'd be easy enough to now convert AM1.5 to photon's per nm using a factor that is dependent on the wavelength x (see the notes!) and then multiply with the EQE spectrum and then integrate the dataframe using a sum function.
    
    
if __name__ == "__main__" :
    main()