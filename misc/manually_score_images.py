# The MIT License (MIT)
#
# Copyright (c) 2014 WUSTL ZPLAB
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Authors: Erik Hvatum

import enum
import numpy
import os
import skimage.io as skio
from pathlib import Path
from PyQt5 import Qt, uic

class ScoreableImage:
    def __init__(self, fileName, score=None):
        self.fileName = fileName
        self.score = score
    def __repr__(self):
        return 'ScoreableImage({}, {})'.format(self.fileName, self.score)

class ManualScorer(Qt.QDialog):
    class _ScoreRadioId(enum.IntEnum):
        ClearScore = 1
        SetScore0 = 2
        SetScore1 = 3
        SetScore2 = 4

    _radioIdToScore = {_ScoreRadioId.ClearScore : None,
                       _ScoreRadioId.SetScore0 : 0,
                       _ScoreRadioId.SetScore1 : 1,
                       _ScoreRadioId.SetScore2 : 2}

    def __init__(self, risWidget, dict_, parent):
        super().__init__(parent)

        self._rw = risWidget
        self._db = dict_

        self._ui = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'manually_score_images.ui'))[0]()
        self._ui.setupUi(self)

        self._scoreRadioGroup = Qt.QButtonGroup(self)
        self._scoreRadioGroup.addButton(self._ui.radioNone, self._ScoreRadioId.ClearScore)
        self._scoreRadioGroup.addButton(self._ui.radio0, self._ScoreRadioId.SetScore0)
        self._scoreRadioGroup.addButton(self._ui.radio1, self._ScoreRadioId.SetScore1)
        self._scoreRadioGroup.addButton(self._ui.radio2, self._ScoreRadioId.SetScore2)

        self._ui.actionUp.triggered.connect(self._ui.prevGroupButton.animateClick)
        self._ui.actionDown.triggered.connect(self._ui.nextGroupButton.animateClick)
        self._ui.actionLeft.triggered.connect(self._ui.prevButton.animateClick)
        self._ui.actionRight.triggered.connect(self._ui.nextButton.animateClick)
        self._ui.actionBackspace.triggered.connect(self._ui.radioNone.animateClick)
        self._ui.action0.triggered.connect(self._ui.radio0.animateClick)
        self._ui.action1.triggered.connect(self._ui.radio1.animateClick)
        self._ui.action2.triggered.connect(self._ui.radio2.animateClick)

        self.addActions([self._ui.actionUp,
                         self._ui.actionDown,
                         self._ui.actionLeft,
                         self._ui.actionRight,
                         self._ui.actionBackspace,
                         self._ui.action0,
                         self._ui.action1,
                         self._ui.action2])


#class ManualImageScorer(ManualScorer):
#    def __init__(self, imageDbFileName, modifyDbIfExists=True, imageFileNames=None, subtractPrefix=None, parent=None):
#        super().__init__(imageDbFileName, modifyDbIfExists, parent)
#
#        self.removeAction(self._ui.actionUp)
#        self.removeAction(self._ui.actionDown)
#        self._ui.actionUp.deleteLater()
#        self._ui.actionDown.deleteLater()
#        del self._ui.actionUp
#        del self._ui.actionDown
#
#        self._ui.prevGroupButton.deleteLater()
#        self._ui.nextGroupButton.deleteLater()
#        del self._ui.prevGroupButton
#        del self._ui.nextGroupButton

class ManualImageGroupScorer(ManualScorer):
    '''groupDict format: {'group name' : [ScoreableImage, ScoreableImage, ...]}'''
    _GroupIndexRole = 42
    _FileIndexRole = 43
    _RowIndexRole = 44
    _Forward = 0
    _Backward = 1

    def __init__(self, risWidget, groupDict, parent=None):
        super().__init__(risWidget, groupDict, parent)

        imageCount = sum((len(images) for images in self._db.values()))
        self._ui.tableWidget.setRowCount(imageCount)
        self._ui.tableWidget.setHorizontalHeaderLabels(['Group', 'File name', 'Rating'])

        rowIndex = 0
        self._groupNames = sorted(list(self._db.keys()))
        for groupIndex, groupName in enumerate(self._groupNames):
            images = self._db[groupName]
            for imageIndex, image in enumerate(images):
                groupItem = Qt.QTableWidgetItem(groupName)
                groupItem.setData(self._GroupIndexRole, Qt.QVariant(groupIndex))
                groupItem.setData(self._FileIndexRole, Qt.QVariant(imageIndex))
                groupItem.setData(self._RowIndexRole, Qt.QVariant(rowIndex))
                self._ui.tableWidget.setItem(rowIndex, 0, groupItem)
                self._ui.tableWidget.setItem(rowIndex, 1, Qt.QTableWidgetItem(str(image.fileName)))
                self._ui.tableWidget.setItem(rowIndex, 2, Qt.QTableWidgetItem('None' if image.score is None else str(image.score)))
                rowIndex += 1

        self._curGroupName = None
        self._curGroupIndex = None
        self._curGroupImages = None
        self._curImage = None
        self._curImageIndex = None
        self._curRowIndex = None

        self._inRefreshScoreButtons = False

        self._ui.tableWidget.currentItemChanged.connect(self._listWidgetSelectionChange)
        self._scoreRadioGroup.buttonClicked[int].connect(self._scoreButtonClicked)
        self._ui.prevGroupButton.clicked.connect(lambda: self._stepGroup(self._Backward))
        self._ui.nextGroupButton.clicked.connect(lambda: self._stepGroup(self._Forward))
        self._ui.prevButton.clicked.connect(lambda: self._stepImage(self._Backward))
        self._ui.nextButton.clicked.connect(lambda: self._stepImage(self._Forward))

        self._ui.tableWidget.setCurrentItem(self._ui.tableWidget.item(0, 0))

    def _listWidgetSelectionChange(self, curItem, prevItem):
        groupItem = self._ui.tableWidget.item(curItem.row(), 0)
        self._curGroupIndex = groupItem.data(self._GroupIndexRole)
        self._curGroupName = groupItem.text()
        self._curGroupImages = self._db[self._curGroupName]
        self._curImageIndex = groupItem.data(self._FileIndexRole)
        self._curImage = self._curGroupImages[self._curImageIndex]
        self._curRowIndex = groupItem.data(self._RowIndexRole)
        self._refreshScoreButtons()
        image = skio.imread(str(self._curImage.fileName))
        if image.dtype == numpy.float32:
            image = (image * 65535).astype(numpy.uint16)
        self._rw.showImage(image)

    def _refreshScoreButtons(self):
        self._inRefreshScoreButtons = True
        score = self._curImage.score
        if score is None:
            self._ui.radioNone.click()
        elif score is 0:
            self._ui.radio0.click()
        elif score is 1:
            self._ui.radio1.click()
        elif score is 2:
            self._ui.radio2.click()
        else:
            self._inRefreshScoreButtons = False
            raise RuntimeError('Bad value for image score.')
        self._inRefreshScoreButtons = False

    def _scoreButtonClicked(self, radioId):
        if not self._inRefreshScoreButtons:
            self._setScore(self._radioIdToScore[radioId])
            self._ui.nextButton.animateClick()

    def _setScore(self, score):
        '''Set current image score.'''
        if score != self._curImage.score:
            self._curImage.score = score
            self._ui.tableWidget.item(self._curRowIndex, 2).setText('None' if score is None else str(score))

    def _stepImage(self, direction):
        newRow = None
        if direction == self._Forward:
            if self._curRowIndex + 1 < self._ui.tableWidget.rowCount():
                newRow = self._curRowIndex + 1
        elif direction == self._Backward:
            if self._curRowIndex > 0:
                newRow = self._curRowIndex - 1
        
        if newRow is not None:
            self._ui.tableWidget.setCurrentItem(self._ui.tableWidget.item(newRow, 0))

    def _stepGroup(self, direction):
        newRow = None
        if direction == self._Forward:
            if self._curGroupIndex + 1 < len(self._db):
                newRow = self._curRowIndex + len(self._curGroupImages) - self._curImageIndex
        elif direction == self._Backward:
            if self._curGroupIndex > 0:
                newGroup = self._curGroupIndex - 1
                newRow = self._curRowIndex - len(self._curGroupImages) + self._curImageIndex - 1

        if newRow is not None:
            self._ui.tableWidget.setCurrentItem(self._ui.tableWidget.item(newRow, 0))

def makeWeekendImagesScorer(risWidget, basePath):
    import re
    groups = {}
    basePath = Path(basePath)

    for well in basePath.glob('*'):
        if well.is_dir():
            wellIdx = well.name
            match = re.search('^(\d\d)', wellIdx)
            if match is not None:
                wellIdx = match.group(1)
                for mag in well.glob('*'):
                    magName = mag.name
                    if mag.is_dir() and magName in ['5x', '10x']:
                        for run in mag.glob('*'):
                            runNum = run.name
                            if run.is_dir() and re.match('\d+', runNum):
                                runNum = int(runNum)
                                images = [ScoreableImage(imageFile) for imageFile in run.glob('*.png')]
                                group = '{}/{}/{:02}'.format(wellIdx, magName, runNum)
                                groups[group] = images

    migs = ManualImageGroupScorer(risWidget, groups)
    migs.show()
    return groups, migs
