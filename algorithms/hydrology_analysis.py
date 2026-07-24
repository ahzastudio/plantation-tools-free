# -*- coding: utf-8 -*-

import os
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterRasterDestination,
    QgsFeatureSink,
    QgsRasterLayer
)
import processing
from .base_algorithm import BasePlantationAlgorithm

class HydrologyAnalysis(BasePlantationAlgorithm):
    """
    QGIS Implementation of Hydrology Analysis tool.
    Analyzes DEM to extract drainage networks and flow patterns.
    """

    P_IN_DEM = 'IN_DEM'
    P_THRESHOLD_HA = 'THRESHOLD_HA'
    P_OUT_STREAMS = 'OUT_STREAMS'
    P_OUT_FLOWDIR = 'OUT_FLOWDIR'
    P_OUT_FLOWACC = 'OUT_FLOWACC'

    def get_minimum_tier(self):
        return "free" # Hydrology is in Topography & Hydrology category

    def name(self):
        return 'hydrologyanalysis'

    def displayName(self):
        return '05. Hydrology & Drainage Analysis (Analisis Hidrologi)'

    def group(self):
        return "02. Topography & Hydrology"

    def groupId(self):
        return 'topography'

    def createInstance(self):
        return HydrologyAnalysis()

    def shortHelpString(self):
        return (
            "Analyzes DEM to extract drainage networks and flow patterns using plantation standards.\n\n"
            "This tool utilizes GRASS GIS (r.watershed) to compute Flow Accumulation and Drainage Direction, "
            "then extracts vector streams based on a Catchment Area Threshold in Hectares."
        )

    def initAlgorithm(self, config=None):
        # 0. Input DEM
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.P_IN_DEM,
                'Input DEM (Raster)'
            )
        )

        # 1. Flow Accumulation Threshold (Hectares)
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_THRESHOLD_HA,
                'Stream Definition Threshold (Hectares)',
                QgsProcessingParameterNumber.Double,
                defaultValue=5.0
            )
        )

        # 2. Output Drainage Lines
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.P_OUT_STREAMS,
                'Output Drainage Lines (Polyline)',
                QgsProcessing.TypeVectorLine
            )
        )

        # 3. Output Flow Direction (Optional)
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.P_OUT_FLOWDIR,
                'Output Flow Direction (Raster) [Optional]',
                optional=True
            )
        )

        # 4. Output Flow Accumulation (Optional)
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.P_OUT_FLOWACC,
                'Output Flow Accumulation (Raster) [Optional]',
                optional=True
            )
        )

    def checkParameterValues(self, parameters, context):
        return super(HydrologyAnalysis, self).checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):
        # 1. License Check
        self.check_license_gate()

        in_dem = self.parameterAsRasterLayer(parameters, self.P_IN_DEM, context)
        if in_dem is None:
            raise Exception('Invalid input DEM.')

        threshold_ha = self.parameterAsDouble(parameters, self.P_THRESHOLD_HA, context)

        out_streams_path = self.parameterAsOutputLayer(parameters, self.P_OUT_STREAMS, context)
        out_flowdir_path = self.parameterAsOutputLayer(parameters, self.P_OUT_FLOWDIR, context)
        out_flowacc_path = self.parameterAsOutputLayer(parameters, self.P_OUT_FLOWACC, context)

        # Get Resolution for Threshold Calculation
        cell_size_x = in_dem.rasterUnitsPerPixelX()
        cell_size_y = in_dem.rasterUnitsPerPixelY()
        
        # Check if spatial reference is geographic (degrees)
        if in_dem.crs().isGeographic():
            # Approximate 1 degree to 111320 meters at equator
            cell_size_x_m = cell_size_x * 111320.0
            cell_size_y_m = cell_size_y * 111320.0
            cell_area_m2 = cell_size_x_m * cell_size_y_m
            feedback.pushInfo(f"DEM is in Geographic Coordinate System.")
            feedback.pushInfo(f"Resolution (Deg): {cell_size_x:.6f} x {cell_size_y:.6f}")
            feedback.pushInfo(f"Approx Resolution (m): {cell_size_x_m:.2f}m x {cell_size_y_m:.2f}m")
        else:
            cell_area_m2 = cell_size_x * cell_size_y
            feedback.pushInfo(f"Resolution: {cell_size_x:.2f}m x {cell_size_y:.2f}m")
        
        # Convert Threshold (Ha) to Cell Count
        # 1 Ha = 10,000 m2
        threshold_cells = int((threshold_ha * 10000) / cell_area_m2)
        if threshold_cells < 1:
            threshold_cells = 1
            
        feedback.pushInfo(f"Catchment Threshold: {threshold_ha} Ha (~{threshold_cells} cells)")

        # Prepare outputs for r.watershed
        flow_acc_target = out_flowacc_path if out_flowacc_path else 'TEMPORARY_OUTPUT'
        flow_dir_target = out_flowdir_path if out_flowdir_path else 'TEMPORARY_OUTPUT'
        
        feedback.pushInfo("Calculating Flow Accumulation and Direction using GRASS (r.watershed)...")
        # Run r.watershed
        # Note: In GRASS, r.watershed generates accumulation and drainage simultaneously.
        watershed_params = {
            'elevation': in_dem,
            'threshold': threshold_cells,
            '-s': False, # Do not force flow out of DEM
            '-m': False,
            '-a': True, # Positive flow accumulation even for likely underestimates
            'accumulation': flow_acc_target,
            'drainage': flow_dir_target,
            'stream': 'TEMPORARY_OUTPUT', # We just need this temporarily to convert to vector
            'GRASS_REGION_PARAMETER': None,
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_RASTER_FORMAT_META': ''
        }
        
        res_watershed = processing.run(
            "grass7:r.watershed", 
            watershed_params, 
            context=context, 
            feedback=feedback, 
            is_child_algorithm=True
        )
        
        tmp_stream_raster = res_watershed['stream']
        
        feedback.pushInfo("Extracting Drainage Network to Vector (Polyline)...")

        # r.to.vect harus menulis ke file fisik (tidak bisa ke memory layer)
        from qgis.core import (
            QgsProcessingUtils, QgsFeatureSink, QgsFields,
            QgsWkbTypes, QgsField, QgsFeature
        )
        from qgis.PyQt.QtCore import QVariant
        import tempfile, os

        tmp_gpkg = QgsProcessingUtils.generateTempFilename('streams.gpkg')

        to_vect_params = {
            'input': tmp_stream_raster,
            'type': 0,     # 0 = line dalam enum grass7:r.to.vect di QGIS
            '-s': True,    # Smooth corners
            '-v': False,
            '-z': False,
            'column': 'value',
            'output': tmp_gpkg,
            'GRASS_REGION_PARAMETER': None,
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_OUTPUT_TYPE_PARAMETER': 2,  # line
            'GRASS_VECTOR_DSCO': '',
            'GRASS_VECTOR_LCO': '',
            'GRASS_VECTOR_EXPORT_NOCAT': False
        }

        res_vect = processing.run(
            "grass7:r.to.vect", to_vect_params,
            context=context, feedback=feedback, is_child_algorithm=True
        )

        # Baca hasil GRASS dari file temp dan tulis ke FeatureSink
        vect_path = res_vect.get('output', tmp_gpkg)
        stream_layer = QgsProcessingUtils.mapLayerFromString(vect_path, context)
        if stream_layer is None or not stream_layer.isValid():
            # Fallback: coba load langsung dari path
            from qgis.core import QgsVectorLayer
            stream_layer = QgsVectorLayer(vect_path, 'streams', 'ogr')

        if stream_layer and stream_layer.isValid():
            (sink, dest_id) = self.parameterAsSink(
                parameters, self.P_OUT_STREAMS, context,
                stream_layer.fields(),
                QgsWkbTypes.LineString,
                stream_layer.sourceCrs()
            )
            for feat in stream_layer.getFeatures():
                if feedback.isCanceled():
                    break
                sink.addFeature(feat, QgsFeatureSink.FastInsert)
        else:
            feedback.pushWarning("Peringatan: Layer drainase tidak dapat dimuat. Periksa apakah GRASS berhasil mengekstrak garis.")
            (sink, dest_id) = self.parameterAsSink(
                parameters, self.P_OUT_STREAMS, context,
                QgsFields(), QgsWkbTypes.LineString, in_dem.crs()
            )

        results = {self.P_OUT_STREAMS: dest_id}
        if out_flowdir_path:
            results[self.P_OUT_FLOWDIR] = out_flowdir_path
        if out_flowacc_path:
            results[self.P_OUT_FLOWACC] = out_flowacc_path

        feedback.pushInfo("============================================================")
        feedback.pushInfo("          LAPORAN ANALISIS HIDROLOGI")
        feedback.pushInfo("============================================================")
        feedback.pushInfo(f"- Threshold Sungai : {threshold_ha} Hektar")
        feedback.pushInfo("============================================================")

        return results

