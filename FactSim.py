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
from itertools import count


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


class Network():
    """abstraction for the connections"""
    _ids = count(1)

    def __init__(self, upstream=None, downstream=None, poles=None, color=None):
        self.nw_N = next(self._ids)
        self.upstream = upstream or []
        self.downstream = downstream or []
        self.poles = poles or []
        self.color = color

    @property
    def members(self):
        return self.upstream + self.downstream + self.poles

    def include_upstream(self, entitynr):
        if entitynr not in self.upstream:
            self.upstream += [entitynr]

    def include_downstream(self, entitynr):
        if entitynr not in self.downstream:
            self.downstream += [entitynr]

    def __str__(self):
        return "Network {}\n" \
               "    upstream:   {}\n" \
               "    downstream: {}\n" \
               "    poles:      {}".format(
                   self.nw_N, self.upstream, self.downstream, self.poles)


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


class ConnectedEntity(Entity):
    """Any entity that can have connections"""

    def __init__(self, dictionary, simulation):
        super().__init__(dictionary)
        self.simulation = simulation
        self.connections = dictionary.get('connections')
        self.tick = 0
        self.inputs = [[]]
        self.outputs = [[]]
        if self.connections:
            self.connect1 = self.connections.get(
                '1') or {'red': [], 'green': []}
            self.connect2 = self.connections.get(
                '2') or {'red': [], 'green': []}
        else:
            self.connect1 = {'red': [], 'green': []}
            self.connect2 = {'red': [], 'green': []}
        self.connectIN = None
        self.connectOUT = None

    def advance(self):
        raise NotImplementedError

    def get_output(self, tick):
        while len(self.outputs) < tick + 1:
            self.advance()
        return self.outputs[tick]


class ElectricPole(ConnectedEntity):
    """Any pole of any size, is a subclass of ConnectedEntity."""

    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)

    def advance(self):
        pass


class Constant_Combinator(ConnectedEntity):
    """Constant combinator, outputs constant signal."""

    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)
        self.direction = dictionary.get('direction')
        self.c_behavior = dictionary.get('control_behavior').get('filters')
        self.connectOUT = self.connect1
        self.outputs = [[Signal(f) for f in self.c_behavior]]

    def advance(self):
        self.tick += 1
        self.outputs += [[Signal(f) for f in self.c_behavior]]


class Combinator(ConnectedEntity):
    """Generic class for combinators with 2 attachments"""

    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)
        self.direction = dictionary.get('direction')
        self.c_behavior = dictionary.get('control_behavior')
        self.connectIN = self.connect1
        self.connectOUT = self.connect2

    def gather_input(self, tick):
        inputs = []
        nwred = self.simulation.get_nw_with_downstream(self.entity_N, 'red')
        nwgreen = self.simulation.get_nw_with_downstream(self.entity_N, 'green')

        if nwred:
            for up in nwred.upstream:
                inputs += self.simulation.get_entity(up).get_output(tick)
        if nwgreen:
            for up in nwgreen.upstream:
                inputs += self.simulation.get_entity(up).get_output(tick)

        return inputs

    def advance(self):
        raise NotImplementedError


class Decider(Combinator):
    """Decider combinator, given a condition decides if a signal must output"""
    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)
        self.c_behavior = self.c_behavior.get('decider_conditions')
        self.first_signal = self.c_behavior.get('first_signal')
        self.constant = self.c_behavior.get('constant')
        self.second_signal = self.c_behavior.get('second_signal')
        self.comparator = self.c_behavior.get('comparator')
        if self.comparator == '=':
            self.comparator = '=='
        elif self.comparator == '≥':
            self.comparator = '>='
        elif self.comparator == '≤':
            self.comparator = '<='
        elif self.comparator == '≠':
            self.comparator = '!='

        self.output_signal = self.c_behavior.get('output_signal')
        self.copy_count = self.c_behavior.get('copy_count_from_input')

    def advance(self):
        self.inputs += [self.gather_input(self.tick)]
        self.tick += 1
        input_count = {}
        for i in self.inputs[self.tick]:
            print("checking .. {}".format(i))
            if isinstance(i, Signal):
                if i.name in input_count:
                    input_count[i.name] += i.count
                else:
                    input_count[i.name] = i.count

        self.outputs += [[]]


        if not self.first_signal or not self.output_signal:
            return

        if self.constant != None:

            compare_value = self.constant

        elif self.second_signal:

            compare_value = input_count.get(
                self.second_signal.get('name'), 0)

        else:
            return

        if self.first_signal.get('name') == 'signal-everything':

            result = all([eval(str(c) + self.comparator + str(compare_value)) for c in input_count.values()])
            if result:
                if self.output_signal.get('name') == 'signal-everything':
                    if self.copy_count:
                        self.outputs[self.tick] += [
                            Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': count}) for name, count in
                            input_count.items() if count != 0]
                    else:
                        self.outputs[self.tick] += [
                            Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': 1}) for name in
                            input_count.keys()]
                else:
                    name = self.output_signal.get('name')
                    if self.copy_count:
                        count = input_count.get(name, 0)
                        if count > 0:
                            self.outputs[self.tick] += [
                                Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': count})]
                    else:
                        self.outputs[self.tick] += [
                            Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': 1})]


        elif self.first_signal.get('name') == 'signal-anything':
            pass

        
        elif self.first_signal.get('name') == 'signal-each':
            if self.output_signal.get('name') == 'signal-each':

                for inp, c in input_count.items():
                    condition = str(c) + self.comparator + str(compare_value)
                    result = eval(condition)
                    if result:
                        name = inp
                        if self.copy_count:
                            count = c
                        else:
                            count = 1
                        if count > 0:
                            self.outputs[self.tick] += [Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': count})]

            else:
                count = 0
                for inp, c in input_count.items():
                    condition = str(c) + self.comparator + str(compare_value)
                    result = eval(condition)
                    if result:
                        count += c
                name = self.output_signal.get('name')
                if count > 0:
                    self.outputs[self.tick] += [Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': count})]

        else:
            test_value = input_count.get(self.first_signal.get('name'), 0)

            condition = str(test_value) + self.comparator + str(compare_value)

            result = eval(condition)

            print('Evaluating {}: {}, {}'.format(condition, result, type(result)))

            if result:
                name = self.output_signal.get('name')
                if self.copy_count:
                    count = input_count.get(name, 0)
                else:
                    count = 1
                if count > 0:
                    self.outputs[self.tick] += [Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': count})]


class Arithmetic(Combinator):
    """Arithmetic combinator, given inputs and operation generates output"""
    
    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)


class Factsimcmd():
    """Class holding all the Factsim simulation."""

    def __init__(self, filename=None):
        self.blueprint = open_blueprint(filename=filename)
        self.Entities = []
        self.bpEntities = []
        self.networks = {'red': [], 'green': []}
        self.create_entities()
        for c in ('red', 'green'):
            self.create_networks(c)

    def create_entities(self):
        """Parse the blueprint into objects. Fill the Entities list."""
        self.bpEntities = self.blueprint['blueprint']['entities']
        genericentities = [Entity(e) for e in self.bpEntities]
        for e in genericentities:
            if 'pole' in e.name.split('-') or e.name == 'substation':
                self.Entities += [ElectricPole(e.dictionary, self)]
            elif e.name == 'constant-combinator':
                self.Entities += [Constant_Combinator(e.dictionary, self)]
            elif e.name == 'decider-combinator':
                self.Entities += [Decider(e.dictionary, self)]
            elif e.name == 'arithmetic-combinator':
                self.Entities += [Arithmetic(e.dictionary, self)]
            else:
                self.Entities += [e]

    def get_nw_for_Entity(self, entity, color):
        """get the network object that has entity as member"""
        for nw in self.networks.get(color):
            if entity in nw.members:
                return nw

    def get_nw_with_upstream(self, entityup, color):

        for nw in self.networks.get(color):
            if entityup in nw.upstream:
                return nw

    def get_nw_with_downstream(self, entitydown, color):
        for nw in self.networks.get(color):
            if entitydown in nw.downstream:
                return nw

    def add_network(self, nw):
        color = nw.color
        existent = None
        for up in nw.upstream:
            existent = self.get_nw_with_upstream(up, color)
            if existent:
                for upstream in nw.upstream:
                    existent.include_upstream(upstream)
                for downstream in nw.downstream:
                    existent.include_downstream(downstream)

        for down in nw.downstream:
            existent = self.get_nw_with_downstream(down, color)
            if existent:
                for upstream in nw.upstream:
                    existent.include_upstream(upstream)
                for downstream in nw.downstream:
                    existent.include_downstream(downstream)
        if not existent:
            self.networks[color] += [nw]

    def create_networks(self, color):
        """Create the networks"""
        # First we convert the poles
        done = []
        for e in self.Entities:
            if isinstance(e, ElectricPole):
                if e.connect1.get(color):
                    nw = self.get_nw_for_Entity(e, color)
                    if not nw:
                        nw = Network(poles=[e.entity_N], color=color)
                        self.networks[color] += [nw]
                    connections = e.connect1.get(color)
                    if connections:
                        for conn in connections:
                            ent_id = conn.get('entity_id')
                            side = conn.get('circuit_id')
                            ent = self.get_entity(ent_id)
                            if ent_id in done:
                                continue
                            if isinstance(ent, ElectricPole):
                                nw.poles += [ent_id]
                            elif isinstance(ent, Constant_Combinator):
                                nw.upstream += [ent_id]
                            elif side == 1:
                                nw.downstream += [ent_id]
                            elif side == 2:
                                nw.upstream += [ent_id]
                done += [e.entity_N]


        for e in self.Entities:
            if e.entity_N in done:
                continue
            if isinstance(e, Constant_Combinator):
                if e.connectOUT.get(color):
                    nw = self.get_nw_for_Entity(e, color)
                    if not nw:
                        nw = Network(upstream=[e.entity_N], color=color)
                    connections = e.connect1.get(color)
                    if connections:
                        for conn in connections:
                            ent_id = conn.get('entity_id')
                            side = conn.get('circuit_id')
                            ent = self.get_entity(ent_id)
                            if isinstance(ent, Constant_Combinator) or side == 2:
                                nw.include_upstream(ent_id)
                            elif side == 1:
                                nw.include_downstream(ent_id)
                    self.add_network(nw)


            elif isinstance(e, Combinator):

                if e.connectIN.get(color):
                    nw = self.get_nw_with_downstream(e.entity_N, color)
                    if not nw:
                        nw = Network(downstream=[e.entity_N], color=color)

                    for conn_in in e.connectIN.get(color):
                        ent_id = conn_in.get('entity_id')
                        side = conn_in.get('circuit_id')
                        ent = self.get_entity(ent_id)
                        if isinstance(ent, Constant_Combinator):
                            nw.include_upstream(ent_id)
                        elif side == 2:
                            nw.include_upstream(ent_id)
                        elif side == 1:
                            nw.include_downstream(ent_id)
                    self.add_network(nw)

                if e.connectOUT.get(color):
                    nw = self.get_nw_with_upstream(e.entity_N, color)
                    if not nw:
                        nw = Network(upstream=[e.entity_N], color=color)

                    for conn_out in e.connectOUT.get(color):
                        ent_id = conn_out.get('entity_id')
                        side = conn_out.get('circuit_id')
                        ent = self.get_entity(ent_id)
                        if isinstance(ent, Constant_Combinator):
                            nw.include_upstream(ent_id)
                        elif side == 2:
                            nw.include_upstream(ent_id)
                        elif side == 1:
                            nw.include_downstream(ent_id)
                    self.add_network(nw)


    def get_entity(self, n):
        """Get an entity by number"""
        return self.Entities[n-1]

f = Factsimcmd()

#print(f.get_entity(3).get_output(10))
#print(f.get_entity(4).get_output(10))
#print(f.get_entity(5).get_output(10))
#print(f.get_entity(7).get_output(10))
