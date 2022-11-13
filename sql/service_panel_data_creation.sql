-- Parse ZTRAX Geometries in Point Field

ALTER TABLE ztrax.main ADD COLUMN centroid geometry(Point, 3310);
UPDATE ztrax.main SET centroid = ST_TRANSFORM(ST_SetSRID(ST_MakePoint("PropertyAddressLongitude", "PropertyAddressLatitude"), 4326), 3310);
CREATE INDEX idx_ztrax_main_centroid ON ztrax.main USING gist (centroid);

-- Index Tract Geometries

CREATE INDEX idx_ztrax_ca_tr_geom_2019_index 
ON census.ca_tr_geom_2019 
USING GIST(geom);

-- Extract ZTRAX Data for LADWP

SELECT DISTINCT 
		A."RowID",
		A."AssessorParcelNumber",
		A."NoOfBuildings",
		A."LotSizeSquareFeet",
		B."PropertyCountyLandUseDescription",
		B."OccupancyStatusStndCode",
		B."YearBuilt",
		B."NoOfUnits",
		B."TotalBedrooms",
		B."TotalActualBathCount",
		B."HeatingTypeorSystemStndCode",
		B."AirConditioningTypeorSystemStndCode",
		C."BuildingAreaSqFt",
		A."centroid"
INTO 	la100es.panel_data
FROM 	ztrax.main AS A,
		ztrax.building AS B,
		ztrax.building_areas AS C,
		ladwp.service_territory AS D
WHERE 	
		A."RowID" = B."RowID" AND
		B."RowID" = C."RowID" AND 
		ST_INTERSECTS(A."centroid", D."geom");
		
-- Add Census Tract ID Based Upon Polygon Location

ALTER TABLE la100es.panel_data
ADD COLUMN "census_tract" VARCHAR;

UPDATE la100es.panel_data AS A
SET "census_tract" = B."geoid"
FROM census.ca_tr_geom_2019 AS B
WHERE ST_INTERSECTS(A."centroid", B."geom");

-- Add fields from assessor's parcel database

ALTER TABLE la100es.panel_data
ADD COLUMN "ain" VARCHAR,
ADD COLUMN "usetype" VARCHAR,
ADD COLUMN "usedescription" VARCHAR,
ADD COLUMN "roll_year" VARCHAR,
ADD COLUMN "roll_landvalue" INT4,
ADD COLUMN "roll_landbaseyear" VARCHAR,
ADD COLUMN "roll_impvalue" INT4,
ADD COLUMN "roll_impbaseyear" VARCHAR;

UPDATE la100es.panel_data AS A
SET "ain" = B."ain",
	"usetype" = B."usetype",
 	"usedescription" = B."usedescription",
 	"roll_year" = B."roll_year",
	"roll_landvalue" = B."roll_landvalue",
	"roll_landbaseyear" = B."roll_landbaseyear",
	"roll_impvalue" = B."roll_impvalue",
	"roll_impbaseyear" = B."roll_impbaseyear"
FROM lac.parcels_2021 AS B
WHERE A."AssessorParcelNumber" = B."apn";

-- Add city information

ALTER TABLE la100es.panel_data
ADD COLUMN city VARCHAR;

UPDATE la100es.panel_data AS A
SET city = city_name
FROM lac.cities_multi AS B
WHERE ST_INTERSECTS(A."centroid", B."geom");

-- Add fields from permit database

SELECT 	A.*,
		B."PERMIT_TYPE" AS "permit_type",
		B."PERMIT_SUB_TYPE" AS "permit_sub_type",
		B."WORK_DESC" AS "permit_description",
	 	B."ISSUE_DATE" AS "permit_issue_date"
INTO la100es.panel_data_permits
FROM la100es.panel_data AS A 
LEFT JOIN la100es.la_city_building_permits AS B
ON A."ain" = B."APN";

-- Determine where panel upgrades occurred based upon permit description

ALTER TABLE la100es.panel_data_permits
ADD COLUMN panel_related_permit BOOL;

UPDATE la100es.panel_data_permits
SET panel_related_permit = FALSE;

UPDATE la100es.panel_data_permits
SET panel_related_permit = TRUE
WHERE "permit_description" ~* 'UPGRADE' OR
	  "permit_description" ~* 'MAIN' OR
	  "permit_description" ~* 'PANEL' OR
	  "permit_description" ~* 'SERVICE' OR 
	  "permit_description" ~* 'AMP' OR 
	  "permit_description" ~* 'SOLAR' OR
	  "permit_description" ~* 'PV' OR
	  "permit_description" ~* 'PHOTOVOLTAIC' OR
	  "permit_description" ~* 'EV CHARGER' OR
	  "permit_description" ~* 'AC ' OR
	  "permit_description" ~* 'A/C' OR 
	  "permit_description" ~* 'AIR CONDITIONER' OR
	  "permit_description" ~* 'HEAT PUMP';
	 
-- Add physical geography fields
	 
CREATE INDEX idx_la100es_panel_data_permits_centroid_index 
ON la100es.panel_data_permits 
USING GIST(centroid);
	 
ALTER TABLE la100es.panel_data_permits
ADD COLUMN "elevation_m" INT4;

UPDATE la100es.panel_data_permits
SET elevation_m = ST_VALUE(R.rast, centroid)
FROM srtm.ca_elevation AS R;

ALTER TABLE la100es.panel_data_permits
ADD COLUMN "slope_deg" FLOAT;

-- Rename fields

ALTER TABLE la100es.panel_data_permits
RENAME COLUMN "RowID" TO "ztrax_rowid";

ALTER TABLE la100es.panel_data_permits
RENAME COLUMN "AssessorParcelNumber" TO "apn";

ALTER TABLE la100es.panel_data_permits
RENAME COLUMN "NoOfBuildings" TO "buildings";

ALTER TABLE la100es.panel_data_permits
RENAME COLUMN "LotSizeSquareFeet" TO "lot_sqft";

ALTER TABLE la100es.panel_data_permits
RENAME COLUMN "PropertyCountyLandUseDescription" TO "county_landuse_description";

ALTER TABLE la100es.panel_data_permits
RENAME COLUMN "OccupancyStatusStndCode" TO "occupancy_status_stnd_code";

ALTER TABLE la100es.panel_data_permits
RENAME COLUMN "YearBuilt" TO "year_built";

ALTER TABLE la100es.panel_data_permits
RENAME COLUMN "NoOfUnits" TO "units";

ALTER TABLE la100es.panel_data_permits
RENAME COLUMN "TotalBedrooms" TO "bedrooms";

ALTER TABLE la100es.panel_data_permits
RENAME COLUMN "TotalActualBathCount" TO "bathrooms";

ALTER TABLE la100es.panel_data_permits
RENAME COLUMN "HeatingTypeorSystemStndCode" TO "heating_system_stnd_code";

ALTER TABLE la100es.panel_data_permits
RENAME COLUMN "AirConditioningTypeorSystemStndCode" TO "ac_system_stnd_code";

ALTER TABLE la100es.panel_data_permits
RENAME COLUMN "BuildingAreaSqFt" TO "building_sqft";

-- Cast fields to appropriate types

ALTER TABLE la100es.panel_data_permits
ALTER COLUMN buildings TYPE INT4
USING buildings::INT4;

ALTER TABLE la100es.panel_data_permits
ALTER COLUMN lot_sqft TYPE INT8
USING lot_sqft::INT8;

ALTER TABLE la100es.panel_data_permits
ALTER COLUMN year_built TYPE DATE
USING TO_DATE(year_built::VARCHAR, 'YYYY');

ALTER TABLE la100es.panel_data_permits
ALTER COLUMN units TYPE INT4
USING units::INT4;

ALTER TABLE la100es.panel_data_permits
ALTER COLUMN bedrooms TYPE INT4
USING bedrooms::INT4;

ALTER TABLE la100es.panel_data_permits
ALTER COLUMN bathrooms TYPE INT4 
USING bathrooms::INT4;

ALTER TABLE la100es.panel_data_permits
ALTER COLUMN roll_year TYPE DATE
USING TO_DATE(roll_year, 'YYYY');

ALTER TABLE la100es.panel_data_permits
ALTER COLUMN roll_landbaseyear TYPE DATE
USING TO_DATE(roll_landbaseyear, 'YYYY');

ALTER TABLE la100es.panel_data_permits 
ALTER COLUMN roll_impbaseyear TYPE DATE
USING TO_DATE(roll_impbaseyear, 'YYYY');






