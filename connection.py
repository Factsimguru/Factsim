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


from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPen, QPainterPath
from PySide6.QtCore import QPointF

class Connection(QGraphicsPathItem):
    def __init__(self, start_pin, end_pin, color):
        super().__init__()
        self.start_pin = start_pin
        self.end_pin = end_pin
        self.setPen(QPen(color, 2))
        self.update_path()

    def update_path(self):
        path = QPainterPath()
        start_pos = self.start_pin.mapToScene(self.start_pin.boundingRect().center())
        end_pos = self.end_pin.mapToScene(self.end_pin.boundingRect().center())
        control_point1 = QPointF(start_pos.x(), (start_pos.y() + end_pos.y()) / 2)
        control_point2 = QPointF(end_pos.x(), (start_pos.y() + end_pos.y()) / 2)
        path.moveTo(start_pos)
        path.cubicTo(control_point1, control_point2, end_pos)
        self.setPath(path)
