#%% Package Imports

import pandas as pd
import geopandas as gpd

#%% Function Merge Parcels with CES Data

def MergeCES(sf_buildings, ces4):
    '''Function to merge the sf permit data set and the ces
    spatial dataset.'''

    sf_buildings_ces = pd.merge(sf_buildings, ces4[['tract', 'ciscorep']], left_on = 'census_tract', right_on = 'tract')
    sf_buildings_ces.set_index('tract', inplace = True)

    return sf_buildings_ces

#%% Function to Assign DAC Status

def AssignDACStatus(sf_buildings_ces):
    '''Function to assign DAC status based upon ces composite
    percentile score threshold.'''

    sf_buildings_ces['dac_status'] = 'Non-DAC'
    ind = sf_buildings_ces['ciscorep'] >= 75.0
    sf_buildings_ces.loc[ind, 'dac_status'] = 'DAC'

    return sf_buildings_ces