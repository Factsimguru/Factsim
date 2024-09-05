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


import sys
import logging
from PySide6.QtCore import Qt, QRectF, QPointF, QLineF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QAction, QTransform, QPainterPath
from PySide6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsItem, QApplication, 
    QGraphicsEllipseItem, QGraphicsLineItem, QMainWindow, QToolBar, QGraphicsPathItem
)

# Setup logging (optional logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#Custom Pin class
class Pin(QGraphicsEllipseItem):
    def __init__(self, parent, x, y, width, height, pin_name, is_input, color):
        super().__init__(x, y, width, height, parent)
        self.pin_name = pin_name
        self.owningNode = parent
        self.is_input = is_input
        self.is_output = not is_input
        self.setZValue(1)  # Ensure pins are always on top
        if color == "red":
            self.setBrush(QBrush(QColor(255, 0, 0)))  # Red pins
        elif color == "green":
            self.setBrush(QBrush(QColor(0, 255, 0))) # Green pins
        else:
            raise Exception("Only red or green colors, for now")
    def boundingRect(self):
        rect = super().boundingRect()
        # Slightly increase the bounding rectangle for better detection
        return rect.adjusted(-2, -2, 2, 2)


# Pins (4 pins: 2 inputs, 2 outputs) for the generic Node class
DEFAULT_PINS = {
            'input_red': (0, 20, 15, 15, 'input_red', True, 'red'),
            'output_red': (90, 20, 15, 15, 'output_red', False, 'red'),
            'input_green': (0, 35, 15, 15, 'input_green', True, 'green'),
            'output_green': (90, 35, 15, 15, 'output_green', False, 'green'),
        }
    
# Custom Node Class
class Node(QGraphicsItem):
    node_counter = 0  # Class variable to count node instances

    def __init__(self, name, node_type, color=QColor(100, 100, 255), pins=DEFAULT_PINS):
        super().__init__()
        self.rect = QRectF(0, 0, 100, 50)  # Define the rectangle for the node
        self.node_type = node_type
        self.color = color  # Initialize the color attribute
        Node.node_counter += 1
        self.node_id = Node.node_counter  # Unique ID for each node
        self.name = self.node_type + "  " +str(self.node_id)

        self.pins = {}
        self.create_pins(pins)

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    def create_pins(self, pins_dict):
        for key, value in pins_dict.items():
            updated_value = (self,) + value
            self.pins[key] = Pin(*updated_value)

            
    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self.color))
        painter.drawRect(self.rect)
        painter.drawText(self.rect, Qt.AlignCenter, f"{self.name}")

    # When the node is moved, inform the connections to update their positions
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            scene = self.scene()
            if isinstance(scene, FactsimScene):
                scene.update_connections()
        return super().itemChange(change, value)






# Custom Connection Class (to connect pins)
class Connection(QGraphicsPathItem):
    def __init__(self, start_pin, end_pin, color):
        super().__init__()
        self.start_pin = start_pin
        self.end_pin = end_pin
        self.setPen(QPen(color, 2))
        self.update_path()

    def update_path(self):
        path = QPainterPath()

        # Get the start and end positions
        start_pos = self.start_pin.mapToScene(self.start_pin.boundingRect().center())
        end_pos = self.end_pin.mapToScene(self.end_pin.boundingRect().center())

        # Create a cubic Bezier curve
        control_point1 = QPointF(start_pos.x(), (start_pos.y() + end_pos.y()) / 2)
        control_point2 = QPointF(end_pos.x(), (start_pos.y() + end_pos.y()) / 2)

        path.moveTo(start_pos)
        path.cubicTo(control_point1, control_point2, end_pos)

        self.setPath(path)

# Scene and View
class FactsimScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.setSceneRect(0, 0, 800, 600)
        self.current_connection = None
        self.current_pin = None
        self.connections_dict = {}  # Dictionary to store connections by frozenset of pins

    def start_connection(self, pin, color):
        self.current_pin = pin
        self.current_connection = QGraphicsPathItem()
        self.current_connection.setPen(QPen(color, 2, Qt.SolidLine))
        self.addItem(self.current_connection)

        # Log starting point for connection
        parent_node = self.current_pin.parentItem()
        pin_name = self.get_pin_name(self.current_pin)
        logging.info(f"Connection started from {pin_name} on Node {parent_node.node_id}")

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

                    logging.info(f"Connection done between {start_pin_name} on Node {start_node.node_id} and "
                                 f"{end_pin_name} on Node {end_node.node_id}")
                else:
                    logging.warning(f"Connection failed: Mismatched colors or pin types between pins "
                                    f"on Node {start_node.node_id}")
            else:
                # Different nodes: Check if the end pin is the same color as the start pin
                if self.current_pin.brush().color() == end_pin.brush().color():
                    color = self.current_connection.pen().color()
                    connection = Connection(self.current_pin, end_pin, color)
                    self.addItem(connection)
                    self.connections_dict[connection_key] = connection  # Store the connection

                    logging.info(f"Connection done between {start_pin_name} from Node {start_node.node_id} "
                                 f"and {end_pin_name} from Node {end_node.node_id}")
                else:
                    logging.warning(f"Connection failed: Mismatched colors between pins "
                                    f"on Node {start_node.node_id} and Node {end_node.node_id}")
            self.removeItem(self.current_connection)

        # Reset the temporary connection and pin tracking
        self.current_connection = None
        self.current_pin = None

    def get_pin_name(self, pin):
        # Helper function to get the pin's name from the parent node's dictionary
        node = pin.parentItem()
        for name, p in node.pins.items():
            if p is pin:
                return name
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
            logging.info(f"Pin detected at release position: {pin_item} on Node {pin_item.parentItem().name}")
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

    def update_connections(self):
        for conn in self.connections_dict.values():
            conn.update_path()

    # Method to create and place a node at a specific position
    def create_node(self, name, node_type, color, position):
        node = Node(name, node_type, color)
        node.setPos(position)
        self.addItem(node)
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
    def create_connection(self, start_node, start_pin_name, end_node, end_pin_name, color):
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
                if ('input' in start_pin_name and 'output' in end_pin_name or
                    'output' in start_pin_name and 'input' in end_pin_name):
                    connection = Connection(start_pin, end_pin, color)
                    self.addItem(connection)
                    self.connections_dict[connection_key] = connection
                    logging.info(f"Connection done between {start_pin_name} on Node {start_node.node_id} and "
                                 f"{end_pin_name} on Node {end_node.node_id}")
                else:
                    logging.warning(f"Connection failed: Pin types do not match between {start_pin_name} on Node "
                                    f"{start_node.node_id} and {end_pin_name} on Node {end_node.node_id}")
            else:
                logging.warning(f"Connection failed: Colors do not match between {start_pin_name} on Node "
                                f"{start_node.node_id} and {end_pin_name} on Node {end_node.node_id}")
    def delete_connection(self, start_pin, end_pin):
        connection_key = frozenset([start_pin, end_pin])

        if connection_key in self.connections_dict:
            connection = self.connections_dict[connection_key]
            self.removeItem(connection)  # Remove the connection from the scene
            del self.connections_dict[connection_key]  # Remove the connection from the dictionary
            logging.info(f"Connection between {self.get_pin_name(start_pin)} and {self.get_pin_name(end_pin)} deleted.")
        else:
            logging.warning(f"Connection between {self.get_pin_name(start_pin)} and {self.get_pin_name(end_pin)} not found.")




class FactsimView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setScene(FactsimScene())
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.scene().update_connections()

# Main Window with Toolbar for adding nodes
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.view = FactsimView()
        self.setCentralWidget(self.view)
        # Initialize a global tick
        self.global_tick = 0

        # Create toolbars
        self.create_top_toolbar()
        self.create_left_toolbar()

        self.node_counter = 1

        

    def create_top_toolbar(self):
        # Create the top toolbar
        top_toolbar = QToolBar("Simulation Controls", self)
        self.addToolBar(Qt.TopToolBarArea, top_toolbar)

        # Add Open and Save As buttons
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        top_toolbar.addAction(open_action)

        save_as_action = QAction("Save As", self)
        save_as_action.triggered.connect(self.save_as_file)
        top_toolbar.addAction(save_as_action)

        # Add a separator
        top_toolbar.addSeparator()

        # Add Simulation control buttons
        start_action = QAction("Start", self)
        start_action.triggered.connect(self.simulation_start)
        top_toolbar.addAction(start_action)

        backward_action = QAction("Back", self)
        backward_action.triggered.connect(self.simulation_back)
        top_toolbar.addAction(backward_action)

        # Add an entry to display and edit the current global tick
        self.tick_edit = self.create_tick_edit(top_toolbar)

        forward_action = QAction("Forward", self)
        forward_action.triggered.connect(self.simulation_forward)
        top_toolbar.addAction(forward_action)

        play_action = QAction("Play", self)
        play_action.triggered.connect(self.simulation_play)
        top_toolbar.addAction(play_action)

    def create_left_toolbar(self):
        # Create the left toolbar for adding nodes
        toolbar = QToolBar("Tools", self)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)

        # Action to add a node
        add_node_action = QAction("Add Node", self)
        add_node_action.triggered.connect(self.add_node)
        toolbar.addAction(add_node_action)

    def create_tick_edit(self, toolbar):
        # Entry to edit and display the global tick
        tick_edit = QAction(f"Tick: {self.global_tick}", self)
        tick_edit.setText(f"Tick: {self.global_tick}")
        tick_edit.triggered.connect(self.edit_tick)
        toolbar.addAction(tick_edit)
        return tick_edit

    def open_file(self):
        # Implement functionality to open a file (left as an exercise)
        logging.info("Open file triggered")

    def save_as_file(self):
        # Implement functionality to save as a file (left as an exercise)
        logging.info("Save As file triggered")

    def simulation_start(self):
        self.global_tick = 0
        self.update_tick_display()
        logging.info("Simulation reset to start")

    def simulation_back(self):
        if self.global_tick > 0:
            self.global_tick -= 1
            self.update_tick_display()
        logging.info(f"Simulation moved back to tick {self.global_tick}")

    def simulation_forward(self):
        self.global_tick += 1
        self.update_tick_display()
        logging.info(f"Simulation advanced to tick {self.global_tick}")

    def simulation_play(self):
        # Implement play functionality (simulation loop, left as an exercise)
        logging.info("Simulation play triggered")

    def edit_tick(self):
        # Edit the global tick manually (left as an exercise)
        logging.info("Edit tick triggered")

    def update_tick_display(self):
        # Update the tick display in the toolbar
        self.tick_edit.setText(f"Tick: {self.global_tick}")

    def add_node(self):
        # Call the create_node method from FactsimScene
        node_name = f"Node {self.node_counter}"
        node_type = "Type A"
        node_color = QColor(150, 200, 150)
        position = QPointF(100 + (self.node_counter * 20), 100 + (self.node_counter * 20))

        self.view.scene().create_node(node_name, node_type, node_color, position)
        self.node_counter += 1


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.setWindowTitle("Factsim UI")
    main_window.setGeometry(100, 100, 1000, 600)
    main_window.show()

    # Access the scene through the view
    scene = main_window.view.scene()

    # Create nodes programmatically
#    node1 = scene.create_node("Node 1", "Type A", QColor(150, 200, 150), QPointF(100, 100))
#    node2 = scene.create_node("Node 2", "Type B", QColor(150, 200, 150), QPointF(300, 100))

    # Create connections programmatically
#    scene.create_connection(node1, 'output_red', node2, 'input_red', QColor(255, 0, 0))
#    scene.create_connection(node1, 'output_green', node2, 'input_green', QColor(0, 255, 0))

    sys.exit(app.exec())
