#%% Package Imports

import pandas as pd
import geopandas as gpd
import sqlalchemy as sql
import os

#%% Building Permit Data Import Function

def ImportBuildingPermitData(sector):
    '''Function to import pre-processed single family building
    permit data from local postgres database'''

    # Extract Database Connection Parameters from Environment
    host = os.getenv('PGHOST')
    user = os.getenv('PGUSER')
    password = os.getenv('PGPASS')
    port = os.getenv('PGPORT')
    db = os.getenv('PGDATABASE')

    # Establish DB Connection
    db_con_string = 'postgresql://' + user + '@' + host + ':' + port + '/' + db
    db_con = sql.create_engine(db_con_string)

    if sector == 'single_family':

        # Read Input Table from DB
        buildings_sql = '''SELECT    "ztrax_rowid",
                                    "apn",
                                    "buildings",
                                    "lot_sqft",
                                    "county_landuse_description",
                                    "occupancy_status_stnd_code",
                                    "year_built"::text,
                                    "units",
                                    "bedrooms",
                                    "bathrooms",
                                    "heating_system_stnd_code",
                                    "ac_system_stnd_code",
                                    "building_sqft",
                                    "centroid",
                                    "census_tract",
                                    "ain",
                                    "usetype",
                                    "usedescription",
                                    "roll_year"::text,
                                    "roll_landvalue",
                                    "roll_landbaseyear"::text,
                                    "roll_impvalue",
                                    "roll_impbaseyear"::text,
                                    "city",
                                    "permit_type",
                                    "permit_sub_type",
                                    "permit_description",
                                    "permit_issue_date"::text,
                                    "panel_related_permit"
                        FROM        la100es.panel_data_permits
                        WHERE       "usetype" = 'Residential' AND
                                    "usedescription" = 'Single' AND
                                    "county_landuse_description" NOT IN ('SINGLE RESIDENTIAL - CONDOMINIUM', 'SINGLE FAMILY RESIDENTIAL - VACANT');'''

    elif sector == 'multi_family':

        # Read Input Table from DB
        buildings_sql = '''SELECT    "ztrax_rowid",
                                    "apn",
                                    "buildings",
                                    "lot_sqft",
                                    "county_landuse_description",
                                    "occupancy_status_stnd_code",
                                    "year_built"::text,
                                    "units",
                                    "bedrooms",
                                    "bathrooms",
                                    "heating_system_stnd_code",
                                    "ac_system_stnd_code",
                                    "building_sqft",
                                    "centroid",
                                    "census_tract",
                                    "ain",
                                    "usetype",
                                    "usedescription",
                                    "roll_year"::text,
                                    "roll_landvalue",
                                    "roll_landbaseyear"::text,
                                    "roll_impvalue",
                                    "roll_impbaseyear"::text,
                                    "city",
                                    "permit_type",
                                    "permit_sub_type",
                                    "permit_description",
                                    "permit_issue_date"::text,
                                    "panel_related_permit"
                        FROM        la100es.panel_data_permits
                        WHERE       "usetype" = 'Residential' AND
                                    "usedescription" IN ('Five or more apartments',
                                                        'Four Units (Any Combination)',
                                                        'Three Units (Any Combination)',
                                                        'Two Units)') AND
                                    "county_landuse_description" NOT IN ('APARTMENT 5+ UNITS VACANT',
                                                                        'RESIDENTIAL - FOURPLEX VACANT',
                                                                        'RESIDENTIAL - TRIPLEX VACANT');'''
    else:

        raise Exception("Sector must be either 'single-family' or multi_family'")

    buildings = pd.read_sql(buildings_sql, db_con)

    buildings['census_tract'] = pd.to_numeric(buildings['census_tract'], errors = 'coerce')

    buildings.loc[buildings['year_built'] == '0001-01-01 BC', 'year_built'] = ''
    buildings.loc[buildings['roll_year'] == '0001-01-01 BC', 'roll_year'] = ''
    buildings.loc[buildings['roll_landbaseyear'] == '0001-01-01 BC', 'roll_landbaseyear'] = ''
    buildings.loc[buildings['roll_impbaseyear'] == '0001-01-01 BC', 'roll_impbaseyear'] = ''
    buildings.loc[buildings['permit_issue_date'] == '0001-01-01 BC', 'permit_issue_date'] = ''

    buildings['year_built'] = pd.to_datetime(buildings['year_built'], format = '%Y-%m-%d')
    buildings['roll_year'] = pd.to_datetime(buildings['roll_year'], format = '%Y-%m-%d')
    buildings['roll_landbaseyear'] = pd.to_datetime(buildings['roll_landbaseyear'], format = '%Y-%m-%d')
    buildings['roll_impbaseyear'] = pd.to_datetime(buildings['roll_impbaseyear'], format = '%Y-%m-%d')
    buildings['permit_issue_date'] = pd.to_datetime(buildings['permit_issue_date'], format = 'mixed')

    return buildings

#%% Read Census Tract Level DAC Data

def ImportCalEnviroScreenData():
    '''Function to import cal-enviro-screen census tract level
    geospatial data from local postgres database'''

    # Extract Database Connection Parameters from Environment
    host = os.getenv('PGHOST')
    user = os.getenv('PGUSER')
    password = os.getenv('PGPASS')
    port = os.getenv('PGPORT')
    db = os.getenv('PGDATABASE')

    # Establish DB Connection
    db_con_string = 'postgresql://' + user + '@' + host + ':' + port + '/' + db
    db_con = sql.create_engine(db_con_string)

    # Read table from database and format columns
    ces4_sql = '''SELECT * FROM ladwp.ces4'''
    ces4 = gpd.read_postgis(ces4_sql, db_con, geom_col = 'geom')
    cols = [x.lower() for x in ces4.columns]
    ces4.columns = cols

    return ces4

#%% Import SB-535 DAC Data

def ImportSB535Data():
    '''Function to import SB-535 census tract level geospatial
    data from local postgres database'''

    # Extract Database Connection Parameters from Environment
    host = os.getenv('PGHOST')
    user = os.getenv('PGUSER')
    password = os.getenv('PGPASS')
    port = os.getenv('PGPORT')
    db = os.getenv('PGDATABASE')

    # Establish DB Connection
    db_con_string = 'postgresql://' + user + '@' + host + ':' + port + '/' + db
    db_con = sql.create_engine(db_con_string)

    # Read table from database and format columns
    sb535_sql = '''SELECT * FROM ladwp.sb535_dacs'''
    sb535 = gpd.read_postgis(sb535_sql, db_con, geom_col = 'geom')
    cols = [x.lower() for x in sb535.columns]
    sb535.columns = cols

    return sb535

#%% Read LADWP Boundary

def ImportLadwpServiceTerritoryData():
    '''Function to import ladwp utility service territory
    geospatial data from local postgres database'''

    # Extract Database Connection Parameters from Environment
    host = os.getenv('PGHOST')
    user = os.getenv('PGUSER')
    password = os.getenv('PGPASS')
    port = os.getenv('PGPORT')
    db = os.getenv('PGDATABASE')

    # Establish DB Connection
    db_con_string = 'postgresql://' + user + '@' + host + ':' + port + '/' + db
    db_con = sql.create_engine(db_con_string)

    # Read table from database and format columns
    ladwp_sql = '''SELECT * FROM ladwp.service_territory'''
    ladwp = gpd.read_postgis(ladwp_sql, con = db_con, geom_col = 'geom')

    return ladwp
