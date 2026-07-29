# -*- coding: utf-8 -*-

import os
import json
import urllib.request
import urllib.error
import ssl
import zipfile
import shutil
import tempfile
import stat
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsMessageLog,
    Qgis
)

class UpdatePlugin(QgsProcessingAlgorithm):
    """
    Auto-Updater for Plantation Tools QGIS Plugin
    """
    
    # Kredensial Supabase Otomatis
    SUPABASE_URL = "https://mbfzmvlivyuajmxrecne.supabase.co" 
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1iZnptdmxpdnl1YWpteHJlY25lIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU0NzgwODQsImV4cCI6MjA4MTA1NDA4NH0.sZltNY30ww2Hb_oopiVDcvXnZRehWRvK2jZZU5MO64s"  # pragma: allowlist secret
    CURRENT_VERSION = "2.1.4" # Ganti ini saat merilis versi baru

    def initAlgorithm(self, config=None):
        pass

    def processAlgorithm(self, parameters, context, feedback):
        feedback.pushInfo("=" * 60)
        feedback.pushInfo("Pengecekan Pembaruan QGIS Plugin (Auto-Updater)")
        feedback.pushInfo("=" * 60)
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        latest_version = self.CURRENT_VERSION
        download_url = ""
        
        try:
            feedback.pushInfo("Menghubungi server Supabase...")
            req_ver = urllib.request.Request(
                f"{self.SUPABASE_URL}/rest/v1/system_config?key=eq.qgis_toolbox_version",
                headers={"apikey": self.SUPABASE_KEY, "Authorization": f"Bearer {self.SUPABASE_KEY}"}
            )
            with urllib.request.urlopen(req_ver, context=ctx, timeout=10) as response:  # nosec
                data = json.loads(response.read().decode())
                if data: latest_version = data[0]['value']
                
            req_url = urllib.request.Request(
                f"{self.SUPABASE_URL}/rest/v1/system_config?key=eq.qgis_toolbox_download_url",
                headers={"apikey": self.SUPABASE_KEY, "Authorization": f"Bearer {self.SUPABASE_KEY}"}
            )
            with urllib.request.urlopen(req_url, context=ctx, timeout=10) as response:  # nosec
                data = json.loads(response.read().decode())
                if data: download_url = data[0]['value']
                
        except Exception as e:
            feedback.reportError(f"Gagal menghubungi server: {str(e)}")
            return {}
            
        feedback.pushInfo(f"Versi Anda saat ini : {self.CURRENT_VERSION}")
        feedback.pushInfo(f"Versi Terbaru       : {latest_version}")
        
        if latest_version == self.CURRENT_VERSION:
            feedback.pushInfo("Plugin QGIS Anda sudah dalam versi terbaru!")
            return {}
            
        feedback.pushInfo("Versi baru tersedia! Memulai proses pengunduhan...")
        if not download_url:
            feedback.reportError("URL unduhan tidak ditemukan di database.")
            return {}
            
        try:
            # Tentukan direktori plugin saat ini
            current_plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Download file ZIP ke file temporer
            temp_dir = tempfile.gettempdir()
            new_zip_temp = os.path.join(temp_dir, f"PlantationTools_QGIS_v{latest_version}.zip")
            extract_temp = os.path.join(temp_dir, f"qgis_plugin_extracted_v{latest_version}")
            
            req_dl = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_dl, context=ctx, timeout=60) as response, open(new_zip_temp, 'wb') as out_file:  # nosec
                shutil.copyfileobj(response, out_file)
                
            feedback.pushInfo("Unduhan selesai. Mengekstrak file ZIP...")
            
            # Ekstrak ZIP
            if os.path.exists(extract_temp):
                shutil.rmtree(extract_temp, ignore_errors=True)
            os.makedirs(extract_temp, exist_ok=True)
            
            with zipfile.ZipFile(new_zip_temp, 'r') as zip_ref:
                zip_ref.extractall(extract_temp)
                
            # Biasanya ZIP Github release memiliki 1 root folder, kita perlu temukan folder plugin aslinya
            extracted_items = os.listdir(extract_temp)
            source_dir = extract_temp
            if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_temp, extracted_items[0])):
                source_dir = os.path.join(extract_temp, extracted_items[0])
                
            feedback.pushInfo("Mengganti file plugin lama...")
            
            # Timpa file lama secara rekursif
            def copy_tree_overwrite(src, dst):
                for src_dir, dirs, files in os.walk(src):
                    dst_dir = src_dir.replace(src, dst, 1)
                    if not os.path.exists(dst_dir):
                        os.makedirs(dst_dir)
                    for file_ in files:
                        src_file = os.path.join(src_dir, file_)
                        dst_file = os.path.join(dst_dir, file_)
                        if os.path.exists(dst_file):
                            try:
                                os.chmod(dst_file, stat.S_IWRITE)
                                os.remove(dst_file)
                            except: pass
                        shutil.copy2(src_file, dst_dir)
                        
            copy_tree_overwrite(source_dir, current_plugin_dir)
            
            # Bersihkan temp
            try:
                shutil.rmtree(extract_temp, ignore_errors=True)
                os.remove(new_zip_temp)
            except: pass
            
            feedback.pushInfo("UPDATE BERHASIL!")
            feedback.pushInfo(f"Plugin telah diupdate ke versi {latest_version}.")
            feedback.pushInfo("=== SILAKAN RESTART QGIS ANDA UNTUK MENERAPKAN PERUBAHAN ===")
            
            # Memunculkan notifikasi UI
            QgsMessageLog.logMessage("Update Plantation Tools berhasil. Silakan Restart QGIS.", "Plantation Tools", Qgis.Success)
            
        except Exception as e:
            feedback.reportError(f"Gagal melakukan update otomatis: {str(e)}")
            feedback.reportError("Silakan download manual dari: " + download_url)

        return {}

    def name(self):
        return 'update_plugin'

    def displayName(self):
        return '00b. Update QGIS Plugin'

    def group(self):
        return '00. System & Licensing'

    def groupId(self):
        return 'system'

    def shortHelpString(self):
        return 'Periksa dan unduh versi terbaru dari Plantation Tools QGIS Plugin via GitHub & Supabase.'

    def createInstance(self):
        return UpdatePlugin()
