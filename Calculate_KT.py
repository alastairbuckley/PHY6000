#!/usr/bin/python3
"""
Demo script to calculate KT time series.
- Alastair Buckley <alastair.buckley@sheffield.ac.uk>
- First Authored: 2020-07-01
"""

from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import pytz
import pvlib
import numpy as np

def main():
    """Run the script."""
    ##### INPUTS #####  make sure these are consistent with the Global horizontal observation data that you are loading!
    start = datetime(2014, 1, 1, 0, 0, tzinfo=pytz.UTC)
    end = datetime(2014, 12, 31, 0, 0, tzinfo=pytz.UTC)
    #For sheffield - but change if you change locations!
    latitude = 53.381
    longitude = -1.486
    #Air mass depends on altitude!
    altitude = 100
    tz = "UTC"
    filetoread = "sheffield2014global.csv"
    df = pd.read_csv(filetoread, index_col=0, parse_dates=True)
    df = df.tz_localize('UTC')
    filename = "pv_test_data.csv"
    ##################
        
    times = pd.date_range(start = start, end = end, tz = tz, freq = "min")
    loc = pvlib.location.Location(latitude=latitude, longitude=longitude, altitude=altitude)
    
    #solpos calculates the position of the sun in the sky. It returns a set of angles that you should investigate in detail.
    solpos = loc.get_solarposition(times, temperature=12)
    #etr is the extraterrestrial solar radiation - but it is not corrected to the horizontal plane at a particular latitude and longitude. to do this correction we need to know the zenith angle (which is contained within the solpos method).
    etr = pvlib.irradiance.get_extra_radiation(times)
    zen = solpos["apparent_zenith"]
    etr_hor = np.cos(np.radians(zen)) * etr
    #etr in the horizontal plane is calculated for all times at minutely resolution. when the sun is behind the earth the value is negative (which makes no sense) so we set it to zero.
    etr_hor[etr_hor < 0] = 0
    #we can then resample the minutely time series to hourly by taking the hourly average power.
    etr_h_hor = etr_hor.resample("1h", label="left").mean()
        
    ax = etr_h_hor.plot()
    #correct by x1000 to get the same units of both the etr and Global data.
    df.global_h = df.global_h * 1000
    df.global_h.plot(ax=ax)
    plt.show()
    kt = df.global_h / etr_h_hor
    #very high values of KT (due to bad measurements) are filtered out.
    kt[kt > 1.3] = np.nan
    kt.plot()
    plt.show()
    plt.hist(kt, bins=100)
    plt.show()

if __name__ == "__main__":
    main()
