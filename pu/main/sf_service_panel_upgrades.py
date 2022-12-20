#%% Package Imports

os.chdir('/Users/edf/repos/la100es-panel-upgrades/pu/')

import pkg.io as io
import pkg.plot as plot
import pkg.utils as utils
import pkg.decide as decide
import datetime

#%% Set Output Figures Directory

figure_dir = '/Users/edf/repos/la100es-panel-upgrades/figs/sf/'
output_dir = '/Users/edf/repos/la100es-panel-upgrades/data/outputs/sf/'
sector = 'single_family'

#%% Import SF Data and Context Layers

sf_buildings = io.ImportBuildingPermitData(sector)
ces4 = io.ImportCalEnviroScreenData()
ladwp = io.ImportLadwpServiceTerritoryData()
sf_buildings_ces = utils.AssignDACStatus(utils.MergeCES(sf_buildings, ces4))

#%% Implement Initial Decision Tree

sf_buildings_ces = decide.AssignAsBuiltFromDecisionTree(sf_buildings_ces, sector)
sf_buildings_ces = decide.AssignExistingFromPermit(sf_buildings_ces, sector)
sf_buildings_ces = decide.InferExistingFromModel(sf_buildings_ces, sector)
sf_buildings_ces = utils.UpgradeTimeDelta(sf_buildings_ces)

#%% Compute Statistics

panel_stats_ces_geo = utils.ChangeStatistics(sf_buildings_ces, ces4)

#%% Generate Plots

plot.CountsMap(sf_buildings, ces4, ladwp, figure_dir)
plot.AsBuiltPanelRatingsMap(sf_buildings_ces, ces4, ladwp, figure_dir)
plot.AsBuiltPanelRatingsHist(sf_buildings_ces, ces4, ladwp, figure_dir)
plot.AsBuiltPanelRatingsBar(sf_buildings_ces, figure_dir)
plot.PermitTimeSeries(sf_buildings_ces, figure_dir)
plot.PermitCountsMap(sf_buildings_ces, ces4, ladwp, figure_dir)
plot.PermitCountsHistAnimation(sf_buildings_ces, figure_dir)
plot.PermitVintageYearECDF(sf_buildings_ces, figure_dir)
plot.ExistingPanelRatingsChangeCountsBar(panel_stats_ces_geo, figure_dir)
plot.ExistingPanelRatingsChangeAmpsBox(panel_stats_ces_geo, figure_dir)
plot.ExistingPanelRatingsChangeAmpsScatter(panel_stats_ces_geo, figure_dir)
plot.ExistingPanelRatingsChangeAmpsHist(panel_stats_ces_geo, figure_dir)
plot.ExistingPanelRatingsChangePctMap(panel_stats_ces_geo, ces4, ladwp, figure_dir)
plot.ExistingPanelRatingsHist(sf_buildings_ces, ces4, ladwp, figure_dir)
plot.ExistingPanelRatingsMap(panel_stats_ces_geo, ces4, ladwp, figure_dir)

#%% Print Diagnostics

utils.AsBuiltPanelRatingsDiagnostics(sf_buildings_ces, sector)
utils.PanelUpgradeDiagnostics(sf_buildings_ces)
utils.ExistingPanelRatingsDiagnostics(sf_buildings_ces)

#%% Process and Output to File

final = utils.SortColumns(sf_buildings_ces)
ts = str(datetime.datetime.now())
final.to_csv(output_dir + 'la100es_sf_electricity_service_panel_capacity_analysis_'+ ts[:10] + '.csv')
final.to_json(output_dir + 'la100es_sf_electricity_service_panel_capacity_analysis_'+ ts[:10] + '.geojson')
