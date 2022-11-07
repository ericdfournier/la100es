#%% Package Imports

import pandas as pd
import geopandas as gpd
import sqlalchemy as sql
import scipy.stats as stats
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, StrMethodFormatter
import seaborn as sns
import os
import sys
from matplotlib import animation

from itertools import product
from sklearn.metrics import r2_score
from statsmodels.distributions.empirical_distribution import ECDF
from numpy.random import MT19937
from numpy.random import RandomState, SeedSequence

sys.path.append('/Users/edf/repos/la100es/pu/')
import pkg.io as io
import pkg.plot as plot

#%% Set Output Figures Directory

figure_dir = '/Users/edf/repos/la100es/figures/'

#%% Import SF Data and Context Layers

sf_buildings = io.ImportSingleFamilyBuildingPermitData()
ces4 = io.ImportCalEnviroScreenData()
ladwp = io.ImportLadwpServiceTerritoryData()

#%% Merge Parcels with CES Data and Assign DAC Status

sf_buildings_ces = pd.merge(sf_buildings, ces4[['tract', 'ciscorep']], left_on = 'census_tract', right_on = 'tract')
sf_buildings_ces.set_index('tract', inplace = True)
sf_buildings_ces['dac_status'] = 'Non-DAC'
ind = sf_buildings_ces['ciscorep'] >= 75.0
sf_buildings_ces.loc[ind, 'dac_status'] = 'DAC'

#%% Plot Single Family Building Counts by Tract

plot.SingleFamilyCountsByTract(sf_buildings, ces4, ladwp, figure_dir)

#%% Implement Initial Decision Tree

vintage_pre_1978 = sf_buildings_ces['year_built'].dt.year < 1978
vintage_post_1978 = sf_buildings_ces['year_built'].dt.year >= 1978

size_minus_1k = (sf_buildings_ces['building_sqft'] >= 0) & (sf_buildings_ces['building_sqft'] < 1000) 
size_1k_2k = (sf_buildings_ces['building_sqft'] >= 1000) & (sf_buildings_ces['building_sqft'] < 2000) 
size_2k_3k = (sf_buildings_ces['building_sqft'] >= 2000) & (sf_buildings_ces['building_sqft'] < 3000)
size_3k_4k = (sf_buildings_ces['building_sqft'] >= 3000) & (sf_buildings_ces['building_sqft'] < 4000)
size_4k_5k = (sf_buildings_ces['building_sqft'] >= 4000) & (sf_buildings_ces['building_sqft'] < 5000)
size_5k_8k = (sf_buildings_ces['building_sqft'] >= 5000) & (sf_buildings_ces['building_sqft'] < 8000)
size_8k_10k = (sf_buildings_ces['building_sqft'] >= 8000) & (sf_buildings_ces['building_sqft'] < 10000)
size_10k_20k = (sf_buildings_ces['building_sqft'] >= 10000) & (sf_buildings_ces['building_sqft'] < 20000)
size_20k_plus = (sf_buildings_ces['building_sqft'] >= 20000)

vintage_names = ['vintage_pre_1978', 'vintage_post_1979']

size_names = [      'size_minus_1k',
                    'size_1k_2k',
                    'size_2k_3k',
                    'size_3k_4k',
                    'size_4k_5k',
                    'size_5k_8k',
                    'size_8k_10k'
                    'size_10k_20k',
                    'size_20k_plus']

vintage_bins = [    vintage_pre_1978, 
                    vintage_post_1978]

size_bins = [       size_minus_1k, 
                    size_1k_2k,
                    size_2k_3k,
                    size_3k_4k,
                    size_4k_5k,
                    size_5k_8k,
                    size_8k_10k,
                    size_10k_20k,
                    size_20k_plus]

names = list(map(list, product(vintage_names, size_names)))
combs = list(map(list, product(vintage_bins, size_bins)))

panel_sizes = [     30,     # [['vintage_pre_1978', 'size_minus_1k'],
                    60,     # ['vintage_pre_1978', 'size_1k_2k'],
                    100,    # ['vintage_pre_1978', 'size_2k_3k'], 
                    125,    # ['vintage_pre_1978', 'size_3k_4k'],
                    150,    # ['vintage_pre_1978', 'size_4k_5k'],
                    200,    # ['vintage_pre_1978', 'size_5k_8k'],
                    300,    # ['vintage_pre_1978', 'size_8k_10k']
                    400,    # ['vintage_pre_1978', 'size_10k_20k'],
                    600,    # ['vintage_pre_1978', 'size_20k_plus'],
                    100,    # ['vintage_post_1979', 'size_minus_1k'],
                    125,    # ['vintage_post_1979', 'size_1k_2k'],
                    150,    # ['vintage_post_1979', 'size_2k_3k'],
                    200,    # ['vintage_post_1979', 'size_3k_4k'],
                    225,    # ['vintage_post_1979', 'size_4k_5k']
                    300,    # ['vintage_post_1979', 'size_5k_8k'],
                    400,    # ['vintage_post_1979', 'size_8k_10k']] 
                    600,    # ['vintage_post_1979', 'size_10k_20k']]
                    800]    # ['vintage_post_1979', 'size_20k_plus']]

sf_buildings_ces['panel_size_as_built'] = np.nan

for i in range(len(combs)):

    sf_buildings_ces.loc[(combs[i][0] & combs[i][1]),'panel_size_as_built'] = panel_sizes[i]

sf_buildings_ces.reset_index(inplace = True, drop = True)

#%% Plot As-Built Average Panel Size by Tract

sf_as_built_avg = sf_buildings_ces.groupby('census_tract')['panel_size_as_built'].agg('mean')
sf_as_built_df = pd.merge(ces4.loc[:,['geom','tract','ciscorep']], sf_as_built_avg, left_on = 'tract', right_on = 'census_tract')
sf_as_built_df.rename(columns = {'geom':'geometry'}, inplace = True)
sf_as_built = gpd.GeoDataFrame(sf_as_built_df)

fig, ax = plt.subplots(1, 1, figsize = (10,10))

dac_ind = ces4['ciscorep'] >= 75.0
non_dac_ind = ces4['ciscorep'] < 75.0

ces4.loc[~(dac_ind | non_dac_ind)].boundary.plot(ax = ax, edgecolor = 'k', linewidth = 0.5)
ces4.loc[dac_ind].boundary.plot(ax = ax, color = 'tab:orange', linewidth = 0.5)
ces4.loc[non_dac_ind].boundary.plot(ax = ax, color = 'tab:blue', linewidth = 0.5)
ladwp.boundary.plot(ax = ax, edgecolor = 'black', linewidth = 1.5)

sf_as_built.plot(ax = ax, 
    column = 'panel_size_as_built',
    scheme='user_defined',
    classification_kwds = {'bins' : [30,60,100,125,150,200,400]},
    k = 10,
    cmap='bone_r',
    legend = True,
    legend_kwds = {'title': 'Single Family Homes\nAverage Panel Rating\nAs-Built [Amps]\n',
                    'loc': 'lower left',
                    "labels": ["30-60", "60-100", "100-125", "125-150", "150-200", "200-300", "300-400"]})

ax.set_ylim((-480000,-405000))
ax.set_xlim((120000,170000))
ax.set_axis_off()

fig.patch.set_facecolor('white')
fig.tight_layout()

fig.savefig(figure_dir + 'lac_sf_as_built_avg_panel_size_map.png', bbox_inches = 'tight', dpi = 300)

#%% SF Diagnostic Stats

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

#%% Plot SF as built panel size ratings

fig, ax = plt.subplots(1,2,figsize = (10,8), sharey = True)

dac_sample['year_built_int'] = dac_sample['year_built'].dt.year
non_dac_sample['year_built_int'] = non_dac_sample['year_built'].dt.year

sns.histplot(x = 'year_built_int', 
    y = 'panel_size_as_built', 
    data = dac_sample, 
    color = 'tab:orange', 
    ax = ax[0], 
    bins = 60, 
    legend = True, 
    label = 'DAC', 
    cbar = True, 
    cbar_kws = {'label':'Number of Single Family Homes', 'orientation':'horizontal'}, 
    vmin=0, vmax=4000)
sns.histplot(x = 'year_built_int',
    y = 'panel_size_as_built', 
    data = non_dac_sample, 
    color = 'tab:blue', 
    ax = ax[1], 
    bins = 60, 
    legend = True, 
    label = 'Non-DAC', 
    cbar = True, 
    cbar_kws = {'label':'Number of Single Family Homes', 'orientation':'horizontal'}, 
    vmin=0, vmax=4000)

ax[0].set_yticks([30, 60, 100, 125, 150, 200, 225, 300, 400, 600, 800])

ax[0].grid(True)
ax[1].grid(True)

ax[0].set_ylabel('As-Built Panel Rating \n[Amps]')
ax[1].set_ylabel('')

ax[0].set_xlabel('Vintage \n[Year]')
ax[1].set_xlabel('Vintage \n[Year]')

ax[0].set_title('DAC')
ax[1].set_title('Non-DAC')

ax[0].set_ylim(0, 820)
ax[1].set_ylim(0, 820)

ax[0].set_xlim(1830, 2025)
ax[1].set_xlim(1830, 2025)

fig.patch.set_facecolor('white')
fig.tight_layout()

fig.savefig(figure_dir + 'lac_sf_as_built_panel_ratings_hist.png', bbox_inches = 'tight', dpi = 300)

#%% Compute Stats

counts = sf_buildings_ces.groupby('panel_size_as_built')['apn'].agg('count')
dac_counts = sf_buildings_ces.groupby(['dac_status', 'panel_size_as_built'])['apn'].agg('count')
dac_counts = dac_counts.unstack(level= 0)
dac_counts.index = dac_counts.index.astype(int)

#%% Plot Counts

fig, ax = plt.subplots(1,1, figsize = (5,5))

dac_counts.plot.barh(ax = ax, color = ['tab:orange', 'tab:blue'])

ax.grid(True)
ax.set_ylabel('As-Built Panel Rating \n[Amps]')
ax.set_xlabel('Number of Single-Family Homes')
plt.xticks(rotation = 45)

ax.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))

fig.patch.set_facecolor('white')
fig.tight_layout()

fig.savefig(figure_dir + 'lac_sf_as_built_panel_ratings_barchart.png', bbox_inches = 'tight', dpi = 300)

#%% Generate Time Series of Permits by DAC Status

upgrade_ind = sf_buildings_ces['panel_upgrade'] == True

permit_ts = sf_buildings_ces.loc[upgrade_ind].groupby([pd.Grouper(key='permit_issue_date', axis=0, freq='1Y'), 'dac_status'])['apn'].agg('count')
permit_ts = permit_ts.reset_index()
permit_ts = permit_ts.rename(columns = {'apn': 'permit_count'})

#%% Generate Cumsum of Permits by DAC Status

permit_cs = sf_buildings_ces.loc[upgrade_ind].groupby([pd.Grouper(key='permit_issue_date', axis=0, freq='1Y'), 'dac_status'])['apn'].agg('count')
permit_cs = permit_cs.sort_index()

dac_vals = permit_cs.loc(axis = 0)[:,'DAC'].cumsum()
non_dac_vals = permit_cs.loc(axis = 0)[:,'Non-DAC'].cumsum()

permit_cs = pd.concat([dac_vals, non_dac_vals], axis = 0).sort_index()
permit_cs = permit_cs.reset_index()
permit_cs = permit_cs.rename(columns = {'apn': 'permit_count'})

# %% Plot Time Series of Permit Counts and Cumulative Sums

fig, ax = plt.subplots(2, 1, figsize = (8,8), sharex = True)

hue_order = ['Non-DAC', 'DAC']

sns.lineplot(x = 'permit_issue_date', 
    y = 'permit_count', 
    hue = 'dac_status',
    hue_order = hue_order,
    data = permit_ts,
    ax = ax[0])

l1 = ax[0].lines[0]
x1 = l1.get_xydata()[:, 0]
y1 = l1.get_xydata()[:, 1]
ax[0].fill_between(x1, y1, color="tab:blue", alpha=0.3)

l2 = ax[0].lines[1]
x2 = l2.get_xydata()[:, 0]
y2 = l2.get_xydata()[:, 1]
ax[0].fill_between(x2, y2, color="tab:orange", alpha=0.3)

ax[0].yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))

sns.lineplot(x = 'permit_issue_date',
    y = 'permit_count',
    hue = 'dac_status',
    hue_order = hue_order,
    data = permit_cs,
    ax = ax[1])

l1 = ax[1].lines[0]
x1 = l1.get_xydata()[:, 0]
y1 = l1.get_xydata()[:, 1]
ax[1].fill_between(x1, y1, color="tab:blue", alpha=0.3)

l2 = ax[1].lines[1]
x2 = l2.get_xydata()[:, 0]
y2 = l2.get_xydata()[:, 1]
ax[1].fill_between(x2, y2, color="tab:orange", alpha=0.3)

ax[1].yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))

ax[1].margins(x=0, y=0)

ax[0].grid(True)
ax[1].grid(True)

ax[1].set_xlabel('Permit Issue Date \n[Year]')
ax[0].set_ylabel('Panel Upgrades in Sample Area \n[Annual]')
ax[1].set_ylabel('Panel Upgrades in Sample Area \n[Cumulative]')

fig.patch.set_facecolor('white')
fig.tight_layout()

fig.savefig(figure_dir + 'lac_sf_permit_time_series_plot.png', bbox_inches = 'tight', dpi = 300)

# %% Count the Total Number of Buildings in the Permit Data Tracts

tracts = sf_buildings_ces['census_tract'].unique()
ind = ces4['tract'].isin(tracts)
sf_permit_tracts = ces4.loc[ind,:]

permits_per_tract = sf_buildings_ces.groupby(['census_tract'])['apn'].agg('count')
permits_per_tract_ces = pd.merge(ces4.loc[:,['geom','tract']], permits_per_tract, left_on = 'tract', right_index = True)

#%% Plot Census Tracts with Permit Data

fig, ax = plt.subplots(1, 1, figsize = (10,10))

dac_ind = ces4['ciscorep'] >= 75.0
non_dac_ind = ces4['ciscorep'] < 75.0

ces4.loc[~(dac_ind | non_dac_ind)].boundary.plot(ax = ax, edgecolor = 'k', linewidth = 0.5)
ces4.loc[dac_ind].boundary.plot(ax = ax, color = 'tab:orange', linewidth = 0.5)
ces4.loc[non_dac_ind].boundary.plot(ax = ax, color = 'tab:blue', linewidth = 0.5)
ladwp.boundary.plot(ax = ax, edgecolor = 'black', linewidth = 1.5)

permits_per_tract_ces.plot(ax = ax,
    column = 'apn',
    k = 7,
    cmap = 'bone_r', 
    scheme = 'user_defined',
    classification_kwds = {'bins' : [100,250,500,750,1000,1500,2000]},
    legend = True,
    legend_kwds = {'title': 'Single Family Homes\nPermitted Panel Upgrades\n[Counts]\n',
                    'loc': 'lower left',
                     "labels": ["1-100", "100-250", "250-500", "500-750","750-1000", "1000-1500", "1500-2000"]})

ax.set_ylim((-480000,-405000))
ax.set_xlim((120000,170000))
ax.set_axis_off()

fig.patch.set_facecolor('white')
fig.tight_layout()

fig.savefig(figure_dir + 'lac_sf_permit_geographic_distribution_map.png', bbox_inches = 'tight', dpi = 300)

# %% Find Locations with Upgrades of Different Size

pu_100 = sf_buildings_ces['permit_description'].str.contains(' 100')
pu_125 = sf_buildings_ces['permit_description'].str.contains(' 125')
pu_150 = sf_buildings_ces['permit_description'].str.contains(' 150')
pu_200 = sf_buildings_ces['permit_description'].str.contains(' 200')
pu_225 = sf_buildings_ces['permit_description'].str.contains(' 225')
pu_300 = sf_buildings_ces['permit_description'].str.contains(' 300')
pu_400 = sf_buildings_ces['permit_description'].str.contains(' 400')
pu_600 = sf_buildings_ces['permit_description'].str.contains(' 600')

pu_solar = sf_buildings_ces['permit_description'].str.contains('solar', case = False)
pu_ev = sf_buildings_ces['permit_description'].str.contains('ev', case = False)
pu_ac = sf_buildings_ces['permit_description'].str.contains('ac', case = False)

pu_other = ~(pu_100 | pu_125 | pu_150 | pu_200 | pu_225 | pu_300 | pu_400 | pu_600 | pu_solar | pu_ev | pu_ac)

#%% Peform Filtering Assignment

sf_buildings_ces['panel_size_existing'] = sf_buildings_ces['panel_size_as_built']

upgrade_scale = [ 30., 60., 100., 125., 150., 200., 225., 300., 400., 600., 800.0, 1000.0]

ind_dict = {100.0:pu_100,
            125.0:pu_125,
            150.0:pu_150, 
            200.0:pu_200, 
            225.0:pu_225,
            300.0:pu_300, 
            400.0:pu_400,
            600.0:pu_600}

sf_buildings_ces['permitted_panel_upgrade'] = False

for k, v in ind_dict.items():
    
    v[v.isna()] = False
    proposed = sf_buildings_ces.loc[v,'panel_size_as_built']
    change_ind = proposed < k
    proposed.loc[change_ind] = k
    sf_buildings_ces.loc[proposed.index,'panel_size_existing'] = proposed

other_ind = (pu_solar | pu_other | pu_ev | pu_ac)
other_ind[other_ind.isna()] = False
apns = sf_buildings_ces.loc[other_ind, 'apn']
as_built_ind = sf_buildings_ces.index.isin(apns)
proposed = sf_buildings_ces.loc[as_built_ind, 'panel_size_as_built']

for p in proposed.iteritems():
    c = None
    if np.isnan(p[1]):
        c = 100.0
    else:
        c = p[1]
    k = upgrade_scale.index(c)
    upgrade = upgrade_scale[k+1]
    if upgrade < 200:
        upgrade = 200
    proposed.loc[p[0]] = upgrade

sf_buildings_ces.loc[proposed.index, 'panel_size_existing'] = proposed

upgrade_ind = sf_buildings_ces['panel_size_existing'] > sf_buildings_ces['panel_size_as_built']
sf_buildings_ces.loc[upgrade_ind, 'permitted_panel_upgrade'] = True

#%% Compute Time Difference Between Construction Date and Upgrade Date

upgrade_time_delta = pd.to_numeric(sf_buildings_ces.loc[:,'permit_issue_date'].dt.year - sf_buildings_ces.loc[:,'year_built'].dt.year)
neg = upgrade_time_delta < 0
upgrade_time_delta.loc[neg] = 0
sf_buildings_ces['upgrade_time_delta'] = np.nan
sf_buildings_ces.loc[upgrade_time_delta.index.get_level_values(0),'upgrade_time_delta'] = upgrade_time_delta.values

#%% Plot Time-Delta Distribution for Each Permit Year

def animate_func(num):

    hue_order = [ 'Non-DAC','DAC']

    ax.clear()
    test_years = sf_buildings_ces['permit_issue_date'].dt.year.unique()
    test_years = np.sort(test_years)
    y = test_years[num+1]
    ind = sf_buildings_ces['permit_issue_date'].dt.year == y
    data = sf_buildings_ces.loc[ind]
    year = data.loc[:,'year_built'].dt.year
    data.loc[:,'year_built'] = year.values

    sns.histplot(x = 'year_built',
        data = data,
        hue = 'dac_status',
        kde = True,
        legend = True,
        hue_order = hue_order,
        ax = ax,
        bins = np.arange(1900,2020,2))

    ax.grid(True)
    ax.set_title(str(y))
    ax.set_xlim(1900,2020)
    ax.set_ylim(0,1500)
    ax.set_xlabel('Year Built')
    ax.set_ylabel('Count')
        
fig = plt.figure()
ax = plt.axes()

numDataPoints = sf_buildings_ces['permit_issue_date'].dt.year.unique().shape[0]-1

line_ani = animation.FuncAnimation(fig, 
    animate_func, 
    interval=1000,   
    frames=numDataPoints)

plt.show()

f = figure_dir + 'la_city_panel_permits_histogram_animation.gif'
writergif = animation.PillowWriter(fps=numDataPoints/16)
line_ani.save(f, writer=writergif)

# %% Compute ECDF for As-Built Year

nan_ind = ~sf_buildings_ces['year_built'].isna()
dac_ind = sf_buildings_ces['dac_status'] == 'DAC'
dac_permit_sum = dac_ind.sum()
non_dac_ind = sf_buildings_ces['dac_status'] == 'Non-DAC'
non_dac_permit_sum = non_dac_ind.sum()

dac_ages = pd.DataFrame(2022-sf_buildings_ces.loc[(nan_ind & dac_ind),'year_built'].dt.year)
non_dac_ages = pd.DataFrame(2022-sf_buildings_ces.loc[(nan_ind & non_dac_ind),'year_built'].dt.year)

fig, ax = plt.subplots(1,1,figsize = (8,5))
sns.ecdfplot(data=dac_ages, x='year_built', ax=ax, color = 'tab:orange')
sns.ecdfplot(data=non_dac_ages, x='year_built', ax=ax, color = 'tab:blue')
ax.set_xlabel('Age of Home')
ax.set_ylabel('Proportion of Single Family Homes\nwith Permitted Panel Upgrades')
ax.autoscale(enable=True, axis='x', tight = True)
range_max = dac_ages['year_built'].max()
interval = 10
x_ticks = np.arange(0.0, range_max, interval)
y_ticks = np.arange(0.0, 1.1, 0.1)
ax.set_xticks(x_ticks)
ax.autoscale(enable=True, axis='x', tight=True)
ax.grid(True)
ax.set_ylim(0.0,1.0)
ax.set_xlim(0.0, 150)
ax.set_yticks(y_ticks)

ax.legend(['DAC', 'Non-DAC'])

fig.tight_layout()
fig.patch.set_facecolor('white')

fig.savefig(figure_dir + 'lac_sf_vintage_empirical_cdf_plot.png', bbox_inches = 'tight', dpi = 300)

# %% Simulate Previous Year Upgrades Based Upon ECDF

rs = RandomState(MT19937(SeedSequence(987654321)))

dac_ecdf = ECDF(dac_ages['year_built'])

dac_odds_ratio = non_dac_permit_sum / dac_permit_sum
start_year = 1996

dac_ind = (~sf_buildings_ces['year_built'].isna()) & (sf_buildings_ces['dac_status'] == 'DAC') & (sf_buildings_ces['permitted_panel_upgrade'] == False)
dac_x = pd.DataFrame(start_year - sf_buildings_ces.loc[dac_ind,'year_built'].dt.year)
dac_neg_ind = dac_x['year_built'] < 0
dac_x.loc[dac_neg_ind,'year_built'] = 0
dac_y = dac_ecdf(dac_x) / dac_odds_ratio
dac_upgrade_list = []

for pr in dac_y[:,0]: 
    dac_upgrade_list.append(np.random.choice(np.array([False, True]), size = 1, p = [1.0-pr, pr])[0])

dac_x['previous_upgrade'] = dac_upgrade_list

non_dac_ecdf = ECDF(non_dac_ages['year_built'])

non_dac_ind = (~sf_buildings_ces['year_built'].isna()) & (sf_buildings_ces['dac_status'] == 'Non-DAC') & (sf_buildings_ces['permitted_panel_upgrade'] == False)
non_dac_x = pd.DataFrame(start_year - sf_buildings_ces.loc[non_dac_ind,'year_built'].dt.year)
non_dac_neg_ind = non_dac_x['year_built'] < 0
non_dac_x.loc[non_dac_neg_ind,'year_built'] = 0
non_dac_y = non_dac_ecdf(non_dac_x)
non_dac_upgrade_list = []

for pr in non_dac_y[:,0]: 
    non_dac_upgrade_list.append(np.random.choice(np.array([False, True]), size = 1, p = [1.0-pr, pr])[0])

non_dac_x['previous_upgrade'] = non_dac_upgrade_list

#%% Loop Through and Assess Upgrades for DAC and Non-DAC cohorts

upgrade_scale = [ 30., 60., 100., 125., 150., 200., 225., 300., 400., 600., 800.0, 1000.0]

sf_buildings_ces['inferred_panel_upgrade'] = False

# DAC Loop
for apn, row in dac_x.iterrows():

    as_built = sf_buildings_ces.loc[apn,'panel_size_as_built']
    
    if as_built == np.nan:
        continue
    
    existing = as_built

    if (row['previous_upgrade'] == True) & (sf_buildings_ces.loc[apn, 'permitted_panel_upgrade'] == False):
        level = upgrade_scale.index(as_built)
        existing = upgrade_scale[level + 1]
        sf_buildings_ces.loc[apn,'inferred_panel_upgrade'] = True
    
    sf_buildings_ces.loc[apn,'panel_size_existing'] = existing

# Non-DAC Loop
for apn, row in non_dac_x.iterrows():

    as_built = sf_buildings_ces.loc[apn,'panel_size_as_built']
    
    if as_built == np.nan:
        continue
    
    existing = as_built

    if (row['previous_upgrade'] == True) & (sf_buildings_ces.loc[apn, 'permitted_panel_upgrade'] == False):
        level = upgrade_scale.index(as_built)
        existing = upgrade_scale[level + 1]
        sf_buildings_ces.loc[apn,'inferred_panel_upgrade'] = True
    
    sf_buildings_ces.loc[apn,'panel_size_existing'] = existing

# %% Generate Change Statistics 

sf_buildings_ces['panel_upgrade'] = sf_buildings_ces.loc[:,['permitted_panel_upgrade','inferred_panel_upgrade']].any(axis = 1)

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
