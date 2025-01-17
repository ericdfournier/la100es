#%% Package Imports

import pandas as pd
import geopandas as gpd
import numpy as np
import pickle
from itertools import product
from statsmodels.distributions.empirical_distribution import ECDF

#%% Implement Decision Tree Function

def AssignAsBuiltFromDecisionTree(buildings_ces, sector):
    '''Function to assign as-built panel size ratings to residential
    buildings using a vintage year and square footage based decision tree'''

    if sector == 'single_family':
        size_col = 'building_sqft'
    elif sector == 'multi_family':
        size_col = 'avg_unit_sqft'
    else:
        raise Exception("Sector must be either 'single_family' or 'multi_family'")

    if sector == 'single_family':

        vintage_pre_1883 = buildings_ces['year_built'].dt.year < 1883
        vintage_1883_1950 = (buildings_ces['year_built'].dt.year >= 1883) & (buildings_ces['year_built'].dt.year < 1950)
        vintage_1950_1978 = (buildings_ces['year_built'].dt.year >= 1950) & (buildings_ces['year_built'].dt.year < 1978)
        vintage_1978_2010 = (buildings_ces['year_built'].dt.year >= 1978) & (buildings_ces['year_built'].dt.year < 2010)
        vintage_post_2010 = buildings_ces['year_built'].dt.year >= 2010

        size_minus_1k = (buildings_ces[size_col] >= 0) & (buildings_ces[size_col] < 1000)
        size_1k_2k = (buildings_ces[size_col] >= 1000) & (buildings_ces[size_col] < 2000)
        size_2k_3k = (buildings_ces[size_col] >= 2000) & (buildings_ces[size_col] < 3000)
        size_3k_4k = (buildings_ces[size_col] >= 3000) & (buildings_ces[size_col] < 4000)
        size_4k_5k = (buildings_ces[size_col] >= 4000) & (buildings_ces[size_col] < 5000)
        size_5k_8k = (buildings_ces[size_col] >= 5000) & (buildings_ces[size_col] < 8000)
        size_8k_10k = (buildings_ces[size_col] >= 8000) & (buildings_ces[size_col] < 10000)
        size_10k_20k = (buildings_ces[size_col] >= 10000) & (buildings_ces[size_col] < 20000)
        size_20k_plus = (buildings_ces[size_col] >= 20000)

        vintage_names = [   'vintage_pre_1883',
                            'vintage_1883_1950',
                            'vintage_1950_1978',
                            'vintage_1978_2010',
                            'vintage_post_2010']

        size_names = [      'size_minus_1k',
                            'size_1k_2k',
                            'size_2k_3k',
                            'size_3k_4k',
                            'size_4k_5k',
                            'size_5k_8k',
                            'size_8k_10k'
                            'size_10k_20k',
                            'size_20k_plus']

        vintage_bins = [    vintage_pre_1883,
                            vintage_1883_1950,
                            vintage_1950_1978,
                            vintage_1978_2010,
                            vintage_post_2010]

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

        panel_sizes = [ 0.,         # [['vintage_pre_1883', 'size_minus_1k'],
                        0.,         # ['vintage_pre_1883', 'size_1k_2k'],
                        0.,         # ['vintage_pre_1883', 'size_2k_3k'],
                        0.,         # ['vintage_pre_1883', 'size_3k_4k'],
                        0.,         # ['vintage_pre_1883', 'size_4k_5k'],
                        0.,         # ['vintage_pre_1883', 'size_5k_8k'],
                        0.,         # ['vintage_pre_1883', 'size_8k_10k']
                        0.,         # ['vintage_pre_1883', 'size_10k_20k'],
                        0.,         # ['vintage_pre_1883', 'size_20k_plus'],
                        30.,        # ['vintage_1883_1950', 'size_minus_1k'],
                        40.,        # ['vintage_1883_1950', 'size_1k_2k'],
                        60.,        # ['vintage_1883_1950', 'size_2k_3k'],
                        100.,       # ['vintage_1883_1950', 'size_3k_4k'],
                        125.,       # ['vintage_1883_1950', 'size_4k_5k'],
                        150.,       # ['vintage_1883_1950', 'size_5k_8k'],
                        200.,       # ['vintage_1883_1950', 'size_8k_10k']
                        320.,       # ['vintage_1883_1950', 'size_10k_20k'],
                        400.,       # ['vintage_1883_1950', 'size_20k_plus'],
                        30.,        # ['vintage_1950_1978', 'size_minus_1k'],
                        60.,        # ['vintage_1950_1978', 'size_1k_2k'],
                        100.,       # ['vintage_1950_1978', 'size_2k_3k'],
                        125.,       # ['vintage_1950_1978', 'size_3k_4k'],
                        150.,       # ['vintage_1950_1978', 'size_4k_5k'],
                        200.,       # ['vintage_1950_1978', 'size_5k_8k'],
                        320.,       # ['vintage_1950_1978', 'size_8k_10k']
                        400.,       # ['vintage_1950_1978', 'size_10k_20k'],
                        600.,       # ['vintage_1950_1978', 'size_20k_plus'],
                        100.,       # ['vintage_1978_2010', 'size_minus_1k'],
                        125.,       # ['vintage_1978_2010', 'size_1k_2k'],
                        150.,       # ['vintage_1978_2010', 'size_2k_3k'],
                        200.,       # ['vintage_1978_2010', 'size_3k_4k'],
                        225.,       # ['vintage_1978_2010', 'size_4k_5k']
                        320.,       # ['vintage_1978_2010', 'size_5k_8k'],
                        400.,       # ['vintage_1978_2010', 'size_8k_10k']
                        600.,       # ['vintage_1978_2010', 'size_10k_20k']
                        800.,       # ['vintage_1978_2010', 'size_20k_plus']
                        150.,       # ['vintage_post_2010', 'size_minus_1k'],
                        200.,       # ['vintage_post_2010', 'size_1k_2k'],
                        225.,       # ['vintage_post_2010', 'size_2k_3k'],
                        320.,       # ['vintage_post_2010', 'size_3k_4k'],
                        400.,       # ['vintage_post_2010', 'size_4k_5k']
                        600.,       # ['vintage_post_2010', 'size_5k_8k'],
                        800.,       # ['vintage_post_2010', 'size_8k_10k']
                        1000.,      # ['vintage_post_2010', 'size_10k_20k']
                        1200.]      # ['vintage_post_2010', 'size_20k_plus']]

    elif sector == 'multi_family':

        vintage_pre_1883 = buildings_ces['year_built'].dt.year < 1883
        vintage_1883_1950 = (buildings_ces['year_built'].dt.year >= 1883) & (buildings_ces['year_built'].dt.year < 1950)
        vintage_1950_1978 = (buildings_ces['year_built'].dt.year >= 1950) & (buildings_ces['year_built'].dt.year < 1978)
        vintage_1978_2010 = (buildings_ces['year_built'].dt.year >= 1978) & (buildings_ces['year_built'].dt.year < 2010)
        vintage_post_2010 = buildings_ces['year_built'].dt.year >= 2010

        vintage_names = [   'vintage_pre_1883',
                            'vintage_1883_1950',
                            'vintage_1950_1978',
                            'vintage_1978_2010',
                            'vintage_post_2010']

        vintage_bins = [    vintage_pre_1883,
                            vintage_1883_1950,
                            vintage_1950_1978,
                            vintage_1978_2010,
                            vintage_post_2010 ]

        names = vintage_names
        combs = vintage_bins

        panel_sizes = [ 0.,      # 'vintage_pre_1883',
                        40.,     # 'vintage_1883_1950'
                        60.,     # 'vintage_1950_1978'
                        90.,     # 'vintage_1978_2010'
                        150. ]   # 'vintage_post_2010'

    buildings_ces['panel_size_as_built'] = np.nan

    for i in range(len(combs)):

        if sector == 'single_family':

            buildings_ces.loc[(combs[i][0] & combs[i][1]),'panel_size_as_built'] = panel_sizes[i]

        elif sector == 'multi_family':

            buildings_ces.loc[combs[i],'panel_size_as_built'] = panel_sizes[i]

    buildings_ces.reset_index(inplace = True, drop = True)

    return buildings_ces

#%% Assign Existing Panel Size Based Upon Permit Description

def AssignExistingFromPermit(buildings_ces, sector):
    '''Use work description from permit data to assign existing panel rating'''

    # Peform Filtering Assignment

    buildings_ces['panel_size_existing'] = buildings_ces['panel_size_as_built']

    if sector == 'single_family':

        # Find Locations with Upgrades of Different Size

        pu_100 = (buildings_ces['permit_description'].str.contains(' 100')) | (buildings_ces['permit_description'].str.startswith('100'))
        pu_125 = (buildings_ces['permit_description'].str.contains(' 125')) | (buildings_ces['permit_description'].str.startswith('120'))
        pu_150 = (buildings_ces['permit_description'].str.contains(' 150')) | (buildings_ces['permit_description'].str.startswith('150'))
        pu_200 = (buildings_ces['permit_description'].str.contains(' 200')) | (buildings_ces['permit_description'].str.startswith('200'))
        pu_225 = (buildings_ces['permit_description'].str.contains(' 225')) | (buildings_ces['permit_description'].str.startswith('225'))
        pu_320 = (buildings_ces['permit_description'].str.contains(' 320')) | (buildings_ces['permit_description'].str.startswith('320'))
        pu_400 = (buildings_ces['permit_description'].str.contains(' 400')) | (buildings_ces['permit_description'].str.startswith('400'))
        pu_600 = (buildings_ces['permit_description'].str.contains(' 600')) | (buildings_ces['permit_description'].str.startswith('600'))

        pu_solar = (buildings_ces['permit_description'].str.contains(' solar', case = False)) | (buildings_ces['permit_description'].str.contains(' pv', case = False))  | (buildings_ces['permit_description'].str.contains('photovoltaic', case = False))
        pu_ev = (buildings_ces['permit_description'].str.contains(' ev', case = False)) | (buildings_ces['permit_description'].str.contains(' charger', case = False))
        pu_ac = (buildings_ces['permit_description'].str.contains(' ac', case = False)) | (buildings_ces['permit_description'].str.contains(" a/c", case = False))

        pu_any = buildings_ces['panel_related_permit'] == True
        pu_other = pu_any & ~(pu_100 | pu_125 | pu_150 | pu_200 | pu_225 | pu_320 | pu_400 | pu_600)

        upgrade_scale = [   0.,
                            30.,
                            40.,
                            60.,
                            100.,
                            125.,
                            150.,
                            200.,
                            225.,
                            320.,
                            400.,
                            600.,
                            800.,
                            1000.,
                            1200.,
                            1400.]

    elif sector == 'multi_family':

        # Find Locations with Upgrades of Different Size

        pu_100 = (buildings_ces['permit_description'].str.contains(' 100')) | (buildings_ces['permit_description'].str.startswith('100'))
        pu_125 = (buildings_ces['permit_description'].str.contains(' 125')) | (buildings_ces['permit_description'].str.startswith('120'))
        pu_150 = (buildings_ces['permit_description'].str.contains(' 150')) | (buildings_ces['permit_description'].str.startswith('150'))
        pu_200 = (buildings_ces['permit_description'].str.contains(' 200')) | (buildings_ces['permit_description'].str.startswith('200'))

        pu_solar = (buildings_ces['permit_description'].str.contains(' solar', case = False)) | (buildings_ces['permit_description'].str.contains(' pv', case = False))  | (buildings_ces['permit_description'].str.contains('photovoltaic', case = False))
        pu_ev = (buildings_ces['permit_description'].str.contains(' ev', case = False)) | (buildings_ces['permit_description'].str.contains(' charger', case = False))
        pu_ac = (buildings_ces['permit_description'].str.contains(' ac', case = False)) | (buildings_ces['permit_description'].str.contains(" a/c", case = False))

        pu_any = buildings_ces['panel_related_permit'] == True
        pu_other = pu_any & ~(pu_100 | pu_125 | pu_150 | pu_200 )

        upgrade_scale = [   0.,
                            40.,
                            60.,
                            90.,
                            100.,
                            150.,
                            200.]

    ind_dict = {100.:pu_100,
                125.:pu_125,
                150.:pu_150,
                200.:pu_200}

    buildings_ces['permitted_panel_upgrade'] = False

    for k, v in ind_dict.items():

        v[v.isna()] = False
        proposed = buildings_ces.loc[v,'panel_size_as_built']
        change_ind = proposed < k
        proposed.loc[change_ind] = k
        buildings_ces.loc[proposed.index,'panel_size_existing'] = proposed

    pu_other[pu_other.isna()] = False
    proposed = buildings_ces.loc[pu_other, 'panel_size_as_built']

    for p in proposed.items():
        c = None
        if np.isnan(p[1]):
            c = 100.
        else:
            c = p[1]
        k = upgrade_scale.index(c)
        upgrade = upgrade_scale[k+1]
        if upgrade < 200.:
            if sector == 'single_family':
                upgrade = 200.
            elif sector == 'multi_family':
                upgrade = 150.
        proposed.loc[p[0]] = upgrade

    buildings_ces.loc[proposed.index, 'panel_size_existing'] = proposed
    upgrade_ind = buildings_ces['panel_size_existing'] > buildings_ces['panel_size_as_built']
    buildings_ces.loc[upgrade_ind, 'permitted_panel_upgrade'] = True

    return buildings_ces

#%% Infer Previous Year Upgrades Based Upon Permitted Data ECDF

def InferExistingFromModel(buildings_ces, sector):
    '''Function to infer the existing panel size for a buildng that did not
    receive any previous permitted work. The inference model is based upon
    the empirical ECDF which relates the age of the home to the probability
    of permitted work by DAC status.'''

    # Filter Properties with no construction vintage data
    nan_ind = ~buildings_ces.loc[:,'year_built'].isna()

    # Filter DAC and Non-DAC Properties
    dac_ind = buildings_ces.loc[:,'dac_status'] == 'DAC'
    non_dac_ind = buildings_ces.loc[:,'dac_status'] == 'Non-DAC'

    # Filter Properties with Panel Upgrade Permits
    permit_ind = buildings_ces.loc[:,'permitted_panel_upgrade'] == True

    # Extract Permit Issue Year
    permit_issue_year = buildings_ces.loc[:,'permit_issue_date'].dt.year

    # Extract Construction Vintage Year
    construction_year = buildings_ces.loc[:,'year_built'].dt.year

    # Compute the Current Age of the Properties
    current_age = 2022 - construction_year

    # Compute the Age of the Properties in the Year in Which Permits were Issued (if any)
    permit_age = current_age - (2022 - permit_issue_year)

    # Generate ECDFS Based Upon the Age of Properties at the time Their Permits Were Issued for Permitted Properties
    dac_ecdf = ECDF(permit_age.loc[nan_ind & dac_ind & permit_ind])
    non_dac_ecdf = ECDF(permit_age.loc[nan_ind & non_dac_ind & permit_ind])

    # Output DAC ECDF to File for LBNL
    with open('/Users/edf/repos/la100es-panel-upgrades/data/ecdfs/{}_dac_ecdf.pkl'.format(sector), 'wb') as handle:
        pickle.dump(dac_ecdf, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # Output non-DAC ECDF to File for LBNL
    with open('/Users/edf/repos/la100es-panel-upgrades/data/ecdfs/{}_non_dac_ecdf.pkl'.format(sector), 'wb') as handle:
        pickle.dump(non_dac_ecdf, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # Seed the Random Number Generator to Create Deterministic Outputs
    rs = 12345678
    np.random.seed(rs)

    # Extract the Current Ages of the DAC Inference Group of Non-Permitted Properties
    dac_x = current_age.loc[(nan_ind & dac_ind & ~permit_ind)]

    # Output the Probability of an Upgrade Based upon the DAC-ECDF
    dac_y = dac_ecdf(dac_x)
    dac_upgrade_list = []

    # Infer Upgrade based Upon Pseudo-Random Choice Using the Output Probability
    for pr in dac_y:
        dac_upgrade_list.append(np.random.choice(np.array([False, True]), size = 1, p = [1.0-pr, pr])[0])

    dac_x = dac_x.to_frame()
    dac_x['previous_upgrade'] = dac_upgrade_list

    # Extract the Current Ages of the non-DAC Inference Group of Non-Permitted Properties
    non_dac_x = current_age.loc[(nan_ind & non_dac_ind & ~permit_ind)]

    # Output the Probability of an Upgrade Based upon the non-DAC-ECDF
    non_dac_y = non_dac_ecdf(non_dac_x)
    non_dac_upgrade_list = []

    # Infer Upgrade based Upon Pseudo-Random Choice Using the Output Probability
    for pr in non_dac_y:
        non_dac_upgrade_list.append(np.random.choice(np.array([False, True]), size = 1, p = [1.0-pr, pr])[0])

    non_dac_x = non_dac_x.to_frame()
    non_dac_x['previous_upgrade'] = non_dac_upgrade_list

    # Loop Through and Assess Upgrades for DAC and Non-DAC cohorts
    upgrade_scale = []

    if sector == 'single_family':

        upgrade_scale = [   0.,
                            30.,
                            40.,
                            60.,
                            100.,
                            125.,
                            150.,
                            200.,
                            225.,
                            320.,
                            400.,
                            600.,
                            800.,
                            1000.,
                            1200.,
                            1400.]

    elif sector == 'multi_family':

        upgrade_scale = [   0.,
                            40.,
                            60.,
                            90.,
                            150.,
                            200.]

    # DAC Loop
    buildings_ces['inferred_panel_upgrade'] = False

    for ind, row in dac_x.iterrows():

        as_built = buildings_ces.loc[ind,'panel_size_as_built']
        existing = as_built

        if (row['previous_upgrade'] == True) & (buildings_ces.loc[ind, 'permitted_panel_upgrade'] == False):
            level = upgrade_scale.index(as_built)
            existing = upgrade_scale[level + 1]
            buildings_ces.loc[ind,'inferred_panel_upgrade'] = True

        buildings_ces.loc[ind,'panel_size_existing'] = existing

    # Non-DAC Loop
    for ind, row in non_dac_x.iterrows():

        as_built = buildings_ces.loc[ind,'panel_size_as_built']
        existing = as_built

        if (row['previous_upgrade'] == True) & (buildings_ces.loc[ind, 'permitted_panel_upgrade'] == False):
            level = upgrade_scale.index(as_built)
            existing = upgrade_scale[level + 1]
            buildings_ces.loc[ind,'inferred_panel_upgrade'] = True

        buildings_ces.loc[ind,'panel_size_existing'] = existing

    buildings_ces['panel_upgrade'] = buildings_ces.loc[:,['permitted_panel_upgrade','inferred_panel_upgrade']].any(axis = 1)

    return buildings_ces
