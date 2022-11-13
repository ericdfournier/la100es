# README

## Introduction

This repository contains a set of data and scripts that have been used to develop a technical analyses of the need for single-family residential home electrical service panel upgrades within the Los Angeles Department of Water and Power utility service territory. This analysis is the work of Eric Fournier, Research Director at the UCLA California Center for Sustainable Communities as part of the LA-100 Equity Strategies Project. Be advised that the workflow draws upon data tables which have been pre-processed and stored on a local postgres database server. Thus, the code is not intended to be able to be executed by others, but rather, it is being made available to provide transparency of methods. 

Contact Info: 
Eric D Fournier
efournier@ioes.ucla.edu 

## Methods

There are three key steps involved with this analysis:

1) Determine the expected "as-built" condition of the electrical service panels on homes based upon the combination of physical building attributes. This step is implemented as a decision tree which operates on the size (sq.ft.) and construction vintage year of each home. This decision trees assigns the as-built panel capacity rating based upon recommendations in previous iterations of the national electrical code and empirical data from previous studies on as|built panel size distributions.

   See the following relevant references for more information:

   - Addressing an Electrification Roadblock: Residential Electric Panel Capacity
Analysis and Policy Recommendations on Electric Panel Sizing. Pecan Street. August 2021. 
   - Decoding Grid Integrated Buildings. Building Decarbonization Coalition. January 2021.
   - Service Upgrades for Electrification Retrofits Study Draft Report. NV5. March 21, 2022. 

2) Import, process, and filter, historical building permit data for the city and assign upgraded service panel capacities to properties based on the description of relevant activities and system upgrades contained in building work permits. In instances where panel sizes are explicitly enumerated in the permit work description, and these sizes are greater than the as|built size assigned in the previous, they are directly applied as the "existing" condition of the panel. However, in instances where the nature of the permitted work is strongly suggestive of the need for a panel upgrade (such as with a new solar install or high output EV charger) the size of the existing panel is determined based upon the relationship of the as|built panel size to a predefined "upgrade ladder" comprised of an ordinally ranked set of commonly ocurring service panel component sizes.

3) Model the empirical frequency distribution of permitted panel upgrades for DAC/Non|DAC communities as a function of the home's age. Use these functions to simulate the likelihood of an upgrade having previously occurred (if not explicitly permitted) and assign this as an "inferred upgrade."

Following the completion of these three steps, each single|family parcel possessing the necessary attribute data will be assigned a set of attributes indicating its condition "as|built", whether a panel upgrade permit was received in the past, whether an inferred upgrade has likely occurred, and, based upon the combination of the previous, what a best assessement of the "existing" rated capacity of the electrical service panel is.

## Outputs

The output of this analysis is a geospatial dataset, with records for each single|family parcel in the LADWP service territory, containing the following attributes:

| Field Name | Data Type | Data Description | Data Source |
|------------|-----------|------------------|-------------|
|index| float64 | serial numerical primary key | Derived
|apn| string | assessor parcel number | Primary, LA County Assessor
|ain| string | assessor information number | Primary, LA County Assessor
|ztrax_rowid| string | zillow ztrax database row id number | Primary, Zilllow ZTRAX
|city| string | city name | Primary, LA County Assessor
|census_tract| int64 | census tract geoid | Primary, CES-4.0
|ciscorep| float64 | census tract cal-enviroscreen 4.0 composite index percentile score | Primary, CES-4.0
|dac_status| string | disadvantaged community status based upon >=75th percentile composite score threshold | Derived
|buildings| float64 | buildings count | Primary, Zilllow ZTRAX
|lot_sqft| float64 | lot size in square feet | Primary, LA County Assessor
|year_built| datetime64 | building construction vintage | Primary, LA County Assessor
|building_sqft| float64 | building size in square feet | Primary, LA County Assessor
|units| float64 | units count | Primary, LA County Assessor
|bedrooms| float64 | bedrooms count | Primary, LA County Assessor
|bathrooms| float64 | bathrooms count | Primary, LA County Assessor
|county_landuse_description| string | standardized county landuse description | Primary, Zilllow ZTRAX
|occupancy_status_stnd_code| string | standardized occupany status code | Primary, Zilllow ZTRAX
|usetype| string | property usetype category | Primary, LA County Assessor
|usedescription| string | property usetype description | Primary, LA County Assessor
|heating_system_stnd_code| string | heating system standard code | Primary, Zilllow ZTRAX
|ac_system_stnd_code| string | air conditioning system standard code | Primary, Zilllow ZTRAX
|roll_year| datetime64 | assessor tax roll year | Primary, LA County Assessor
|roll_landvalue| float64 | assessor tax roll land value in dollars | Primary, LA County Assessor
|roll_landbaseyear| datetime64 | assessor tax roll land base year | Primary, LA County Assessor
|roll_impvalue| float64 | assessor tax roll improvement value in dollars | Primary, LA County Assessor
|roll_impbaseyear| datetime64 | assessor tax roll improvement base year | Primary, LA County Assessor
|permit_type| string  | building permit type | Primary, LA City Building Permit Office
|permit_sub_type| string | building permit sub-type | Primary, LA City Building Permit Office
|permit_description| string | building permit work description | Primary, LA City Building Permit Office
|panel_related_permit| bool | boolean flag for panel related building permits | Derived
|permit_issue_date| datetime64 | building permit issue date | Primary, LA City Building Permit Office
|permitted_panel_upgrade| bool | boolean flag for permitted panel upgrades | Derived
|panel_size_as_built| float64 | estimated as-built electricity service panel rated capacity in Amps | Derived
|inferred_panel_upgrade| bool | boolean flag for inferred panel upgrades | Derived
|upgrade_time_delta| float64 | years between construction vintage and panel upgrade permit issue date | Derived
|panel_size_existing| float64 | estimated existing electricity service panel rated capacity in Amps | Derived
|centroid| float64 point geometry | parcel centroid in meters northing and easting after projection into EPSG:3310 coordinate system | Primary, LA County Assessor

## Recomendations

Please use caution when interpreting the results at the individual property level as the "as-built" and "existing" service panel ratings are both estimated values, derived from best available assumptions and data. This dataset is perhaps most useful in aggregated form, when used to develop statistical distributions of panel sizes for sub-groups within the city to support various types of simulation routines or other analyses. 
