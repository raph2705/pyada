#!/usr/bin/env python3

'''
 PyADA -- Simple program to retrieve Cardano staking rewards
 
  This file is part of PyADA.
 
  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
 
 Copyright (c) 2021  Raphaël Bazaud <rbazaud@pm.me>
'''

import json
import platform
import requests as rq
import socket
import signal
import sys

# PyQT imports for GUI
from PyQt5 import QtGui, QtWidgets
from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5.QtCore import Qt, QObject, pyqtSlot, QRunnable, QThreadPool, QT_VERSION_STR
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QDialogButtonBox, \
                            QFormLayout, QGroupBox, QHBoxLayout, QLabel, \
                            QLineEdit, QMainWindow, QMessageBox, \
                            QPushButton, QTextEdit, QVBoxLayout, QWidget

# a few string constants
PROJECT_ID = u'q5NT3BzY2P73EzKfCprE1oprU6Nx1yq1'
CARDANO_BF_URL = u'https://cardano-mainnet.blockfrost.io/api/v0'
CARDANO_ASSETS_URL = u'https://cardano.org/brand-assets/'
DEV_EMAIL = u'rbazaud@pm.me'
ADA_SYMBOL = u'\u20b3'
__version__ = u'0.1-alpha'
PYADA_GITHUB_URL = u'https://github.com/raph2705/pyada'
PYADA_TITLE_BAR = u'PyADA - Cardano staking rewards'
PYADA_REWARDS_INFO = u'Cardano staking information'
PYADA_STAKE_KEY = u'Enter your stake key'
QUIT_MSG = u'Are you sure you want to exit the program ?'
BUTTON_ABOUT = 'About'

# Cardano logo from https://cardano.org/brand-assets/ and converted to XPM
# format using ImageMagick
cardano_ada_logo = [
#  /* XPM */
#  static char *cardano_ada_logo[] = {
#  /* columns rows colors chars-per-pixel */
"64 64 2 1 ",
"  c #0033AD",
". c None",
#  /* pixels */
"................................................................",
"................................................................",
"................................................................",
"..............................    ..............................",
"................ .............    ............  ................",
"...............   .............  .............   ...............",
"................  ............................  ................",
"................................................................",
"................................................................",
"................................................................",
".................... .....................  ....................",
"...................    ..................    ...................",
"...................    ........  ........    ...................",
"...................    .......    .......    ...................",
".................... ........     ......... ....................",
"..............................    ..............................",
"....... ......................    .....................  .......",
"......   .............................................    ......",
"......    ............................................    ......",
".......  ................    ......    ................  .......",
"........................      ....      ........................",
"...............    ....        ..        ....    ...............",
"...............    ....        ..        ....    ...............",
"..............     ....        ..        ....     ..............",
"...............    ....        ..        ....    ...............",
"................  .....        ..        .....  ................",
"........................      ....      ........................",
"................................................................",
"...................     ................     ...................",
"..................       ..............       ..................",
"........   .......        ............        .......   ........",
"   ....    .......        ............        .......    ....   ",
"   ....    .......        ............        .......    ....   ",
"........   .......        ............        .......   ........",
"..................       ..............       ..................",
"...................     ................     ...................",
"................................................................",
"........................      ....      ........................",
"................  .....        ..        .....  ................",
"...............    ....        ..        ....    ...............",
"..............     ....        ..        ....     ..............",
"...............    ....        ..        ....    ...............",
"...............    ....        ..        ....    ...............",
"........................      ....      ........................",
".......  ................    ......    ................  .......",
"......    ............................................    ......",
"......    .............................................   ......",
".......  .....................   ....................... .......",
"..............................    ..............................",
".................... ........     ......... ....................",
"...................    .......    .......    ...................",
"...................    ........  ........    ...................",
"...................    ..................    ...................",
"....................  ..................... ....................",
"................................................................",
"................................................................",
"................................................................",
"................  ............................  ................",
"...............   .............  .............   ...............",
"................  ............    ............. ................",
"..............................   ...............................",
"................................................................",
"................................................................",
"................................................................"
] # };


# Worker thread
class Worker(QRunnable):
    # :param args: callback method in PyADA
    def __init__(self, *args, **kwargs):
        super(Worker, self).__init__()
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        #  print(self.args, self.kwargs)
        if self.args[0] is not None:
            self.args[0]()


class PyADA(QMainWindow):

    def __init__(self, *args, **kwargs):

        super(PyADA, self).__init__(*args, **kwargs)

        # multithreading with a max of 12 threads
        self.threadpool = QThreadPool()
        #  print(f'Multithreading with maximum {self.threadpool.maxThreadCount()} threads')

        self.epoch = 0
        self.pool_name = ''
        self.pool_ticker = ''
        self.ctrl_amount = 0
        self.rew_sum = 0
        self.rewards = ''

        self.sk = QLineEdit()
        self.epochLE = QLineEdit()
        self.poolName = QLineEdit()
        self.poolTicker = QLineEdit()
        self.ctrlAmount = QLineEdit()
        self.rewardsSum = QLineEdit()
        self.rewardsDetails = QTextEdit()

        self.setup_ui()

    def create_stakekeygroupbox(self):

        skgb = QGroupBox(PYADA_STAKE_KEY)
        l = QHBoxLayout()
        self.sk.setMaxLength(59)
        self.sk.setAlignment(Qt.AlignRight)
        # call our very own custom slot on signal textChanged
        self.sk.textChanged.connect(self.update_data)
        font = QFont("Source Code Pro")
        # in case we do not have 'Source Code Pro', we still want Monospace
        font.setStyleHint(QFont.Monospace)
        self.sk.setFont(font)
        l.addWidget(self.sk)
        skgb.setLayout(l);
        return skgb

    def create_rewardinfogroupbox(self):

        # we do not need to change those text boxes
        self.epochLE.setReadOnly(True)
        self.poolName.setReadOnly(True)
        self.poolTicker.setReadOnly(True)
        self.ctrlAmount.setReadOnly(True)
        self.rewardsSum.setReadOnly(True)
        self.rewardsDetails.setReadOnly(True)

        rewardInfoGroupBox = QGroupBox(PYADA_REWARDS_INFO)
        l = QFormLayout()
        l.addRow(QLabel('Current epoch:'), self.epochLE)
        l.addRow(QLabel('Pool name:'), self.poolName)
        l.addRow(QLabel('Pool ticker:'), self.poolTicker)
        l.addRow(QLabel('Controlled amount:'), self.ctrlAmount)
        l.addRow(QLabel('Rewards sum:'), self.rewardsSum)
        l.addRow(QLabel('Rewards details:'), self.rewardsDetails)
        rewardInfoGroupBox.setLayout(l)
        return rewardInfoGroupBox

    def createButtonBox(self):
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Reset
                                               | QtWidgets.QDialogButtonBox.Close)
        btnAbout = QPushButton(BUTTON_ABOUT)
        buttonBox.addButton(btnAbout, QtWidgets.QDialogButtonBox.ActionRole)
        buttonBox.rejected.connect(self.close)
        btnAbout.clicked.connect(self.show_about)
        buttonBox.button(QtWidgets.QDialogButtonBox.Reset).clicked.connect(self.clearFields)
        return buttonBox

    def setup_ui(self):

        self.resize(640, 480)
        self.setWindowTitle(PYADA_TITLE_BAR)
        v = QVBoxLayout()
        v.addWidget(self.create_stakekeygroupbox())
        v.addWidget(self.create_rewardinfogroupbox())
        v.addWidget(self.createButtonBox())
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(v)
        widget = QWidget()
        widget.setLayout(mainLayout)
        self.setCentralWidget(widget)
        self.center()
        self.set_window_icon()

    def do_http_get(self, url_suffix):
        try:
            r = rq.get(CARDANO_BF_URL + url_suffix, headers = {'project_id': PROJECT_ID})
            if r.status_code != 200:
                r.raise_for_status()
        except rq.HTTPError as e:
            print(e)
        return r

    def fetch_data(self):

        r = self.do_http_get('/epochs/latest')
        self.epoch = r.json()['epoch']

        j = self.do_http_get('/accounts/{}'.format(self.stake_key)).json()
        self.pool_id = j['pool_id']
        self.ctrl_amount = int(j['controlled_amount']) / 1000000
        self.rew_sum = int(j['rewards_sum']) / 1000000

        j = self.do_http_get('/pools/{}/metadata'.format(self.pool_id)).json()
        self.pool_ticker = j['ticker']
        self.pool_name = j['name']

        j = self.do_http_get('/accounts/{}/rewards'.format(self.stake_key)).json()
        self.rewards = j

        # TBD: instead of updating UI syncronously and possibly block UI
        # refreshing (web data fetching is a typical I/O-bound processing), we
        # could use signal and slot mechanism which provides us with a mean to
        # stay asynchronous
        self.update_ui()

    def update_ui(self):

        if self.epoch:
            self.epochLE.setText(f'{self.epoch}')
        if self.pool_ticker:
            self.poolTicker.setText(f'{self.pool_ticker}')
        if self.pool_name:
            self.poolName.setText(f'{self.pool_name}')
        if self.ctrl_amount:
            self.ctrlAmount.setText(f'{self.ctrl_amount} {ADA_SYMBOL}')
            # no div by zero
            self.rewardsSum.setText(f'{self.rew_sum} {ADA_SYMBOL} ({self.rew_sum * 100 / self.ctrl_amount:.2f} %)')

        # iterate through JSON elements
        for element in self.rewards:
            epoch = 0
            reward = ''
            for key, val in element.items():
                if key == 'epoch':
                    epoch = val
                if key == 'amount':
                    reward = int(val) / 1000000
                if len(f'{epoch}') and len(f'{reward}'):
                    break
            # make sure we have something meaningful to display
            if epoch != 0 and reward:
                self.rewardsDetails.append(f'Epoch {epoch} => {reward} {ADA_SYMBOL}')

    def set_window_icon(self):
        
        icon = QIcon(QtGui.QPixmap(cardano_ada_logo))
        self.setWindowIcon(icon)

    def show_about(self):

        contributors = [
               'Tony (Elite Stake Pool)',
               'X'
               ]

        QMessageBox.about(self, PYADA_TITLE_BAR,
                f'''<b> About PyADA </b> (v{__version__})
                <br>
                <p>Copyright © 2021 Raphaël Bazaud.
                All rights reserved in accordance with
                GPL v3 or later - No warranties.
                <p>This simple multithreaded application can be used for
                getting a brief summary of Cardano staking information. It does
                currently use Blockfrost API. The embedded Cardano logo was
                downloaded from <a href="{CARDANO_ASSETS_URL}"
                style="text-decoration: none;">{CARDANO_ASSETS_URL}</a> and is
                used under the Cardano Foundation trademark policy.
                <div><span style="font-weight: bold">Contributors</span>: {', '.join(contributors)}</div>
                <div><span style="font-weight: bold">Dev</span>: Raphaël Bazaud &lt;<a href="mailto:{DEV_EMAIL}" style="text-decoration: none;">{DEV_EMAIL}</a>&gt;</div>
                <div><span style="font-weight: bold">Source code</span>: <a href="{PYADA_GITHUB_URL}" style="text-decoration: none;">{PYADA_GITHUB_URL}</a></div></p>
                <p>Python {platform.python_version()} - PyQt {PYQT_VERSION_STR} - Qt version {QT_VERSION_STR} on {platform.system()}''')

    def center(self):
        # center the main window
        fg = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerpt = QApplication.desktop().screenGeometry(screen).center()
        fg.moveCenter(centerpt)
        self.move(fg.topLeft())

    def clearFields(self):
        # we disconnect signal before clearing stake,
        # otherwise update_data() will be called twice
        self.sk.textChanged.disconnect(self.update_data)
        self.sk.setText('')
        self.sk.textChanged.connect(self.update_data)

        self.epochLE.setText('')
        self.poolName.setText('')
        self.poolTicker.setText('')
        self.ctrlAmount.setText('')
        self.rewardsSum.setText('')
        self.rewardsDetails.setText('')

    # check that we are indeed connected to the Internet, to avoid ugly exceptions
    @staticmethod
    def is_connected():
        try:
            # connect to the host -- tells us if the host is actually reachable
            s = socket.create_connection(('www.google.com', 80))
            if s is not None:
                # closing socket
                s.close()
            return True
        except OSError:
            pass
        return False

    @pyqtSlot()
    def update_data(self):

        self.stake_key = self.sk.text()
        # a stake key is 59 bytes long
        if len(self.stake_key) == 59:
            # we pass fetch_data as the function to execute (callback)
            worker = Worker(self.fetch_data)
            self.threadpool.start(worker)

        else:
            self.clearFields()

    def keyPressEvent(self, e):
        # we want to exit on <Esc> key stroke
        if e.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        # we ask for confirmation first
        reply = QMessageBox.question(self, 'Question', QUIT_MSG, QMessageBox.Yes, QMessageBox.No)
        # ternary construct, equivalent to the C++ ternary operator ? :
        event.accept() if reply == QtWidgets.QMessageBox.Yes else event.ignore()


def main():

    if not PyADA.is_connected():
        sys.stderr.write('No Internet access, please try again.\n')
        sys.exit(-1)

    app = QApplication(sys.argv)
    window = PyADA()

    window.show()
    try:
        # starts the event loop
        sys.exit(app.exec_())
    except:
        #  sys.stderr.write('Ciao…\n')
        pass

if __name__ == '__main__':
    main()

