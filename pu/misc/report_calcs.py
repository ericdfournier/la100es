#%% Package Imports

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

#%% Read Single Family Data

sf_data_dir = '/Users/edf/repos/la100es-panel-upgrades/data/outputs/sf/'
sf_data = pd.read_pickle(sf_data_dir + 'la100es_sf_electricity_service_panel_capacity_analysis.pk')

#%% SF Average Size

sf_data[['dac_status','building_sqft']].groupby('dac_status').agg(['mean','count'])

#%% Average Vintage Year

sf_data[['dac_status','year_built']].groupby('dac_status').agg(['mean','count'])

#%% SF Bin Ranged Averages

sf_data.groupby(pd.cut(sf_data['year_built'], pd.to_datetime(np.arange(1850, 2022, 10), format = '%Y'))).agg(['count','mean'])['building_sqft'].to_csv('/Users/edf/Desktop/scratch1.csv')

#%% SF Counts

sf_data.groupby('dac_status')['permitted_panel_upgrade'].agg('sum') / sf_data.groupby('dac_status')['apn'].agg('count')
sf_data.groupby('dac_status')['inferred_panel_upgrade'].agg('sum') / sf_data.groupby('dac_status')['apn'].agg('count')

#%% Read Multi_Family Data

mf_data_dir = '/Users/edf/repos/la100es-panel-upgrades/data/outputs/mf/'
mf_data = pd.read_pickle(mf_data_dir + 'la100es_mf_electricity_service_panel_capacity_analysis.pk')

#%% MF Average Size

mf_data[['dac_status','building_sqft','units']].groupby('dac_status').agg(['mean','count'])

#%% MF Bin Ranged Averages

mf_data.groupby(pd.cut(mf_data['year_built'], pd.to_datetime(np.arange(1850, 2022, 10), format = '%Y'))).agg(['count','mean'])['building_sqft'].to_csv('/Users/edf/Desktop/scratch1.csv')
mf_data.groupby(pd.cut(mf_data['year_built'], pd.to_datetime(np.arange(1850, 2022, 10), format = '%Y'))).agg(['mean'])['units'].to_csv('/Users/edf/Desktop/scratch2.csv')
mf_data.groupby(pd.cut(mf_data['year_built'], pd.to_datetime(np.arange(1850, 2022, 10), format = '%Y'))).agg(['mean'])['avg_unit_sqft'].to_csv('/Users/edf/Desktop/scratch3.csv')
mf_data.groupby(['dac_status', 'panel_size_existing'])['panel_size_existing'].agg('count').to_csv('/Users/edf/Desktop/scratch4.csv')

# %% SF Stats Data

sf_data['building_sqft_log10'] = np.log10(sf_data['building_sqft'])
sf_data['existing_amps_per_sqft_log10'] = np.log10(sf_data['panel_size_existing'] / sf_data['building_sqft'])

non_dacs_ind = sf_data['dac_status'] == 'Non-DAC'
dacs_ind = sf_data['dac_status'] == 'DAC'

non_dacs = sf_data.loc[non_dacs_ind,:]
dacs = sf_data.loc[dacs_ind,:]

#%% SF Stats

upgrade_ind = dacs['permitted_panel_upgrade'] == True
non_upgrade_ind = (dacs['permitted_panel_upgrade'] == False) & ~(np.isinf(dacs['existing_amps_per_sqft_log10']))

print(dacs.loc[upgrade_ind, 'existing_amps_per_sqft_log10'].mean())
print(dacs.loc[non_upgrade_ind, 'existing_amps_per_sqft_log10'].mean())

upgrade_ind = non_dacs['permitted_panel_upgrade'] == True
non_upgrade_ind = (non_dacs['permitted_panel_upgrade'] == False) & ~(np.isinf(non_dacs['existing_amps_per_sqft_log10']))

print(non_dacs.loc[upgrade_ind, 'existing_amps_per_sqft_log10'].mean())
print(non_dacs.loc[non_upgrade_ind, 'existing_amps_per_sqft_log10'].mean())

#%% DAC Case

upgrade_ind = dacs['permitted_panel_upgrade'] == True
x = dacs.loc[upgrade_ind, 'building_sqft_log10']
y = dacs.loc[upgrade_ind, 'existing_amps_per_sqft_log10']

a, b = np.polyfit(x, y, 1)

non_upgrade_ind = dacs['permitted_panel_upgrade'] == False
x_hat = dacs.loc[non_upgrade_ind, 'building_sqft_log10']
z = dacs.loc[non_upgrade_ind, 'building_sqft']

def dac_fn(a, b, x_hat, z):

    y_hat = (a * x_hat) + b
    out = (np.power(10, y_hat) * z)

    return out

out = dac_fn(a, b, x_hat, z)

dacs.loc[non_upgrade_ind,'panel_size_predicted_future_upgrade'] = out
deficient_ind = dacs.loc[non_upgrade_ind,'panel_size_predicted_future_upgrade'] > dacs.loc[non_upgrade_ind, 'panel_size_existing']
upgrade_ratio = deficient_ind.sum() / dacs.shape[0]

#%% Non-DAC Case

upgrade_ind = non_dacs['permitted_panel_upgrade'] == True
x = non_dacs.loc[upgrade_ind, 'building_sqft_log10']
y = non_dacs.loc[upgrade_ind, 'existing_amps_per_sqft_log10']

a, b = np.polyfit(x, y, 1)

non_upgrade_ind = non_dacs['permitted_panel_upgrade'] == False
x_hat = non_dacs.loc[non_upgrade_ind, 'building_sqft_log10']
z = non_dacs.loc[non_upgrade_ind, 'building_sqft']

def non_dac_fn(a, b, x_hat, z):

    y_hat = (a * x_hat) + b
    out = (np.power(10, y_hat) * z)

    return out

out = non_dac_fn(a, b, x_hat, z)

non_dacs.loc[non_upgrade_ind,'panel_size_predicted_future_upgrade'] = out
deficient_ind = non_dacs.loc[non_upgrade_ind,'panel_size_predicted_future_upgrade'] > non_dacs.loc[non_upgrade_ind, 'panel_size_existing']
upgrade_ratio = deficient_ind.sum() / non_dacs.shape[0]

#%% Compute MF Permit Stats

dac = sf_data.loc[mf_data['dac_status'] == 'DAC']
non_dac = sf_data.loc[mf_data['dac_status'] == 'Non-DAC']

dac['permitted_panel_upgrade'].sum() / dac.shape[0]
non_dac['permitted_panel_upgrade'].sum() / non_dac.shape[0]

dac['inferred_panel_upgrade'].sum() / dac.shape[0]
non_dac['inferred_panel_upgrade'].sum() / non_dac.shape[0]

#%% MF Stats Data

mf_data['avg_unit_sqft_log10'] = np.log10(mf_data['avg_unit_sqft'])
mf_data['existing_amps_per_sqft_log10'] = np.log10(mf_data['panel_size_existing'] / mf_data['avg_unit_sqft'])

non_dacs_ind = mf_data['dac_status'] == 'Non-DAC'
dacs_ind = mf_data['dac_status'] == 'DAC'

non_dacs = mf_data.loc[non_dacs_ind,:]
dacs = mf_data.loc[dacs_ind,:]

#%% MF Stats

upgrade_ind = dacs['permitted_panel_upgrade'] == True
non_upgrade_ind = (dacs['permitted_panel_upgrade'] == False) & ~(np.isinf(dacs['existing_amps_per_sqft_log10']))

print(dacs.loc[upgrade_ind, 'existing_amps_per_sqft_log10'].mean())
print(dacs.loc[non_upgrade_ind, 'existing_amps_per_sqft_log10'].mean())

upgrade_ind = non_dacs['permitted_panel_upgrade'] == True
non_upgrade_ind = (non_dacs['permitted_panel_upgrade'] == False) & ~(np.isinf(non_dacs['existing_amps_per_sqft_log10']))

print(non_dacs.loc[upgrade_ind, 'existing_amps_per_sqft_log10'].mean())
print(non_dacs.loc[non_upgrade_ind, 'existing_amps_per_sqft_log10'].mean())

#%% DAC Case

upgrade_ind = dacs['permitted_panel_upgrade'] == True
x = dacs.loc[upgrade_ind, 'avg_unit_sqft_log10']
y = dacs.loc[upgrade_ind, 'existing_amps_per_sqft_log10']

ix = np.isfinite(x)
iy = np.isfinite(y)

a, b = np.polyfit(x.loc[ix], y.loc[iy], 1)

#%% Non-DAC Case

upgrade_ind = non_dacs['permitted_panel_upgrade'] == True
x = non_dacs.loc[upgrade_ind, 'avg_unit_sqft_log10']
y = non_dacs.loc[upgrade_ind, 'existing_amps_per_sqft_log10']

ix = np.isfinite(x)
iy = np.isfinite(y)

a, b = np.polyfit(x.loc[ix], y.loc[iy], 1)

#%% Compute MF Permit Stats
dac = mf_data.loc[mf_data['dac_status'] == 'DAC']
non_dac = mf_data.loc[mf_data['dac_status'] == 'Non-DAC']

dac['permitted_panel_upgrade'].sum() / dac.shape[0]
non_dac['permitted_panel_upgrade'].sum() / non_dac.shape[0]

dac['inferred_panel_upgrade'].sum() / dac.shape[0]
non_dac['inferred_panel_upgrade'].sum() / non_dac.shape[0]
