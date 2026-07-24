# -*- coding: utf-8 -*-

import os
import math
import time
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsField,
    QgsFeature,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsWkbTypes,
    QgsMessageLog,
    Qgis,
    QgsCoordinateTransform,
    QgsRectangle
)
from qgis.PyQt.QtCore import QVariant
from .base_algorithm import BasePlantationAlgorithm
try:
    from osgeo import gdal
except ImportError:
    import gdal

class OilPalmDetection(BasePlantationAlgorithm):
    P_INPUT_RASTER = 'INPUT_RASTER'
    P_MODEL_FILE = 'MODEL_FILE'
    P_AOI_MASK = 'AOI_MASK'
    P_CONF_THRESHOLD = 'CONF_THRESHOLD'
    P_IOU_THRESHOLD = 'IOU_THRESHOLD'
    P_TILE_SIZE = 'TILE_SIZE'
    P_OVERLAP = 'OVERLAP'
    P_MIN_SIZE = 'MIN_SIZE'
    P_MAX_SIZE = 'MAX_SIZE'
    P_CLUSTER_DIST = 'CLUSTER_DIST'
    P_STRICT_AOI = 'STRICT_AOI'
    P_ENGINE = 'ENGINE'
    P_OUTPUT = 'OUTPUT'

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'oilpalmdetection'

    def displayName(self):
        return '18. Oil Palm Detection (Deteksi Pohon Sawit)'

    def group(self):
        return '04. Plantation Intelligence (AI)'

    def groupId(self):
        return 'ai'

    def createInstance(self):
        return OilPalmDetection()

    def shortHelpString(self):
        return "Automatically detects oil palm trees from high-resolution imagery using AI (Deep Learning ONNX)."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.P_INPUT_RASTER, 'Input Image (Raster RGB)'
        ))
        
        self.addParameter(QgsProcessingParameterFile(
            self.P_MODEL_FILE, 'AI Model File (.onnx)', extension='onnx'
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_AOI_MASK, 'Area of Interest (AOI)', types=[QgsProcessing.TypeVectorPolygon], optional=True
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_CONF_THRESHOLD, 'Confidence Threshold', type=QgsProcessingParameterNumber.Double, defaultValue=0.15
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_IOU_THRESHOLD, 'IoU Threshold', type=QgsProcessingParameterNumber.Double, defaultValue=0.25
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_TILE_SIZE, 'Tile Size (px)', type=QgsProcessingParameterNumber.Integer, defaultValue=640
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_OVERLAP, 'Overlap (%)', type=QgsProcessingParameterNumber.Integer, defaultValue=25
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_MIN_SIZE, 'Min Tree Size (px)', type=QgsProcessingParameterNumber.Integer, defaultValue=80
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_MAX_SIZE, 'Max Tree Size (px)', type=QgsProcessingParameterNumber.Integer, defaultValue=300
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_CLUSTER_DIST, 'Clustering Distance (m) [Deduplication]', type=QgsProcessingParameterNumber.Double, defaultValue=3.0
        ))
        
        self.addParameter(QgsProcessingParameterBoolean(
            self.P_STRICT_AOI, 'Strict AOI Enforcement', defaultValue=True
        ))
        
        self.addParameter(QgsProcessingParameterEnum(
            self.P_ENGINE, 'Processing Engine', options=['Auto-Detect (GPU if available)', 'Force CPU'], defaultValue=0
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUTPUT, 'Output Detections (Point)', type=QgsProcessing.TypeVectorPoint
        ))

    def check_dependencies(self, feedback):
        missing = []
        try:
            import onnxruntime
        except ImportError:
            missing.append("onnxruntime")
            
        try:
            import cv2
        except ImportError:
            missing.append("opencv-python")
            
        if missing:
            raise QgsProcessingException(
                f"Modul Python berikut belum terinstal: {', '.join(missing)}. "
                "Silakan buka OSGeo4W Shell dan jalankan: python -m pip install onnxruntime opencv-python"
            )

    def calculate_iou(self, box1, box2):
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        xi1 = max(x1_1, x1_2); yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2); yi2 = min(y2_1, y2_2)

        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = box1_area + box2_area - inter_area

        return inter_area / union_area if union_area > 0 else 0.0

    def non_max_suppression(self, detections, iou_thresh):
        if not detections: return []
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        filtered = []
        while detections:
            best = detections.pop(0)
            filtered.append(best)
            detections = [d for d in detections if self.calculate_iou(best['bbox'], d['bbox']) < iou_thresh]
        return filtered

    def deduplicate_points(self, points, clustering_distance, feedback):
        import numpy as np
        if not points: return []
        
        # We can try sklearn DBSCAN, or fallback to distance check
        try:
            from sklearn.cluster import DBSCAN
            centers = np.array([[d['x'], d['y']] for d in points])
            clustering = DBSCAN(eps=clustering_distance, min_samples=1).fit(centers)
            unique = []
            for cid in set(clustering.labels_):
                c_indices = np.where(clustering.labels_ == cid)[0]
                c_points = [points[i] for i in c_indices]
                unique.append(max(c_points, key=lambda x: x['confidence']))
            return unique
        except ImportError:
            feedback.pushInfo("Sklearn tidak ditemukan, menggunakan Distance Fallback untuk deduplikasi...")
            unique = []
            used_pos = []
            for p in sorted(points, key=lambda x: x['confidence'], reverse=True):
                curr = (p['x'], p['y'])
                is_dup = False
                for used in used_pos:
                    dist = math.sqrt((curr[0]-used[0])**2 + (curr[1]-used[1])**2)
                    if dist < clustering_distance:
                        is_dup = True; break
                if not is_dup:
                    unique.append(p)
                    used_pos.append(curr)
            return unique

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