#%% Package Imports

import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
import os

#%% Set Environment

os.chdir('/Users/edf/gdrive/projects/ladwp_la100_es/analysis/service_panel_upgrades/permit_data/')

#%% Read Data

pre_2010 = pd.read_csv('City_LosAngeles_ElecBefore2010.csv', low_memory = False)
post_2010 = pd.read_csv('City_LosAngeles_ElecAfter2010.csv', low_memory = False)

#%% Concatenate Tables

all_permits = pd.concat([pre_2010, post_2010], axis = 0, ignore_index = True)

#%% Format Columns

all_permits['SUBMITTED_DATE'] = pd.to_datetime(all_permits['SUBMITTED_DATE'])
all_permits['ISSUE_DATE'] = pd.to_datetime(all_permits['ISSUE_DATE'])
all_permits['COFO_DATE'] = pd.to_datetime(all_permits['COFO_DATE'])

#%% Create GeoDataFrame

all_permits_gdf = gpd.GeoDataFrame(
    all_permits, 
    geometry = gpd.points_from_xy(all_permits['LON'], all_permits['LAT']))

#%% Set CRS and Reproject to 3310

all_permits_gdf = all_permits_gdf.set_crs(4326)
all_permits_gdf = all_permits_gdf.to_crs(3310)

#%% Test Plot

all_permits_gdf.plot()

#%% Import to Database

engine = create_engine("postgresql://edf@localhost:5432/edf")  
all_permits_gdf.to_postgis(schema = 'la100es', 
    name = 'la_city_building_permits', 
    con = engine,
    if_exists = 'replace')  
