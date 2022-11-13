#%% Package Imports

import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, StrMethodFormatter
import seaborn as sns

#%% Plot the Number of SF Buildings by Tract

def SingleFamilyCountsMap(sf_buildings, ces4, ladwp, figure_dir):

    fig, ax = plt.subplots(1, 1, figsize = (10,10))

    sf_count = sf_buildings.groupby('census_tract')['apn'].agg('count')
    sf_count_df = pd.merge(ces4.loc[:,['geom','tract','ciscorep']], sf_count, left_on = 'tract', right_on = 'census_tract')
    sf_count_df.rename(columns = {'geom':'geometry'}, inplace = True)
    sf_count_gdf = gpd.GeoDataFrame(sf_count_df)
    sf_count_gdf.plot(column = 'apn', 
        ax = ax, 
        cmap = 'bone_r', 
        scheme = 'naturalbreaks',
        legend = True,
        legend_kwds = {'title': 'Single Family Homes\n[Counts]\n',
                        'loc': 'lower left'})

    dac_ind = ces4['ciscorep'] >= 75.0
    non_dac_ind = ces4['ciscorep'] < 75.0

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

    return

#%% Plot As-Built Average Panel Size by Tract

def AsBuiltPanelRatingsMap(sf_buildings_ces, ces4, ladwp, figure_dir):

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

    return

#%% Plot SF as built panel size ratings

def AsBuiltPanelRatingsHist(sf_buildings_ces, ces4, ladwp, figure_dir):
    '''Paired DAC / Non-DAC 2D histogram of panel sizes by building
    construction vintage years'''
    
    fig, ax = plt.subplots(1,2,figsize = (10,8), sharey = True)

    dac_ind = sf_buildings_ces['dac_status'] == 'DAC'
    non_dac_ind = sf_buildings_ces['dac_status'] == 'Non-DAC'

    dac_sample = sf_buildings_ces.loc[dac_ind,:]
    non_dac_sample = sf_buildings_ces.loc[non_dac_ind,:]

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
        bins = 80, 
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

    return

#%% Plot As-Built Panel Stats

def AsBuiltPanelRatingsBar(sf_buildings_ces, figure_dir):
    '''Simple barplot of single family as-built panel ratings
    separated by DAC status'''
    
    # Compute counts

    counts = sf_buildings_ces.groupby('panel_size_as_built')['apn'].agg('count')
    dac_counts = sf_buildings_ces.groupby(['dac_status', 'panel_size_as_built'])['apn'].agg('count')
    dac_counts = dac_counts.unstack(level= 0)
    dac_counts.index = dac_counts.index.astype(int)

    # Plot Counts

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

    return

def PermitTimeSeries(sf_buildings_ces, figure_dir):
    '''Plot annual total and cumulative total panel upgrade permits
    separated by DAC status'''

    # Generate Time Series of Permits by DAC Status

    upgrade_ind = sf_buildings_ces['panel_related_permit'] == True
    permit_ts = sf_buildings_ces.loc[upgrade_ind].groupby([pd.Grouper(key='permit_issue_date', axis=0, freq='1Y'), 'dac_status'])['apn'].agg('count')
    permit_ts = permit_ts.reset_index()
    permit_ts = permit_ts.rename(columns = {'apn': 'permit_count'})

    # Generate Cumsum of Permits by DAC Status

    permit_cs = sf_buildings_ces.loc[upgrade_ind].groupby([pd.Grouper(key='permit_issue_date', axis=0, freq='1Y'), 'dac_status'])['apn'].agg('count')
    permit_cs = permit_cs.sort_index()
    dac_vals = permit_cs.loc(axis = 0)[:,'DAC'].cumsum()
    non_dac_vals = permit_cs.loc(axis = 0)[:,'Non-DAC'].cumsum()
    permit_cs = pd.concat([dac_vals, non_dac_vals], axis = 0).sort_index()
    permit_cs = permit_cs.reset_index()
    permit_cs = permit_cs.rename(columns = {'apn': 'permit_count'})

    # Plot Time Series of Permit Counts and Cumulative Sums

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

    return

#%% Function to Map the Cumulative Total Number of Permits by Tract

def PermitCountsMap(sf_buildings_ces, ces4, ladwp, figure_dir):
    '''Function to map the cumulative total number of buildings with
    panel upgrade pemits by census tract and DAC status'''

    # Count the Total Number of Buildings in the Permit Data Tracts

    tracts = sf_buildings_ces['census_tract'].unique()
    ind = ces4['tract'].isin(tracts)
    sf_permit_tracts = ces4.loc[ind,:]

    permits_per_tract = sf_buildings_ces.groupby(['census_tract'])['apn'].agg('count')
    permits_per_tract_ces = pd.merge(ces4.loc[:,['geom','tract']], permits_per_tract, left_on = 'tract', right_index = True)

    # Plot Census Tracts with Permit Data

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
                        "labels": ["1-100", "100-250", "250-500", "500-750","750-1000", "1000-1500", "1500-2000","2000-3160"]})

    ax.set_ylim((-480000,-405000))
    ax.set_xlim((120000,170000))
    ax.set_axis_off()

    fig.patch.set_facecolor('white')
    fig.tight_layout()

    fig.savefig(figure_dir + 'lac_sf_permit_geographic_distribution_map.png', bbox_inches = 'tight', dpi = 300)

    return

#%% Function to Animate Permit Histogram by Vintage Year

def PermitCountsHistAnimation(sf_buildings_ces, figure_dir):
    '''Generate a vintage year based permit frequency count histogram
    for each unique year in the permit dataset interval.'''

    def AnimateFunc(num):
        '''Animation worker function'''

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

        return
        
    fig = plt.figure()
    ax = plt.axes()

    numDataPoints = sf_buildings_ces['permit_issue_date'].dt.year.unique().shape[0]-1

    line_ani = animation.FuncAnimation(fig, 
        AnimateFunc, 
        interval=1000,   
        frames=numDataPoints)

    plt.show()

    f = figure_dir + 'la_city_panel_permits_histogram_animation.gif'
    writergif = animation.PillowWriter(fps=numDataPoints/16)
    line_ani.save(f, writer=writergif)

    return

#%% Plot ECDF for As-Built Year by DAC Status

def PermitVintageYearECDF(sf_buildings_ces, figure_dir):  
    '''Function to plot the empirical cdf's for permitted panel upgrade
    by the vintage year of the property and DAC status'''

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

    return 

#%% Diagnostic Plot of Change Statistics

def ExistingPanelRatingsChangeCountsBar(panel_stats_ces_geo, figure_dir):
    '''Function to generate a paired barchart showing the count of homes
    having received upgrades by DAC Status'''

    total_permit_counts = panel_stats_ces_geo.groupby('dac_status')['upgrade_count'].agg('sum').reset_index()

    fig, ax = plt.subplots(1,1, figsize=(5,5))

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

    return

#%% Diagnostic Plot of Change Statistics

def ExistingPanelRatingsChangeAmpsBox(panel_stats_ces_geo, figure_dir):
    '''Function to generate a pairwise set of boxplots showing the magnitude
    in amps of the upgrades from as-built to existing by DAC status'''

    fig, ax = plt.subplots(1,1, figsize=(5,5))

    sns.boxplot(x = 'dac_status',
        y = 'upgrade_delta_amps', 
        data = panel_stats_ces_geo, 
        ax = ax)

    ax.set_ylabel('Change in Mean Panel Size \n(As-built -> Existing) \n[Amps]')
    ax.set_xlabel('DAC Status')
    ax.grid(True)

    fig.tight_layout()
    fig.patch.set_facecolor('white')

    fig.savefig(figure_dir + 'lac_sf_panel_upgrade_deltas_boxplots.png', bbox_inches = 'tight', dpi = 300)

    return

#%% Diagnostic Plot of Change Statistics

def ExistingPanelRatingsChangeAmpsScatter(panel_stats_ces_geo, figure_dir):
    '''Function to generate a scatterplot of the change in the average panel size
    from as-built to existing condition by DAC status.'''

    fig, ax = plt.subplots(1,1, figsize=(5,5))

    sns.scatterplot(x = 'mean_sf_panel_size_as_built',
        y = 'upgrade_delta_amps',
        hue = 'dac_status',
        data = panel_stats_ces_geo, 
        ax = ax,
        alpha = 0.5)

    ax.set_ylabel('Change in Mean Panel Rating\n(As-built -> Existing) \n[Amps]')
    ax.set_xlabel('Mean Panel Size \n (As-built) [Amps]')
    ax.grid(True)

    fig.tight_layout()
    fig.patch.set_facecolor('white')

    fig.savefig(figure_dir + 'lac_sf_panel_upgrade_deltas_vs_ces_scatterplot.png', bbox_inches = 'tight', dpi = 300)

    return 

#%% Diagnostic Plot of Change Statistics

def ExistingPanelRatingsChangeAmpsHist(panel_stats_ces_geo, figure_dir):
    '''Function to generate a pairwise histogram of the change in the average panel size
    from as-built to existing condition by DAC status.'''

    fig, ax = plt.subplots(1,1, figsize=(5,5))

    sns.histplot(x = 'mean_sf_panel_size_existing',
        hue = 'dac_status',
        data = panel_stats_ces_geo,
        bins = 30,
        ax = ax)

    ax.axvline(200, color = 'r', linestyle = '--', linewidth = 2)
    ax.set_xlabel('Mean Panel Size \n (Existing) \n[Amps]')
    ax.set_ylabel('Census Tracts \n[Counts]')
    ax.grid(True)

    fig.tight_layout()
    fig.patch.set_facecolor('white')

    fig.savefig(figure_dir + 'lac_sf_panel_upgrade_existing_means_histplot.png', bbox_inches = 'tight', dpi = 300)

    return

#%% Generate Diagnostic Map Plot

def ExistingPanelRatingsMap(panel_stats_ces_geo, ces4, ladwp, figure_dir):
    '''Function generate a census tract level map of the average existing
    panel size ratings'''

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
        classification_kwds = {'bins' : [30,60,100,125,150,200,300]},
        k = 10,
        cmap='bone_r',
        legend = True,
        legend_kwds = {'title': 'Single Family Homes\nAverage Panel Size Rating\nExisting [Amps]',
                        'loc': 'lower left',
                        "labels": ["","30-60", "60-100", "100-125", "125-150", "150-200", "200-300"]})

    ax.set_ylim((-480000,-405000))
    ax.set_xlim((120000,170000))
    ax.set_axis_off()

    fig.tight_layout()
    fig.patch.set_facecolor('white')

    fig.savefig(figure_dir + 'lac_sf_panel_ratings_existing_geographic_distribution_map.png', bbox_inches = 'tight', dpi = 300)

    return

#%% Generate Change Percentage Plot

def ExistingPanelRatingsChangePctMap(panel_stats_ces_geo, ces4, ladwp, figure_dir):
    '''Function to plot the percentage change in average panel sizes from 
    as-built to existing condition by census tract and DAC status'''

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

    return

#%% Plot SF Existing panel size ratings

def ExistingPanelRatingsHist(sf_buildings_ces, ces4, ladwp, figure_dir):
    '''Function to plot a set of 2d histograms relating the frequency of 
    existing panel sizes to vintage year by dac status''' 

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
        bins = 60, 
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
        bins = 80, 
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

    return 