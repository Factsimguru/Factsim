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


from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter
from factsim_scene import FactsimScene

class FactsimView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setScene(FactsimScene())
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        # Variables for panning
        self.panning = False
        self.pan_start_pos = QPointF()

    def mousePressEvent(self, event):
        # Check if an item is under the mouse
        item_under_mouse = self.itemAt(event.pos())

        if event.button() == Qt.RightButton and not item_under_mouse:
            # If right-click and no item under mouse, start panning
            self.panning = True
            self.pan_start_pos = event.position()  # Use position() instead of x() and y()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            # Otherwise, pass event to scene (for item interactions)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.panning:
            # Handle panning
            delta = event.position() - self.pan_start_pos
            self.pan_start_pos = event.position()  # Update pan start position
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        else:
            # Pass event to scene (for item interactions)
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            # Stop panning
            self.panning = False
            self.setCursor(Qt.ArrowCursor)
        else:
            # Pass event to scene (for item interactions)
            super().mouseReleaseEvent(event)
            self.scene().update_connections()

    def wheelEvent(self, event):
        # Allow zooming with the mouse wheel only if no item is selected
        item_under_mouse = self.itemAt(event.position().toPoint())
        if item_under_mouse is None:
            zoom_factor = 1.15
            if event.angleDelta().y() > 0:
                self.scale(zoom_factor, zoom_factor)  # Zoom in
            else:
                self.scale(1 / zoom_factor, 1 / zoom_factor)  # Zoom out
        else:
            # Pass event to scene (for item interactions)
            super().wheelEvent(event)
