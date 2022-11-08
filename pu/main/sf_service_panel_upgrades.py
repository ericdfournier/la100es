#%% Package Imports

import pandas as pd
import geopandas as gpd
import sqlalchemy as sql
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, StrMethodFormatter
import seaborn as sns
import os
import sys
from matplotlib import animation

os.chdir('/Users/edf/repos/la100es/pu/')
import pkg.io as io
import pkg.plot as plot
import pkg.utils as utils
import pkg.decide as decide

#%% Set Output Figures Directory

figure_dir = '/Users/edf/repos/la100es/figures/'

#%% Import SF Data and Context Layers

sf_buildings = io.ImportSingleFamilyBuildingPermitData()
ces4 = io.ImportCalEnviroScreenData()
ladwp = io.ImportLadwpServiceTerritoryData()
sf_buildings_ces = utils.AssignDACStatus(utils.MergeCES(sf_buildings, ces4))

#%% Implement Initial Decision Tree

sf_buildings_ces = decide.AssignAsBuiltFromDecisionTree(sf_buildings_ces)
sf_buildings_ces = decide.AssignExistingFromPermit(sf_building_ces)
sf_buildings_ces = decide.InferExistingFromModel(sf_building_ces)
sf_buildings_ces = utils.UpgradeTimeDelta(sf_buildings_ces)

#%% Generate Plots

plot.CountsByTract(sf_buildings, ces4, ladwp, figure_dir)

plot.AsBuiltPanelRatingsMap(sf_buildings_ces, ces4, ladwp, figure_dir)
plot.AsBuiltPanelRatingsHist(sf_buildings_ces, ces4, ladwp, figure_dir)
plot.AsBuiltPanelRatingsBar(sf_buildings, figure_dir)

plot.PermitTimeSeries(sf_buildings_ces, figure_dir)
plot.PermitCountsMap(sf_buildings_ces, ces4, ladwp, figure_dir)
plot.PermitCountsHistAnimation(sf_buildings_ces, figure_dir)
plot.PermitVintageYearECDF(sf_buildings_ces, figure_dir)

#%% Print Diagnostics

utils.AsBuiltDiagnostics(sf_buildings_ces)

# %% Generate Change Statistics 

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

#%% Diagnostic Plot of Change Statistics

fig, ax = plt.subplots(1,1, figsize=(5,5))

total_permit_counts = panel_stats_ces.groupby('dac_status')['upgrade_count'].agg('sum').reset_index()

sns.barplot(x = 'dac_status',
    y = 'upgrade_count', 
    data = total_permit_counts,
    order = ['Non-DAC', 'DAC'], 
    ax = ax)

ax.set_ylabel('Total Number of Panel Upgrades \n[Homes]')
ax.set_xlabel('DAC Status')
ax.grid(True)

ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))

fig.tight_layout()
fig.patch.set_facecolor('white')

fig.savefig(figure_dir + 'lac_sf_panel_upgrade_total_counts_barplot.png', bbox_inches = 'tight', dpi = 300)

#%% Diagnostic Plot of Change Statistics

fig, ax = plt.subplots(1,1, figsize=(5,5))

sns.boxplot(x = 'dac_status',
    y = 'upgrade_delta_amps', 
    data = panel_stats_ces, 
    ax = ax)

ax.set_ylabel('Change in Mean Panel Size \n(As-built -> Existing) \n[Amps]')
ax.set_xlabel('DAC Status')
ax.grid(True)

fig.tight_layout()
fig.patch.set_facecolor('white')

fig.savefig(figure_dir + 'lac_sf_panel_upgrade_deltas_boxplots.png', bbox_inches = 'tight', dpi = 300)

#%% Diagnostic Plot of Change Statistics

fig, ax = plt.subplots(1,1, figsize=(5,5))

sns.scatterplot(x = 'mean_sf_panel_size_as_built',
    y = 'upgrade_delta_amps',
    hue = 'dac_status',
    data = panel_stats_ces, 
    ax = ax,
    alpha = 0.5)

ax.set_ylabel('Change in Mean Panel Rating\n(As-built -> Existing) \n[Amps]')
ax.set_xlabel('Mean Panel Size \n (As-built) [Amps]')
ax.grid(True)

fig.tight_layout()
fig.patch.set_facecolor('white')

fig.savefig(figure_dir + 'lac_sf_panel_upgrade_deltas_vs_ces_scatterplot.png', bbox_inches = 'tight', dpi = 300)

#%% Diagnostic Plot of Change Statistics

fig, ax = plt.subplots(1,1, figsize=(5,5))

sns.histplot(x = 'mean_sf_panel_size_existing',
    hue = 'dac_status',
    data = panel_stats_ces,
    bins = 30,
    ax = ax)

ax.axvline(200, color = 'r', linestyle = '--', linewidth = 2)
ax.set_xlabel('Mean Panel Size \n (Existing) \n[Amps]')
ax.set_ylabel('Census Tracts \n[Counts]')
ax.grid(True)

fig.tight_layout()
fig.patch.set_facecolor('white')

fig.savefig(figure_dir + 'lac_sf_panel_upgrade_existing_means_histplot.png', bbox_inches = 'tight', dpi = 300)

#%% Generate Diagnostic Map Plot

fig, ax = plt.subplots(1,1, figsize=(10,10))

dac_ind = ces4['ciscorep'] >= 75.0
non_dac_ind = ces4['ciscorep'] < 75.0

ces4.loc[~(dac_ind | non_dac_ind)].boundary.plot(ax = ax, edgecolor = 'k', linewidth = 0.5)
ces4.loc[dac_ind].boundary.plot(ax = ax, color = 'tab:orange', linewidth = 0.5)
ces4.loc[non_dac_ind].boundary.plot(ax = ax, color = 'tab:blue', linewidth = 0.5)
ladwp.boundary.plot(ax = ax, edgecolor = 'black', linewidth = 1.5)

panel_stats_ces_geo.plot(column = 'mean_sf_panel_size_existing', 
    ax = ax, 
    scheme='user_defined',
    classification_kwds = {'bins' : [30,60,100,125,150,200,300,400]},
    k = 10,
    cmap='bone_r',
    legend = True,
    legend_kwds = {'title': 'Single Family Homes\nAverage Panel Size Rating\nExisting [Amps]',
                    'loc': 'lower left',
                    "labels": ["","30-60", "60-100", "100-125", "125-150", "150-200", "200-300", "300-400"]})

ax.set_ylim((-480000,-405000))
ax.set_xlim((120000,170000))
ax.set_axis_off()

fig.tight_layout()
fig.patch.set_facecolor('white')

fig.savefig(figure_dir + 'lac_sf_panel_ratings_existing_geographic_distribution_map.png', bbox_inches = 'tight', dpi = 300)

#%% Generate Change Percentage Plot

fig, ax = plt.subplots(1,1, figsize = (10,10))

dac_ind = ces4['ciscorep'] >= 75.0
non_dac_ind = ces4['ciscorep'] < 75.0

ces4.loc[~(dac_ind | non_dac_ind)].boundary.plot(ax = ax, edgecolor = 'k', linewidth = 0.5)
ces4.loc[dac_ind].boundary.plot(ax = ax, color = 'tab:orange', linewidth = 0.5)
ces4.loc[non_dac_ind].boundary.plot(ax = ax, color = 'tab:blue', linewidth = 0.5)
ladwp.boundary.plot(ax = ax, edgecolor = 'black', linewidth = 1.5)
panel_stats_ces_geo.plot(column = 'upgrade_delta_pct', 
    scheme = 'userdefined',
    k = 7,
    cmap = 'bone_r', 
    classification_kwds = {'bins' : [10,25,50,75,100,200]},
    legend = True,
    legend_kwds = {'title': 'Single Family Homes\nChange in Average Panel Size\nFrom As-Built -> Existing\n[Percent Change]\n',
                    'loc': 'lower left'},
    ax = ax)

ax.set_ylim((-480000,-405000))
ax.set_xlim((120000,170000))
ax.set_axis_off()

fig.tight_layout()
fig.patch.set_facecolor('white')

fig.savefig(figure_dir + 'lac_sf_panel_ratings_delta_geographic_distribution_quiver_map.png', bbox_inches = 'tight', dpi = 300)

#%% Plot SF Existing panel size ratings

dac_ind = (sf_buildings_ces['dac_status'] == 'DAC') 
non_dac_ind = (sf_buildings_ces['dac_status'] == 'Non-DAC')

dac_sample = sf_buildings_ces.loc[dac_ind,:]
non_dac_sample = sf_buildings_ces.loc[non_dac_ind,:]

dac_sample['year_built_int'] = dac_sample['year_built'].dt.year
non_dac_sample['year_built_int'] = non_dac_sample['year_built'].dt.year

fig, ax = plt.subplots(1,2,figsize = (10,8), sharey = True, sharex = True)

sns.histplot(x = 'year_built_int', 
    y = 'panel_size_existing', 
    data = dac_sample, 
    color = 'tab:orange', 
    ax = ax[0], 
    bins = 50, 
    legend = True, 
    label = 'DAC', 
    cbar = True, 
    cbar_kws = {'label':'Number of Single Family Homes', 'orientation':'horizontal'}, 
    vmin=0, vmax=4000)
sns.histplot(x = 'year_built_int',
    y = 'panel_size_existing', 
    data = non_dac_sample, 
    color = 'tab:blue', 
    ax = ax[1], 
    bins = 70, 
    legend = True, 
    label = 'Non-DAC', 
    cbar = True, 
    cbar_kws = {'label':'Number of Single Family Homes', 'orientation':'horizontal'}, 
    vmin=0, vmax=4000)

ax[0].set_yticks([30,60,100, 125, 150, 200, 225, 300, 400, 600, 800])

ax[0].grid(True)
ax[1].grid(True)

ax[0].set_ylabel('Existing Panel Rating \n[Amps]')
ax[1].set_ylabel('')

ax[0].set_xlabel('Vintage \n[Year]')
ax[1].set_xlabel('Vintage \n[Year]')

ax[0].set_title('DAC')
ax[1].set_title('Non-DAC')

ax[0].set_ylim(0, 820)
ax[1].set_ylim(0, 820)

ax[0].set_xlim(1830, 2025)
ax[1].set_xlim(1830, 2025)

fig.tight_layout()
fig.patch.set_facecolor('white')

fig.savefig(figure_dir + 'lac_sf_existing_panel_ratings_hist.png', bbox_inches = 'tight', dpi = 300)

#%% Print Upgrade Stats

dac_ind = (sf_buildings_ces['dac_status'] == 'DAC') 
non_dac_ind = (sf_buildings_ces['dac_status'] == 'Non-DAC')

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

#%% Print Capacity Stats

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
