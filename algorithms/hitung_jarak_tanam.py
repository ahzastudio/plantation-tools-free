# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterEnum,
    QgsProcessingParameterField,
    QgsProcessingOutputVectorLayer,
    QgsProcessingException,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsSpatialIndex
)
from qgis.PyQt.QtCore import QVariant
import math
from .base_algorithm import BasePlantationAlgorithm

class HitungJarakTanam(BasePlantationAlgorithm):
    P_IN_POINTS = 'IN_POINTS'
    P_AREA_TYPE = 'AREA_TYPE'
    P_AREA_FIELD = 'AREA_FIELD'
    P_OUT_POINTS = 'OUT_POINTS'

    TYPE_OPTS = ["Areal Flat", "Areal Terasan", "Campuran (Baca dari Field)"]

    def get_minimum_tier(self):
        return "basic"

    def name(self):
        return 'hitungjaraktanam'

    def displayName(self):
        return '08. Hitung Jarak Tanam'

    def group(self):
        return "03. Agronomy & Planting"

    def groupId(self):
        return 'agronomy'

    def createInstance(self):
        return HitungJarakTanam()

    def shortHelpString(self):
        return "Planting Distance Analysis (Hitung Jarak Tanam). Menghitung jarak tanam (Utara-Selatan & Timur-Barat) dan mengevaluasi kategori kerapatan (Areal Flat / Terasan)."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(
            self.P_IN_POINTS,
            'Input Titik Tanam (Point)',
            types=[QgsProcessing.TypeVectorPoint]
        ))

        self.addParameter(QgsProcessingParameterEnum(
            self.P_AREA_TYPE,
            'Tipe Area',
            options=self.TYPE_OPTS,
            defaultValue=0
        ))

        self.addParameter(QgsProcessingParameterField(
            self.P_AREA_FIELD,
            'Field Tipe Area (Opsional jika Campuran)',
            parentLayerParameterName=self.P_IN_POINTS,
            type=QgsProcessingParameterField.String,
            optional=True
        ))

        # Menambahkan output derived agar bisa di-chain (optional tapi bagus untuk QGIS)
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