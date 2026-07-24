# -*- coding: utf-8 -*-

import os
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterFolderDestination,
    QgsProcessingException,
    QgsVectorFileWriter,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext,
    QgsProcessingMultiStepFeedback,
    QgsProject
)
from .base_algorithm import BasePlantationAlgorithm

class ExportToGeoJSON(BasePlantationAlgorithm):
    P_LAYERS = 'INPUT_LAYERS'
    P_FOLDER = 'OUTPUT_FOLDER'

    def get_minimum_tier(self):
        return "free"

    def name(self):
        return 'exporttogeojson'

    def displayName(self):
        return '22. Export to GeoJSON (WebGIS)'

    def group(self):
        return "06. Web & Reporting"

    def groupId(self):
        return 'web_reporting'

    def createInstance(self):
        return ExportToGeoJSON()

    def shortHelpString(self):
        return "Mengekspor beberapa layer sekaligus ke dalam format GeoJSON dengan proyeksi standar WebGIS (WGS84 EPSG:4326) serta membuang dimensi Z/M agar file ringan dibaca Leaflet/Mapbox."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMultipleLayers(
            self.P_LAYERS, 'Input Feature Layers', layerType=QgsProcessing.TypeVectorAnyGeometry
        ))
        
        self.addParameter(QgsProcessingParameterFolderDestination(
            self.P_FOLDER, 'Output Folder'
        ))

    def processAlgorithm(self, parameters, context, feedback):
        self.check_license_gate()
        
        layers = self.parameterAsLayerList(parameters, self.P_LAYERS, context)
        out_folder = self.parameterAsString(parameters, self.P_FOLDER, context)
        
        if not layers:
            raise QgsProcessingException("Pilih setidaknya satu layer untuk diekspor.")
            
        if not os.path.exists(out_folder):
            os.makedirs(out_folder)
            
        multi_feedback = QgsProcessingMultiStepFeedback(len(layers), feedback)
        
        crs_wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        transform_context = context.transformContext()
        
        success_count = 0
        
        for i, layer in enumerate(layers):
            if multi_feedback.isCanceled():
                break
                
            multi_feedback.setCurrentStep(i)
            safe_name = layer.name().replace(" ", "_").replace(".", "_")
            out_file = os.path.join(out_folder, f"{safe_name}.geojson")
            
            multi_feedback.pushInfo(f"Mengekspor [{i+1}/{len(layers)}]: {safe_name}...")
            
            # Setup GeoJSON Writer Options
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GeoJSON"
            options.fileEncoding = "UTF-8"
            
            # Force transform to WGS84
            # QGIS v3 otomatis melakukan transformasi jika destCRS didefinisikan
            options.destCRS = crs_wgs84
            
            # Memangkas desimal koordinat menjadi 8 digit (Akurasi ~1 Milimeter) 
            # untuk menekan ukuran file drastis tanpa merusak bentuk geometri
            options.layerOptions = ["COORDINATE_PRECISION=8"]
            
            # Force drop Z and M dimensions for WebGIS compatibility
            options.force2D = True
            
            # Write file
            result = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, out_file, transform_context, options
            )
            error_code = result[0]
            error_msg = result[1]
            
            if error_code == QgsVectorFileWriter.NoError:
                multi_feedback.pushInfo(f"  -> Tersimpan: {out_file}")
                success_count += 1
            else:
                multi_feedback.pushInfo(f"  -> GAGAL mengekspor {safe_name}: {error_msg}")
                
        feedback.pushInfo("="*50)
        feedback.pushInfo(" BATCH EXPORT SUCCESS")
        feedback.pushInfo(f" Berhasil  : {success_count} Layer")
        feedback.pushInfo(f" Lokasi    : {out_folder}")
        feedback.pushInfo("="*50)
        
        return {self.P_FOLDER: out_folder}
