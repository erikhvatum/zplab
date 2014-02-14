# Copyright 2014 WUSTL ZPLAB

import ctypes as ct
import numpy as np
import os
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from acquisition.andor.andor import (Andor, Zyla)
from acquisition.andor.andor_exception import AndorException

class AndorManipMainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent, andorInstance):
        super().__init__(parent)
        self.andorInstance = andorInstance
        self.zylaInstance = None

        self.ui = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'direct_manip.ui'))[0]()
        self.ui.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.graphicsScene = QtWidgets.QGraphicsScene(self)
        self.graphicsScene.setSceneRect(QtCore.QRectF(0, 0, 1000, 1000))
        self.ui.graphicsView.setScene(self.graphicsScene)
        self.imageItem = None

        self.enableWhenConnected = [
            self.ui.testButton,
            self.ui.exposureTimeLabel,
            self.ui.exposureTimeSpinBox,
            self.ui.acquireButton ]
        self.disableWhenConnected = [
            self.ui.andorDeviceListCombo,
            self.ui.refreshAndorDeviceListButton ]

    def closeEvent(self, event):
        super().closeEvent(event)

    def openImageClicked(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self)
        if fileName is not None and fileName != '':
            impx = QtGui.QPixmap(fileName)
            if impx.isNull():
                QtWidgets.QMessageBox.critical(self, 'Failed to Load Image', 'Failed to load an image from "{}".'.format(fileName))
            else:
                self._usePixmap(impx)

    def saveImageClicked(self):
        pass

    def _usePixmap(self, pixmap):
        if self.imageItem is not None:
            self.graphicsScene.removeItem(self.imageItem)
            self.imageItem = None
        self.imageItem = self.graphicsScene.addPixmap(pixmap)
        self.graphicsScene.setSceneRect(QtCore.QRectF(0, 0, pixmap.width(), pixmap.height()))

    def refreshAndorDeviceListButtonClicked(self):
        deviceNames = self.andorInstance.getDeviceNames()
        # Clear existing contents
        while self.ui.andorDeviceListCombo.count() > 0:
            self.ui.andorDeviceListCombo.removeItem(self.ui.andorDeviceListCombo.count() - 1)

        if deviceNames is None or len(deviceNames) == 0:
            self.ui.andorDeviceListCombo.setEnabled(False)
            self.ui.connectDisconnectAndorDeviceButton.setEnabled(False)
        else:
            # Populate
            deviceIndex = 0
            for deviceName in deviceNames:
                self.ui.andorDeviceListCombo.addItem('{}: {}'.format(deviceIndex, deviceName))
                deviceIndex += 1
            self.ui.andorDeviceListCombo.setEnabled(True)
            self.ui.connectDisconnectAndorDeviceButton.setEnabled(True)

    def connectDisconnectAndorDeviceButtonClicked(self):
        if self.zylaInstance is None:
            # Connect...
            self.zylaInstance = Zyla(self.andorInstance, self.ui.andorDeviceListCombo.currentIndex())
            for widget in self.enableWhenConnected:
                widget.setEnabled(True)
            for widget in self.disableWhenConnected:
                widget.setEnabled(False)
            self.ui.connectDisconnectAndorDeviceButton.setText('Disconnect')
        else:
            # Disconnect...
            self.zylaInstance = None
            for widget in self.enableWhenConnected:
                widget.setEnabled(False)
            for widget in self.disableWhenConnected:
                widget.setEnabled(True)
            self.ui.connectDisconnectAndorDeviceButton.setText('Connect')

    def testButtonClicked(self):
        QtWidgets.QMessageBox.information(self, 'Test Result', self.zylaInstance.getPixelEncoding())

    def acquireButtonClicked(self):
        im16g = self.zylaInstance.acquireImage(self.ui.exposureTimeSpinBox.value())
        shape = im16g.shape

        # Normalize and convert to 8-bit grayscale
        im16gf = im16g.astype(np.float32)
        del im16g
        im16gf -= im16gf.min()
        im16gf *= 0xff / im16gf.max()
        im32argb = im16gf.astype(np.uint8)
        del im16gf

        # Convert to 32-bit color with ignored junk data in alpha channel
        im32argb = np.repeat(im32argb, 4, axis=1)

        # Display
        imq = QtGui.QImage(im32argb.data, shape[1], shape[0], QtGui.QImage.Format_RGB32)
        impx = QtGui.QPixmap.fromImage(imq)
        # It should not be necessary to call detach here, but if this is not done, impx will continue
        # to reference im32argb through imq - without increasing the reference count of either.  According
        # to the Qt docs, QPixmap.fromImage copies the QImage's data, but this does not seem to actually
        # be the case.  Perhaps Qt is too clever for its own good and inserts im32argb into the pixmap cache;
        # calling detach forces QPixmap to copy its data out of the pixmap cache and thus works around the
        # issue.
        impx.detach()
        del imq
        del im32argb
        self._usePixmap(impx)
        del impx

def show(launcherDescription=None, moduleArgs=None, andorInstance=None):
    import sys
    app = QtWidgets.QApplication(sys.argv)
    if andorInstance is None:
        andorInstance = Andor()
    mainWindow = AndorManipMainWindow(None, andorInstance)
    mainWindow.show()
    sys.exit(app.exec_())