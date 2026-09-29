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
    P_PROFILE = 'PROFILE'
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
    P_EXG_THRESH = 'EXG_THRESH'
    P_BLUR_FILTER = 'BLUR_FILTER'
    P_OUTPUT = 'OUTPUT'

    def get_minimum_tier(self):
        return "pro"

    def name(self):
        return 'oilpalmdetection'

    def displayName(self):
        return '17. AI Tree Counting (Hybrid)'

    def group(self):
        return '04. Plantation Intelligence (AI)'

    def groupId(self):
        return 'intelligence'

    def createInstance(self):
        return OilPalmDetection()

    def shortHelpString(self):
        return "Automatically detects oil palm trees or natural forest canopies using Deep Learning (ONNX) or ExG Hybrid algorithms."

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.P_INPUT_RASTER, 'Input Image (Raster RGB)'
        ))
        
        self.addParameter(QgsProcessingParameterEnum(
            self.P_PROFILE, 'Detection Profile', 
            options=['Oil Palm (ONNX Deep Learning)', 'Natural Forest (ExG Hybrid)', 'Oil Palm (ExG Hybrid)'], 
            defaultValue=0
        ))
        
        self.addParameter(QgsProcessingParameterFile(
            self.P_MODEL_FILE, 'AI Model File (.onnx) [Only for ONNX Profile]', extension='onnx', optional=True
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.P_AOI_MASK, 'Area of Interest (AOI)', types=[QgsProcessing.TypeVectorPolygon], optional=True
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_CONF_THRESHOLD, 'Confidence Threshold [ONNX]', type=QgsProcessingParameterNumber.Double, defaultValue=0.15
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_IOU_THRESHOLD, 'IoU Threshold [ONNX]', type=QgsProcessingParameterNumber.Double, defaultValue=0.25
        ))
        
        self.addParameter(QgsProcessingParameterNumber(
            self.P_EXG_THRESH, 'ExG Threshold [Only for ExG Profile]', type=QgsProcessingParameterNumber.Integer, defaultValue=18
        ))
        
        self.addParameter(QgsProcessingParameterBoolean(
            self.P_BLUR_FILTER, 'Exclude Blurry Areas [ExG Profile]', defaultValue=False
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
            self.P_ENGINE, 'Processing Engine [ONNX]', options=['Auto-Detect (GPU if available)', 'Force CPU'], defaultValue=0
        ))
        
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.P_OUTPUT, 'Output Detections (Point)', type=QgsProcessing.TypeVectorPoint
        ))

    def ensure_dependencies(self, feedback, needs_onnx, needs_scipy):
        missing = []
        if needs_onnx:
            try:
                import onnxruntime
            except ImportError:
                missing.append("onnxruntime")
            try:
                import cv2
            except ImportError:
                missing.append("opencv-python")
        
        if needs_scipy:
            try:
                import scipy.ndimage
            except ImportError:
                missing.append("scipy")
                
        if missing:
            feedback.pushInfo(f"Memulai instalasi otomatis modul yang kurang: {', '.join(missing)}...")
            import subprocess, sys
            try:
                python_exe = sys.executable
                subprocess.check_call([python_exe, "-m", "pip", "install"] + missing, 
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                feedback.pushInfo("Instalasi berhasil! Memuat ulang modul...")
            except Exception as e:
                raise QgsProcessingException(
                    f"Gagal menginstal {missing} secara otomatis. Error: {str(e)}. "
                    "Silakan buka OSGeo4W Shell dan instal secara manual dengan pip."
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

    def refine_centroid(self, veg_mask, exg, px_i, py_i, radius):
        import numpy as np
        h, w = veg_mask.shape
        y0, y1 = max(0, py_i - radius), min(h, py_i + radius + 1)
        x0, x1 = max(0, px_i - radius), min(w, px_i + radius + 1)
        if x1 <= x0 or y1 <= y0: return px_i, py_i
        ys, xs = np.mgrid[y0:y1, x0:x1]
        dist2 = (xs - px_i) ** 2 + (ys - py_i) ** 2
        decay = np.exp(-dist2 / (2 * (max(1, radius / 2.0)) ** 2))
        local_w = np.clip(exg[y0:y1, x0:x1], 0, None) * veg_mask[y0:y1, x0:x1] * decay
        total = local_w.sum()
        if total <= 0: return px_i, py_i
        cy = float((ys * local_w).sum() / total)
        cx = float((xs * local_w).sum() / total)
        return int(round(cx)), int(round(cy))

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