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
import logging
from functools import partial

VERSION = '0.0'

ORDER = ["signal-{}".format(n) for n in range(10)] + ["signal-{}".format(chr(n)) for n in range(65,91)] +\
        ["signal-red", "signal-green", "signal-blue", "signal-yellow", "signal-pink", "signal-cyan", "signal-white",
         "signal-grey", "signal-black", "signal-check", "signal-info", "signal-dot"]

def sig_sort(signal):
    """Helper function to order the signals"""
    if signal not in ORDER:
        ORDER.append(signal)
    return ORDER.index(signal)


def open_blueprint(filename=None):
    """Open a blueprint by filename or prompting the user for one.

    Return a dictionary of the blueprint contents
    """
    if not filename:
        root = tk.Tk()
        root.withdraw()
        filename = tkinter.filedialog.askopenfilename()
        print("opening: {} from filedialog".format(filename))
        root.destroy()
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

    def __eq__(self, other):
        if isinstance(other, Signal) and self.name == other.name and \
                self.kind == other.kind and self.count == other.count:
            return True
        else:
            return False

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
        return "{} - Network {}\n" \
               "    upstream:   {}\n" \
               "    downstream: {}\n" \
               "    poles:      {}".format(
                   self.color.capitalize(), self.nw_N, self.upstream, self.downstream, self.poles)


class Entity():
    """Generic Factsim entity.

    Generated from a entity dictionary from a blueprint
    """

    def __init__(self, dictionary):
        self.dictionary = dictionary
        self.entity_N = dictionary['entity_number']
        self.name = dictionary['name']
        self.position = dictionary['position']
        self.tick = 0
        self.inputs = [[]]
        self.outputs = [[]]

    def __str__(self):

        return 'Entity nr {:0>3d} - {}'.format(self.entity_N,  self.name)

    def label(self):

        return 'Entity nr {:0>3d} \n {}'.format(self.entity_N,  self.name)




class ConnectedEntity(Entity):
    """Any entity that can have connections"""

    def __init__(self, dictionary, simulation):
        super().__init__(dictionary)
        self.simulation = simulation
        self.connections = dictionary.get('connections')
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
        """Method to generate the output in the current tick with the inputs from the previous one."""
        print("WARNING!!!: entity {} is not implemented in the simulation".format(self))  # It it is not overriden
        self.outputs += [[]]

    def get_output(self, tick):
        """Get the output of an entity in desired tick.

        If necessary advance the entity enough to be able to retrieve the output"""

        while len(self.outputs) < tick + 1:
            self.advance()
        return self.outputs[tick]




class ElectricPole(ConnectedEntity):
    """Any pole of any size, is a subclass of ConnectedEntity."""

    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)
        self.inputs = [{'red': [], 'green': []}]
        self.outputs = [{'red': [], 'green': []}]

    def gather_input(self, tick):
        """Get the inputs seen by the pole in desired tick."""
        inputs = {'red': [], 'green': []}
        nwred = self.simulation.get_nw_with_pole(self.entity_N, 'red')
        nwgreen = self.simulation.get_nw_with_pole(self.entity_N, 'green')

        if nwred:
            for up in nwred.upstream:
                inputs['red'] += self.simulation.get_entity(up).get_output(tick)
        if nwgreen:
            for up in nwgreen.upstream:
                inputs['green'] += self.simulation.get_entity(up).get_output(tick)

        return inputs

    def advance(self):
        self.tick += 1
        self.inputs += [self.gather_input(self.tick)]
        input_count = {'red': {}, 'green': {}}

        for color in ('red', 'green'):
            for i in self.inputs[self.tick].get(color):
                logging.debug("checking .. {} in {} with color {}".format(i, self, color))
                if isinstance(i, Signal):
                    if i.name in input_count[color]:
                        input_count[color][i.name] += i.count
                    else:
                        input_count[color][i.name] = i.count

        self.outputs += [{'red': [], 'green': []}]
        for color in ('red', 'green'):
            self.outputs[self.tick][color] += [
                Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': count}) for name, count in
                input_count[color].items() if count != 0]


class Constant_Combinator(ConnectedEntity):
    """Constant combinator, outputs constant signal."""

    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)
        self.c_behavior = dictionary.get('control_behavior').get('filters')
        self.connectOUT = self.connect1
        self.outputs = [[Signal(con) for con in self.c_behavior]]

    def advance(self):
        self.tick += 1
        self.outputs += [[Signal(con) for con in self.c_behavior]]


class Pushbutton(Constant_Combinator):
    """Pulses a signal for one tick in tick nr 1"""

    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)
        self.outputs = [[], [Signal(con) for con in self.c_behavior]]

    def advance(self):
        self.tick += 1
        self.outputs += [[]]


class Lamp(ConnectedEntity):
    """Lamp that emits light depending on a condition"""

    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)
        self.connectIN = self.connect1
        self.c_behavior = dictionary.get('control_behavior').get('circuit_condition')
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
        # Initialize, so if there is output in tick 0 we get it
        self.advance()
        self.tick -= 1
        self.inputs = [self.inputs[1]]
        self.outputs = [self.outputs[1]]

    def gather_input(self, tick):
        """Get the inputs seen by the Lamp in desired tick."""
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
        self.inputs += [self.gather_input(self.tick)]
        self.tick += 1
        input_count = {}
        for i in self.inputs[self.tick]:
            logging.debug("checking .. {} in {}".format(i, self))
            if isinstance(i, Signal):
                if i.name in input_count:
                    input_count[i.name] += i.count
                else:
                    input_count[i.name] = i.count

        self.outputs += [{}]

        if not self.first_signal:
            return
        if self.constant != None:
            compare_value = self.constant
        elif self.second_signal:
            compare_value = input_count.get(
                self.second_signal.get('name'), 0)
        else:
            return

        logging.debug(
            'Evaluating {} {} {} in {}'.format(self.first_signal.get('name'), self.comparator, str(compare_value),
                                               self))
        if self.first_signal.get('name') == 'signal-everything':

            result = all([eval(str(c) + self.comparator + str(compare_value)) for c in input_count.values()])
            if result:
                self.outputs[self.tick] = {'light': 'ON', 'color': 'white'}       # no colors for now
            else:
                self.outputs[self.tick] = {'light': 'OFF', 'color': 'white'}

        elif self.first_signal.get('name') == 'signal-anything':

            result = any([eval(str(c) + self.comparator + str(compare_value)) for c in input_count.values()])
            if result:
                self.outputs[self.tick] = {'light': 'ON', 'color': 'white'}  # no colors for now
            else:
                self.outputs[self.tick] = {'light': 'OFF', 'color': 'white'}

        else:
            test_value = input_count.get(self.first_signal.get('name'), 0)

            condition = str(test_value) + self.comparator + str(compare_value)

            result = eval(condition)

            logging.debug('Evaluating {} = {}: {} in {}'.format(self.first_signal.get('name'), condition, result, self))

            if result:
                self.outputs[self.tick] = {'light': 'ON', 'color': 'white'}  # no colors for now
            else:
                self.outputs[self.tick] = {'light': 'OFF', 'color': 'white'}

class Combinator(ConnectedEntity):
    """Generic class for combinators with 2 attachments"""

    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)
        self.direction = dictionary.get('direction')
        self.c_behavior = dictionary.get('control_behavior')
        self.connectIN = self.connect1
        self.connectOUT = self.connect2

    def gather_input(self, tick):
        """Get the inputs seen by the combinator in desired tick."""
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
        self.output_signal = self.c_behavior.get('output_signal')
        self.copy_count = self.c_behavior.get('copy_count_from_input')
        self.comparator = self.c_behavior.get('comparator')
        if self.comparator == '=':
            self.comparator = '=='
        elif self.comparator == '≥':
            self.comparator = '>='
        elif self.comparator == '≤':
            self.comparator = '<='
        elif self.comparator == '≠':
            self.comparator = '!='
        # Initialize, so if there is output in tick 0 we get it
        self.advance()
        self.tick -= 1
        self.inputs = [self.inputs[1]]
        self.outputs = [self.outputs[1]]

    def advance(self):
        self.inputs += [self.gather_input(self.tick)]
        self.tick += 1
        input_count = {}
        for i in self.inputs[self.tick]:
            logging.debug("checking .. {} in {}".format(i, self))
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

        logging.debug(
            'Evaluating {} {} {} in {}'.format(self.first_signal.get('name'), self.comparator, str(compare_value), self))

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
                        if count != 0:
                            self.outputs[self.tick] += [
                                Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': count})]
                    else:
                        self.outputs[self.tick] += [
                            Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': 1})]


        elif self.first_signal.get('name') == 'signal-anything':

            result = any([eval(str(c) + self.comparator + str(compare_value)) for c in input_count.values()])
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
                elif self.output_signal.get('name') == 'signal-anything':
                    logging.warning('Using signal-anything in the output with non-vanilla signals can result \
                                    in a different output than inside the game as the ordering in-game is not \
                                    exported in the blueprint')
                    sorted_signals = sorted(input_count.keys(), key=lambda x: sig_sort(x))
                    name = sorted_signals[0]
                    if self.copy_count:
                        count = input_count.get(name, 0)
                    else:
                        count = 1
                    if count != 0:
                        self.outputs[self.tick] += [
                            Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': count})]

                else:
                    name = self.output_signal.get('name')
                    if self.copy_count:
                        count = input_count.get(name, 0)
                    else:
                        count = 1
                    if count != 0:
                        self.outputs[self.tick] += [
                            Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': count})]


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
                        if count != 0:
                            self.outputs[self.tick] += [Signal({'signal': {'name': name, 'type': 'virtual'},
                                                                'count': count})]

            else:
                count = 0
                for inp, c in input_count.items():
                    condition = str(c) + self.comparator + str(compare_value)
                    result = eval(condition)
                    if result:
                        count += c
                name = self.output_signal.get('name')
                if count != 0:
                    self.outputs[self.tick] += [Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': count})]



        else:
            test_value = input_count.get(self.first_signal.get('name'), 0)

            condition = str(test_value) + self.comparator + str(compare_value)

            result = eval(condition)

            logging.debug('Evaluating {} = {}: {} in {}'.format(self.first_signal.get('name'), condition, result, self))

            if result:
                name = self.output_signal.get('name')
                if self.copy_count:
                    count = input_count.get(name, 0)
                else:
                    count = 1
                if count != 0:
                    self.outputs[self.tick] += [Signal({'signal': {'name': name, 'type': 'virtual'}, 'count': count})]


class Arithmetic(Combinator):
    """Arithmetic combinator, given inputs and operation generates output"""
    
    def __init__(self, dictionary, simulation):
        super().__init__(dictionary, simulation)
        self.c_behavior = self.c_behavior.get('arithmetic_conditions')
        self.first_signal = self.c_behavior.get('first_signal')
        self.second_constant = self.c_behavior.get('second_constant')
        self.second_signal = self.c_behavior.get('second_signal')
        self.output_signal = self.c_behavior.get('output_signal')
        self.operation = self.c_behavior.get('operation')
        if self.operation == '^':
            self.operation = '**'
        elif self.operation == 'AND':
            self.operation = '&'
        elif self.operation == 'OR':
            self.operation = '|'
        elif self.operation == 'XOR':
            self.operation = '^'

    def advance(self):
        self.inputs += [self.gather_input(self.tick)]
        self.tick += 1
        input_count = {}
        for i in self.inputs[self.tick]:
            logging.debug("processing .. {} in {}".format(i, self))
            if isinstance(i, Signal):
                if i.name in input_count:
                    input_count[i.name] += i.count
                else:
                    input_count[i.name] = i.count

        self.outputs += [[]]

        if not self.first_signal or not self.output_signal:
            return

        if self.second_constant != None:
            second_term = self.second_constant
        elif self.second_signal:
            second_term = input_count.get(
                self.second_signal.get('name'), 0)
        else:
            return

        logging.debug(
            'Processing {} {} {} in {}'.format(self.first_signal.get('name'), self.operation, str(second_term), self))

        if self.first_signal.get('name') == 'signal-each':
            if self.output_signal.get('name') == 'signal-each':
                for inp, c in input_count.items():
                    operation = str(c) + self.operation + str(second_term)
                    result = int(eval(operation))
                    if result != 0:
                        name = inp
                        self.outputs[self.tick] += [Signal({'signal': {'name': name, 'type': 'virtual'},
                                                            'count': result})]

            else:
                name = self.output_signal.get('name')
                total = 0
                for inp, c in input_count.items():
                    operation = str(c) + self.operation + str(second_term)
                    result = int(eval(operation))
                    total += result

                if total != 0:
                    self.outputs[self.tick] += [Signal({'signal': {'name': name, 'type': 'virtual'},
                                                        'count': total})]

        else:
            first_term = input_count.get(self.first_signal.get('name'), 0)
            operation = str(first_term) + self.operation + str(second_term)
            result = eval(operation)
            if result != 0:
                name = self.output_signal.get('name')
                self.outputs[self.tick] += [Signal({'signal': {'name': name, 'type': 'virtual'},
                                                    'count': result})]


class Factsimcmd():
    """Class holding all the Factsim simulation."""

    def __init__(self, filename=None, loglevel=logging.ERROR):
        logging.basicConfig(level=loglevel)
        self.blueprint = open_blueprint(filename=filename)
        self.Entities = []
        self.bpEntities = []
        self.sim_tick = 0
        self.networks = {'red': [], 'green': []}
        self.create_entities()
        for c in ('red', 'green'):
            self.create_networks(c)
        self.normalize_coordinates()
        self.scale_coordinates(80)
        self.draw()


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
            elif 'lamp' in e.name.split('-'):
                self.Entities += [Lamp(e.dictionary, self)]
            elif e.name == 'pushbutton':
                self.Entities += [Pushbutton(e.dictionary, self)]
            else:
                self.Entities += [ConnectedEntity(e.dictionary, self)]

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

    def get_nw_with_pole(self, pole, color):
        for nw in self.networks.get(color):
            if pole in nw.poles:
                return nw

    def add_network(self, nw):
        color = nw.color
        existent_up = None
        existent_down = None
        for up in nw.upstream:
            existent_up = self.get_nw_with_upstream(up, color)
            if existent_up:
                for upstream in nw.upstream:
                    existent_up.include_upstream(upstream)
                for downstream in nw.downstream:
                    existent_up.include_downstream(downstream)

        for down in nw.downstream:
            existent_down = self.get_nw_with_downstream(down, color)
            if existent_down:
                for upstream in nw.upstream:
                    existent_down.include_upstream(upstream)
                for downstream in nw.downstream:
                    existent_down.include_downstream(downstream)
        existent = existent_up or existent_down
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
                    nw = self.get_nw_with_upstream(e, color)
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

            elif isinstance(e, Lamp):
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



    def get_entity(self, n):
        """Get an entity by number"""
        return self.Entities[n-1]

    def print_entities(self):
        """List all entities"""
        for e in self.Entities:
            print(e)

    def print_networks(self):
        """List all networks"""
        for nw in self.networks.get('red') + self.networks.get('green'):
            print(nw)


    def normalize_coordinates(self):
        xmin = 0
        ymin = 0
        for ent in self.Entities:
            x = ent.position['x']
            y = ent.position['y']
            xmin = min(xmin, x)
            ymin = min(ymin, y)
        for ent in self.Entities:
            ent.position['x'] -= xmin
            ent.position['y'] -= ymin

    def scale_coordinates(self, factor):
        for ent in self.Entities:
            ent.position['x'] *= factor
            ent.position['y'] *= factor



    def draw(self):
        """Draw a window with GUI to interact with the simulation"""
        root = tk.Tk()
        root.geometry('800x600')
        root.title('FactSim v{}'.format(VERSION))

        for i in range(3):
            root.columnconfigure(i, weight=1)
        root.rowconfigure(1, weight=1)

        def fwd_button_fn():
            self.sim_tick += 1
            current_tick_entry.delete(0, len(current_tick_entry.get()))
            current_tick_entry.insert(0, str(self.sim_tick))
            update_simulation()

        def bck_button_fn():
            if self.sim_tick > 1:
                self.sim_tick -= 1
            else:
                self.sim_tick = 1
            current_tick_entry.delete(0, len(current_tick_entry.get()))
            current_tick_entry.insert(0, str(self.sim_tick))
            update_simulation()

        def update_tick_fn(event):
            if current_tick_entry.get().isdigit():
                self.sim_tick = int(current_tick_entry.get())
            else:
                current_tick_entry.delete(0, len(current_tick_entry.get()))
                current_tick_entry.insert(0, str(self.sim_tick))
            update_simulation()

        def show_entity_info(entity):
            """Open a window and show the relevant information"""
            info_window = tk.Toplevel(root)
            info_window.geometry('400x500')
            info_window.title(ent.__str__())
            output = entity.outputs[self.sim_tick]
            if isinstance(entity, ElectricPole):
                text = tk.Label(info_window, text="{}\nTick nr. {}\nSignals passing:\n".format(entity, self.sim_tick) +
                                                  'Red:\n' + '\n'.join([str(i) for i in output['red']]) +
                                                  '\nGreen:\n' + '\n'.join([str(i) for i in output['green']]), justify=tk.LEFT)

            elif isinstance(entity, Lamp):
                text = tk.Label(info_window, text="{}\nTick nr. {}\nLight status: {}\nColour: {}".format(entity,
                                self.sim_tick, output['light'], output['color']))


            else:
                text = tk.Label(info_window, text="{}\nTick nr. {}\nOutput signals:\n".format(entity, self.sim_tick) +
                                                  '\n'.join([str(i) for i in output]), justify=tk.LEFT)
            text.pack()

        def update_simulation():
            for ent in self.Entities:
                ent.get_output(int(current_tick_entry.get()))

        fwd_button = tk.Button(root, text='+1 tick', command=fwd_button_fn)
        fwd_button.grid(row=2, column=2, sticky='e')
        bck_button = tk.Button(root, text='-1 tick', command=bck_button_fn)
        bck_button.grid(row=2, column=0, sticky='w')
        current_tick_entry = tk.Entry(root, width=5)
        current_tick_entry.grid(row=2, column=1)
        current_tick_entry.bind('<Return>', update_tick_fn)
        current_tick_entry.insert(0, str(self.sim_tick))
        window = tk.Frame(root, width=700, height=500)
        window.grid(row=1, column=1)
        display = tk.Canvas(window, bg='#FFFFFF', width=700, height=500)
        hbar = tk.Scrollbar(window, orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        hbar.config(command=display.xview)
        vbar = tk.Scrollbar(window, orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        vbar.config(command=display.yview)
        display.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        display.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        for ent in self.Entities:
            x = ent.position['x']
            y = ent.position['y']
            button = tk.Button(display, text=ent.label(), bg='gold', command=partial(show_entity_info, ent))
            display.create_window(x, y, window=button)

        fwd_button_fn()
        root.mainloop()


if __name__ == "__main__":
    f = Factsimcmd()
