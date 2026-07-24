# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterDistance,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsFeatureSink,
    QgsFeature,
    QgsGeometry,
    QgsFields,
    QgsField,
    QgsWkbTypes,
    QgsVectorLayer
)
from qgis.PyQt.QtCore import QVariant
from qgis import processing
from .base_algorithm import BasePlantationAlgorithm

class CreateKontur(BasePlantationAlgorithm):
    """
    QGIS Implementation of Create Contours tool.
    Ported from ArcGIS Pro PlantationTools.
    """
    
    P_INPUT_DEM = 'INPUT_DEM'
    P_INTERVAL = 'INTERVAL'
    P_INDEX_INTERVAL = 'INDEX_INTERVAL'
    P_MIN_LENGTH = 'MIN_LENGTH'
    P_APPLY_SMOOTHING = 'APPLY_SMOOTHING'
    P_SMOOTHING_ITERATIONS = 'SMOOTHING_ITERATIONS'
    P_OUTPUT = 'OUTPUT'

    def get_minimum_tier(self):
        return "free"

    def name(self):
        return 'createkontur'

    def displayName(self):
        return '02. Create Contours (Buat Kontur)'

    def group(self):
        return "02. Topography & Hydrology"

    def groupId(self):
        return 'topography'

    def shortHelpString(self):
        return "Membuat garis kontur dari DEM dengan klasifikasi interval reguler dan indeks."

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.P_INPUT_DEM,
                'Input DEM'
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_INTERVAL,
                'Interval Kontur (meter)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_INDEX_INTERVAL,
                'Interval Indeks (meter)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=50.0
            )
        )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.P_MIN_LENGTH,
                'Minimum Contour Length (meter)',
                defaultValue=50.0,
                parentParameterName=self.P_INPUT_DEM
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.P_APPLY_SMOOTHING,
                'Apply Smoothing',
                defaultValue=False
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_SMOOTHING_ITERATIONS,
                'Smoothing Iterations (1-5)',
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=3,
                minValue=1,
                maxValue=10,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.P_OUTPUT,
                'Output Kontur'
            )
        )

    def createInstance(self):
        return CreateKontur()


    def checkParameterValues(self, parameters, context):
        return super(CreateKontur, self).checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):
        # 1. License Check
        self.check_license_gate()
        
        # 2. Extract Parameters
        dem_layer = self.parameterAsRasterLayer(parameters, self.P_INPUT_DEM, context)
        interval = self.parameterAsDouble(parameters, self.P_INTERVAL, context)
        index_interval = self.parameterAsDouble(parameters, self.P_INDEX_INTERVAL, context)
        min_length = self.parameterAsDouble(parameters, self.P_MIN_LENGTH, context)
        apply_smoothing = self.parameterAsBool(parameters, self.P_APPLY_SMOOTHING, context)
        smooth_iter = self.parameterAsInt(parameters, self.P_SMOOTHING_ITERATIONS, context)

        if dem_layer is None:
            raise QgsProcessingException("Input DEM tidak valid.")

        # 3. Create Contours using GDAL
        feedback.pushInfo("1. Membuat kontur dari DEM (GDAL Contour)...")
        contour_res = processing.run("gdal:contour", {
            'INPUT': dem_layer,
            'BAND': 1,
            'INTERVAL': interval,
            'FIELD_NAME': 'ELEV',
            'CREATE_3D': False,
            'IGNORE_NODATA': False,
            'NODATA': None,
            'OFFSET': 0,
            'EXTRA': '',
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }, context=context, feedback=feedback, is_child_algorithm=True)
        
        contour_layer_path = contour_res['OUTPUT']
        contour_layer = QgsVectorLayer(contour_layer_path, "contour", "ogr")

        # 4. Filter by Length and Add Attributes
        feedback.pushInfo("2. Menghitung panjang, memfilter kontur pendek, dan mengisi TYPE/LABEL...")
        
        fields = contour_layer.fields()
        fields.append(QgsField('TYPE', QVariant.String, len=10))
        fields.append(QgsField('LABEL', QVariant.String, len=20))
        fields.append(QgsField('LENGTH_M', QVariant.Double))

        # We will filter and calculate in memory before smoothing
        temp_filtered_layer = QgsVectorLayer(f"LineString?crs={contour_layer.crs().authid()}", "Filtered", "memory")
        pr = temp_filtered_layer.dataProvider()
        pr.addAttributes(fields.toList())
        temp_filtered_layer.updateFields()
        
        feats_to_add = []
        elev_idx = contour_layer.fields().indexOf('ELEV')
        
        for feat in contour_layer.getFeatures():
            geom = feat.geometry()
            length_m = geom.length()  # Planar length. For geodesic, context is needed, but we keep it simple here.
            
            if length_m >= min_length:
                elev = feat.attributes()[elev_idx]
                
                new_feat = QgsFeature(fields)
                new_feat.setGeometry(geom)
                
                # Copy original attributes
                for i in range(contour_layer.fields().count()):
                    new_feat.setAttribute(i, feat.attribute(i))
                    
                # New attributes
                new_feat.setAttribute('LENGTH_M', length_m)
                if elev % index_interval == 0:
                    new_feat.setAttribute('TYPE', 'INDEKS')
                    new_feat.setAttribute('LABEL', f"{int(elev)} m")
                else:
                    new_feat.setAttribute('TYPE', 'REGULER')
                    new_feat.setAttribute('LABEL', '')
                    
                feats_to_add.append(new_feat)
                
        pr.addFeatures(feats_to_add)
        feedback.pushInfo(f"Mempertahankan {len(feats_to_add)} garis kontur (Panjang >= {min_length}m).")
        
        # 5. Apply Smoothing
        if apply_smoothing:
            feedback.pushInfo("3. Melakukan smoothing pada kontur...")
            smooth_res = processing.run("native:smoothgeometry", {
                'INPUT': temp_filtered_layer,
                'ITERATIONS': smooth_iter,
                'OFFSET': 0.25,
                'MAX_ANGLE': 180,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }, context=context, feedback=feedback, is_child_algorithm=True)
            from qgis.core import QgsProcessingUtils
            final_layer = QgsProcessingUtils.mapLayerFromString(smooth_res['OUTPUT'], context)
        else:
            final_layer = temp_filtered_layer

        # 6. Save to Output
        feedback.pushInfo("4. Menyimpan hasil akhir...")
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.P_OUTPUT, context,
            final_layer.fields(), final_layer.wkbType(), final_layer.sourceCrs()
        )
        
        if sink is None:
            raise QgsProcessingException("Gagal menyiapkan output layer.")

        for feat in final_layer.getFeatures():
            sink.addFeature(feat, QgsFeatureSink.FastInsert)

        return {self.P_OUTPUT: dest_id}
