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

from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtGui import QBrush, QColor

class Pin(QGraphicsEllipseItem):
    def __init__(self, parent, x, y, width, height, pin_name, pin_type, color):
        super().__init__(x, y, width, height, parent)
        self.pin_name = pin_name
        self.owningNode = parent
        self.pin_type = pin_type
        self.setZValue(1)  # Ensure pins are always on top
        if color == "red":
            self.setBrush(QBrush(QColor(255, 0, 0)))  # Red pins
        elif color == "green":
            self.setBrush(QBrush(QColor(0, 255, 0)))  # Green pins
        else:
            raise Exception("Only red or green colors, for now")

    def boundingRect(self):
        rect = super().boundingRect()
        return rect.adjusted(-2, -2, 2, 2)
