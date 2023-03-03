#%% Package Imports

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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

# %% SF Plot

sf_data['building_sqft_log10'] = np.log10(sf_data['building_sqft'])
sf_data['existing_amps_per_sqft_log10'] = np.log10(sf_data['panel_size_existing'] / sf_data['building_sqft'])

non_dacs_ind = sf_data['dac_status'] == 'Non-DAC'
dacs_ind = sf_data['dac_status'] == 'DAC'

non_dacs = sf_data.loc[non_dacs_ind,:]
dacs = sf_data.loc[dacs_ind,:]

#%% Generate Plot
bw = 0.75

fig1 = sns.jointplot(data = non_dacs,
    x = 'building_sqft_log10',
    y = 'existing_amps_per_sqft_log10',
    hue = 'permitted_panel_upgrade',
    palette = ['lightblue', 'tab:blue'],
    kind = 'kde',
    bw_method = bw)

upgrade_ind = non_dacs['permitted_panel_upgrade'] == True
non_upgrade_ind = non_dacs['permitted_panel_upgrade'] == False


fig1.ax_joint.axhline(non_dacs.loc[upgrade_ind, 'existing_amps_per_sqft_log10'].mean(), color = 'tab:blue', linestyle = ':')
fig1.ax_joint.axvline(non_dacs.loc[upgrade_ind, 'building_sqft_log10'].mean(), color = 'tab:blue', linestyle = ':')

fig1.ax_joint.axhline(non_dacs.loc[non_upgrade_ind, 'existing_amps_per_sqft_log10'].mean(), color = 'lightblue', linestyle = ':')
fig1.ax_joint.axvline(non_dacs.loc[non_upgrade_ind, 'building_sqft_log10'].mean(), color = 'lightblue', linestyle = ':')

ylim = (-2.0, 0.0)
yticks = [-2, -1, 0]
ytick_labels = ['0.01', '0.1', '1.0']

xlim = (2.0, 4.0)
xticks = [2, 3, 4]
xtick_labels = ['100', '1,000', '10,000']

fig1.ax_marg_x.set_xlim(xlim)
fig1.ax_marg_x.set_xticks(xticks)
fig1.ax_marg_x.set_xticklabels(xtick_labels)
fig1.ax_joint.set_xlabel('Property Size\n [$ft^2$]')

fig1.ax_marg_y.set_ylim(ylim)
fig1.ax_marg_y.set_yticks(yticks)
fig1.ax_marg_y.set_yticklabels(ytick_labels)
fig1.ax_joint.set_ylabel('Rated Panel Capacity\n [$Amps / ft^2$]')

fig2 = sns.jointplot(data = dacs,
    x = 'building_sqft_log10',
    y = 'existing_amps_per_sqft_log10',
    hue = 'permitted_panel_upgrade',
    palette = ['navajowhite', 'tab:orange'],
    kind = 'kde',
    bw_method = bw)

upgrade_ind = dacs['permitted_panel_upgrade'] == True
non_upgrade_ind = (dacs['permitted_panel_upgrade'] == False) & ~(np.isinf(dacs['existing_amps_per_sqft_log10']))

fig2.ax_joint.axhline(dacs.loc[upgrade_ind, 'existing_amps_per_sqft_log10'].mean(), color = 'tab:orange', linestyle = ':')
fig2.ax_joint.axvline(dacs.loc[upgrade_ind, 'building_sqft_log10'].mean(), color = 'tab:orange', linestyle = ':')

fig2.ax_joint.axhline(dacs.loc[non_upgrade_ind, 'existing_amps_per_sqft_log10'].mean(), color = 'navajowhite', linestyle = ':')
fig2.ax_joint.axvline(dacs.loc[non_upgrade_ind, 'building_sqft_log10'].mean(), color = 'navajowhite', linestyle = ':')

fig2.ax_marg_x.set_xlim(xlim)
fig2.ax_marg_x.set_xticks(xticks)
fig2.ax_marg_x.set_xticklabels(xtick_labels)
fig2.ax_joint.set_xlabel('Property Size\n [$ft^2$]')

fig2.ax_marg_y.set_ylim(ylim)
fig2.ax_marg_y.set_yticks(yticks)
fig2.ax_marg_y.set_yticklabels(ytick_labels)
fig2.ax_joint.set_ylabel('Rated Panel Capacity\n [$Amps / ft^2$]')

figure_dir = '/Users/edf/repos/la100es-panel-upgrades/figs/sf/'
fig1.savefig(figure_dir + 'ladwp_non_dac_permitted_upgrade_amps_per_sqft_jointplot.png', bbox_inches = 'tight', dpi = 500)
fig2.savefig(figure_dir + 'ladwp_dac_permitted_upgrade_amps_per_sqft_jointplot.png', bbox_inches = 'tight', dpi = 500)

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

#%% Non-DAC Case

upgrade_ind = non_dacs['permitted_panel_upgrade'] == True
x = non_dacs.loc[upgrade_ind, 'building_sqft_log10']
y = non_dacs.loc[upgrade_ind, 'existing_amps_per_sqft_log10']

a, b = np.polyfit(x, y, 1)

#%% MF Plot

mf_data['avg_unit_sqft_log10'] = np.log10(mf_data['avg_unit_sqft'])
mf_data['existing_amps_per_sqft_log10'] = np.log10(mf_data['panel_size_existing'] / mf_data['avg_unit_sqft'])

non_dacs_ind = mf_data['dac_status'] == 'Non-DAC'
dacs_ind = mf_data['dac_status'] == 'DAC'

non_dacs = mf_data.loc[non_dacs_ind,:]
dacs = mf_data.loc[dacs_ind,:]

#%% Generate MF Plots

bw = 0.75

fig1 = sns.jointplot(data = non_dacs,
    x = 'avg_unit_sqft_log10',
    y = 'existing_amps_per_sqft_log10',
    hue = 'permitted_panel_upgrade',
    palette = ['lightblue', 'tab:blue'],
    kind = 'kde',
    bw_method = bw)

upgrade_ind = non_dacs['permitted_panel_upgrade'] == True
non_upgrade_ind = non_dacs['permitted_panel_upgrade'] == False

fig1.ax_joint.axhline(non_dacs.loc[upgrade_ind, 'existing_amps_per_sqft_log10'].mean(), color = 'tab:blue', linestyle = ':')
fig1.ax_joint.axvline(non_dacs.loc[upgrade_ind, 'avg_unit_sqft_log10'].mean(), color = 'tab:blue', linestyle = ':')

fig1.ax_joint.axhline(non_dacs.loc[non_upgrade_ind, 'existing_amps_per_sqft_log10'].mean(), color = 'lightblue', linestyle = ':')
fig1.ax_joint.axvline(non_dacs.loc[non_upgrade_ind, 'avg_unit_sqft_log10'].mean(), color = 'lightblue', linestyle = ':')

ylim = (-2.0, 0.0)
yticks = [-2, -1, 0]
ytick_labels = ['0.01', '0.1', '1.0']

xlim = (2.0, 4.0)
xticks = [2, 3, 4]
xtick_labels = ['100', '1,000', '10,000']

fig1.ax_marg_x.set_xlim(xlim)
fig1.ax_marg_x.set_xticks(xticks)
fig1.ax_marg_x.set_xticklabels(xtick_labels)
fig1.ax_joint.set_xlabel('Average Unit Size\n [$ft^2$]')

fig1.ax_marg_y.set_ylim(ylim)
fig1.ax_marg_y.set_yticks(yticks)
fig1.ax_marg_y.set_yticklabels(ytick_labels)
fig1.ax_joint.set_ylabel('Rated Panel Capacity\n [$Amps / ft^2$]')

fig2 = sns.jointplot(data = dacs,
    x = 'avg_unit_sqft_log10',
    y = 'existing_amps_per_sqft_log10',
    hue = 'permitted_panel_upgrade',
    palette = ['navajowhite', 'tab:orange'],
    kind = 'kde',
    bw_method = bw)

upgrade_ind = dacs['permitted_panel_upgrade'] == True
non_upgrade_ind = (dacs['permitted_panel_upgrade'] == False) & ~(np.isinf(dacs['existing_amps_per_sqft_log10']))

fig2.ax_joint.axhline(dacs.loc[upgrade_ind, 'existing_amps_per_sqft_log10'].mean(), color = 'tab:orange', linestyle = ':')
fig2.ax_joint.axvline(dacs.loc[upgrade_ind, 'avg_unit_sqft_log10'].mean(), color = 'tab:orange', linestyle = ':')

fig2.ax_joint.axhline(dacs.loc[non_upgrade_ind, 'existing_amps_per_sqft_log10'].mean(), color = 'navajowhite', linestyle = ':')
fig2.ax_joint.axvline(dacs.loc[non_upgrade_ind, 'avg_unit_sqft_log10'].mean(), color = 'navajowhite', linestyle = ':')

fig2.ax_marg_x.set_xlim(xlim)
fig2.ax_marg_x.set_xticks(xticks)
fig2.ax_marg_x.set_xticklabels(xtick_labels)
fig2.ax_joint.set_xlabel('Average Unit Size\n [$ft^2$]')

fig2.ax_marg_y.set_ylim(ylim)
fig2.ax_marg_y.set_yticks(yticks)
fig2.ax_marg_y.set_yticklabels(ytick_labels)
fig2.ax_joint.set_ylabel('Rated Panel Capacity\n [$Amps / ft^2$]')

figure_dir = '/Users/edf/repos/la100es-panel-upgrades/figs/sf/'
fig1.savefig(figure_dir + 'ladwp_multi_family_non_dac_permitted_upgrade_amps_per_sqft_jointplot.png', bbox_inches = 'tight', dpi = 500)
fig2.savefig(figure_dir + 'ladwp_multi_family_dac_permitted_upgrade_amps_per_sqft_jointplot.png', bbox_inches = 'tight', dpi = 500)

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
