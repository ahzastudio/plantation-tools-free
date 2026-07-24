# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsFeatureSink,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext
)
from qgis.PyQt.QtCore import QVariant
from qgis import processing
from .base_algorithm import BasePlantationAlgorithm


class SinkDetection(BasePlantationAlgorithm):
    """
    QGIS Implementation of Sink Detection (Identifikasi Area Genangan).
    Ported from ArcGIS Pro PlantationTools.

    Pipeline:
    1.  Reproject DEM if geographic (GCS)
    2.  Fill Sinks (SAGA: Fill Sinks (Wang & Liu))
    3.  Calculate Sink Depth: filled_dem - original_dem
    4.  Extract sinks >= min_depth
    5.  Polygonise the extracted sink areas
    6.  Clip to blocks if provided
    7.  Calculate attributes: LUAS_M2, LUAS_HA, KATEGORI
    """

    P_INPUT_DEM        = 'INPUT_DEM'
    P_MIN_DEPTH        = 'MIN_DEPTH'
    P_IN_BLOCKS        = 'IN_BLOCKS'
    P_OUT_FC           = 'OUT_FC'
    P_OUT_DEPTH_RASTER = 'OUT_DEPTH_RASTER'

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'sinkdetection'

    def displayName(self):
        return '25. Identifikasi Area Genangan (Sink Detection)'

    def group(self):
        return "07. Analisa Infrastruktur (Jalan & Parit)"

    def groupId(self):
        return 'infrastructure_analysis'

    def shortHelpString(self):
        return (
            "<b>Identifikasi Area Genangan (Sink Detection)</b><br>"
            "Mengidentifikasi area genangan atau cekungan (sink) dari data DEM.<br><br>"
            "Sesuai panduan teknis: kajian ketinggian kawasan perlu dilaksanakan sebelum "
            "pembangunan parit/drainase untuk meminimalkan risiko banjir/genangan air.<br><br>"
            "<b>Kedalaman Minimum</b>: Kedalaman minimum (meter) untuk mendeteksi genangan. "
            "Cekungan dengan kedalaman kurang dari nilai ini akan diabaikan.<br><br>"
            "<b>Output</b>:<br>"
            "<ul>"
            "<li><b>Area Genangan (Polygon)</b>: Layer polygon area genangan lengkap dengan atribut "
            "<i>LUAS_M2</i>, <i>LUAS_HA</i>, dan <i>KATEGORI</i> (Genangan Kecil, Sedang, Besar).</li>"
            "<li><b>Raster Kedalaman (Opsional)</b>: Raster selisih tinggi antara DEM terisi (filled) "
            "dan DEM asli.</li>"
            "</ul>"
        )

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.P_INPUT_DEM,
                'Input DEM Raster'
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.P_MIN_DEPTH,
                'Kedalaman Minimum Genangan (meter)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.1,
                minValue=0.01
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.P_IN_BLOCKS,
                'Clip ke Layer Blok (Opsional)',
                optional=True,
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.P_OUT_FC,
                'Output Area Genangan (Polygon)'
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.P_OUT_DEPTH_RASTER,
                'Output Raster Kedalaman Genangan (Opsional)',
                optional=True,
                createByDefault=False
            )
        )

    def createInstance(self):
        return SinkDetection()

    # ------------------------------------------------------------------ #
    #  HELPER: auto UTM zone from raster extent                           #
    # ------------------------------------------------------------------ #
    def _get_utm_epsg(self, raster_layer):
        ext = raster_layer.extent()
        cx = (ext.xMinimum() + ext.xMaximum()) / 2
        cy = (ext.yMinimum() + ext.yMaximum()) / 2

        src_crs = raster_layer.crs()
        if not src_crs.isGeographic():
            from qgis.core import QgsCoordinateTransform
            geo_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            xform = QgsCoordinateTransform(src_crs, geo_crs, QgsCoordinateTransformContext())
            pt = xform.transform(cx, cy)
            cx, cy = pt.x(), pt.y()

        utm_zone = int((cx + 180) / 6) % 60 + 1
        epsg = 32600 + utm_zone if cy >= 0 else 32700 + utm_zone
        return epsg

    # ------------------------------------------------------------------ #
    #  MAIN                                                               #
    # ------------------------------------------------------------------ #

    def checkParameterValues(self, parameters, context):
        return super(SinkDetection, self).checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):
        from qgis.core import QgsProcessingException
        try:
            import qgis.utils
            from ..license_guard import LicenseDashboardDialog
            parent = qgis.utils.iface.mainWindow() if qgis.utils.iface else None
            dlg = LicenseDashboardDialog(parent, error_msg='FITUR PRO: Ini adalah versi Community/Free Edition. Silakan klik tombol di bawah untuk aktivasi/upgrade ke PRO.')
            if hasattr(dlg, 'exec'): dlg.exec()
            else: dlg.exec_()
        except Exception as e:
            import qgis.core
            qgis.core.QgsMessageLog.logMessage('License Check Error: ' + str(e), 'PlantationTools', qgis.core.Qgis.Warning)
        raise QgsProcessingException('FITUR PRO: Ini adalah versi Community/Free Edition. Silakan hubungi Admin via WhatsApp (+62 822-5476-0769) atau link wa.me/6282254760769 untuk Klaim Trial 14-Hari.')