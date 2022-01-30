# -*- coding: utf-8 -*-
#######################################################################
# This file is part of FACTSIM a simulator for Factorio
# circuit network entities.
#
# Python 3 version 0.0
#
# Copyright (C) 2022 Factsimguru (factsimguru@gmail.com)
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





import zlib
import base64
import json
import tkinter as tk
import tkinter.filedialog
import time


def open_blueprint(filename=None):
    """Open a blueprint by filename or prompting the user for one.

    Return a dictionary of the blueprint contents
    """
    if not filename:
        root = tk.Tk()
        root.withdraw()
        filename = tkinter.filedialog.askopenfilename()
    file = open(filename, encoding='utf-8')
    jsonstring64 = file.read()[1:]
    jsonstringdata = base64.b64decode(jsonstring64)
    jsonstring = zlib.decompress(jsonstringdata)
    bpdict = json.loads(jsonstring)
    return bpdict

class Entity():
    """Generic Factsim entity.

    Generated from a entity dictionary from a blueprint
    """

    def __init__(self, dictionary):
        self.dictionary = dictionary
        self.entity_N = dictionary['entity_number']
        self.name = dictionary['name']
        self.position = dictionary['position']

    def __str__(self):

        return 'Entity nr {:0>3d} - {}'.format(self.entity_N,  self.name)


class Connected_Entity(Entity):
    """Any entity that has connections"""
    def __init__(self,dictionary):
        super().__init__(dictionary)
        self.connections = dictionary['connections']
        self.step = 0
        self.inputs = []
        self.outputs = []
        self.connectIN = self.connections.get('1')
        self.connectOUT = self.connections.get('2')



class Electric_pole(Connected_Entity):
    """Any pole of any size, is a subclass of Connected_Entity"""

    def __init__(self, dictionary):
        super().__init__(dictionary)



class Factsimcmd():
    """Class holding all the Factsim simulation"""
    def __init__(self):
        self.blueprint = open_blueprint()
        self.Entities = []
        self.bpEntities = []

    def create_entities(self):
        """Parse the blueprint entities into objects and fill the Entities list"""
        self.bpEntities = self.blueprint['blueprint']['entities']
        genericentities = [Entity(e) for e in self.bpEntities]
        for e in genericentities:
            if 'pole' in e.name.split('-'): 
                self.Entities += [Electric_pole(e.dictionary)]
            else:
                self.Entities += [e]

f = Factsimcmd()
f.create_entities()
