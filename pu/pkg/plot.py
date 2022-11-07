#%% Package Imports

import pandas as pd
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, StrMethodFormatter
import seaborn as sns

#%% Plot the Number of SF Buildings by Tract

def SingleFamilyCountsByTract(sf_buildings, ces4, ladwp, figure_dir):

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
