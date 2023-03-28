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

mf_buildings = io.ImportBuildingPermitData(sector)
mf_buildings = utils.CoalesceRecords(mf_buildings)
ces4 = io.ImportCalEnviroScreenData()
ladwp = io.ImportLadwpServiceTerritoryData()
mf_buildings_ces = utils.AssignDACStatus(utils.MergeCES(mf_buildings, ces4))
mf_buildings_ces = utils.ComputeAverageUnitSize(mf_buildings_ces)

#%% Implement Initial Decision Tree

mf_buildings_ces = decide.AssignAsBuiltFromDecisionTree(mf_buildings_ces, sector)
mf_buildings_ces = decide.AssignExistingFromPermit(mf_buildings_ces, sector)
mf_buildings_ces = decide.InferExistingFromModel(mf_buildings_ces, sector)
mf_buildings_ces = utils.UpgradeTimeDelta(mf_buildings_ces)

#%% Compute Statistics

panel_stats_ces_geo = utils.ChangeStatistics(mf_buildings_ces, ces4)

#%% Generate Plots

plot.CountsMap(mf_buildings, ces4, ladwp, sector, figure_dir)
plot.AsBuiltPanelRatingsMap(mf_buildings_ces, ces4, ladwp, sector, figure_dir)
plot.AsBuiltPanelRatingsHist(mf_buildings_ces, ces4, ladwp, sector, figure_dir)
plot.JointDistributionPlot(mf_buildings_ces, sector, figure_dir)
plot.AsBuiltPanelRatingsBar(mf_buildings_ces, sector, figure_dir)
plot.PermitTimeSeries(mf_buildings_ces, sector, figure_dir)
plot.PermitCountsMap(mf_buildings_ces, ces4, ladwp, sector, figure_dir)
plot.PermitCountsHistAnimation(mf_buildings_ces, figure_dir)
plot.PermitVintageYearECDF(mf_buildings_ces, sector, figure_dir)
plot.ExistingPanelRatingsBar(mf_buildings_ces, sector, figure_dir)
plot.ExistingPanelRatingsChangeCountsBar(panel_stats_ces_geo, sector, figure_dir)
plot.ExistingPanelRatingsChangeAmpsBox(panel_stats_ces_geo, sector, figure_dir)
plot.ExistingPanelRatingsChangeAmpsScatter(panel_stats_ces_geo, sector, figure_dir)
plot.ExistingPanelRatingsChangeAmpsHist(panel_stats_ces_geo, sector, figure_dir)
plot.ExistingPanelRatingsHist(mf_buildings_ces, ces4, ladwp, sector, figure_dir)
#plot.ExistingPanelRatingsChangePctMap(panel_stats_ces_geo, ces4, ladwp, figure_dir)
plot.ExistingPanelRatingsMap(panel_stats_ces_geo, ces4, ladwp, sector, figure_dir)
plot.AreaNormalizedComparisonKDE(mf_buildings_ces, sector, figure_dir)

#%% Print Diagnostics

utils.AsBuiltPanelRatingsDiagnostics(mf_buildings_ces, sector)
utils.PanelUpgradeDiagnostics(mf_buildings_ces)
utils.ExistingPanelRatingsDiagnostics(mf_buildings_ces, sector)

#%% Process and Output to File

final = utils.SortColumns(mf_buildings_ces, sector)
ts = str(datetime.datetime.now())
final.to_pickle(output_dir + 'la100es_mf_electricity_service_panel_capacity_analysis.pk')
final.to_csv(output_dir + 'la100es_mf_electricity_service_panel_capacity_analysis_'+ ts[:10] + '.csv')
final.to_json(output_dir + 'la100es_mf_electricity_service_panel_capacity_analysis_'+ ts[:10] + '.geojson')
