# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingOutputVectorLayer,
    QgsProcessingException,
    QgsFeature,
    QgsFields,
    QgsField
)
from qgis.PyQt.QtCore import QVariant
from .base_algorithm import BasePlantationAlgorithm

class NumberingRowsAndPoints(BasePlantationAlgorithm):
    P_IN_POINTS = 'IN_POINTS'
    P_BLOCK_FIELD = 'BLOCK_FIELD'
    P_ORIENTATION = 'ORIENTATION'
    P_ORIGIN_CORNER = 'ORIGIN_CORNER'
    P_TOLERANCE = 'TOLERANCE'
    P_OUT_POINTS = 'OUT_POINTS'

    OPTS_ORIENTATION = ["North-South (Utara-Selatan)", "West-East (Barat-Timur)"]
    OPTS_CORNER = ["Top Left", "Top Right", "Bottom Left", "Bottom Right"]

    def get_minimum_tier(self):
        return "basic"

    def name(self):
        return 'numberingrowsandpoints'

    def displayName(self):
        return '09. Numbering Rows & Points (Penomoran Baris & Pokok)'

    def group(self):
        return '03. Agronomy & Planting'

    def groupId(self):
        return 'agronomy'

    def createInstance(self):
        return NumberingRowsAndPoints()

    def shortHelpString(self):
        return "Menomori titik tanam secara sistematis berdasarkan urutan baris dan kolom. Update dilakukan secara in-place (langsung ke atribut layer)."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.P_IN_POINTS,
            'Planting Points (Titik Tanam)',
            types=[QgsProcessing.TypeVectorPoint]
        ))

        self.addParameter(QgsProcessingParameterField(
            self.P_BLOCK_FIELD,
            'Block ID Field (Field Blok)',
            parentLayerParameterName=self.P_IN_POINTS,
            type=QgsProcessingParameterField.Any
        ))

        self.addParameter(QgsProcessingParameterEnum(
            self.P_ORIENTATION,
            'Row Orientation (Arah Baris)',
            options=self.OPTS_ORIENTATION,
            defaultValue=0
        ))

        self.addParameter(QgsProcessingParameterEnum(
            self.P_ORIGIN_CORNER,
            'Origin Start (Mulai dari)',
            options=self.OPTS_CORNER,
            defaultValue=2 # Bottom Left
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.P_TOLERANCE,
            'Row Width / Tolerance (m)',
            type=QgsProcessingParameterNumber.Double,
            defaultValue=1.0
        ))

        self.addOutput(QgsProcessingOutputVectorLayer(
            self.P_OUT_POINTS,
            'Titik Tanam Terupdate'
        ))

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