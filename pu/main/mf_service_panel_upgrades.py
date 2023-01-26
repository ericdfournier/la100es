#%% Package Imports

os.chdir('/Users/edf/repos/la100es-panel-upgrades/pu/')

import pkg.io as io
import pkg.plot as plot
import pkg.utils as utils
import pkg.decide as decide
import datetime

#%% Set Output Figures Directory

figure_dir = '/Users/edf/repos/la100es-panel-upgrades/figs/mf/'
output_dir = '/Users/edf/repos/la100es-panel-upgrades/data/outputs/mf/'
sector = 'multi_family'

#%% Import Data and Context Layers

buildings = io.ImportBuildingPermitData(sector)
ces4 = io.ImportCalEnviroScreenData()
ladwp = io.ImportLadwpServiceTerritoryData()
buildings_ces = utils.AssignDACStatus(utils.MergeCES(buildings, ces4))
buildings_ces = utils.ComputeAverageUnitSize(buildings_ces)

#%% Implement Initial Decision Tree

buildings_ces = decide.AssignAsBuiltFromDecisionTree(buildings_ces, sector)
buildings_ces = decide.AssignExistingFromPermit(buildings_ces, sector)
buildings_ces = decide.InferExistingFromModel(buildings_ces, sector)
buildings_ces = utils.UpgradeTimeDelta(buildings_ces)

#%% Compute Statistics

panel_stats_ces_geo = utils.ChangeStatistics(buildings_ces, ces4)

#%% Generate Plots

# TODO: Modify plot routines to differentiate by sector input flag.
# Make sure to keep track of the difference between properties and units!

plot.CountsMap(buildings, ces4, ladwp, figure_dir)
plot.AsBuiltPanelRatingsMap(buildings_ces, ces4, ladwp, figure_dir)
plot.AsBuiltPanelRatingsHist(buildings_ces, ces4, ladwp, figure_dir)
plot.AsBuiltPanelRatingsBar(buildings_ces, figure_dir)
plot.PermitTimeSeries(buildings_ces, figure_dir)
plot.PermitCountsMap(buildings_ces, ces4, ladwp, figure_dir)
plot.PermitCountsHistAnimation(buildings_ces, figure_dir)
plot.PermitVintageYearECDF(buildings_ces, figure_dir)
plot.ExistingPanelRatingsChangeCountsBar(panel_stats_ces_geo, figure_dir)
plot.ExistingPanelRatingsChangeAmpsBox(panel_stats_ces_geo, figure_dir)
plot.ExistingPanelRatingsChangeAmpsScatter(panel_stats_ces_geo, figure_dir)
plot.ExistingPanelRatingsChangeAmpsHist(panel_stats_ces_geo, figure_dir)
plot.ExistingPanelRatingsChangePctMap(panel_stats_ces_geo, ces4, ladwp, figure_dir)
plot.ExistingPanelRatingsHist(buildings_ces, ces4, ladwp, figure_dir)
plot.ExistingPanelRatingsMap(panel_stats_ces_geo, ces4, ladwp, figure_dir)

#%% Print Diagnostics

utils.AsBuiltPanelRatingsDiagnostics(buildings_ces, sector)
utils.PanelUpgradeDiagnostics(buildings_ces)
utils.ExistingPanelRatingsDiagnostics(buildings_ces)

#%% Process and Output to File

final = utils.SortColumns(buildings_ces, sector)
ts = str(datetime.datetime.now())
final.to_csv(output_dir + 'la100es_mf_electricity_service_panel_capacity_analysis_'+ ts[:10] + '.csv')
final.to_json(output_dir + 'la100es_mf_electricity_service_panel_capacity_analysis_'+ ts[:10] + '.geojson')
