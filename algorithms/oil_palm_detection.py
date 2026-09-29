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
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec B603
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
        self.check_license_gate()
        
        profile_idx = self.parameterAsEnum(parameters, self.P_PROFILE, context)
        is_onnx = (profile_idx == 0)
        
        self.ensure_dependencies(feedback, needs_onnx=is_onnx, needs_scipy=not is_onnx)
        
        arcpro_lib_bin = r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\Library\bin"
        if os.path.exists(arcpro_lib_bin):
            if hasattr(os, 'add_dll_directory'): os.add_dll_directory(arcpro_lib_bin)
            if arcpro_lib_bin not in os.environ.get('PATH', ''):
                os.environ['PATH'] = f"{arcpro_lib_bin};{os.environ.get('PATH', '')}"

        import numpy as np
        raster = self.parameterAsRasterLayer(parameters, self.P_INPUT_RASTER, context)
        aoi_source = self.parameterAsSource(parameters, self.P_AOI_MASK, context)
        tile_size = self.parameterAsInt(parameters, self.P_TILE_SIZE, context)
        overlap = self.parameterAsInt(parameters, self.P_OVERLAP, context)
        min_size = self.parameterAsInt(parameters, self.P_MIN_SIZE, context)
        max_size = self.parameterAsInt(parameters, self.P_MAX_SIZE, context)
        cluster_dist = self.parameterAsDouble(parameters, self.P_CLUSTER_DIST, context)
        strict_aoi = self.parameterAsBool(parameters, self.P_STRICT_AOI, context)
        
        crs = raster.crs()
        ext = raster.extent()
        
        aoi_geom = None
        if aoi_source:
            feedback.pushInfo("Membaca AOI...")
            for feat in aoi_source.getFeatures():
                if aoi_geom is None: aoi_geom = feat.geometry()
                else: aoi_geom = aoi_geom.combine(feat.geometry())
            if aoi_source.sourceCrs() != crs:
                xform = QgsCoordinateTransform(aoi_source.sourceCrs(), crs, context.transformContext())
                aoi_geom.transform(xform)
            intersect_ext = ext.intersect(aoi_geom.boundingBox())
            if intersect_ext.isEmpty():
                raise QgsProcessingException("AOI tidak bersinggungan dengan Raster.")
            start_x, end_x = intersect_ext.xMinimum(), intersect_ext.xMaximum()
            start_y, end_y = intersect_ext.yMinimum(), intersect_ext.yMaximum()
        else:
            start_x, end_x = ext.xMinimum(), ext.xMaximum()
            start_y, end_y = ext.yMinimum(), ext.yMaximum()

        ds = gdal.Open(raster.source())
        if not ds: raise QgsProcessingException("Gagal membaca raster dengan GDAL.")
        gt = ds.GetGeoTransform()
        inv_gt = gdal.InvGeoTransform(gt)
        
        def geo_to_pixel(x, y):
            return int(inv_gt[0] + x * inv_gt[1] + y * inv_gt[2]), int(inv_gt[3] + x * inv_gt[4] + y * inv_gt[5])
            
        def pixel_to_geo(px, py):
            return gt[0] + px * gt[1] + py * gt[2], gt[3] + px * gt[4] + py * gt[5]

        p_xmin, p_ymax = geo_to_pixel(start_x, start_y)
        p_xmax, p_ymin = geo_to_pixel(end_x, end_y)
        p_start_col = max(0, min(p_xmin, p_xmax))
        p_end_col = min(ds.RasterXSize, max(p_xmin, p_xmax))
        p_start_row = max(0, min(p_ymin, p_ymax))
        p_end_row = min(ds.RasterYSize, max(p_ymin, p_ymax))
        
        steps = tile_size - int(tile_size * (overlap / 100.0))
        all_pts = []
        
        total_cols = p_end_col - p_start_col
        total_rows = p_end_row - p_start_row
        total_tiles = math.ceil(total_cols / steps) * math.ceil(total_rows / steps)
        tile_count = 0
        start_time = time.time()

        if is_onnx:
            import onnxruntime as ort
            import cv2
            model_file = self.parameterAsFile(parameters, self.P_MODEL_FILE, context)
            if not model_file or not os.path.exists(model_file):
                raise QgsProcessingException(f"File model tidak valid: {model_file}")
            
            engine_idx = self.parameterAsEnum(parameters, self.P_ENGINE, context)
            conf_thresh = self.parameterAsDouble(parameters, self.P_CONF_THRESHOLD, context)
            iou_thresh = self.parameterAsDouble(parameters, self.P_IOU_THRESHOLD, context)
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if engine_idx == 0 else ['CPUExecutionProvider']
            try:
                session = ort.InferenceSession(model_file, providers=providers)
                input_name = session.get_inputs()[0].name
                tgt_h = session.get_inputs()[0].shape[2] if isinstance(session.get_inputs()[0].shape[2], int) else tile_size
                tgt_w = session.get_inputs()[0].shape[3] if isinstance(session.get_inputs()[0].shape[3], int) else tile_size
            except Exception as e:
                raise QgsProcessingException(f"Gagal memuat model ONNX: {str(e)}")
                
            feedback.pushInfo(f"Memulai Scanning ONNX AI (Tile: {tile_size}px) - Total ~{total_tiles} Tiles")
            
            for y in range(p_start_row, p_end_row, steps):
                if feedback.isCanceled(): break
                for x in range(p_start_col, p_end_col, steps):
                    if feedback.isCanceled(): break
                    tile_count += 1
                    feedback.setProgress((tile_count / total_tiles) * 80)
                    
                    w_t, h_t = min(tile_size, p_end_col - x), min(tile_size, p_end_row - y)
                    if w_t < 50 or h_t < 50: continue
                    
                    gx_min, gy_max = pixel_to_geo(x, y)
                    gx_max, gy_min = pixel_to_geo(x+w_t, y+h_t)
                    
                    if aoi_geom and strict_aoi:
                        if not aoi_geom.intersects(QgsGeometry.fromRect(QgsRectangle(gx_min, gy_min, gx_max, gy_max))):
                            continue
                            
                    img_arr = ds.ReadAsArray(x, y, w_t, h_t)
                    if img_arr is None: continue
                    
                    if img_arr.shape[0] > 3: img_arr = img_arr[:3, :, :]
                    elif img_arr.shape[0] < 3: continue
                    img_arr = np.transpose(img_arr, (1, 2, 0))
                    
                    orig_h, orig_w = img_arr.shape[:2]
                    blob = cv2.resize(img_arr, (tgt_w, tgt_h))
                    blob = blob.astype(np.float32) / 255.0
                    blob = blob.transpose(2, 0, 1)
                    blob = np.expand_dims(blob, axis=0)
                    
                    outputs = session.run(None, {input_name: blob})
                    preds = outputs[0][0]
                    
                    tile_boxes = []
                    for i in range(preds.shape[1]):
                        row = preds[:, i]
                        box, scores = row[:4], row[4:]
                        class_id = np.argmax(scores)
                        prob = scores[class_id]
                        if prob >= conf_thresh:
                            xc, yc, bw, bh = box
                            x1 = (xc - bw/2) * (orig_w / tgt_w)
                            y1 = (yc - bh/2) * (orig_h / tgt_h)
                            x2 = (xc + bw/2) * (orig_w / tgt_w)
                            y2 = (yc + bh/2) * (orig_h / tgt_h)
                            w_real = x2 - x1
                            h_real = y2 - y1
                            if min_size <= w_real <= max_size and min_size <= h_real <= max_size:
                                tile_boxes.append({'bbox': [x1, y1, x2, y2], 'confidence': float(prob), 'class': int(class_id)})
                    
                    tile_boxes = self.non_max_suppression(tile_boxes, iou_thresh)
                    for det in tile_boxes:
                        bx1, by1, bx2, by2 = det['bbox']
                        c_x, c_y = x + (bx1 + bx2)/2, y + (by1 + by2)/2
                        g_x, g_y = pixel_to_geo(c_x, c_y)
                        if strict_aoi and aoi_geom:
                            if not aoi_geom.contains(QgsPointXY(g_x, g_y)): continue
                        all_pts.append({'x': g_x, 'y': g_y, 'confidence': det['confidence'], 'class': det['class']})

        else: # ExG Hybrid Profile
            import scipy.ndimage
            exg_thresh = self.parameterAsInt(parameters, self.P_EXG_THRESH, context)
            blur_filter = self.parameterAsBool(parameters, self.P_BLUR_FILTER, context)
            
            sigma_px = 75 if profile_idx == 1 else 20
            min_smooth = 10 if profile_idx == 1 else 30
            min_density = 0.6 if profile_idx == 1 else 0.0
            extra_scales = [] if profile_idx == 1 else [12]
            refine_radius = sigma_px if profile_idx == 1 else 20
            
            # GSD approx
            gsd_m = abs(gt[1])
            scale = 0.05 / gsd_m if gsd_m > 0 else 1.0
            sigma_px = max(1, int(round(sigma_px * scale)))
            extra_scales = [max(1, int(round(s * scale))) for s in extra_scales]
            if refine_radius is not None:
                refine_radius = max(1, int(round(refine_radius * scale)))
            
            scales = sorted(set([sigma_px] + extra_scales), reverse=True)
            fp_by_scale = {s: np.ones((s*2+1, s*2+1), dtype=bool) for s in scales}
            
            feedback.pushInfo(f"Memulai Scanning ExG (Tile: {tile_size}px) - Total ~{total_tiles} Tiles")
            
            for y in range(p_start_row, p_end_row, steps):
                if feedback.isCanceled(): break
                for x in range(p_start_col, p_end_col, steps):
                    if feedback.isCanceled(): break
                    tile_count += 1
                    feedback.setProgress((tile_count / total_tiles) * 80)
                    
                    w_t, h_t = min(tile_size, p_end_col - x), min(tile_size, p_end_row - y)
                    if w_t < 50 or h_t < 50: continue
                    
                    gx_min, gy_max = pixel_to_geo(x, y)
                    gx_max, gy_min = pixel_to_geo(x+w_t, y+h_t)
                    if aoi_geom and strict_aoi:
                        if not aoi_geom.intersects(QgsGeometry.fromRect(QgsRectangle(gx_min, gy_min, gx_max, gy_max))):
                            continue
                            
                    img_arr = ds.ReadAsArray(x, y, w_t, h_t)
                    if img_arr is None or img_arr.shape[0] < 3: continue
                    R = img_arr[0].astype(np.int16)
                    G = img_arr[1].astype(np.int16)
                    B = img_arr[2].astype(np.int16)
                    
                    exg = 2.0 * G - R - B
                    valid = (R != 0) | (G != 0) | (B != 0)
                    veg_mask = (valid & (exg > exg_thresh)).astype(np.float32)
                    
                    sharp = None
                    if blur_filter:
                        gray = (R+G+B)/3.0
                        lap = scipy.ndimage.laplace(gray)
                        bw = max(5, int(round(25 * scale)))
                        mean = scipy.ndimage.uniform_filter(lap, size=bw)
                        sq_mean = scipy.ndimage.uniform_filter(lap * lap, size=bw)
                        var = sq_mean - mean**2
                        sharp = var > 20.0
                        
                    for s in scales:
                        margin = max(15, s//4)
                        dist_edge = scipy.ndimage.distance_transform_edt(valid)
                        valid_core = dist_edge > margin
                        valid_core[:margin,:] = False; valid_core[-margin:,:] = False
                        valid_core[:,:margin] = False; valid_core[:,-margin:] = False
                        if sharp is not None: valid_core = valid_core & sharp
                        
                        signal = scipy.ndimage.gaussian_filter(np.where(veg_mask>0, exg, 0.0), sigma=s)
                        density = scipy.ndimage.uniform_filter(veg_mask, size=int(s*3))
                        density_ok = density > min_density
                        
                        lmax = (signal == scipy.ndimage.maximum_filter(signal, footprint=fp_by_scale[s])) & valid_core & (signal > min_smooth) & density_ok
                        
                        labeled, num = scipy.ndimage.label(lmax)
                        if num == 0: continue
                        for py_l, px_l in scipy.ndimage.center_of_mass(lmax, labeled, range(1, num+1)):
                            py_i, px_i = int(py_l), int(px_l)
                            px_i, py_i = self.refine_centroid(veg_mask, exg, px_i, py_i, refine_radius)
                            
                            c_x, c_y = x + px_i, y + py_i
                            g_x, g_y = pixel_to_geo(c_x, c_y)
                            if strict_aoi and aoi_geom:
                                if not aoi_geom.contains(QgsPointXY(g_x, g_y)): continue
                            all_pts.append({'x': g_x, 'y': g_y, 'confidence': float(s), 'class': 0})

        feedback.setProgress(85)
        feedback.pushInfo(f"Ditemukan {len(all_pts)} kandidat pohon awal. Memproses deduplikasi (Jarak: {cluster_dist}m)...")
        final_pts = self.deduplicate_points(all_pts, cluster_dist, feedback)
        
        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))
        fields.append(QgsField("confidence", QVariant.Double))
        fields.append(QgsField("class_id", QVariant.Int))
        fields.append(QgsField("X", QVariant.Double))
        fields.append(QgsField("Y", QVariant.Double))
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.P_OUTPUT, context, fields, QgsWkbTypes.Point, crs)
        
        for idx, pt in enumerate(final_pts):
            f = QgsFeature(fields)
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(pt['x'], pt['y'])))
            f.setAttributes([idx + 1, pt['confidence'], pt['class'], pt['x'], pt['y']])
            sink.addFeature(f)
            
        elapsed = time.time() - start_time
        feedback.pushInfo(f"Selesai! {len(final_pts)} pohon terdeteksi. Waktu: {elapsed:.2f} detik.")
        return {self.P_OUTPUT: dest_id}
