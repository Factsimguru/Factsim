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
import base64
import zlib
import json
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QToolBar, QFileDialog, QMessageBox, QApplication
)
from factsim_view import FactsimView
import asyncio
from qasync import asyncSlot

# Main Window with Toolbar for adding nodes
class MainWindow(QMainWindow):
    global_tick_changed = Signal(int)
    
    def __init__(self):
        super().__init__()

        self.view = FactsimView()
        self.setCentralWidget(self.view)
        # Initialize a global tick
        self.global_tick = 0

       # Connect the signal to an async slot in FactsimScene
        self.global_tick_changed.connect(self.on_global_tick_changed)

        # Create toolbars
        self.create_top_toolbar()
        self.create_left_toolbar()

    @asyncSlot(int)
    async def on_global_tick_changed(self, tick):
        await self.view.scene().update_global_tick(tick)
        

    def create_top_toolbar(self):
        # Create the top toolbar
        top_toolbar = QToolBar("Simulation Controls", self)
        self.addToolBar(Qt.TopToolBarArea, top_toolbar)

        #add New button
        new_action = QAction("New", self)
        new_action.triggered.connect(self.view.scene().reset_scene)
        top_toolbar.addAction(new_action)

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

        # Create actions for different node types
        node_types = ["Decider", "Arithmetic", "Constant"]
           
        # Create buttons for each node type
        for node_type in node_types:
            action = QAction(node_type, self)
            # Use a lambda to pass the node_type to add_node
            action.triggered.connect(lambda checked, nt=node_type: self.add_node(nt))
            toolbar.addAction(action)


    def create_tick_edit(self, toolbar):
        # Entry to edit and display the global tick
        tick_edit = QAction(f"Tick: {self.global_tick}", self)
        tick_edit.setText(f"Tick: {self.global_tick}")
        tick_edit.triggered.connect(self.edit_tick)
        toolbar.addAction(tick_edit)
        return tick_edit

    def open_file(self):
        # Implement functionality to open a file
        logging.info("Open file triggered")
        # Open a file dialog to select the file
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open File", "", "Blueprint Files (*.bp);;All Files (*)")

        if file_path:
            try:
                # Assuming you're opening a JSON file or some text-based format
                with open(file_path, 'r') as file:
                    #file_contents = file.read()
                    # Process the file (you can parse the content here if needed)
                    logging.info(f"Opened file: {file_path}")
                    jsonstring64 = file.read()[1:]
                    jsonstringdata = base64.b64decode(jsonstring64)
                    jsonstring = zlib.decompress(jsonstringdata)
                    self.jsonstring = jsonstring
                    self.bpdict = json.loads(jsonstring)['blueprint']
                    for entity in self.bpdict['entities']:
                        print(f"{entity}")
                        position =  QPointF(entity['position']['x']*100, entity['position']['y']*100)
                        node_id = (entity['entity_number'])
                        #print(node_id)
                        if entity['name'] == 'decider-combinator':
                            self.view.scene().create_node("Decider", position, node_id=node_id)
                        elif entity['name'] == 'arithmetic-combinator':
                            self.view.scene().create_node("Arithmetic", position, node_id=node_id)
                        elif entity['name'] == 'constant-combinator':
                            self.view.scene().create_node("Constant", position, node_id=node_id)
                        if 'electric-pole' in entity['name'] or 'substation' in entity['name']:
                            self.view.scene().create_node("Pole", position, node_id=node_id)
                            
                    for entity in self.bpdict.get('entities'):
                        current_node = entity['entity_number']
                        if entity.get('connections').get('1'):
                            for color, connections in entity.get('connections').get('1').items():
                                print(color, connections)
                                for connection in connections:
                                    orig = self.view.scene().nodes_dict[current_node]
                                    dest = self.view.scene().nodes_dict[connection.get('entity_id')]
                                    #print(orig,dest)
                                    if connection.get('circuit_id') == 1:
                                        self.view.scene().create_connection(orig, 'input_'+color, dest , 'input_'+color)
                                    elif connection.get('circuit_id') == 2:
                                        self.view.scene().create_connection(orig, 'input_'+color, dest , 'output_'+color)
                                    else:
                                        self.view.scene().create_connection(orig, 'input_'+color, dest , color)
                                        self.view.scene().create_connection(orig, color, dest , color)
                                        
                                    
                        if entity.get('connections').get('2'):
                            for color, connections in entity.get('connections').get('2').items():
                                print(color, connections)
                                for connection in connections:
                                    orig = self.view.scene().nodes_dict[current_node]
                                    dest = self.view.scene().nodes_dict[connection.get('entity_id')]
                                    #print(orig,dest)
                                    if connection.get('circuit_id') == 1:
                                        self.view.scene().create_connection(orig, 'output_'+color, dest , 'input_'+color)
                                    elif connection.get('circuit_id') == 2:
                                        self.view.scene().create_connection(orig, 'output_'+color, dest , 'output_'+color)
                                    else:
                                        self.view.scene().create_connection(orig, 'output_'+color, dest , color)
                                        self.view.scene().create_connection(orig, color, dest , color)
                                        
                #self.view.scene().setSceneRect(self.view.scene().itemsBoundingRect())

                        
            except Exception as e:
                # Show an error message if the file could not be opened
                error_msg = QMessageBox()
                error_msg.setIcon(QMessageBox.Critical)
                error_msg.setText(f"Failed to open the file: {e}")
                error_msg.setWindowTitle("File Open Error")
                error_msg.exec()
        else:
            logging.info("File selection canceled")

        
    def save_as_file(self):
        # Implement functionality to save as a file
        logging.info("Save As file triggered")

    def simulation_start(self):
        self.global_tick = 0
        self.update_tick_display()
        logging.info("Simulation reset to start")
        self.global_tick_changed.emit(self.global_tick)

    def simulation_back(self):
        if self.global_tick > 0:
            self.global_tick -= 1
            self.update_tick_display()
        logging.info(f"Simulation moved back to tick {self.global_tick}")
        self.global_tick_changed.emit(self.global_tick)

    def simulation_forward(self):
        self.global_tick += 1
        self.update_tick_display()
        logging.info(f"Simulation advanced to tick {self.global_tick}")
        self.global_tick_changed.emit(self.global_tick)

    def simulation_play(self):
        # Implement play functionality (simulation loop, left as an exercise)
        logging.info("Simulation play triggered")

    def edit_tick(self):
        # Edit the global tick manually (left as an exercise)
        logging.info("Edit tick triggered")

    def update_tick_display(self):
        # Update the tick display in the toolbar
        self.tick_edit.setText(f"Tick: {self.global_tick}")

    def add_node(self, node_type):
        # Call the create_node method from FactsimScene
        self.view.scene().create_node(node_type, QPointF(100,100))
