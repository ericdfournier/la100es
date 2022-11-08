#%% Package Imports

import pandas as pd
import geopandas as gpd
import numpy as np
from itertools import product
from statsmodels.distributions.empirical_distribution import ECDF
from numpy.random import MT19937
from numpy.random import RandomState, SeedSequence

#%% Implement Decision Tree Function

def AssignAsBuiltFromDecisionTree(sf_buildings_ces):
    '''Function to assign as-built panel size ratings to building 
    using a vintage year and square footage based decision tree'''

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

    return sf_buildings_ces

#%% Assign Existing Panel Size Based Upon Permit Description

def AssignExistingFromPermit(sf_buildings_ces):
    '''Use work description from permit data to assign existing panel rating'''

    # Find Locations with Upgrades of Different Size

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

    # Peform Filtering Assignment

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

    return sf_buildings_ces

#%% Infer Previous Year Upgrades Based Upon Permitted Data ECDF

def InferExistingFromModel(sf_buildings_ces):
    '''Function to infer the existing panel size for a buildng that did not
    receive any previous permitted work. The inference model is based upon
    the empirical ECDF which relates the age of the home to the probability
    of permitted work by DAC status.'''

    rs = RandomState(MT19937(SeedSequence(987654321)))
    dac_ecdf = ECDF(dac_ages['year_built'])

    dac_odds_ratio = non_dac_permit_sum / dac_permit_sum
    start_year = np.min(sf_buildings_ces['permit_issue_date'].dt.year)

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

    # Loop Through and Assess Upgrades for DAC and Non-DAC cohorts

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
    
    sf_buildings_ces['panel_upgrade'] = sf_buildings_ces.loc[:,['permitted_panel_upgrade','inferred_panel_upgrade']].any(axis = 1)
    
    return sf_buildings_ces