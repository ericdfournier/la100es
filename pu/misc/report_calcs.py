#%% Package Imports

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

#%% Read Single Family Data

sf_data_dir = '/Users/edf/repos/la100es-panel-upgrades/data/outputs/sf/'
sf_data = pd.read_pickle(sf_data_dir + 'la100es_sf_electricity_service_panel_capacity_analysis.pk')

#%% Read Multi_Family Data

mf_data_dir = '/Users/edf/repos/la100es-panel-upgrades/data/outputs/mf/'
mf_data = pd.read_pickle(mf_data_dir + 'la100es_mf_electricity_service_panel_capacity_analysis.pk')

#%% SF Average Size

sf_data[['dac_status','building_sqft']].groupby('dac_status').agg(['mean','count'])

#%% MF Average Size

mf_data[['dac_status','building_sqft','units']].groupby('dac_status').agg(['mean','count'])

#%% Average Vintage Year

sf_data[['dac_status','year_built']].groupby('dac_status').agg(['mean','count'])

#%% SF Bin Ranged Averages

sf_data.groupby(pd.cut(sf_data['year_built'], pd.to_datetime(np.arange(1830, 2022, 10), format = '%Y'))).agg('mean')['building_sqft']

#%% MF Bin Ranged Averages

mf_data.groupby(pd.cut(mf_data['year_built'], pd.to_datetime(np.arange(1850, 2022, 10), format = '%Y'))).agg(['count','mean'])['building_sqft'].to_csv('/Users/edf/Desktop/scratch.csv')
#%%
mf_data.groupby(pd.cut(mf_data['year_built'], pd.to_datetime(np.arange(1850, 2022, 10), format = '%Y'))).agg(['mean'])['units'].to_csv('/Users/edf/Desktop/scratch.csv')

#%%

test = sf_data.groupby(['dac_status', 'panel_size_existing'])['panel_size_existing'].agg('count')
test.to_csv('/Users/edf/Desktop/test.csv')

# %%
