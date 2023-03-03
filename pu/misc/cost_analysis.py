#%% Package Imports

import pandas as pd
import numpy as np
import os

#%% Read Input Data

working_dir = '/Users/edf/gdrive/projects/ladwp_la100_es/data/tech_program/'
filename = 'TECHWorkingDataset_2022-12-02.xlsx'
df = pd.read_excel(working_dir + filename, sheet_name = 'Sheet1')

#%%

df['Total Project Cost ($) Float'] = pd.to_numeric(df['Total Project Cost ($)'], errors = 'coerce')
costs = df.groupby(['Panel Upgrade', 'Product Type'])['Total Project Cost ($) Float'].agg(['mean'])
p1 = costs.loc(axis=0)[True,:].index.get_level_values(1)
p2 = costs.loc(axis=0)[False,:].index.get_level_values(1)
shared = p1.intersection(p2)
panel_upgrade_cost_deltas = costs.loc(axis=0)[True, shared].values - costs.loc(axis=0)[False,shared].values
