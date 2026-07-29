# -*- coding: utf-8 -*-

# pyrefly: ignore [missing-import]
from qgis.core import QgsProcessingProvider
# pyrefly: ignore [missing-import]
from qgis.PyQt.QtGui import QIcon
import os

from .algorithms.create_block_grid import CreateBlockGrid
from .algorithms.create_kontur import CreateKontur
from .algorithms.create_lereng import CreateLereng
from .algorithms.create_morfologi import CreateMorfologi
from .algorithms.hydrology_analysis import HydrologyAnalysis
from .algorithms.sink_detection import SinkDetection
from .algorithms.generate_planting_points import GeneratePlantingPoints
from .algorithms.terrace_planting_points import TerracePlantingPoints
from .algorithms.calculate_sph import CalculateSPH
from .algorithms.planting_cost_estimator import PlantingCostEstimator
from .algorithms.hitung_jarak_tanam import HitungJarakTanam
from .algorithms.numbering_rows_points import NumberingRowsAndPoints
from .algorithms.fertilizer_calculator import FertilizerCalculator
from .algorithms.road_cut_fill_analysis import RoadCutFillAnalysis
from .algorithms.planting_distance_assessment import PlantingDistanceAssessment
from .algorithms.ndvi_analysis import NDVIAnalysis
from .algorithms.oil_palm_detection import OilPalmDetection
from .algorithms.install_dependencies import InstallDependencies
from .algorithms.harvest_route_optimizer import HarvestRouteOptimizer
from .algorithms.road_stability_analysis import RoadStabilityAnalysis
from .algorithms.drone_mission_planner import DroneMissionPlanner
from .algorithms.export_geojson import ExportToGeoJSON
from .algorithms.infrastructure_density_analysis import InfrastructureDensityAnalysis
from .algorithms.infrastructure_buffer_analysis import InfrastructureBufferAnalysis
from .algorithms.optimal_road_routing import OptimalRoadRouting
from .algorithms.placeholders import (
    CheckLicenseStatus,
    AnalisisAreaKonservasi
)
from .algorithms.update_plugin import UpdatePlugin
from .algorithms.generate_dummy_data import GenerateDummyData
from .algorithms.soil_moisture_analysis import SoilMoistureAnalysis
from .algorithms.block_centroid_routing import BlockCentroidRouting
from .algorithms.flood_prediction_analysis import FloodPredictionAnalysis
from .algorithms.deteksi_klorosis_pokok import DeteksiKlorosisPokok

class PlantationProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        # 00. System & Licensing
        self.addAlgorithm(CheckLicenseStatus())
        self.addAlgorithm(UpdatePlugin())
        self.addAlgorithm(InstallDependencies())
        
        # 01. Land Preparation
        self.addAlgorithm(CreateBlockGrid())

        # 02. Topography & Hydrology
        self.addAlgorithm(CreateKontur())
        self.addAlgorithm(CreateLereng())
        self.addAlgorithm(CreateMorfologi())
        self.addAlgorithm(HydrologyAnalysis())
        
        # 03. Agronomy & Planting
        self.addAlgorithm(GeneratePlantingPoints())
        self.addAlgorithm(TerracePlantingPoints())
        self.addAlgorithm(HitungJarakTanam())
        self.addAlgorithm(NumberingRowsAndPoints())
        self.addAlgorithm(PlantingCostEstimator())
        self.addAlgorithm(FertilizerCalculator())
        self.addAlgorithm(CalculateSPH())
        self.addAlgorithm(RoadCutFillAnalysis())
        self.addAlgorithm(PlantingDistanceAssessment())
        self.addAlgorithm(NDVIAnalysis())
        self.addAlgorithm(DeteksiKlorosisPokok())
        self.addAlgorithm(SoilMoistureAnalysis())
        
        
        # 04. Plantation Intelligence (AI)
        self.addAlgorithm(OilPalmDetection())
        
        # 05. Infrastructure & Logistics
        self.addAlgorithm(HarvestRouteOptimizer())
        self.addAlgorithm(RoadStabilityAnalysis())
        self.addAlgorithm(DroneMissionPlanner())
        
        # 06. Web & Reporting
        self.addAlgorithm(ExportToGeoJSON())
        
        # 07. Analisa Infrastruktur (Jalan & Parit)
        self.addAlgorithm(InfrastructureDensityAnalysis())
        self.addAlgorithm(InfrastructureBufferAnalysis())
        self.addAlgorithm(SinkDetection())
        self.addAlgorithm(OptimalRoadRouting())
        self.addAlgorithm(BlockCentroidRouting())
        
        # 08. Analisa Lingkungan & NKT
        self.addAlgorithm(AnalisisAreaKonservasi())
        self.addAlgorithm(FloodPredictionAnalysis())
        
        # 99. Testing & Utilities
        self.addAlgorithm(GenerateDummyData())

    def id(self):
        return 'plantation_tools'

    def name(self):
        return 'Plantation Tools'

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        return QIcon()
