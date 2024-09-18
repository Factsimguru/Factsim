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

import logging
from PySide6.QtWidgets import QGraphicsItem, QComboBox, QGraphicsProxyWidget
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainter, QTransform
from pin import Pin


DEFAULT_PINS = {
    'input_red': (0, 20, 15, 15, 'input_red', "input", 'red'),
    'output_red': (90, 20, 15, 15, 'output_red', "output", 'red'),
    'input_green': (0, 35, 15, 15, 'input_green', "input", 'green'),
    'output_green': (90, 35, 15, 15, 'output_green', "output", 'green'),
}

OUT_PINS = {
    'output_red': (40, 20, 15, 15, 'output_red', "output", 'red'),
    'output_green': (40, 35, 15, 15, 'output_green', "output", 'green')
}


# Custom Node Class
class Node(QGraphicsItem):
    max_id = 0  # Class variable to count node instancestrack the max id

    def __init__(self, node_type, color=QColor(150, 200, 150), pos=QPointF(100,100) , pins=DEFAULT_PINS, rect = QRectF(0, 0, 110, 50), from_dict = False, node_id=None):
        super().__init__()
        self.rect = rect  # Define the rectangle for the node
        self.node_type = node_type
        self.color = color  # Initialize the color attribute
        if not node_id: # Unique ID for each node
            Node.max_id += 1
            self.node_id = Node.max_id  
        else:
            self.node_id = node_id
            Node.max_id = max(node_id, Node.max_id)
            
        self.name = "Node" + "  " +str(self.node_id)

        self.pins = {}
        self.create_pins(pins)
        self.local_tick = 0
        self.active = True

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        
        self.create_options_combobox()
        self.setPos(pos)

    def create_options_combobox(self):
        # Create combobox for configuration
        self.combo_box = QComboBox()
        self.combo_box.addItems(["Option 1", "Option 2", "Option 3"])
        self.combo_box.currentIndexChanged.connect(self.combo_changed)
        self.combo_box.setFixedWidth(50)

        # Use a QGraphicsProxyWidget to embed the combo box inside the scene
        self.proxy_widget = QGraphicsProxyWidget(self)
        self.proxy_widget.setWidget(self.combo_box)
        self.proxy_widget.setPos(25,25)  # Adjust this position based on where you want the combobox inside the node
        

    def create_pins(self, pins_dict):
        for key, value in pins_dict.items():
            updated_value = (self,) + value
            self.pins[key] = Pin(*updated_value)

    def combo_changed(self, index):
        # Handle combo box change
        selected_option = self.combo_box.currentText()
        logging.info(f"Node {self.node_id} - ComboBox changed to {selected_option}")

            
    def boundingRect(self):
        return self.rect.adjusted(0, 0, 0, 30)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self.color))
        painter.drawRect(self.rect)
        textrect = self.rect.adjusted(5,0,-5,-20)

        # Set a default font
        font = painter.font()
        font.setPointSize(12)  
        painter.setFont(font)

        
        painter.drawText(textrect, Qt.AlignCenter, f"{self.name}")

    # When the node is moved, inform the connections to update their positions
    def itemChange(self, change, value):
        from factsim_scene import FactsimScene
        if change == QGraphicsItem.ItemPositionHasChanged:
            scene = self.scene()
            if isinstance(scene, FactsimScene):
                scene.update_connections()
        return super().itemChange(change, value)
    def compute(self):
        if self.active:
            self.local_tick += 1
    def handle_global_tick(self, tick):
        logging.info(f"Node {self.node_id} received global tick: {tick}")
            



class Decider(Node):
    def __init__(self, node_type, color=QColor(100, 100, 255),pos=QPointF(100,100), pins=DEFAULT_PINS, from_dict=False, node_id=None):
        super().__init__(node_type, color=color,pos=pos, pins=pins, from_dict=from_dict, node_id=node_id)
        self.name = "DEC" + " " + str(self.node_id)
        
class Arithmetic(Node):
    def __init__(self, node_type, color=QColor(107, 179, 0),pos=QPointF(100,100), pins=DEFAULT_PINS, from_dict=False, node_id=None):
        super().__init__(node_type, color=color, pos=pos, pins=pins, from_dict=from_dict, node_id=node_id)
        self.name = "ART" + " " + str(self.node_id)

class Constant(Node):
    def __init__(self, node_type, color=QColor(180,27,0), pos=QPointF(100,100), pins=OUT_PINS, rect=QRectF(0,0,50, 50), from_dict=False, node_id=None):
        super().__init__(node_type, color=color,pos=pos, pins=OUT_PINS, rect=rect, from_dict=from_dict, node_id=node_id)
        self.name = "C" + "  " + str(self.node_id)
    def create_options_combobox(self):
        pass
