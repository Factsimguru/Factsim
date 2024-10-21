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


from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QTransform, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsScene, QGraphicsEllipseItem, QGraphicsPathItem
from connection import Connection
from node_details_window import NodeDetailsWindow
from node import Decider, Arithmetic, Constant, Pole, Node
import logging

class FactsimScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        #self.setSceneRect(0, 0, 800, 600)
        self.current_connection = None
        self.current_pin = None
        self.connections_dict = {}  # Dictionary to store connections by frozenset of pins
        self.nodes_dict = {}

    def reset_scene(self):
        self.current_connection = None
        self.current_pin = None
        for name,node in self.nodes_dict.items():
            self.delete_node(node)
        self.nodes_dict = {}
        for item in self.items():
            self.removeItem(item)
        

    def start_connection(self, pin, color):
        self.current_pin = pin
        self.current_connection = QGraphicsPathItem()
        self.current_connection.setPen(QPen(color, 2, Qt.SolidLine))
        self.addItem(self.current_connection)

        # Log starting point for connection
        parent_node = self.current_pin.parentItem()
        pin_name = self.get_pin_name(self.current_pin)
        logging.info(f"Connection started from {pin_name} on Node {parent_node.name}")

    def finish_connection(self, end_pin):
        if self.current_connection and self.current_pin:
            start_node = self.current_pin.parentItem()
            end_node = end_pin.parentItem()
            start_pin_name = self.get_pin_name(self.current_pin)
            end_pin_name = self.get_pin_name(end_pin)

            connection_key = frozenset([self.current_pin, end_pin])

            # Check if the connection already exists
            if connection_key in self.connections_dict:
                # Remove the existing connection
                connection = self.connections_dict[connection_key]
                self.removeItem(connection)
                del self.connections_dict[connection_key]
                logging.info(f"Existing connection between {start_pin_name} and {end_pin_name} deleted.")
            elif self.current_pin == end_pin:
                logging.warning(f"Connection failed: Same pin (Node {start_node.node_id})")
            elif start_node == end_node:
                # Same node: Allow connection if pins are of different types (input to output) and colors match
                if self.current_pin.brush().color() == end_pin.brush().color() and \
                   ('input' in start_pin_name and 'output' in end_pin_name or
                    'output' in start_pin_name and 'input' in end_pin_name):
                    color = self.current_connection.pen().color()
                    connection = Connection(self.current_pin, end_pin, color)
                    self.addItem(connection)
                    self.connections_dict[connection_key] = connection  # Store the connection

                    logging.info(f"Connection done between {start_pin_name} on Node {start_node.name} and "
                                 f"{end_pin_name} on Node {end_node.name}")
                else:
                    logging.warning(f"Connection failed: Mismatched colors or pin types between pins "
                                    f"on Node {start_node.name}")
            else:
                # Different nodes: Check if the end pin is the same color as the start pin
                if self.current_pin.brush().color() == end_pin.brush().color():
                    color = self.current_connection.pen().color()
                    connection = Connection(self.current_pin, end_pin, color)
                    self.addItem(connection)
                    self.connections_dict[connection_key] = connection  # Store the connection

                    logging.info(f"Connection done between {start_pin_name} from Node {start_node.name} "
                                 f"and {end_pin_name} from Node {end_node.name}")
                else:
                    logging.warning(f"Connection failed: Mismatched colors between pins "
                                    f"on Node {start_node.name} and Node {end_node.name}")
            self.removeItem(self.current_connection)

        # Reset the temporary connection and pin tracking
        self.current_connection = None
        self.current_pin = None

    def get_pin_name(self, pin):
        # Helper function to get the pin's name from the parent node's dictionary
        node = pin.parentItem()
        for name, p in node.pins.items():
            if p is pin:
                return p.pin_name
        return "Unknown pin"

    def mouseMoveEvent(self, event):
        if self.current_connection and self.current_pin:
            start_pos = self.current_pin.mapToScene(self.current_pin.boundingRect().center())
            end_pos = event.scenePos()

            # Update the path with new end position
            path = QPainterPath()
            control_point1 = QPointF(start_pos.x(), (start_pos.y() + end_pos.y()) / 2)
            control_point2 = QPointF(end_pos.x(), (start_pos.y() + end_pos.y()) / 2)

            path.moveTo(start_pos)
            path.cubicTo(control_point1, control_point2, end_pos)

            self.current_connection.setPath(path)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())
        if isinstance(item, QGraphicsEllipseItem):
            # Determine the color of the clicked pin
            brush_color = item.brush().color()
            self.start_connection(item, brush_color)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        release_pos = event.scenePos()
        logging.info(f"Mouse released at scene position: {release_pos}")

        # Get all items at the release position
        items_at_pos = self.items(release_pos)

        # Filter out the pins (QGraphicsEllipseItem) from the list of items
        pin_item = None
        for item in items_at_pos:
            if isinstance(item, QGraphicsEllipseItem):
                pin_item = item
                break

        if pin_item:
            logging.info(f"Pin {pin_item.pin_name} detected at release position on Node {pin_item.parentItem().name}")
        else:
            logging.info("No valid pin detected at release position")

        if isinstance(pin_item, QGraphicsEllipseItem) and self.current_connection:
            self.finish_connection(pin_item)
        else:
            if self.current_connection:
                logging.info(f"Connection canceled: No valid pin reached")
                self.removeItem(self.current_connection)
                self.current_connection = None
                self.current_pin = None

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())
        if isinstance(item, Node):  # Assuming your nodes are represented by a `Node` class
            self.open_node_details(item)
        else:
            super().mouseDoubleClickEvent(event)

    def open_node_details(self, node):
        # Create and show the NodeDetailsWindow
        self.details_window = NodeDetailsWindow(node)
        self.details_window.exec()
        
    def update_connections(self):
        for conn in self.connections_dict.values():
            conn.update_path()

    # Method to create and place a node at a specific position
    def create_node(self, node_type, position, node_id=None, direction=None, control_behavior=None):
        if node_type == "Decider":
            node = Decider(node_type, pos=position, node_id=node_id, direction=direction, control_behavior=control_behavior)
        elif node_type == "Arithmetic":
            node = Arithmetic(node_type, pos=position, node_id=node_id, direction=direction, control_behavior=control_behavior)
        elif node_type == "Constant":
            node = Constant(node_type, pos=position, node_id=node_id, direction=direction, control_behavior=control_behavior)
        elif node_type == "Pole":
            node = Pole(node_type, pos=position, node_id=node_id)
        else:
            node = Node(node_type, pos=position,  node_id=node_id)
        self.addItem(node)
        self.nodes_dict[node.node_id] = node
        #print(self.nodes_dict)
        return node

    def delete_node(self, node):
        # Delete all connections related to this node
        pins_to_delete = list(node.pins.values())
        for pin in pins_to_delete:
            # Check for any connections related to each pin
            connections_to_delete = [key for key in self.connections_dict if pin in key]
            for connection_key in connections_to_delete:
                connection = self.connections_dict[connection_key]
                self.removeItem(connection)  # Remove the connection from the scene
                del self.connections_dict[connection_key]  # Remove the connection from the dictionary

        self.removeItem(node)  # Remove the node itself from the scene
        logging.info(f"Node {node.name} deleted.")


    # Method to create a connection programmatically
    def create_connection(self, start_node, start_pin_name, end_node, end_pin_name):
        start_pin = None
        end_pin = None

        # Find the start and end pins
        if start_node and end_node:
            start_pin = start_node.pins.get(start_pin_name)
            end_pin = end_node.pins.get(end_pin_name)

        if start_pin and end_pin:
            # Check if the connection already exists
            connection_key = frozenset([start_pin, end_pin])
            if connection_key in self.connections_dict:
                logging.info(f"Connection between {start_pin_name} on Node {start_node.node_id} and "
                             f"{end_pin_name} on Node {end_node.node_id} already exists.")
                return

            # Check if the pins match in color and type
            if start_pin.brush().color() == end_pin.brush().color():
                color = start_pin.brush().color()
                connection = Connection(start_pin, end_pin, color)
                self.addItem(connection)
                self.connections_dict[connection_key] = connection
                logging.info(f"Connection done between {start_pin_name} on Node {start_node.node_id} and "
                             f"{end_pin_name} on Node {end_node.node_id}")
            else:
                logging.warning(f"Connection failed: Colors do not match between {start_pin_name} on Node "
                                f"{start_node.node_id} and {end_pin_name} on Node {end_node.node_id}")
        else:
            if not start_pin:
                logging.warning(f"start pin {start_pin_name} does not exist on Node {start_node.name}")
                
            if not end_pin:
                logging.warning(f"end pin {end_pin_name} does not exist on Node {end_node.name}")

                
    def delete_connection(self, start_pin, end_pin):
        connection_key = frozenset([start_pin, end_pin])

        if connection_key in self.connections_dict:
            connection = self.connections_dict[connection_key]
            self.removeItem(connection)  # Remove the connection from the scene
            del self.connections_dict[connection_key]  # Remove the connection from the dictionary
            logging.info(f"Connection between {self.get_pin_name(start_pin)} and {self.get_pin_name(end_pin)} deleted.")
        else:
            logging.warning(f"Connection between {self.get_pin_name(start_pin)} and {self.get_pin_name(end_pin)} not found.")

    async def update_global_tick(self, tick):
        # Method to handle the global tick update
        logging.info(f"Updating nodes with new global tick: {tick}")
        for item in self.items():
            if isinstance(item, Node):
                await item.handle_global_tick(tick)


