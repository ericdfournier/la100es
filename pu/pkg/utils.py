#%% Package Imports

import pandas as pd
import geopandas as gpd
import numpy as np

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

def AsBuiltPanelRatingsDiagnostics(sf_buildings_ces):

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

# %% Generate Change Statistics 

def ChangeStatistics(sf_buildings_ces, ces4):
    '''Function to compute relevant statistics about the rate and location of changes
    in panel sizes from as-built to existing condition.'''

    as_built_mean = sf_buildings_ces.groupby('census_tract')['panel_size_as_built'].agg(['mean'])
    as_built_mean.columns = ['mean_sf_panel_size_as_built']

    sf_property_count = sf_buildings_ces.groupby('census_tract')['lot_sqft'].agg(['count'])
    sf_property_count.columns = ['sf_homes_count']

    existing_mean = sf_buildings_ces.groupby('census_tract')['panel_size_existing'].agg(['mean'])
    existing_mean.columns = ['mean_sf_panel_size_existing']

    upgrades_count = sf_buildings_ces.groupby('census_tract')['panel_upgrade'].agg('sum')
    upgrades_count.name = 'upgrade_count'

    panel_stats = pd.concat([as_built_mean, existing_mean, upgrades_count, sf_property_count], axis = 1)

    panel_stats['upgrade_freq_pct'] = (panel_stats['upgrade_count'] / panel_stats['sf_homes_count']).multiply(100.0)

    panel_stats['upgrade_delta_amps'] = panel_stats['mean_sf_panel_size_existing'] - panel_stats['mean_sf_panel_size_as_built']
    panel_stats['upgrade_delta_pct'] = panel_stats[['mean_sf_panel_size_as_built', 'mean_sf_panel_size_existing']].pct_change(axis = 1).iloc[:,1].multiply(100.0)

    panel_stats_ces = pd.merge(panel_stats, ces4[['tract','ciscorep', 'geom']], left_index = True, right_on = 'tract', how = 'left')

    dac_ind = panel_stats_ces['ciscorep'] >= 75.0
    panel_stats_ces['dac_status'] = 'Non-DAC'
    panel_stats_ces.loc[dac_ind, 'dac_status'] = 'DAC'

    panel_stats_ces = panel_stats_ces.set_index('tract', drop = True)
    panel_stats_ces_geo = gpd.GeoDataFrame(panel_stats_ces, geometry = 'geom')

    return panel_stats_ces_geo

#%% Print Upgrade Stats

def PanelUpgradeDiagnostics(sf_buildings_ces):
    '''Function to print diagnostic information about the number
    and location of permitted and inferred panel upgrades'''

    dac_ind = sf_buildings_ces['dac_status'] == 'DAC'
    non_dac_ind = sf_buildings_ces['dac_status'] == 'Non-DAC'

    dac_sample = sf_buildings_ces.loc[dac_ind,:]
    non_dac_sample = sf_buildings_ces.loc[non_dac_ind,:]

    dac_permitted_panel_stats = dac_sample.groupby(['permitted_panel_upgrade'])['census_tract'].agg('count')
    non_dac_permitted_panel_stats = non_dac_sample.groupby(['permitted_panel_upgrade'])['census_tract'].agg('count')

    dac_inferred_panel_stats = dac_sample.groupby(['inferred_panel_upgrade'])['census_tract'].agg('count')
    non_dac_inferred_panel_stats = non_dac_sample.groupby(['inferred_panel_upgrade'])['census_tract'].agg('count')

    dac_sample['roll_impbaseyear_int'] = dac_sample.loc[:,'roll_impbaseyear'].dt.year
    dac_sample.loc[np.isinf(dac_sample['roll_impbaseyear_int']),'roll_impbaseyear_int'] = np.nan
    dac_imp_year_mean = dac_sample['roll_impbaseyear_int'].mean()
    dac_vintage_year_mean = dac_sample['year_built'].dt.year.mean()

    non_dac_sample['roll_impbaseyear_int'] = non_dac_sample.loc[:,'roll_impbaseyear'].dt.year
    non_dac_sample.loc[np.isinf(non_dac_sample['roll_impbaseyear_int']),'roll_impbaseyear_int'] = np.nan
    non_dac_imp_year_mean = non_dac_sample['roll_impbaseyear_int'].mean()
    non_dac_vintage_year_mean = non_dac_sample['year_built'].dt.year.mean()

    print('DAC Census Tract Upgrade Stats:')

    print('Average Home Vintage Year: {:.0f}'.format(dac_vintage_year_mean))
    print('Average Improvement Year: {:.0f}'.format(dac_imp_year_mean))
    print('Permitted Upgrades: {:.2f}%'.format(dac_permitted_panel_stats.loc[True] / dac_sample.shape[0] * 100))
    print('Inferred Upgrades: {:.2f}%'.format(dac_inferred_panel_stats.loc[True] / dac_sample.shape[0] * 100))
    print('Not Upgraded: {:.2f}%'.format((dac_sample.shape[0] - (dac_inferred_panel_stats.loc[True] + dac_permitted_panel_stats.loc[True])) / dac_sample.shape[0] * 100))

    print('\n')

    print('Non-DAC Census Tract Upgrade Stats:')

    print('Average Home Vintage Year: {:.0f}'.format(non_dac_vintage_year_mean))
    print('Average Improvement Year: {:.0f}'.format(non_dac_imp_year_mean))
    print('Permitted Upgrades: {:.2f}%'.format(non_dac_permitted_panel_stats.loc[True] / non_dac_sample.shape[0] * 100))
    print('Inferred Upgrades: {:.2f}%'.format(non_dac_inferred_panel_stats.loc[True] / non_dac_sample.shape[0] * 100))
    print('Not Upgraded: {:.2f}%'.format((non_dac_sample.shape[0] - (non_dac_inferred_panel_stats.loc[True] + non_dac_permitted_panel_stats.loc[True])) / non_dac_sample.shape[0] * 100))

    return

#%% Print Capacity Stats

def ExistingPanelRatingsDiagnostics(sf_buildings_ces):
    '''Function to print diagnostic information about the rated capacity of 
    existing panels'''

    dac_ind = sf_buildings_ces['dac_status'] == 'DAC'
    non_dac_ind = sf_buildings_ces['dac_status'] == 'Non-DAC'

    dac_sample = sf_buildings_ces.loc[dac_ind,:]
    non_dac_sample = sf_buildings_ces.loc[non_dac_ind,:]

    dac_sample_stats = dac_sample.groupby(['panel_size_existing'])['census_tract'].agg('count')
    non_dac_sample_stats = non_dac_sample.groupby(['panel_size_existing'])['census_tract'].agg('count')

    insufficient = [30.0, 60.0]
    uncertain = [100.0, 125.0, 150.0]
    sufficient = [200.0, 300.0, 400.0, 600.0]

    print('DAC Existing Capacity Stats:')

    print('<100 Amps: {:.2f}%'.format(dac_sample_stats[insufficient].sum() / dac_sample.shape[0] * 100))
    print('>=100 : <200 Amps: {:.2f}%'.format(dac_sample_stats[uncertain].sum() / dac_sample.shape[0] * 100))
    print('>=200 Amps: {:.2f}%'.format(dac_sample_stats[sufficient].sum() / dac_sample.shape[0] * 100))

    print('\n')

    print('Non-DAC Existing Capacity Stats:')

    print('<100 Amps: {:.2f}%'.format(non_dac_sample_stats[insufficient].sum() / non_dac_sample.shape[0] * 100))
    print('>=100 : <200 Amps: {:.2f}%'.format(non_dac_sample_stats[uncertain].sum() / non_dac_sample.shape[0] * 100))
    print('>=200 Amps: {:.2f}%'.format(non_dac_sample_stats[sufficient].sum() / non_dac_sample.shape[0] * 100))

    return

#%% Function to re-order columns of final dataset for export output

def SortColumns(sf_buildings_ces):
    '''Reorder columns in final dataframe in preparation for final
    output dataset export'''

    cols = ['apn',
            'ain',
            'ztrax_rowid',
            'city',
            'census_tract',
            'ciscorep',
            'dac_status',
            'buildings',
            'lot_sqft',
            'year_built',
            'building_sqft',
            'units',
            'bedrooms',
            'bathrooms',
            'county_landuse_description',
            'occupancy_status_stnd_code',
            'usetype',
            'usedescription',
            'heating_system_stnd_code',
            'ac_system_stnd_code',
            'roll_year',
            'roll_landvalue',
            'roll_landbaseyear',
            'roll_impvalue',
            'roll_impbaseyear',
            'permit_type',
            'permit_sub_type',
            'permit_description',
            'panel_related_permit',
            'permit_issue_date',
            'permitted_panel_upgrade',
            'panel_size_as_built',
            'inferred_panel_upgrade',
            'upgrade_time_delta',
            'panel_size_existing',
            'centroid']

    sf_buildings_ces = sf_buildings_ces[cols]

    return sf_buildings_ces
