# -*- coding: utf-8 -*-

import os
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import QgsApplication
from .license_guard import LicenseDashboardDialog, CURRENT_VERSION
from .plantation_provider import PlantationProvider

class PlantationToolsPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.action = None
        self.menu_name = "Plantation Tools"

    def initGui(self):
        # 1. Initialize Processing Provider
        self.provider = PlantationProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

        # 2. Add action to Plugins menu and Toolbar
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            # Fallback icon from QGIS system
            icon = QIcon()

        self.action = QAction(
            icon,
            "Cek Status Lisensi",
            self.iface.mainWindow()
        )
        self.action.triggered.connect(self.run)

        # Create About action
        from qgis.PyQt.QtWidgets import QMessageBox
        self.about_action = QAction(
            icon,
            "Tentang (About)",
            self.iface.mainWindow()
        )
        self.about_action.triggered.connect(self.show_about)

        # Add to Menu
        self.iface.addPluginToMenu(self.menu_name, self.action)
        self.iface.addPluginToMenu(self.menu_name, self.about_action)
        
        # Add to Toolbar
        self.iface.addToolBarIcon(self.action)
        
        # Set icon for the parent 'Plantation Tools' menu
        for act in self.iface.pluginMenu().actions():
            if act.text() == self.menu_name:
                act.setIcon(icon)
                break

    def show_about(self):
        from qgis.PyQt.QtWidgets import QMessageBox
        QMessageBox.information(
            self.iface.mainWindow(),
            "Tentang Plantation Tools",
            f"Plantation Tools v{CURRENT_VERSION}\n\n"
            "Alat Analisis Spasial Profesional untuk Perkebunan Kelapa Sawit.\n\n"
            "Hak Cipta © 2026 Ahza Studio\n"
            "Dikembangkan oleh: Ardi Abu Ridho\n\n"
            "Mendukung analisis jalan, drainase, hidrologi, pemetaan jarak tanam,\n"
            "deteksi AI, dan perencanaan logistik panen."
        )

    def unload(self):
        # 1. Remove menu action and toolbar icon
        if self.action:
            self.iface.removePluginMenu(self.menu_name, self.action)
            self.iface.removeToolBarIcon(self.action)
        if hasattr(self, 'about_action') and self.about_action:
            self.iface.removePluginMenu(self.menu_name, self.about_action)

        # 2. Unregister Processing Provider
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)

    def run(self, *args):
        # Open the license dialog
        dialog = LicenseDashboardDialog(self.iface.mainWindow())
        dialog.exec()
