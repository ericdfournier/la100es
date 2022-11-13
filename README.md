# README

## Introduction

This repository contains a set of data and scripts that have been used to develop a technical analyses of the need for single-family residential home electrical service panel upgrades within the Los Angeles Department of Water and Power utility service territory. This analysis is the work of Eric Fournier, Research Director at the UCLA California Center for Sustainable Communities as part of the LA-100 Equity Strategies Project. Be advised that the workflow draws upon data tables which have been pre-processed and stored on a local postgres database server. Thus, the code is not intended to be able to be executed by others, but rather, it is being made available to provide transparency of methods. 

Contact Info: 
Eric D Fournier
efournier@ioes.ucla.edu 

## Methods

There are three key steps involved with this analysis:

1) Determine the expected "as-built" condition of the electrical service panels on homes based upon the combination of physical building attributes. This step is implemented as a decision tree which operates on the size (sq.ft.) and construction vintage year of each home. This decision trees assigns the as-built panel capacity rating based upon recommendations in previous iterations of the national electrical code and empirical data from previous studies on as-built panel size distributions.

    See the following relevant references for more information: 

   - Addressing an Electrification Roadblock: Residential Electric Panel Capacity
Analysis and Policy Recommendations on Electric Panel Sizing. Pecan Street. August 2021. 
   - Decoding Grid Integrated Buildings. Building Decarbonization Coalition. January 2021.
   - Service Upgrades for Electrification Retrofits Study Draft Report. NV5. March 21, 2022. 

2) Import, process, and filter, historical building permit data for the city and assign upgraded service panel capacities to properties based on the description of relevant activities and system upgrades contained in building work permits. In instances where panel sizes are explicitly enumerated in the permit work description, and these sizes are greater than the as-built size assigned in the previous, they are directly applied as the "existing" condition of the panel. However, in instances where the nature of the permitted work is strongly suggestive of the need for a panel upgrade (such as with a new solar install or high output EV charger) the size of the existing panel is determined based upon the relationship of the as-built panel size to a predefined "upgrade ladder" comprised of an ordinally ranked set of commonly ocurring service panel component sizes.

3) Model the empirical frequency distribution of permitted panel upgrades for DAC/Non-DAC communities as a function of the home's age. Use these functions to simulate the likelihood of an upgrade having previously occurred (if not explicitly permitted) and assign this as an "inferred upgrade."

Following the completion of these three steps, each single-family parcel possessing the necessary attribute data will be assigned a set of attributes indicating its condition "as-built", whether a panel upgrade permit was received in the past, whether an inferred upgrade has likely occurred, and, based upon the combination of the previous, what a best assessement of the "existing" rated capacity of the electrical service panel is.

## Outputs

The output of this analysis is a geospatial dataset, with records for each single-family parcel in the LADWP service territory, containing the following attributes:

index: String (0.0) - Derived
apn: String (0.0) - Primary, LA County Assessor
ain: String (0.0) - Primary, LA County Assessor
ztrax_rowid: String (0.0) - Primary, Zilllow ZTRAX
city: String (0.0) - Primary, LA County Assessor
census_tract: String (0.0) - Primary, CES-4.0
ciscorep: String (0.0) - Primary, CES-4.0
dac_status: String (0.0) - Derived
buildings: String (0.0) - Primary, Zilllow ZTRAX
lot_sqft: String (0.0) - Primary, LA County Assessor
year_built: String (0.0) - Primary, LA County Assessor
building_sqft: String (0.0) - Primary, LA County Assessor
units: String (0.0) - Primary, LA County Assessor
bedrooms: String (0.0) - Primary, LA County Assessor
bathrooms: String (0.0) - Primary, LA County Assessor
county_landuse_description: String (0.0) - Primary, Zilllow ZTRAX
occupancy_status_stnd_code: String (0.0) - Primary, Zilllow ZTRAX
usetype: String (0.0) - Primary, LA County Assessor
usedescription: String (0.0) - Primary, LA County Assessor
heating_system_stnd_code: String (0.0) - Primary, Zilllow ZTRAX 
ac_system_stnd_code: String (0.0) - Primary, Zilllow ZTRAX
roll_year: String (0.0) - Primary, LA County Assessor
roll_landvalue: String (0.0) - Primary, LA County Assessor
roll_landbaseyear: String (0.0) - Primary, LA County Assessor
roll_impvalue: String (0.0) - Primary, LA County Assessor
roll_impbaseyear: String (0.0) - Primary, LA County Assessor
permit_type: String (0.0) - Primary, LA City Building Permit Office
permit_sub_type: String (0.0) - Primary, LA City Building Permit Office
permit_description: String (0.0) - Primary, LA City Building Permit Office
panel_related_permit: String (0.0) - Derived
permit_issue_date: String (0.0) - Primary, LA City Building Permit Office
permitted_panel_upgrade: String (0.0) - Derived
panel_size_as_built: String (0.0) - Derived
inferred_panel_upgrade: String (0.0) - Derived
upgrade_time_delta: String (0.0) - Derived
panel_size_existing: String (0.0) - Derived
centroid: String (0.0) - Primary, LA County Assessor

## Recomendations

Please use caution when interpreting the results at the individual property level as the "as-bult" and "existing" service panel ratings are both estimated values, derived from best available assumptions and data. This dataset is perhaps most useful in aggregated form, when used to develop statistical distributions of panel sizes for sub-groups within the city to support various types of simulation routines or other analyses. 
