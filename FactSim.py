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
        print("opening: {} from filedialog".format(filename))
    else:
        print("opening: {}".format(filename))
    file = open(filename, encoding='utf-8')
    jsonstring64 = file.read()[1:]
    jsonstringdata = base64.b64decode(jsonstring64)
    jsonstring = zlib.decompress(jsonstringdata)
    bpdict = json.loads(jsonstring)
    file.close()
    return bpdict


class Signal():
    """Object to manipulate signals."""
    def __init__(self, dictionary):
        self.name = dictionary.get('signal').get('name')
        self.count = dictionary.get('count')
        self.kind = dictionary.get('signal').get('type')
        self.index = dictionary.get('index')
    def __str__(self):
        return "{} = {}".format(self.name, self.count)


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
    """Any entity that can have connections"""
    def __init__(self, dictionary, simulation):
        super().__init__(dictionary)
        self.simulation = simulation
        self.connections = dictionary.get('connections')
        self.tick = 0
        self.inputs = []
        self.outputs = []
        if self.connections:
            self.connect1 = self.connections.get('1')
            self.connect2 = self.connections.get('2')
        self.connectIN = {}
        self.connectOUT = {}
        
    def advance(self):
        raise NotImplementedError

    def get_output(self, tick):
        while len(self.outputs) < tick + 1:
            self.advance()
        return self.outputs[tick]


class Electric_pole(Connected_Entity):
    """Any pole of any size, is a subclass of Connected_Entity."""

    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)
    def advance(self):
        pass


class Constant_Combinator(Connected_Entity):
    """Constant combinator, outputs constant signal."""
    
    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)
        self.direction = dictionary.get('direction')
        self.c_behavior = dictionary.get('control_behavior').get('filters')
        self.connectOUT = self.connect1
        
    def advance(self):
        self.tick += 1
        self.outputs += [[Signal(f) for f in self.c_behavior]]



class Decider_Combinator(Connected_Entity):
    """Decider combinator, given a condition decides if a signal must output"""
    
    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)
        self.direction = dictionary.get('direction')
        self.c_behavior = dictionary.get('control_behavior').get('decider_conditions')
        self.cond_first_signal = self.c_behavior.get('first_signal')
        self.cond_constant = self.c_behavior.get('constant')
        self.cond_second_signal = self.c_behavior.get('second_signal')
        self.cond_comparator = self.c_behavior.get('comparator')
        self.cond_output_signal = self.c_behavior.get('output_signal')
        self.cond_copy_count = self.c_behavior.get('copy_count_from_input')
        self.connectIN = self.connect1
        self.connectOUT = self.connect2
        self.red_input = self.connectIN.get('red')
        self.green_input = self.connectIN.get('green')
        #on first tick will never output anything
        self.tick += 1
        self.outputs = [[]]
        self.inputs = [[]]

    def advance(self):
        self.inputs += [[]]
        if self.red_input:
            for e in self.red_input:
                self.inputs[self.tick] += self.simulation.get_entity(
                    e.get('entity_id')).get_output(self.tick - 1)
        if self.green_input:
            for e in self.green_input:
                self.inputs[self.tick] += self.simulation.get_entity(
                    e.get('entity_id')).get_output(self.tick - 1)

        input_count = {}
        for i in self.inputs[self.tick]:
            print("checking .. {}".format(i))
            if isinstance(i, Signal):
                if i.name in input_count:
                    input_count[i.name] += i.count
                else:
                    input_count[i.name] = i.count

        self.outputs += [[]]
        self.tick += 1

        if not self.cond_first_signal or not self.cond_output_signal:

            return

        if self.cond_constant:

            compare_value = self.cond_constant

        elif self.cond_second_signal:

            compare_value = input_count.get(self.cond_second_signal.get('name'))

        if self.cond_first_signal.get('name') == 'signal-everything':
            pass
        elif self.cond_first_signal.get('name') == 'signal-anything':
            pass
        elif self.cond_first_signal.get('name') == 'signal-each':
            pass
        else:
            test_value = input_count.get(self.cond_first_signal.get('name'))

            condition = str(test_value) + self.cond_comparator + str(compare_value)

            result = eval(condition)

            print('Evaluating {}: {}'.format(condition, result))

            if result:
                self.outputs[self.tick - 1] += ["Signal"]









class Arithmetic_Combinator(Connected_Entity):
    """Arithmetic combinator, given inputs and operation generates output"""
    
    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)
        self.direction = dictionary.get('direction')
        self.c_behavior = dictionary.get('control_behavior')
        self.connectIN = self.connect1
        self.connectOUT = self.connect2



class Factsimcmd():
    """Class holding all the Factsim simulation."""

    def __init__(self, filename=None):
        self.blueprint = open_blueprint(filename=filename)
        self.Entities = []
        self.bpEntities = []
        self.create_entities()

    def create_entities(self):
        """Parse the blueprint into objects. Fill the Entities list."""
        self.bpEntities = self.blueprint['blueprint']['entities']
        genericentities = [Entity(e) for e in self.bpEntities]
        for e in genericentities:
            if 'pole' in e.name.split('-') or e.name == 'substation':
                self.Entities += [Electric_pole(e.dictionary, self)]
            elif e.name == 'constant-combinator':
                self.Entities += [Constant_Combinator(e.dictionary, self)]
            elif e.name == 'decider-combinator':
                self.Entities += [Decider_Combinator(e.dictionary, self)]
            elif e.name == 'arithmetic-combinator':
                self.Entities += [Arithmetic_Combinator(e.dictionary, self)]
            else:
                self.Entities += [e]

    def get_entity(self, n):
        """Get an entity by number"""
        return self.Entities[n-1]

f = Factsimcmd()
