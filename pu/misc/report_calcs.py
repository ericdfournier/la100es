#%% Package Imports

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

#%% Read Data from File

figure_dir = '/Users/edf/repos/la100es-panel-upgrades/figs/sf/'
data_dir = '/Users/edf/repos/la100es-panel-upgrades/data/outputs/sf/'
data = pd.read_pickle(data_dir + 'la100es_sf_electricity_service_panel_capacity_analysis_2023-02-28.pk')

#%% Average Size

data[['dac_status','building_sqft']].groupby('dac_status').agg(['mean','count'])

#%% Average Vintage Year

data[['dac_status','year_built']].groupby('dac_status').agg(['mean','count'])

#%% Bin Ranged Averages

data.groupby(pd.cut(data['year_built'], pd.to_datetime(np.arange(1830, 2022, 10), format = '%Y'))).agg('mean')['building_sqft']
data.groupby(pd.cut(data['year_built'], pd.to_datetime(np.arange(1830, 2022, 10), format = '%Y'))).agg('count')['building_sqft']
