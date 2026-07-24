# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsFeatureSink,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsWkbTypes,
    QgsPointXY,
    QgsGeometry
)
from qgis.PyQt.QtCore import QVariant
import math
from .base_algorithm import BasePlantationAlgorithm

class GeneratePlantingPoints(BasePlantationAlgorithm):
    P_INPUT_POLY = 'INPUT_POLY'
    P_PATTERN = 'PATTERN'
    P_ROW_SPACING = 'ROW_SPACING'
    P_PLANT_SPACING = 'PLANT_SPACING'
    P_ORIENTATION = 'ORIENTATION'
    P_MANUAL_ROTATION = 'MANUAL_ROTATION'
    P_MARGIN = 'MARGIN'
    P_MARGIN_KIRI = 'MARGIN_KIRI'
    P_MARGIN_KANAN = 'MARGIN_KANAN'
    P_OUT_POINTS = 'OUT_POINTS'

    PATTERN_OPTS = ["Triangular (Mata Lima)", "Triangular (Equilateral / Sama Sisi)", "Rectangular (Persegi)"]
    ORIENT_OPTS = ["North-South", "West-East", "Longest Side (Auto)", "Manual Angle"]

    def get_minimum_tier(self):
        return "basic" # Required for user to test if it works/expires properly

    def name(self):
        return 'generateplantingpoints'

    def displayName(self):
        return '06. Generate Planting Points (Titik Tanam)'

    def group(self):
        return "03. Agronomy & Planting"

    def groupId(self):
        return 'agronomy'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_INPUT_POLY,
            'Planting Blocks (Polygon)',
            types=[QgsProcessing.TypeVectorPolygon]
        ))

        self.addParameter(QgsProcessingParameterEnum(
            self.P_PATTERN,
            'Planting Pattern',
            options=self.PATTERN_OPTS,
            defaultValue=1
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_ROW_SPACING,
            'Jarak Diagonal (Sisi Miring) / Antar Baris (m)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=9.0
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_PLANT_SPACING,
            'Jarak Dalam Baris (Tegak) / Plant Spacing (m)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=9.0
        ))

        self.addParameter(QgsProcessingParameterEnum(
            self.P_ORIENTATION,
            'Orientation',
            options=self.ORIENT_OPTS,
            defaultValue=0
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_MANUAL_ROTATION,
            'Manual Rotation Angle (Degrees) (Optional)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=0,
            optional=True
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_MARGIN,
            'Boundary Margin (m)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=2.5
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_MARGIN_KIRI,
            'Margin Kiri (m) (Optional)',
            type=QgsProcessingParameterNumber.Double,
            optional=True
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_MARGIN_KANAN,
            'Margin Kanan (m) (Optional)',
            type=QgsProcessingParameterNumber.Double,
            optional=True
        ))

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUT_POINTS,
            'Output Points'
        ))

    def createInstance(self):
        return GeneratePlantingPoints()

    def detect_polygon_attributes(self, fields):
        field_priority = {
            'afdeling': ['afdeling', 'afd', 'divisi', 'division', 'estate'],
            'blok': ['blok', 'block', 'block_id', 'blok_id', 'id_blok'],
            'petak': ['petak', 'plot', 'no_petak', 'anak_petak']
        }
        detected = {}
        available_fields = [f.name().lower() for f in fields]
        real_fields = {f.name().lower(): f.name() for f in fields}

        for attr_type, candidates in field_priority.items():
            for candidate in candidates:
                if candidate in available_fields:
                    detected[attr_type] = real_fields[candidate]
                    break
        return detected

    def checkParameterValues(self, parameters, context):
        return super(GeneratePlantingPoints, self).checkParameterValues(parameters, context)

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