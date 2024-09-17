# -*- coding: utf-8 -*-
#######################################################################
# This file is part of FACTSIM a simulator for Factorio
# circuit network entities.
#
# Python 3 version 0.0
#
# Copyright (C) 2024 Factsimguru (factsimguru@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/> or
# write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#######################################################################

from PySide6.QtWidgets import QDialog, QTabWidget, QVBoxLayout, QWidget, QLabel

class NodeDetailsWindow(QDialog):
    def __init__(self, node):
        super().__init__()
        self.node = node
        self.setWindowTitle(f"{node.name} Details")
        self.setGeometry(100, 100, 400, 300)

        # Create a QTabWidget
        self.tab_widget = QTabWidget()
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tab_widget)

        # Create tabs
        self.config_tab = QWidget()
        self.results_tab = QWidget()

        # Add tabs to the QTabWidget
        self.tab_widget.addTab(self.config_tab, "Configuration")
        self.tab_widget.addTab(self.results_tab, "Results")

        # Populate Configuration Tab
        self.setup_config_tab()

        # Populate Results Tab
        self.setup_results_tab()

    def setup_config_tab(self):
        layout = QVBoxLayout()
        label = QLabel(f"Configure {self.node.name}")
        layout.addWidget(label)
        self.config_tab.setLayout(layout)

    def setup_results_tab(self):
        layout = QVBoxLayout()
        label = QLabel(f"Results for {self.node.name}")
        layout.addWidget(label)
        self.results_tab.setLayout(layout)
