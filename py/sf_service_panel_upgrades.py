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
from matplotlib import animation

from itertools import product
from sklearn.metrics import r2_score
from statsmodels.distributions.empirical_distribution import ECDF
from numpy.random import MT19937
from numpy.random import RandomState, SeedSequence

#%% Extract Database Connection Parameters from Environment

host = os.getenv('PG_HOST')
user = os.getenv('PG_USER')
password = os.getenv('PG_PASS')
port = os.getenv('PG_PORT')
db = os.getenv('PG_DB')

#%% Set Output Figures Directory

figure_dir = '/Users/edf/gdrive/projects/ladwp_la100_es/analysis/service_panel_upgrades/figures/'

#%% Establish DB Connection

db_con_string = 'postgresql://' + user + '@' + host + ':' + port + '/' + db
db_con = sql.create_engine(db_con_string)

#%% Read SF Input Table from DB

sf_buildings_sql = '''SELECT "AssessorParcelNumber",
                            "LotSizeSquareFeet",
                            "BuildingAreaSqFt",
                            "YearBuilt",
                            "roll_landbaseyear",
                            "roll_impbaseyear",
                            "NoOfUnits",
                            "TotalBedrooms",
                            "TotalActualBathCount",
                            "CensusTract"
                    FROM la100es.panel_data
                    WHERE   "city" = 'Los Angeles' AND
                            "usetype" = 'Residential' AND
                            "usedescription" = 'Single';'''

sf_buildings = pd.read_sql(sf_buildings_sql, db_con)
sf_buildings['CensusTract'] = pd.to_numeric(sf_buildings['CensusTract'], errors = 'coerce')

#%% Read Census Tract Level DAC Data

ces4_sql = '''SELECT * FROM ladwp.ces4'''
ces4 = gpd.read_postgis(ces4_sql, db_con, geom_col = 'geom')

#%% Read LADWP Boundary 

ladwp_sql = '''SELECT * FROM ladwp.service_territory'''
ladwp = gpd.read_postgis(ladwp_sql, con = db_con, geom_col = 'geom')

#%% Merge Parcels with CES Data

sf_buildings_ces = pd.merge(sf_buildings, ces4[['Tract', 'CIscoreP']], left_on = 'CensusTract', right_on = 'Tract')
sf_buildings_ces.set_index('Tract', inplace = True)

#%% Assign DAC Status

sf_buildings_ces['DAC Status'] = 'Non-DAC'
ind = sf_buildings_ces['CIscoreP'] >= 75.0
sf_buildings_ces.loc[ind, 'DAC Status'] = 'DAC'

#%% Plot the Number of SF Buildings by Tract

fig, ax = plt.subplots(1, 1, figsize = (10,10))

sf_count = sf_buildings.groupby('CensusTract')['AssessorParcelNumber'].agg('count')
sf_count_df = pd.merge(ces4.loc[:,['geom','Tract','CIscoreP']], sf_count, left_on = 'Tract', right_on = 'CensusTract')
sf_count_df.rename(columns = {'geom':'geometry'}, inplace = True)
sf_count_gdf = gpd.GeoDataFrame(sf_count_df)
sf_count_gdf.plot(column = 'AssessorParcelNumber', 
    ax = ax, 
    cmap = 'bone_r', 
    scheme = 'naturalbreaks',
    legend = True,
    legend_kwds = {'title': 'Single Family Homes\n[Counts]\n',
                    'loc': 'lower left'})

dac_ind = ces4['CIscoreP'] >= 75.0
non_dac_ind = ces4['CIscoreP'] < 75.0

ces4.loc[~(dac_ind | non_dac_ind)].boundary.plot(ax = ax, edgecolor = 'k', linewidth = 0.5)
ces4.loc[dac_ind].boundary.plot(ax = ax, color = 'tab:orange', linewidth = 0.5)
ces4.loc[non_dac_ind].boundary.plot(ax = ax, color = 'tab:blue', linewidth = 0.5)
ladwp.boundary.plot(ax = ax, edgecolor = 'black', linewidth = 1.5)

ax.set_ylim((-480000,-405000))
ax.set_xlim((120000,170000))
ax.set_axis_off()

fig.patch.set_facecolor('white')
fig.tight_layout()

fig.savefig(figure_dir + 'total_number_of_single_family_homes_by_tract_map.png', bbox_inches = 'tight', dpi = 300)

#%% Implement Initial Decision Tree

vintage_pre_1978 = sf_buildings_ces['YearBuilt'] < 1978
vintage_post_1978 = sf_buildings_ces['YearBuilt'] >= 1978

size_minus_1k = (sf_buildings_ces['BuildingAreaSqFt'] >= 0) & (sf_buildings_ces['BuildingAreaSqFt'] < 1000) 
size_1k_2k = (sf_buildings_ces['BuildingAreaSqFt'] >= 1000) & (sf_buildings_ces['BuildingAreaSqFt'] < 2000) 
size_2k_3k = (sf_buildings_ces['BuildingAreaSqFt'] >= 2000) & (sf_buildings_ces['BuildingAreaSqFt'] < 3000)
size_3k_4k = (sf_buildings_ces['BuildingAreaSqFt'] >= 3000) & (sf_buildings_ces['BuildingAreaSqFt'] < 4000)
size_4k_5k = (sf_buildings_ces['BuildingAreaSqFt'] >= 4000) & (sf_buildings_ces['BuildingAreaSqFt'] < 5000)
size_5k_8k = (sf_buildings_ces['BuildingAreaSqFt'] >= 5000) & (sf_buildings_ces['BuildingAreaSqFt'] < 8000)
size_8k_10k = (sf_buildings_ces['BuildingAreaSqFt'] >= 8000) & (sf_buildings_ces['BuildingAreaSqFt'] < 10000)
size_10k_20k = (sf_buildings_ces['BuildingAreaSqFt'] >= 10000) & (sf_buildings_ces['BuildingAreaSqFt'] < 20000)
size_20k_plus = (sf_buildings_ces['BuildingAreaSqFt'] >= 20000)

vintage_names = [   'vintage_pre_1978', 'vintage_post_1979']

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

sf_buildings_ces['PanelSizeAsBuilt'] = np.nan

for i in range(len(combs)):

    sf_buildings_ces.loc[(combs[i][0] & combs[i][1]),'PanelSizeAsBuilt'] = panel_sizes[i]

sf_buildings_ces.reset_index(inplace = True, drop = True)

#%% Plot As-Built Average Panel Size by Tract

sf_as_built_avg = sf_buildings_ces.groupby('CensusTract')['PanelSizeAsBuilt'].agg('mean')
sf_as_built_df = pd.merge(ces4.loc[:,['geom','Tract','CIscoreP']], sf_as_built_avg, left_on = 'Tract', right_on = 'CensusTract')
sf_as_built_df.rename(columns = {'geom':'geometry'}, inplace = True)
sf_as_built = gpd.GeoDataFrame(sf_as_built_df)

fig, ax = plt.subplots(1, 1, figsize = (10,10))

dac_ind = ces4['CIscoreP'] >= 75.0
non_dac_ind = ces4['CIscoreP'] < 75.0

ces4.loc[~(dac_ind | non_dac_ind)].boundary.plot(ax = ax, edgecolor = 'k', linewidth = 0.5)
ces4.loc[dac_ind].boundary.plot(ax = ax, color = 'tab:orange', linewidth = 0.5)
ces4.loc[non_dac_ind].boundary.plot(ax = ax, color = 'tab:blue', linewidth = 0.5)
ladwp.boundary.plot(ax = ax, edgecolor = 'black', linewidth = 1.5)

sf_as_built.plot(ax = ax, 
    column = 'PanelSizeAsBuilt',
    scheme='user_defined',
    classification_kwds = {'bins' : [30,60,100,125,150,200,300]},
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

dac_ind = sf_buildings_ces['DAC Status'] == 'DAC'
non_dac_ind = sf_buildings_ces['DAC Status'] == 'Non-DAC'

dac_sample = sf_buildings_ces.loc[dac_ind,:].sample(frac = 1.0, ignore_index = True)
non_dac_sample = sf_buildings_ces.loc[non_dac_ind,:].sample(frac = 1.0, ignore_index = True)

print('DAC Total:')
dac_sample['AssessorParcelNumber'].count()
print('DAC <200 Amps:')
print(dac_sample.loc[dac_sample['PanelSizeAsBuilt'] < 200,'AssessorParcelNumber'].count())
print('DAC >=200 Amps')
print(dac_sample.loc[dac_sample['PanelSizeAsBuilt'] >= 200,'AssessorParcelNumber'].count())

print('Non-DAC Total:')
non_dac_sample['AssessorParcelNumber'].count()
print('DAC <200 Amps:')
print(non_dac_sample.loc[non_dac_sample['PanelSizeAsBuilt'] < 200,'AssessorParcelNumber'].count())
print('DAC >=200 Amps')
print(non_dac_sample.loc[non_dac_sample['PanelSizeAsBuilt'] >= 200,'AssessorParcelNumber'].count())

#%% Plot SF as built panel size ratings

fig, ax = plt.subplots(1,2,figsize = (10,8), sharey = True)

sns.histplot(x = 'YearBuilt', 
    y = 'PanelSizeAsBuilt', 
    data = dac_sample, 
    color = 'tab:orange', 
    ax = ax[0], 
    bins = 60, 
    legend = True, 
    label = 'DAC', 
    cbar = True, 
    cbar_kws = {'label':'Number of Single Family Homes', 'orientation':'horizontal'}, 
    vmin=0, vmax=4000)
sns.histplot(x = 'YearBuilt',
    y = 'PanelSizeAsBuilt', 
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

counts = sf_buildings_ces.groupby('PanelSizeAsBuilt')['AssessorParcelNumber'].agg('count')
dac_counts = sf_buildings_ces.groupby(['DAC Status', 'PanelSizeAsBuilt'])['AssessorParcelNumber'].agg('count')
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

#%% Import Permit Data

sf_permits_sql = '''SELECT  "county_landuse_description",
                            "apn",
                            "census_tract",
                            "permit_type",
                            "permit_description",
                            "permit_issue_date"::text,
                            "panel_upgrade"
                    FROM la100es.panel_data_permits
                    WHERE   "city" = 'Los Angeles' AND
                            "usetype" = 'Residential' AND
                            "usedescription" = 'Single';'''

sf_permits = pd.read_sql(sf_permits_sql, db_con)

sf_permits['census_tract'] = pd.to_numeric(sf_permits['census_tract'], errors = 'coerce')               
sf_permits.loc[sf_permits['permit_issue_date'] == '0001-01-01 BC', 'permit_issue_date'] = ''
sf_permits['permit_issue_date'] = pd.to_datetime(sf_permits['permit_issue_date'], format = '%Y-%m-%d')

#%% Join Permit Data on APN

sf_buildings_ces_permits = pd.merge(sf_buildings_ces, sf_permits, left_on = 'AssessorParcelNumber', right_on = 'apn')

#%% Generate Time Series of Permits by DAC Status

upgrade_ind = sf_buildings_ces_permits['panel_upgrade'] == True

permit_ts = sf_buildings_ces_permits.loc[upgrade_ind].groupby([pd.Grouper(key='permit_issue_date', axis=0, freq='1Y'), 'DAC Status'])['AssessorParcelNumber'].agg('count')
permit_ts = permit_ts.reset_index()
permit_ts = permit_ts.rename(columns = {'AssessorParcelNumber': 'PermitCount'})

#%% Generate Cumsum of Permits by DAC Status

permit_cs = sf_buildings_ces_permits.loc[upgrade_ind].groupby([pd.Grouper(key='permit_issue_date', axis=0, freq='1Y'), 'DAC Status'])['AssessorParcelNumber'].agg('count')
permit_cs = permit_cs.sort_index()

dac_vals = permit_cs.loc(axis = 0)[:,'DAC'].cumsum()
non_dac_vals = permit_cs.loc(axis = 0)[:,'Non-DAC'].cumsum()

permit_cs = pd.concat([dac_vals, non_dac_vals], axis = 0).sort_index()
permit_cs = permit_cs.reset_index()
permit_cs = permit_cs.rename(columns = {'AssessorParcelNumber': 'PermitCount'})

# %% Plot Time Series of Permit Counts and Cumulative Sums

fig, ax = plt.subplots(2, 1, figsize = (8,8), sharex = True)

hue_order = ['Non-DAC', 'DAC']

sns.lineplot(x = 'permit_issue_date', 
    y = 'PermitCount', 
    hue = 'DAC Status',
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
    y = 'PermitCount',
    hue = 'DAC Status',
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

tracts = sf_buildings_ces_permits['census_tract'].unique()
ind = ces4['Tract'].isin(tracts)
sf_permit_tracts = ces4.loc[ind,:]

permits_per_tract = sf_buildings_ces_permits.groupby(['census_tract'])['AssessorParcelNumber'].agg('count')
permits_per_tract_ces = pd.merge(ces4.loc[:,['geom','Tract']], permits_per_tract, left_on = 'Tract', right_index = True)

#%% Plot Census Tracts with Permit Data

fig, ax = plt.subplots(1, 1, figsize = (10,10))

dac_ind = ces4['CIscoreP'] >= 75.0
non_dac_ind = ces4['CIscoreP'] < 75.0

ces4.loc[~(dac_ind | non_dac_ind)].boundary.plot(ax = ax, edgecolor = 'k', linewidth = 0.5)
ces4.loc[dac_ind].boundary.plot(ax = ax, color = 'tab:orange', linewidth = 0.5)
ces4.loc[non_dac_ind].boundary.plot(ax = ax, color = 'tab:blue', linewidth = 0.5)
ladwp.boundary.plot(ax = ax, edgecolor = 'black', linewidth = 1.5)

permits_per_tract_ces.plot(ax = ax,
    column = 'AssessorParcelNumber',
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

pu_100 = sf_permits['permit_description'].str.contains(' 100')
pu_125 = sf_permits['permit_description'].str.contains(' 125')
pu_150 = sf_permits['permit_description'].str.contains(' 150')
pu_200 = sf_permits['permit_description'].str.contains(' 200')
pu_225 = sf_permits['permit_description'].str.contains(' 225')
pu_300 = sf_permits['permit_description'].str.contains(' 300')
pu_400 = sf_permits['permit_description'].str.contains(' 400')
pu_600 = sf_permits['permit_description'].str.contains(' 600')

pu_solar = sf_permits['permit_description'].str.contains('solar', case = False)
pu_ev = sf_permits['permit_description'].str.contains('ev', case = False)
pu_ac = sf_permits['permit_description'].str.contains('ac', case = False)

pu_other = ~(pu_100 | pu_125 | pu_150 | pu_200 | pu_225 | pu_300 | pu_400 | pu_600 | pu_solar | pu_ev | pu_ac)

#%% Prep Receiver Columns

sf_buildings_ces['PanelSizeExisting'] = sf_buildings_ces['PanelSizeAsBuilt']

sf_buildings_ces.set_index('AssessorParcelNumber', inplace=True, drop = True)

#%% Peform Filtering Assignment

upgrade_scale = [ 30., 60., 100., 125., 150., 200., 225., 300., 400., 600., 800.0, 1000.0]

ind_dict = {100.0:pu_100,
            125.0:pu_125,
            150.0:pu_150, 
            200.0:pu_200, 
            225.0:pu_225,
            300.0:pu_300, 
            400.0:pu_400,
            600.0:pu_600}

sf_buildings_ces['PermittedPanelUpgrade'] = False

for k, v in ind_dict.items():
    
    v[v.isna()] = False
    apns = sf_permits.loc[v,'apn']
    as_built_ind = sf_buildings_ces.index.isin(apns)
    proposed = sf_buildings_ces.loc[as_built_ind,'PanelSizeAsBuilt']
    change_ind = proposed < k
    proposed.loc[change_ind] = k
    sf_buildings_ces.loc[proposed.index,'PanelSizeExisting'] = proposed

other_ind = (pu_solar | pu_other | pu_ev | pu_ac)
other_ind[other_ind.isna()] = False
apns = sf_permits.loc[other_ind, 'apn']
as_built_ind = sf_buildings_ces.index.isin(apns)
proposed = sf_buildings_ces.loc[as_built_ind, 'PanelSizeAsBuilt']

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

sf_buildings_ces.loc[proposed.index, 'PanelSizeExisting'] = proposed

upgrade_ind = sf_buildings_ces['PanelSizeExisting'] > sf_buildings_ces['PanelSizeAsBuilt']
sf_buildings_ces.loc[upgrade_ind, 'PermittedPanelUpgrade'] = True

#%% Compute Time Difference Between Construction Date and Upgrade Date

upgrade_time_delta = pd.DataFrame(sf_buildings_ces_permits.loc[:,'apn'].copy(deep = True))
upgrade_time_delta['time_delta'] = pd.to_numeric(sf_buildings_ces_permits.loc[:,'permit_issue_date'].dt.year - sf_buildings_ces_permits.loc[:,'YearBuilt'])
upgrade_time_delta.set_index('apn', inplace = True)
neg = upgrade_time_delta['time_delta'] < 0
upgrade_time_delta.loc[neg] = 0

sf_buildings_ces['upgrade_time_delta'] = np.nan
sf_buildings_ces.loc[upgrade_time_delta.index.get_level_values(0),'upgrade_time_delta'] = upgrade_time_delta.values

#%% Plot Time-Delta Distribution for Each Permit Year

def animate_func(num):

    hue_order = [ 'Non-DAC','DAC']

    ax.clear()
    test_years = sf_buildings_ces_permits['permit_issue_date'].dt.year.unique()
    test_years = np.sort(test_years)
    y = test_years[num+1]
    ind = sf_buildings_ces_permits['permit_issue_date'].dt.year == y
    data = sf_buildings_ces_permits.loc[ind]

    sns.histplot(x = 'YearBuilt',
        data = data,
        hue = 'DAC Status',
        kde = True,
        legend = True,
        hue_order = hue_order,
        ax = ax,
        bins = np.arange(1900,2020,2))

    ax.grid(True)
    ax.set_title(str(y))
    ax.set_xlim(1900,2020)
    ax.set_ylim(0,1500)
        
fig = plt.figure()
ax = plt.axes()

numDataPoints = sf_buildings_ces_permits['permit_issue_date'].dt.year.unique().shape[0]-1

line_ani = animation.FuncAnimation(fig, 
    animate_func, 
    interval=1000,   
    frames=numDataPoints)

plt.show()

f = figure_dir + 'la_city_panel_permits_histogram_animation.gif'
writergif = animation.PillowWriter(fps=numDataPoints/16)
line_ani.save(f, writer=writergif)

# %% Compute ECDF for As-Built Year

nan_ind = ~sf_buildings_ces_permits['YearBuilt'].isna()
dac_ind = sf_buildings_ces_permits['DAC Status'] == 'DAC'
dac_permit_sum = dac_ind.sum()
non_dac_ind = sf_buildings_ces_permits['DAC Status'] == 'Non-DAC'
non_dac_permit_sum = non_dac_ind.sum()

dac_ages = pd.DataFrame(2022-sf_buildings_ces_permits.loc[(nan_ind & dac_ind),'YearBuilt'])
non_dac_ages = pd.DataFrame(2022-sf_buildings_ces_permits.loc[(nan_ind & non_dac_ind),'YearBuilt'])

fig, ax = plt.subplots(1,1,figsize = (8,5))
sns.ecdfplot(data=dac_ages, x='YearBuilt', ax=ax, color = 'tab:orange')
sns.ecdfplot(data=non_dac_ages, x='YearBuilt', ax=ax, color = 'tab:blue')
ax.set_xlabel('Age of Home')
ax.set_ylabel('Proportion of Single Family Homes\nwith Permitted Panel Upgrades')
ax.autoscale(enable=True, axis='x', tight = True)
range_max = dac_ages['YearBuilt'].max()
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

dac_ecdf = ECDF(dac_ages['YearBuilt'])

dac_odds_ratio = non_dac_permit_sum / dac_permit_sum
start_year = 1996

dac_ind = (~sf_buildings_ces['YearBuilt'].isna()) & (sf_buildings_ces['DAC Status'] == 'DAC') & (sf_buildings_ces['PermittedPanelUpgrade'] == False)
dac_x = pd.DataFrame(start_year - sf_buildings_ces.loc[dac_ind,'YearBuilt'])
dac_neg_ind = dac_x['YearBuilt'] < 0
dac_x.loc[dac_neg_ind,'YearBuilt'] = 0
dac_y = dac_ecdf(dac_x) / dac_odds_ratio
dac_upgrade_list = []

for pr in dac_y[:,0]: 
    dac_upgrade_list.append(np.random.choice(np.array([False, True]), size = 1, p = [1.0-pr, pr])[0])

dac_x['PreviousUpgrade'] = dac_upgrade_list

non_dac_ecdf = ECDF(non_dac_ages['YearBuilt'])

non_dac_ind = (~sf_buildings_ces['YearBuilt'].isna()) & (sf_buildings_ces['DAC Status'] == 'Non-DAC') & (sf_buildings_ces['PermittedPanelUpgrade'] == False)
non_dac_x = pd.DataFrame(start_year - sf_buildings_ces.loc[non_dac_ind,'YearBuilt'])
non_dac_neg_ind = non_dac_x['YearBuilt'] < 0
non_dac_x.loc[non_dac_neg_ind,'YearBuilt'] = 0
non_dac_y = non_dac_ecdf(non_dac_x)
non_dac_upgrade_list = []

for pr in non_dac_y[:,0]: 
    non_dac_upgrade_list.append(np.random.choice(np.array([False, True]), size = 1, p = [1.0-pr, pr])[0])

non_dac_x['PreviousUpgrade'] = non_dac_upgrade_list

#%% Loop Through and Assess Upgrades for DAC and Non-DAC cohorts

upgrade_scale = [ 30., 60., 100., 125., 150., 200., 225., 300., 400., 600., 800.0, 1000.0]

sf_buildings_ces['InferredPanelUpgrade'] = False

# DAC Loop
for apn, row in dac_x.iterrows():

    as_built = sf_buildings_ces.loc[apn,'PanelSizeAsBuilt']
    
    if as_built == np.nan:
        continue
    
    existing = as_built

    if (row['PreviousUpgrade'] == True) & (sf_buildings_ces.loc[apn, 'PermittedPanelUpgrade'] == False):
        level = upgrade_scale.index(as_built)
        existing = upgrade_scale[level + 1]
        sf_buildings_ces.loc[apn,'InferredPanelUpgrade'] = True
    
    sf_buildings_ces.loc[apn,'PanelSizeExisting'] = existing

# Non-DAC Loop
for apn, row in non_dac_x.iterrows():

    as_built = sf_buildings_ces.loc[apn,'PanelSizeAsBuilt']
    
    if as_built == np.nan:
        continue
    
    existing = as_built

    if (row['PreviousUpgrade'] == True) & (sf_buildings_ces.loc[apn, 'PermittedPanelUpgrade'] == False):
        level = upgrade_scale.index(as_built)
        existing = upgrade_scale[level + 1]
        sf_buildings_ces.loc[apn,'InferredPanelUpgrade'] = True
    
    sf_buildings_ces.loc[apn,'PanelSizeExisting'] = existing

# %% Generate Change Statistics 

sf_buildings_ces['PanelUpgrade'] = sf_buildings_ces.loc[:,['PermittedPanelUpgrade','InferredPanelUpgrade']].any(axis = 1)

as_built_mean = sf_buildings_ces.groupby('CensusTract')['PanelSizeAsBuilt'].agg(['mean'])
as_built_mean.columns = ['mean_sf_panel_size_as_built']

sf_property_count = sf_buildings_ces.groupby('CensusTract')['LotSizeSquareFeet'].agg(['count'])
sf_property_count.columns = ['sf_homes_count']

existing_mean = sf_buildings_ces.groupby('CensusTract')['PanelSizeExisting'].agg(['mean'])
existing_mean.columns = ['mean_sf_panel_size_existing']

upgrades_count = sf_buildings_ces.groupby('CensusTract')['PanelUpgrade'].agg('sum')
upgrades_count.name = 'upgrade_count'

panel_stats = pd.concat([as_built_mean, existing_mean, upgrades_count, sf_property_count], axis = 1)

panel_stats['upgrade_freq_pct'] = (panel_stats['upgrade_count'] / panel_stats['sf_homes_count']).multiply(100.0)

panel_stats['upgrade_delta_amps'] = panel_stats['mean_sf_panel_size_existing'] - panel_stats['mean_sf_panel_size_as_built']
panel_stats['upgrade_delta_pct'] = panel_stats[['mean_sf_panel_size_as_built', 'mean_sf_panel_size_existing']].pct_change(axis = 1).iloc[:,1].multiply(100.0)

panel_stats_ces = pd.merge(panel_stats, ces4[['Tract','CIscoreP', 'geom']], left_index = True, right_on = 'Tract', how = 'left')

dac_ind = panel_stats_ces['CIscoreP'] >= 75.0
panel_stats_ces['DAC Status'] = 'Non-DAC'
panel_stats_ces.loc[dac_ind, 'DAC Status'] = 'DAC'

panel_stats_ces = panel_stats_ces.set_index('Tract', drop = True)
panel_stats_ces_geo = gpd.GeoDataFrame(panel_stats_ces, geometry = 'geom')

#%% Diagnostic Plot of Change Statistics

fig, ax = plt.subplots(1,1, figsize=(5,5))

total_permit_counts = panel_stats_ces.groupby('DAC Status')['upgrade_count'].agg('sum').reset_index()

sns.barplot(x = 'DAC Status',
    y = 'upgrade_count', 
    data = total_permit_counts,
    order = ['Non-DAC', 'DAC'], 
    ax = ax)

ax.set_ylabel('Total Number of Panel Upgrades \n[Homes]')
ax.grid(True)

ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))

fig.tight_layout()
fig.patch.set_facecolor('white')

fig.savefig(figure_dir + 'lac_sf_panel_upgrade_total_counts_barplot.png', bbox_inches = 'tight', dpi = 300)

#%% Diagnostic Plot of Change Statistics

fig, ax = plt.subplots(1,1, figsize=(5,5))

sns.boxplot(x = 'DAC Status',
    y = 'upgrade_delta_amps', 
    data = panel_stats_ces, 
    ax = ax)

ax.set_ylabel('Change in Mean Panel Size \n(As-built -> Existing) \n[Amps]')
ax.grid(True)

fig.tight_layout()
fig.patch.set_facecolor('white')

fig.savefig(figure_dir + 'lac_sf_panel_upgrade_deltas_boxplots.png', bbox_inches = 'tight', dpi = 300)

#%% Diagnostic Plot of Change Statistics

fig, ax = plt.subplots(1,1, figsize=(5,5))

sns.scatterplot(x = 'mean_sf_panel_size_as_built',
    y = 'upgrade_delta_amps',
    hue = 'DAC Status',
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
    hue = 'DAC Status',
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

dac_ind = ces4['CIscoreP'] >= 75.0
non_dac_ind = ces4['CIscoreP'] < 75.0

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

dac_ind = ces4['CIscoreP'] >= 75.0
non_dac_ind = ces4['CIscoreP'] < 75.0

ces4.loc[~(dac_ind | non_dac_ind)].boundary.plot(ax = ax, edgecolor = 'k', linewidth = 0.5)
ces4.loc[dac_ind].boundary.plot(ax = ax, color = 'tab:orange', linewidth = 0.5)
ces4.loc[non_dac_ind].boundary.plot(ax = ax, color = 'tab:blue', linewidth = 0.5)
ladwp.boundary.plot(ax = ax, edgecolor = 'black', linewidth = 1.5)
panel_stats_ces_geo.plot(column = 'upgrade_delta_amps', 
    scheme = 'userdefined',
    k = 7,
    cmap = 'bone_r', 
    classification_kwds = {'bins' : [25,50,75,100,125,150]},
    legend = True,
    legend_kwds = {'title': 'Single Family Homes\nChange in Average Panel Size\nFrom As-Built -> Existing [Amps]\n',
                    'loc': 'lower left'},
    ax = ax)

ax.set_ylim((-480000,-405000))
ax.set_xlim((120000,170000))
ax.set_axis_off()

fig.tight_layout()
fig.patch.set_facecolor('white')

fig.savefig(figure_dir + 'lac_sf_panel_ratings_delta_geographic_distribution_quiver_map.png', bbox_inches = 'tight', dpi = 300)

#%% Plot SF Existing panel size ratings

dac_ind = (sf_buildings_ces['DAC Status'] == 'DAC') 
non_dac_ind = (sf_buildings_ces['DAC Status'] == 'Non-DAC')

dac_sample = sf_buildings_ces.loc[dac_ind,:]
non_dac_sample = sf_buildings_ces.loc[non_dac_ind,:]

fig, ax = plt.subplots(1,2,figsize = (10,8), sharey = True, sharex = True)

sns.histplot(x = 'YearBuilt', 
    y = 'PanelSizeExisting', 
    data = dac_sample, 
    color = 'tab:orange', 
    ax = ax[0], 
    bins = 60, 
    legend = True, 
    label = 'DAC', 
    cbar = True, 
    cbar_kws = {'label':'Number of Single Family Homes', 'orientation':'horizontal'}, 
    vmin=0, vmax=4000)
sns.histplot(x = 'YearBuilt',
    y = 'PanelSizeExisting', 
    data = non_dac_sample, 
    color = 'tab:blue', 
    ax = ax[1], 
    bins = 60, 
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

dac_permitted_panel_stats = dac_sample.groupby(['PermittedPanelUpgrade'])['CensusTract'].agg('count')
non_dac_permitted_panel_stats = non_dac_sample.groupby(['PermittedPanelUpgrade'])['CensusTract'].agg('count')

dac_inferred_panel_stats = dac_sample.groupby(['InferredPanelUpgrade'])['CensusTract'].agg('count')
non_dac_inferred_panel_stats = non_dac_sample.groupby(['InferredPanelUpgrade'])['CensusTract'].agg('count')

dac_sample.loc[:,'roll_impbaseyear'] = pd.to_numeric(dac_sample.loc[:,'roll_impbaseyear'])
dac_sample.loc[np.isinf(dac_sample['roll_impbaseyear']),'roll_impbaseyear'] = np.nan
dac_imp_year_mean = dac_sample['roll_impbaseyear'].mean()
dac_vintage_year_mean = dac_sample['YearBuilt'].mean()

non_dac_sample.loc[:,'roll_impbaseyear'] = pd.to_numeric(non_dac_sample.loc[:,'roll_impbaseyear'])
non_dac_sample.loc[np.isinf(non_dac_sample['roll_impbaseyear']),'roll_impbaseyear'] = np.nan
non_dac_imp_year_mean = non_dac_sample['roll_impbaseyear'].mean()
non_dac_vintage_year_mean = non_dac_sample['YearBuilt'].mean()

print('DAC Census Tract Upgrade Stats:')

print('Average Home Vintage Year: {}'.format(np.round(dac_vintage_year_mean)))
print('Average Improvement Year: {}'.format(np.round(dac_imp_year_mean)))
print('Permitted Upgrades: {}%'.format(np.round(dac_permitted_panel_stats.loc[True] / dac_sample.shape[0] * 100)))
print('Inferred Upgrades: {}%'.format(np.round(dac_inferred_panel_stats.loc[True] / dac_sample.shape[0] * 100)))
print('Not Upgraded: {}%'.format(np.round((dac_sample.shape[0] - (dac_inferred_panel_stats.loc[True] + dac_permitted_panel_stats.loc[True])) / dac_sample.shape[0] * 100)))

print('\n')

print('Non-DAC Census Tract Upgrade Stats:')

print('Average Home Vintage Year: {}'.format(np.round(non_dac_vintage_year_mean)))
print('Average Improvement Year: {}'.format(np.round(non_dac_imp_year_mean)))
print('Permitted Upgrades: {}%'.format(np.round(non_dac_permitted_panel_stats.loc[True] / non_dac_sample.shape[0] * 100)))
print('Inferred Upgrades: {}%'.format(np.round(non_dac_inferred_panel_stats.loc[True] / non_dac_sample.shape[0] * 100)))
print('Not Upgraded: {}%'.format(np.round((non_dac_sample.shape[0] - (non_dac_inferred_panel_stats.loc[True] + non_dac_permitted_panel_stats.loc[True])) / non_dac_sample.shape[0] * 100)))

#%% Print Capacity Stats

dac_sample_stats = dac_sample.groupby(['PanelSizeExisting'])['CensusTract'].agg('count')
non_dac_sample_stats = non_dac_sample.groupby(['PanelSizeExisting'])['CensusTract'].agg('count')

insufficient = [30.0, 60.0]
uncertain = [100.0, 125.0, 150.0]
sufficient = [200.0, 300.0, 400.0, 600.0, 800.0]

print('DAC Census Tract Capacity Stats:')

print('<100 Amps: {}%'.format(np.round(dac_sample_stats[insufficient].sum() / dac_sample.shape[0] * 100, 2)))
print('>=100 : <200 Amps: {}%'.format(np.round(dac_sample_stats[uncertain].sum() / dac_sample.shape[0] * 100, 2)))
print('>=200 Amps: {}%'.format(np.round(dac_sample_stats[sufficient].sum() / dac_sample.shape[0] * 100, 2)))

print('\n')

print('Non-DAC Census Tract Stats:')

print('<100 Amps: {}%'.format(np.round(non_dac_sample_stats[insufficient].sum() / non_dac_sample.shape[0] * 100, 2)))
print('>=100 : <200 Amps: {}%'.format(np.round(non_dac_sample_stats[uncertain].sum() / non_dac_sample.shape[0] * 100, 2)))
print('>=200 Amps: {}%'.format(np.round(non_dac_sample_stats[sufficient].sum() / non_dac_sample.shape[0] * 100, 2)))
