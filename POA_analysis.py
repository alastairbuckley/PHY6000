"""
Compute in plane irradiance over varying time integrations using data from Sheffield Solar testbed.

Jamie Taylor
2019-11-05
Modified A Buckley  
2020-07-02
"""

from datetime import datetime
import pandas as pd
import numpy as np
import pvlib
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

def load_testbed_data(filename):
    """Load pyranometer data from a CSV file."""
    # Use the `with open(...) as ...` syntax (context manager) to ensure files are closed on error
    with open(filename) as fid:
        # Load the CSV file, ensuring the dateandtime column is parsed as a timestamp
        data = pd.read_csv(fid, parse_dates=["dateandtime"])
    # Use the col_mapper dictionary to rename cols
    col_mapper = {"dateandtime": "timestamp", "GHI": "ghi", "DHI": "dhi"}
    data.rename(columns=col_mapper, inplace=True)
    # Set the timestamp as the index of the dataframe
    data.set_index("timestamp", inplace=True)
    # Tell pandas our timestamps are UTC
    data = data.tz_localize(tz="UTC")
    return data

def simulate_eai(start, end, lat, lon, freq="1min"):
    """Simulate EAI for a given time range, location and frequency."""
    # Create a DatetimeIndex of minutely timestamps
    times = pd.date_range(start=start, end=end, freq=freq, tz="UTC")
    # Create a Location object
    loc = pvlib.location.Location(lat, lon, tz="UTC", altitude=130, name="Hicks Bulding Lower Roof")
    # Compute the solar position for the times
    solpos = loc.get_solarposition(times)
    # Simulate EAI for the times (not corrected for location)
    eai_global = pvlib.irradiance.get_extra_radiation(times)
    # Correct for location
    eai = eai_global * np.cos(np.radians(solpos["apparent_zenith"]))
    eai[eai < 0] = 0
    # Convert EAI to a Dataframe with named column (helpful later)
    eai = pd.DataFrame(eai, columns=["eai"])
    eai_global = pd.DataFrame(eai_global, columns=["eai_global"])
    eai = eai.merge(eai_global, left_index=True, right_index=True)
    return eai, solpos

def produce_plots2(erbs, irr, kt, inplane):
    """Produce some nice plots and save them to disk."""
    # Create a new figure
    fig = plt.figure()
    ax = fig.add_subplot()
    # Add title
    fig.suptitle("Modelled vs actual diffuse fraction")
    ## Plot kd_erbs vs kd
    actual_kd = irr["dhi"] / irr["ghi"]
    modelled_kd = erbs["dhi"] / irr["ghi"]
    plt.scatter(actual_kd, modelled_kd, edgecolor='', alpha=0.3)
    # Label the axes
    ax.set_xlabel('Actual kd')
    ax.set_ylabel('Modelled kd')
    ## Plot GTI and GHI
    # Create a new figure
    fig = plt.figure()
    # Add title
    fig.suptitle("GTI vs GHI")
    # Plot GHI
    ax = irr["ghi"].plot(label="GHI")
    # Plot GTI
    inplane["poa_global"].plot(ax=ax, label="GTI")
    # Label the axes
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Irradiance (W/m^2)')
    # Show legend entries
    ax.legend()
    ## Plot GTI vs GHI
    # Create a new figure
    fig = plt.figure()
    ax = fig.add_subplot()
    # Add title
    fig.suptitle("GTI vs GHI")
    # Plot
    plt.scatter(irr["ghi"], inplane["poa_global"], edgecolor='', alpha=0.3)
    ax.set_xlabel('GHI (W/m2)')
    ax.set_ylabel('GTI (W/m2)')

def main(testbed_data_file, lat, lon, orientation, tilt):
    """Run from command line."""
    # Load the pyranometer data from CSV
    irr = load_testbed_data(testbed_data_file)
    # Determine the start/end date based on the pyran data just loaded
    start = irr.index[0]
    end = irr.index[-1]
    # Simulate the minutely EAI for the same period
    eai, solpos = simulate_eai(start, end, lat, lon)
    # Merge the irr, eai and solpos df's so only indices in both are kept
    irr_ = irr.merge(solpos, left_index=True, right_index=True).merge(eai, left_index=True, right_index=True)
    # Calculate kt and then set an INF kt values (caused by dividing by 0) to NaN
    kt = irr_["ghi"] / irr_["eai"]
    kt[kt == np.inf] = np.nan
    # Set any kt values where the EAI is less than 10 W/m^2 to NaN (avoid sunrise/sunset issues)
    kt[irr_["eai"] < 10] = np.nan    
    # Use the Erbs model to estimate diffuse fraction
    erbs = pvlib.irradiance.erbs(irr_["ghi"], irr_["zenith"], irr_.index)
    # Transpose to the inclined plane
    inplane = pvlib.irradiance.get_total_irradiance(tilt, orientation, irr_["zenith"], irr_["azimuth"], erbs["dni"], irr_["ghi"], erbs["dhi"], irr_["eai_global"], surface_type="urban",   model="haydavies")
    # Make some plots...
    produce_plots2(erbs, irr_, kt, inplane)
    plt.show()
    # Resample to hourly (or daily if change to "d", weeekly, monthly etc..) by averaging
    inplane_d = inplane.resample("d", label="left").mean()
    erbs_d = erbs.resample("d", label="left").mean()
    kt_d = kt.resample("d", label="left").mean()
    irr_d = irr_.resample("d", label="left").mean()
    produce_plots2(erbs_d, irr_d, kt_d, inplane_d)
    plt.show()

if __name__ == "__main__":
    #### CONFIG / INPUTS #####
    testbed_data_file = "ss_testbed_irrad_2012.csv"
    lat = 53.23
    lon = -1.15
    ori = 225
    tilt = 35
    ##########################
    main(testbed_data_file, lat, lon, ori, tilt)
