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

#%% Print As-Built Diagnostic Stats

def AsBuiltDiagnostics(sf_buldings_ces):

    dac_ind = sf_buildings_ces['dac_status'] == 'DAC'
    non_dac_ind = sf_buildings_ces['dac_status'] == 'Non-DAC'

    dac_sample = sf_buildings_ces.loc[dac_ind,:]
    non_dac_sample = sf_buildings_ces.loc[non_dac_ind,:]

    print('DAC As-Built Capacity Stats:')
    total = dac_sample['apn'].count()
    print('<100 Amps: {:.2f}%'.format(dac_sample.loc[dac_sample['panel_size_as_built'] < 100,'apn'].count() / total * 100.0))
    print('>=100 & <200 Amps: {:.2f}%'.format(dac_sample.loc[(dac_sample['panel_size_as_built'] >= 100) & (dac_sample['panel_size_as_built'] < 200),'apn'].count() / total * 100.0))
    print('>=200 Amp: {:.2f}%'.format(dac_sample.loc[dac_sample['panel_size_as_built'] >= 200,'apn'].count() / total * 100.0))

    print('\n')

    print('Non-DAC As-Built Capacity Stats:')
    total = non_dac_sample['apn'].count()
    print('<100 Amps: {:.2f}%'.format(non_dac_sample.loc[non_dac_sample['panel_size_as_built'] < 100,'apn'].count() / total * 100.0))
    print('>=100 & <200 Amps: {:.2f}%'.format(non_dac_sample.loc[(non_dac_sample['panel_size_as_built'] >= 100) & (non_dac_sample['panel_size_as_built'] < 200),'apn'].count() / total * 100.0))
    print('>=200 Amps: {:.2f}%'.format(non_dac_sample.loc[non_dac_sample['panel_size_as_built'] >= 200,'apn'].count() / total * 100.0))

    return

#%% Compute Time Difference Between Construction Date and Upgrade Date

def UpgradeTimeDelta(sf_buildings_ces):
    '''Function to compute the length of time that elapsed from the building's 
    construction vintage year and the year of any permitted panel upgrade'''

    upgrade_time_delta = pd.to_numeric(sf_buildings_ces.loc[:,'permit_issue_date'].dt.year - sf_buildings_ces.loc[:,'year_built'].dt.year)
    neg = upgrade_time_delta < 0
    upgrade_time_delta.loc[neg] = 0
    sf_buildings_ces['upgrade_time_delta'] = np.nan
    sf_buildings_ces.loc[upgrade_time_delta.index.get_level_values(0),'upgrade_time_delta'] = upgrade_time_delta.values

    return sf_buildings_ces