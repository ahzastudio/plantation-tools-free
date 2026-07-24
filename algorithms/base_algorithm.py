# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingException
)
from ..license_guard import SupabaseGuard, LicenseDashboardDialog

IS_FREE_VERSION = True

class BasePlantationAlgorithm(QgsProcessingAlgorithm):
    """
    Base class for all Plantation Tools QGIS processing algorithms.
    Ensures license gating is checked before running.
    """
    
    def get_minimum_tier(self):
        """
        Return the minimum required tier.
        To be overridden by subclasses. Values: 'free', 'basic', 'pro', 'pro+'.
        """
        return "basic"

    def check_license_gate(self):
        """
        Validates current machine license against required tier.
        Raises QgsProcessingException if access is denied.
        """
        if IS_FREE_VERSION and self.get_minimum_tier() != 'free':
            raise QgsProcessingException("FITUR PRO: Ini adalah versi Community/Free Edition. Silakan hubungi Admin via WhatsApp untuk aktivasi.")

        is_valid, msg, info = SupabaseGuard.check_license("plantation_tools_qgis", self.get_minimum_tier())
        if not is_valid:
            # Display detailed licensing error inside QGIS processing console
            raise QgsProcessingException(msg)
        return info

    def checkParameterValues(self, parameters, context):
        """
        Called when the algorithm dialog opens and when parameters change.
        We use this to show a popup and block execution if unlicensed.
        """
        if not hasattr(self, '_license_checked'):
            if IS_FREE_VERSION and self.get_minimum_tier() != 'free':
                self._license_valid = False
                self._license_msg = "FITUR PRO: Ini adalah versi Community/Free Edition. Silakan unduh versi PRO atau hubungi Admin via WhatsApp (+62 822-5476-0769) untuk aktivasi."
                self._license_info = None
            else:
                self._license_valid, self._license_msg, self._license_info = SupabaseGuard.check_license("plantation_tools_qgis", self.get_minimum_tier())
            
            self._license_checked = True
            
            if not self._license_valid:
                # Show popup exactly once when dialog opens
                try:
                    import qgis.utils
                    parent = qgis.utils.iface.mainWindow() if qgis.utils.iface else None
                    dlg = LicenseDashboardDialog(parent, error_msg=self._license_msg)
                    if hasattr(dlg, 'exec'):
                        dlg.exec()
                    else:
                        dlg.exec_()
                except Exception as e:
                    from qgis.core import QgsMessageLog, Qgis
                    QgsMessageLog.logMessage("Error popup License Dashboard: " + str(e), "PlantationTools", Qgis.Warning)
        
        if not self._license_valid:
            return False, self._license_msg
            
        return super(BasePlantationAlgorithm, self).checkParameterValues(parameters, context)
