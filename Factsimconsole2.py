# -*- coding: utf-8 -*-
#######################################################################
# This file is part of FACTSIM a simulator for Factorio
# circuit network entities.
#
# Python 2 version 0
#
# Copyright (C) 2017 Factsimguru (factsimguru-at-gmail-dot-com)
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
import Tkinter as tk
import tkFileDialog
import time



"""These are helper functions to extract the information from the blueprints"""

def parse1(data, istart=0, remove=0, sign=',', sep=('{', '}'), lvl=0):
    """A generic parser that walks the string searching for "sign" and 
    convert it to a list. The "sep" are taken into account so separated 
    values by sep inside brackets or braces are skipped"""

    opened = 0
    closed = 0
    result = []
    i = istart
    while i < len(data):
        if data[i] in sep[0]:
            opened += 1
        elif data[i] in sep[1]:
            closed += 1
        if (data[i] is sign) and (opened - closed == lvl):
            result += [str(data[istart: i])]
            istart = i + 1
            i = i + 1
        else:
            i += 1
    result += [data[istart: i - remove]]
    return result


def dictprop(prop, sep=':'):
    """Converts a string containing key-value pairs 
    separated by colon to a dictionary"""

    i = 0
    while i < len(prop):
        if prop[i] is sep:
            return {str(prop[1: i - 1]).strip('"'): str(prop[i + 1:]).strip('"')}
        i += 1


def parsedict(data, istart=0, remove=0, sign=',', sep=('{', '}'), lvl=0, sep2=':'):
    """Combines the parser and the dictionary maker to make dictionaries from complex strings"""

    result = {}
    pdata = parse1(data, istart=istart, remove=remove, sign=sign, sep=sep, lvl=lvl)
    for i in pdata:
        result.update(dictprop(i, sep=sep2))
    return result


def tupleEntCir(data):
    """Takes a string with entity and circuit id and converts it 
    to a tuple. Used for connections"""

    i = 0
    j = 0
    sep = ['}', ',']
    result =[]
    while '"entity_id":' in data:
        prov1 = ''
        prov2 = ''
        i = data.find('"entity_id":')
        i = i+12
        while data[i] not in sep:
            prov1 += data[i]
            i += 1
        prov1 = int (prov1)
        if '"circuit_id":' in data[i:]:
            j = data.find('"circuit_id":')
            j = j+13
            while data[j]not in sep:
                prov2 += data[j]
                j += 1
            prov2 = int(prov2)
        else:
            j = i
            prov2 = 0

        result += [(prov1, prov2)]
        data = data[j:]

    return result


def tupleSignal(signaldata):
    """Take data of a signal and returns a tuple with its type and name"""
    parsed = parsedict(signaldata, istart=1, remove=1)
    return (parsed['type'],parsed['name'])


def parseconnections(conndata):
    """This function will parse the connections for all the connected classes"""

    result = parsedict(conndata, istart=1, remove=1)
    for i in result.keys():
        prov1 = parsedict(result[i], istart=1, remove=1, sep=('[{', ']}'))
        result [i] = prov1
        for j in result[i].keys():
            result[i][j] = tupleEntCir(result[i][j])
    return result


def parsecontrolbeh(controldata, mode=''):
    """This function will parse the control behavior
     for the classes that request it"""

    if mode == 'const':
        result = parsedict(controldata, istart=1, remove=1, sep=('[{', ']}'))
        for i in result.keys():
            if i == 'filters':
                result[i] = parse1(result[i], istart=1, remove=1)
                for j in range(len(result[i])):
                    result[i][j] = parsedict(result[i][j], istart=1, remove=1)
                    result[i][j]['count'] = eval(result[i][j]['count'])
                    result[i][j]['index'] = eval(result[i][j]['index'])
                    result[i][j]['signal'] = tupleSignal(result[i][j]['signal'])
            if i == 'is_on':
                result[i] = eval(result[i].capitalize())
        return result
    else:
        result = parsedict(controldata, istart=1, remove=1)
        for i in result.keys():
            result[i] = parsedict(result[i], istart=1, remove=1)
        return result


"""Here the classes to operate the simulation are defined"""

class Entity(object):
    """Generic factsim entity, it will have a global unique id,
    the name as it is in factorio, and the properties, in string, list
    and dictionary types. It will be an atribute of the class created
    """

    def __init__(self, id):
        self.id = id
        self.name = ''
        self.rawproperties = ''
        self.prawproperties = []
        self.properties = {}
        self.proporder = []

    def __str__(self):

        return 'Entity nr ' + str(self.id) + ' - ' + self.name


class FactSignal(object):
    """The signal class is a list of dictionaries, each list member 
    will be the signal dictionary during that tick. It will support special methods
    to ease the operation respect to conventional lists or dicts"""

    def __init__(self):
        self.LoDSignal = [{}]

    def ontick(self, tick):
        """will return the signal dictionary for desired tick"""

        if tick > len(self.LoDSignal)-1:
            print 'error in tick'
            return
        else:
            return self.LoDSignal[tick]

    def merge(self, othersignal, tick):
        """will merge a dict(a FactSignal.ontick(tick) for example)
         with signals in the desired tick"""
        if tick > len(self.LoDSignal)-1:
            self.LoDSignal += [{}]
        dictsignal = self.LoDSignal[tick]
        for i in dictsignal.keys():
            if i in othersignal.keys():
                dictsignal[i] = dictsignal[i] + othersignal[i]
        for i in othersignal.keys():
            if i not in dictsignal.keys():
                dictsignal.update({i: othersignal[i]})
        self.LoDSignal[tick] = dictsignal


class Network(object):
    """Network object to ease getting the outputs and inputs for each step. In the 
    game it would be a  wire that connects some inputs and outputs together. At any 
    tick it just outputs what it inputs. It starts at t=-1 so initialise the first
    time it is called. It can be called from the factsimcmd or any output member"""

    __NR = 0

    def __init__(self, color):
        self.__class__.__NR += 1
        self.id = self.__class__.__NR
        self.FSignalIN = FactSignal()
        self.FSignalOUT = FactSignal()
        self.poles = []
        self.memberlist = {'IN': [], 'OUT': []}
        self.members = {'IN': {}, 'OUT': {}}
        self.busy = False
        self.tick = -1
        self.color = color

    def addIN(self, entid):
        if entid not in self.memberlist['IN']:
            self.memberlist['IN'] += [entid]

    def addOUT(self, entid):
        if entid not in self.memberlist['OUT']:
            self.memberlist['OUT'] += [entid]

    def getmembers(self, activedict):
        for i in self.memberlist.keys():
            self.members[i].update([(j, activedict[j]) for j in self.memberlist[i]])

    def getFactsimInput(self):
        pass

    def runFactsim(self):
        for i in self.members['IN'].values():
            self.FSignalOUT.merge(i.getFactsimOutput(self.tick), self.tick)
        self.FSignalOUT.merge({}, self.tick)

    def getFactsimOutput(self, tick):
        if tick < self.tick:
            return self.FSignalOUT.ontick(tick)
        elif tick == self.tick:
            while self.busy:
                pass
            return self.FSignalOUT.ontick(tick)
        elif tick == self.tick + 1:
            while self.busy:
                pass
            if not self.busy:
                self.busy = True
                self.tick += 1
                self.runFactsim()
                self.busy = False
                return self.FSignalOUT.ontick(tick)


class ConnEntity(object):
    """Entity that can be connected to other entities, it also manages the position. 
    It will implement the methods necessary to interact in the simulation """

    def __init__(self):
        """When a factsim class is created the part related to the 
        connections is delegated here. The SignalIN and OUT will keep the signals 
        during the simulation"""

        self.connections = parseconnections(self.Entity.properties['connections'])
        self.position = parsedict(self.Entity.properties['position'], istart=1, remove=1)
        for i in self.position.keys():
            self.position[i] = eval(self.position[i])
        self.FSignalIN = FactSignal()
        self.FSignalOUT = FactSignal()
        self.NW_In = {'red': 0, 'green': 0}
        self.NW_Out = {'red': 0, 'green': 0}
        self.tick = 0

    def getFactsimInput(self):
        for nw in self.NW_In.values():
            if nw != 0:
                self.FSignalIN.merge(nw.getFactsimOutput(self.tick-1), self.tick-1)

    def runFactsim(self):
        self.getFactsimInput()
        self.buildotputsignal()

    def getFactsimOutput(self, tick):

        if tick <= self.tick:
            return self.FSignalOUT.ontick(tick)

        elif tick == self.tick + 1:
            self.tick += 1
            self.runFactsim()
            return self.FSignalOUT.ontick(tick)


class Decider(ConnEntity):

    def __init__(self, entity):
        self.Entity = entity
        self.name = '{:25} - E{:4d}'.format(self.Entity.name, self.Entity.id)
        super(Decider, self).__init__()
        self.FSignalOUT.merge({}, self.tick)
        self.ccfInput = False
        self.constant = 0
        self.first_signal = ('','')
        self.second_signal = ('','')
        self.output_signal = ('','')
        self.comparator = '>'
        if 'control_behavior' in self.Entity.properties.keys():
            self.controlbehavior = parsecontrolbeh(self.Entity.properties['control_behavior'])
            for i in self.controlbehavior['decider_conditions'].keys():
                if i == 'copy_count_from_input':
                    self.ccfInput = eval(self.controlbehavior['decider_conditions'][i].capitalize())
                elif i == 'constant':
                    self.constant = eval(self.controlbehavior['decider_conditions'][i])
                elif i == 'first_signal':
                    self.first_signal = tupleSignal(self.controlbehavior['decider_conditions'].get(i))
                elif i == 'second_signal':
                    self.second_signal = tupleSignal(self.controlbehavior['decider_conditions'].get(i))
                elif i == 'output_signal':
                    self.output_signal = tupleSignal(self.controlbehavior['decider_conditions'].get(i))
                else:
                    self.__setattr__(i, self.controlbehavior['decider_conditions'].get(i))

            if self.comparator == '>' or self.comparator == '<':
                pass
            elif self.comparator == '=':
                self.comparator = '=='
            elif self.comparator == '≥':
                self.comparator = '>='
            elif self.comparator == '≤':
                self.comparator = '<='
            elif self.comparator == '≠':
                self.comparator = '!='

    def compare(self, first, second):
        test = eval(str(first)+self.comparator+str(second))
        return test

    def buildotputsignal(self):

        signalin = self.FSignalIN.ontick(self.tick-1)

        if self.first_signal[1] == 'signal-anything':
            if self.second_signal == ('',''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0
            for i in signalin.keys():
                if self.compare(signalin[i], secargument):
                    if self.output_signal[1] == 'signal-everything':
                        if self.ccfInput:
                            self.FSignalOUT.merge(signalin, self.tick)
                            return
                        else:
                            for k in signalin.keys():
                                self.FSignalOUT.merge({k: 1}, self.tick)
                            return
                    elif self.output_signal[1] in signalin.keys():
                        if self.ccfInput:
                            self.FSignalOUT.merge({self.output_signal[1]: signalin[self.output_signal[1]]}, self.tick)
                            return
                        else:
                            self.FSignalOUT.merge({self.output_signal[1]: 1}, self.tick)

                    else:
                        if not self.ccfInput:
                            self.FSignalOUT.merge({self.output_signal[1]: 1}, self.tick)
                        else:
                            self.FSignalOUT.merge({}, self.tick)
                            return
            self.FSignalOUT.merge({}, self.tick)
            return

        elif self.first_signal[1] == 'signal-everything':
            if self.second_signal == ('',''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0
            if len(signalin.keys()) > 0:
                for i in signalin.keys():
                    if self.compare(signalin[i], secargument):
                        pass
                    else:
                        self.FSignalOUT.merge({}, self.tick)
                        return
                    if self.output_signal[1] == 'signal-everything':
                        if self.ccfInput:
                            self.FSignalOUT.merge(signalin, self.tick)
                            return
                        else:
                            for k in signalin.keys():
                                self.FSignalOUT.merge({k: 1}, self.tick)
                            return
                    elif self.output_signal[1] in signalin.keys():
                        if self.ccfInput:
                            self.FSignalOUT.merge({self.output_signal[1]: signalin[self.output_signal[1]]}, self.tick)
                            return
                        else:
                            self.FSignalOUT.merge({self.output_signal[1]: 1}, self.tick)
                    else:
                        if self.output_signal != ('', ''):
                            if len(signalin.keys()) > 0:
                                for k in signalin.keys():
                                    if self.ccfInput:
                                        self.FSignalOUT.merge({self.output_signal[1]: signalin[k]}, self.tick)
                                    else:
                                        self.FSignalOUT.merge({self.output_signal[1]: 1}, self.tick)
                            else:
                                if not self.ccfInput:
                                    self.FSignalOUT.merge({self.output_signal[1]: 1}, self.tick)
                                else:
                                    self.FSignalOUT.merge({}, self.tick)
            elif self.compare(0, secargument):
                if self.output_signal[1] != 'signal-everything' and self.output_signal[1] != ('', ''):
                    if not self.ccfInput:
                        self.FSignalOUT.merge({self.output_signal[1]:1}, self.tick)
                    else:
                        self.FSignalOUT.merge({}, self.tick)
                else:
                    self.FSignalOUT.merge({}, self.tick)
            else:
                self.FSignalOUT.merge({}, self.tick)

        elif self.first_signal[1] == 'signal-each':
            if self.second_signal == ('', ''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0

            if self.output_signal[1] == 'signal-each':
                for i in signalin.keys():
                    if self.compare(signalin[i], secargument):
                        if self.ccfInput:
                            self.FSignalOUT.merge({i: signalin[i]}, self.tick)
                        else:
                            self.FSignalOUT.merge({i: 1}, self.tick)
                self.FSignalOUT.merge({}, self.tick)
                return

            else:
                for i in signalin.keys():
                    if self.compare(signalin[i], secargument):
                        if self.ccfInput:
                            self.FSignalOUT.merge({self.output_signal[1]: signalin[i]}, self.tick)
                        else:
                            self.FSignalOUT.merge({self.output_signal[1]: 1}, self.tick)

                self.FSignalOUT.merge({}, self.tick)
                return

        elif self.first_signal[1] in signalin.keys():
            firstargument = signalin[self.first_signal[1]]
            if self.second_signal == ('',''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0

            if self.compare(firstargument, secargument):
                if self.output_signal[1] == 'signal-everything':
                    if self.ccfInput:
                        self.FSignalOUT.merge(signalin, self.tick)
                        return
                    else:
                        for i in signalin.keys():
                            self.FSignalOUT.merge({i: 1}, self.tick)
                        return
                elif self.output_signal != ('', ''):
                    if self.ccfInput:
                        self.FSignalOUT.merge({self.output_signal[1]:
                                                   signalin.get(self.output_signal[1], 0)}, self.tick)
                        return
                    else:
                        self.FSignalOUT.merge({self.output_signal[1]: 1}, self.tick)
                        return
                else:
                    self.FSignalOUT.merge({}, self.tick)
                    return
            else:
                self.FSignalOUT.merge({}, self.tick)
                return

        else:
            self.FSignalOUT.merge({}, self.tick)
            return


class Arithmetic(ConnEntity):

    def __init__(self, entity):
        self.Entity = entity
        self.name = '{:25} - E{:4d}'.format(self.Entity.name, self.Entity.id)
        super(Arithmetic, self).__init__()
        self.FSignalOUT.merge({}, self.tick)
        self.constant = 0
        self.first_signal = ('', '')
        self.second_signal = ('', '')
        self.output_signal = ('', '')
        self.operation = '*'
        if 'control_behavior' in self.Entity.properties.keys():
            self.controlbehavior = parsecontrolbeh(self.Entity.properties['control_behavior'])
            for i in self.controlbehavior['arithmetic_conditions'].keys():
                if i == 'constant':
                    self.constant = eval(self.controlbehavior['arithmetic_conditions'][i])
                elif i == 'first_signal':
                    self.first_signal = tupleSignal(self.controlbehavior['arithmetic_conditions'].get(i))
                elif i == 'second_signal':
                    self.second_signal = tupleSignal(self.controlbehavior['arithmetic_conditions'].get(i))
                elif i == 'output_signal':
                    self.output_signal = tupleSignal(self.controlbehavior['arithmetic_conditions'].get(i))
                else:
                    self.__setattr__(i, self.controlbehavior['arithmetic_conditions'].get(i))

            noconv = ['+', '-', '*', '/', '<<', '>>', '%']
            if self.operation in noconv:
                pass
            elif self.operation == '^':
                self.operation = '**'
            elif self.operation == 'AND':
                self.operation = '&'
            elif self.operation == 'OR':
                self.operation = '|'
            elif self.operation == 'XOR':
                self.operation = '^'

    def compute(self, first, second):
        result = eval(str(first)+self.operation+str(second))
        return result


    def buildotputsignal(self):
        signalin = self.FSignalIN.ontick(self.tick-1)

        if self.first_signal[1] == 'signal-each':
            if self.second_signal == ('', ''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0

            if self.output_signal[1] == 'signal-each':
                for i in signalin.keys():
                    compval = self.compute(signalin[i], secargument)
                    if compval != 0:
                        self.FSignalOUT.merge({i: compval}, self.tick)
                self.FSignalOUT.merge({}, self.tick)
                return
            elif self.output_signal != ('', ''):
                for i in signalin.keys():
                    self.FSignalOUT.merge({self.output_signal[1]: self.compute(signalin[i], secargument)}, self.tick)
                self.FSignalOUT.merge({}, self.tick)
                return
            else:
                self.FSignalOUT.merge({}, self.tick)
                return

        elif self.first_signal[1] in signalin.keys():
            firstargument = signalin[self.first_signal[1]]
            if self.second_signal == ('', ''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0

            if self.output_signal[1] != ('', ''):
                self.FSignalOUT.merge({self.output_signal[1]: self.compute(firstargument, secargument)}, self.tick)
                return
            else:
                self.FSignalOUT.merge({}, self.tick)
                return

        else:
            self.FSignalOUT.merge({}, self.tick)
            return


class Constant(ConnEntity):

    def __init__(self, entity):
        self.Entity = entity
        self.is_on = True
        self.filters = []
        self.name = '{:25} - E{:4d}'.format(self.Entity.name, self.Entity.id)
        super(Constant, self).__init__()
        self.connections['2'] = self.connections.pop('1', {})  # to make them output
        if 'control_behavior' in self.Entity.properties.keys():
            self.controlbehavior = parsecontrolbeh(self.Entity.properties['control_behavior'], 'const')
            for i in self.controlbehavior.keys():
                    self.__setattr__(i, self.controlbehavior.get(i))
            self.FSignalOUT.merge({}, self.tick)
            self.was_on = [] + [self.is_on]


    def getFactsimInput(self):
        pass

    def runFactsim(self):
        for cb in self.controlbehavior.get('filters', []):
            if cb['count'] != 0:
                self.FSignalOUT.merge({cb['signal'][1]: cb['count']}, self.tick)
            else:
                self.FSignalOUT.merge({}, self.tick)
        self.FSignalOUT.merge({}, self.tick)


    def getFactsimOutput(self, tick):
        if tick <= self.tick:
            if self.was_on[tick]:
                return self.FSignalOUT.ontick(tick)
            else:
                return {}
        elif tick == self.tick + 1:
            self.tick += 1
            self.runFactsim()
            if self.is_on:
                self.was_on += [self.is_on]
                return self.FSignalOUT.ontick(tick)
            else:
                self.was_on += [self.is_on]
                return {}


class Lamp(ConnEntity):

    def __init__(self, entity):
        self.Entity = entity
        self.name = '{:25} - E{:4d}'.format(self.Entity.name, self.Entity.id)
        super(Lamp, self).__init__()
        self.FSignalOUT.merge({}, self.tick)
        self.constant = 0
        self.first_signal = ('', '')
        self.second_signal = ('', '')
        self.output_signal = ('', '')
        self.comparator = '>'
        if 'control_behavior' in self.Entity.properties.keys():
            self.controlbehavior = parsedict(self.Entity.properties['control_behavior'], istart=1, remove=1)
            self.controlbehavior['circuit_condition'] = parsedict(
                self.controlbehavior['circuit_condition'], istart=1, remove=1)
            if 'use_colors' in self.controlbehavior.keys():
                self.controlbehavior['use_colors'] = eval(self.controlbehavior['use_colors'].capitalize())
            for i in self.controlbehavior['circuit_condition'].keys():
                if i == 'constant':
                    self.constant = eval(self.controlbehavior['circuit_condition'][i])
                elif i == 'first_signal':
                    self.first_signal = tupleSignal(self.controlbehavior['circuit_condition'].get(i))
                elif i == 'second_signal':
                    self.second_signal = tupleSignal(self.controlbehavior['circuit_condition'].get(i))
                else:
                    self.__setattr__(i, self.controlbehavior['circuit_condition'].get(i))
        if self.comparator == '>' or self.comparator == '<':
            pass
        elif self.comparator == '=':
            self.comparator = '=='
        elif self.comparator == '≥':
            self.comparator = '>='
        elif self.comparator == '≤':
            self.comparator = '<='
        elif self.comparator == '≠':
            self.comparator = '!='

    def compare(self, first, second):
        test = eval(str(first)+self.comparator+str(second))
        return test

    def buildotputsignal(self):

        signalin = self.FSignalIN.ontick(self.tick-1)

        if self.first_signal[1] == 'signal-anything':
            if self.second_signal == ('', ''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0
            for i in signalin.keys():
                if self.compare(signalin[i], secargument):
                    self.FSignalOUT.merge({'lamp': 'on'}, self.tick)
            self.FSignalOUT.merge({'lamp': 'off'}, self.tick)
            return

        elif self.first_signal[1] == 'signal-everything':
            if self.second_signal == ('', ''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0
            for i in signalin.keys():
                if self.compare(signalin[i], secargument):
                    pass
                else:
                    self.FSignalOUT.merge({'lamp': 'off'}, self.tick)
                    return
            self.FSignalOUT.merge({'lamp': 'on'}, self.tick)

        elif self.first_signal[1] in signalin.keys():
            firstargument = signalin[self.first_signal[1]]
            if self.second_signal == ('',''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0

            if self.compare(firstargument, secargument):
                self.FSignalOUT.merge({'lamp': 'on'}, self.tick)
            else:
                self.FSignalOUT.merge({'lamp': 'off'}, self.tick)

        else:
            firstargument = 0
            if self.second_signal == ('',''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0

            if self.compare(firstargument, secargument):
                self.FSignalOUT.merge({'lamp': 'on'}, self.tick)
            else:
                self.FSignalOUT.merge({'lamp': 'off'}, self.tick)

class Pole(ConnEntity):

    def __init__(self, entity):
        self.Entity = entity
        self.name = '{:25} - E{:4d}'.format(self.Entity.name, self.Entity.id)
        super(Pole, self).__init__()


class Chest(Constant):

    def __init__(self, entity):
        entity.properties['control_behavior'] = '{"filters":[{"signal":{"type":"item",' \
                                                     '"name":"empty"},"count":0,"index":1}]}'
        super(Chest, self).__init__(entity)


class Inserter(ConnEntity):

    def __init__(self, entity):
        self.Entity = entity
        self.name = '{:25} - E{:4d}'.format(self.Entity.name, self.Entity.id)
        super(Inserter, self).__init__()
        self.FSignalOUT.merge({}, self.tick)
        self.constant = 0
        self.first_signal = ('', '')
        self.second_signal = ('', '')
        self.scontinput_signal = ('', '')
        self.comparator = '>'
        if 'control_behavior' in self.Entity.properties.keys():
            self.controlbehavior = parsecontrolbeh(self.Entity.properties['control_behavior'])
            for i in self.controlbehavior['circuit_condition'].keys():
                if i == 'constant':
                    self.constant = eval(self.controlbehavior['circuit_condition'][i])
                elif i == 'first_signal':
                    self.first_signal = tupleSignal(self.controlbehavior['circuit_condition'].get(i))
                elif i == 'second_signal':
                    self.second_signal = tupleSignal(self.controlbehavior['circuit_condition'].get(i))
                elif i == 'stack_control_input_signal':
                    self.scontinput_signal = tupleSignal(self.controlbehavior['circuit_condition'].get(i))
                else:
                    self.__setattr__(i, self.controlbehavior['circuit_condition'].get(i))
        if self.comparator == '>' or self.comparator == '<':
            pass
        elif self.comparator == '=':
            self.comparator = '=='
        elif self.comparator == '≥':
            self.comparator = '>='
        elif self.comparator == '≤':
            self.comparator = '<='
        elif self.comparator == '≠':
            self.comparator = '!='

    def compare(self, first, second):
        test = eval(str(first)+self.comparator+str(second))
        return test

    def buildotputsignal(self):

        signalin = self.FSignalIN.ontick(self.tick-1)

        if self.first_signal[1] == 'signal-anything':
            if self.second_signal == ('', ''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0
            for i in signalin.keys():
                if self.compare(signalin[i], secargument):
                    self.FSignalOUT.merge({'inserter': 'on'}, self.tick)
            self.FSignalOUT.merge({'inserter': 'off'}, self.tick)
            return

        elif self.first_signal[1] == 'signal-everything':
            if self.second_signal == ('', ''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0
            for i in signalin.keys():
                if self.compare(signalin[i], secargument):
                    pass
                else:
                    self.FSignalOUT.merge({'inserter': 'off'}, self.tick)
                    return
            self.FSignalOUT.merge({'inserter': 'on'}, self.tick)

        elif self.first_signal[1] in signalin.keys():
            firstargument = signalin[self.first_signal[1]]
            if self.second_signal == ('',''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0

            if self.compare(firstargument, secargument):
                self.FSignalOUT.merge({'inserter': 'on'}, self.tick)
            else:
                self.FSignalOUT.merge({'inserter': 'off'}, self.tick)

        else:
            self.FSignalOUT.merge({'inserter': 'off'}, self.tick)
            return


class SmarTrainStop(ConnEntity):

    def __init__(self, entity, proxy, cargo):
        self.Entity = entity
        self.proxy = STSProxy(proxy)
        self.cargo = STSProxycargo(cargo)
        self.name = '{:25} - E{:4d}'.format(self.Entity.name, self.Entity.id)
        super(SmarTrainStop, self).__init__()
        if 'control_behavior' in self.Entity.properties.keys():
            self.controlbehavior = parsecontrolbeh(self.Entity.properties['control_behavior'])

    def buildotputsignal(self):
        self.FSignalOUT.merge({}, self.tick)


class STSProxycargo(Constant):
    __count = 0
    def __init__(self, entity):
        self.__class__.__count += 1
        entity.properties['control_behavior'] = '{"filters":[{"signal":{"type":"virtual","name":' \
                                                '"signal-station-number"},"count":'+str(self.__class__.__count) + \
                                                ',"index":1}]}'

        super(STSProxycargo, self).__init__(entity)


class STSProxy(ConnEntity):

    def __init__(self, entity):
        self.Entity = entity
        self.name = '{:25} - E{:4d}'.format(self.Entity.name, self.Entity.id)
        super(STSProxy, self).__init__()
        self.constant = 0
        self.first_signal = ('', '')
        self.second_signal = ('', '')
        self.comparator = '>'
        if 'control_behavior' in self.Entity.properties.keys():
            self.controlbehavior = parsecontrolbeh(self.Entity.properties['control_behavior'])
            for i in self.controlbehavior['circuit_condition'].keys():
                if i == 'constant':
                    self.constant = eval(self.controlbehavior['circuit_condition'][i])
                elif i == 'first_signal':
                    self.first_signal = tupleSignal(self.controlbehavior['circuit_condition'].get(i))
                elif i == 'second_signal':
                    self.second_signal = tupleSignal(self.controlbehavior['circuit_condition'].get(i))
                else:
                    self.__setattr__(i, self.controlbehavior['circuit_condition'].get(i))

        if self.comparator == '>' or self.comparator == '<':
            pass
        elif self.comparator == '=':
            self.comparator = '=='
        elif self.comparator == '≥':
            self.comparator = '>='
        elif self.comparator == '≤':
            self.comparator = '<='
        elif self.comparator == '≠':
            self.comparator = '!='

    def compare(self, first, second):
        test = eval(str(first) + self.comparator + str(second))
        return test

    def buildotputsignal(self):

        signalin = self.FSignalIN.ontick(self.tick - 1)

        if self.first_signal[1] == 'signal-anything':
            if self.second_signal == ('', ''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0
            for i in signalin.keys():
                if self.compare(signalin[i], secargument):
                    self.FSignalOUT.merge({'STS': 'on'}, self.tick)
            self.FSignalOUT.merge({'STS': 'off'}, self.tick)
            return

        elif self.first_signal[1] == 'signal-everything':
            if self.second_signal == ('', ''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0
            for i in signalin.keys():
                if self.compare(signalin[i], secargument):
                    pass
                else:
                    self.FSignalOUT.merge({'STS': 'off'}, self.tick)
                    return
            self.FSignalOUT.merge({'STS': 'on'}, self.tick)

        elif self.first_signal[1] in signalin.keys():
            firstargument = signalin[self.first_signal[1]]
            if self.second_signal == ('', ''):
                secargument = self.constant
            elif self.second_signal[1] in signalin.keys():
                secargument = signalin[self.second_signal[1]]
            else:
                secargument = 0

            if self.compare(firstargument, secargument):
                self.FSignalOUT.merge({'STS': 'on'}, self.tick)
            else:
                self.FSignalOUT.merge({'STS': 'off'}, self.tick)

        else:
            self.FSignalOUT.merge({'STS': 'off'}, self.tick)
            return


class OtherCNE(object):
    __NR = 0

    def __init__(self, entity):
        self.__class__.__NR += 1
        self.Entity = entity
        self.name = 'other nr {} - {}'.format(self.__class__.__NR, self.Entity.name)


class Factsimcmd(object):
    '''The class that holds all the program'''

    def __init__(self):
        self.root = tk.Tk()
        self.bprintfile = file
        self.bprfilename = unicode
        self.todecodestr = str
        self.decoded_data = str
        self.bprintdata = str
        self.rawentities = str
        self.parsed_entities = []
        self.entity_count = int
        self.Entities = []
        self.CNEntities = []
        self.activeEntities = []
        self.poles = []
        self.poledict = {}
        self.activedict = {}
        self.haspoles = False
        self.Networks = {'red': {}, 'green': {}}
        self.globaltick = 0

    def openbpr(self):
        """Opens a blueprint file (you can paste blueprint string on a txt file)
        and creates all the entities and the factsim entities for the simulation"""
        self.root.withdraw()
        self.bprintfile = tkFileDialog.askopenfile()
        self.bprfilename = self.bprintfile.name
        print '\n{} opened\n'.format(self.bprfilename)
        self.todecodestr = self.bprintfile.read()
        self.todecodestr = self.todecodestr[1:]
        self.decoded_data = base64.b64decode(self.todecodestr)
        self.bprintdata = zlib.decompress(self.decoded_data)
        self.rawentities = self.getrwentities(self.bprintdata)
        self.parsed_entities = parse1(self.rawentities)
        self.entity_count = 0
        self.Entities = []
        for i in self.parsed_entities:
            self.entity_count += 1
            entitydata = parse1(i, istart=1, remove=1)
            currentEntity = Entity(self.entity_count)
            for j in entitydata:
                currentEntity.properties.update(dictprop(j))
                currentEntity.proporder += dictprop(j).keys()
            currentEntity.name = currentEntity.properties['name']
            currentEntity.rawproperties = i
            currentEntity.prawproperties = entitydata
            self.Entities += [currentEntity]

        self.CNEntities = self.getCNEntities()
        for i in self.CNEntities:
            if i.name == 'decider-combinator':
                self.activeEntities += [Decider(i)]
            elif i.name == 'arithmetic-combinator':
                self.activeEntities += [Arithmetic(i)]
            elif i.name == 'constant-combinator':
                self.activeEntities += [Constant(i)]
            elif 'lamp' in i.name:
                self.activeEntities += [Lamp(i)]
            elif ('pole'in i.name) or ('substation' in i.name):
                self.haspoles = True
                self.poles += [Pole(i)]
            elif 'chest' in i.name:
                self.activeEntities += [Chest(i)]
            elif 'inserter' in i.name:
                self.activeEntities += [Inserter(i)]
            elif i.name == 'smart-train-stop':
                self.activeEntities += [SmarTrainStop(i, self.getEntity(i.id-1),
                                                      self.getEntity(i.id - 2))]
                self.activeEntities = self.activeEntities[:-1] + [self.activeEntities[-1].cargo] \
                                      + self.activeEntities[-1:]
                self.activeEntities = self.activeEntities[:-1] + [self.activeEntities[-1].proxy] \
                                      + self.activeEntities[-1:]
            elif (i.name == 'smart-train-stop-proxy') or (i.name == 'smart-train-stop-proxy-cargo'):
                pass
            else:
                self.activeEntities += [OtherCNE(i)]
                print 'WARNING: non identified entity - {}'.format(self.activeEntities[-1].name)

        for i in self.activeEntities:
            self.activedict[i.Entity.id] = i
        for i in self.poles:
            self.poledict[i.Entity.id] = i

    def convertpoles(self, color):
        groups = {}
        for pole in self.poledict.values():
            connections = pole.connections.get('1', {})
            conn = connections.get(color, [])
            conn = [tup[0] for tup in conn]
            p = []
            for i in conn:
                if i in self.poledict.keys():
                    p += [i]
            conn = p

            if len(conn) > 0:
                for element in groups.iteritems():
                    if pole.Entity.id in element[1]:
                        for k in conn:
                            if k != element[0] and k not in groups[element[0]]:
                                groups[element[0]] += [k]
                        break
                    for n in conn:
                        if n in element[1]:
                            groups[element[0]] += [pole.Entity.id]
                            for k in conn:
                                if k != n:
                                    groups[element[0]] += [k]
                            break
                valuelist = []
                for i in groups.values():
                    valuelist += i
                if pole.Entity.id not in groups.keys() and pole.Entity.id not in valuelist:
                    groups.update({pole.Entity.id: conn})
            else:
                groups.update({pole.Entity.id: []})


        entities = self.activedict
        nws = self.Networks[color]
        newinst = True
        for net in groups.keys():
            if newinst:
                instance = Network(color)
            instance.poles = [net]
            instance.poles += groups[net]

            for ent in entities.keys():
                conIN = entities[ent].connections.get('1', {}).get(color, [])
                for i in conIN:
                    if i[0] in instance.poles:
                        newconn = []
                        for n in conIN:
                            if n[0] not in instance.poles:
                                newconn += [n]
                        instance.addOUT(ent)
                        entities[ent].NW_In[color] = instance.id
                        entities[ent].connections['1'][color] = newconn
                        break
                conOUT = entities[ent].connections.get('2', {}).get(color, [])
                for i in conOUT:
                    if i[0] in instance.poles:
                        newconn = []
                        for n in conOUT:
                            if n[0] not in instance.poles:
                                newconn += [n]
                        instance.addIN(ent)
                        entities[ent].NW_Out[color] = instance.id
                        entities[ent].connections['2'][color] = newconn
                        break
            expand = True
            while expand:
                expand=False
                for i in instance.memberlist['IN']:
                    conn = entities[i].connections.get('2', {}).get(color, [])
                    conn = [tup[0] for tup in conn]
                    for j in conn:
                        if i in [tup[0] for tup in entities[j].connections.get('2', {}).get(color, [])]:
                            instance.addIN(j)
                            if entities[j].NW_Out[color] == 0:
                                entities[j].NW_Out[color] = instance.id
                                expand = True
                        elif i in [tup[0] for tup in entities[j].connections.get('1', {}).get(color, [])]:
                            instance.addOUT(j)
                            if entities[j].NW_In[color] == 0:
                                entities[j].NW_In[color] = instance.id
                                expand = True
                        else:
                            print 'error creating network #{}'.format(instance.id)

                for i in instance.memberlist['OUT']:
                    conn = entities[i].connections.get('1', {}).get(color, [])
                    conn = [tup[0] for tup in conn]
                    for j in conn:
                        if i in [tup[0] for tup in entities[j].connections.get('2', {}).get(color, [])]:
                            instance.addIN(j)
                            if entities[j].NW_Out[color] == 0:
                                entities[j].NW_Out[color] = instance.id
                                expand = True
                        elif i in [tup[0] for tup in entities[j].connections.get('1', {}).get(color, [])]:
                            instance.addOUT(j)
                            if entities[j].NW_In[color] == 0:
                                entities[j].NW_In[color] = instance.id
                                expand = True
                        else:
                            print 'error creating network #{}'.format(instance.id)
            if len(instance.memberlist['IN']) == 0 and len(instance.memberlist['OUT']) == 0:
                newinst = False
            else:
                newinst = True
                nws.update({instance.id: instance})

    def buildNetworks(self, color):

        if self.haspoles:
            self.convertpoles(color)
        Networks = self.Networks[color]
        entities = self.activedict
        for i in entities.keys():
            if entities[i].NW_In[color] == 0:
                conINt = [tup for tup in entities[i].connections.get('1', {}).get(color, ())]
                if len(conINt) > 0:
                    conIN = [tup[0] for tup in conINt]
                    for j in conIN:
                        if i in [tup[0] for tup in entities[j].connections.get('2', {}).get(color, ())]:
                            if entities[j].NW_Out[color] != 0:
                                nwid = entities[j].NW_Out[color]
                                entities[i].NW_In[color] = nwid
                                Networks[nwid].addOUT(i)
                    if entities[i].NW_In[color] == 0:
                        for j in conIN:
                            if i in [tup[0] for tup in entities[j].connections.get('1', {}).get(color, ())]:
                                if entities[j].NW_In[color] != 0:
                                    nwid = entities[j].NW_In[color]
                                    entities[i].NW_In[color] = nwid
                                    Networks[nwid].addOUT(i)

                    if entities[i].NW_In[color] == 0:
                        for j in conINt:
                            if j[1] == 2:
                                if entities[j[0]].NW_Out[color] != 0:
                                    nwid = entities[j[0]].NW_Out[color]
                                    entities[i].NW_In[color] = nwid
                                    Networks[nwid].addOUT(i)
                            elif j[1] == 1:
                                if entities[j[0]].NW_In[color] != 0:
                                    nwid = entities[j[0]].NW_In[color]
                                    entities[i].NW_In[color] = nwid
                                    Networks[nwid].addOUT(i)

                    if entities[i].NW_In[color] == 0:
                        instance = Network(color)
                        instance.addOUT(i)
                        entities[i].NW_In[color] = instance.id
                        for j in conIN:
                            if i in [tup[0] for tup in entities[j].connections.get('2', {}).get(color, ())]:
                                instance.addIN(j)
                                entities[j].NW_Out[color] = instance.id
                            if i in [tup[0] for tup in entities[j].connections.get('1', {}).get(color, ())]:
                                instance.addOUT(j)
                                entities[j].NW_In[color] = instance.id
                        expand = True
                        while expand:
                            expand = False
                            for i in instance.memberlist['IN']:
                                conn = entities[i].connections.get('2', {}).get(color, [])
                                conn = [tup[0] for tup in conn]
                                for j in conn:
                                    if i in [tup[0] for tup in entities[j].connections.get('2', {}).get(color, [])]:
                                        instance.addIN(j)
                                        if entities[j].NW_Out[color] == 0:
                                            entities[j].NW_Out[color] = instance.id
                                            expand = True
                                    elif i in [tup[0] for tup in entities[j].connections.get('1', {}).get(color, [])]:
                                        instance.addOUT(j)
                                        if entities[j].NW_In[color] == 0:
                                            entities[j].NW_In[color] = instance.id
                                            expand = True
                                    else:
                                        print 'error creating network #{}'.format(instance.id)

                            for i in instance.memberlist['OUT']:
                                conn = entities[i].connections.get('1', {}).get(color, [])
                                conn = [tup[0] for tup in conn]
                                for j in conn:
                                    if i in [tup[0] for tup in entities[j].connections.get('2', {}).get(color, [])]:
                                        instance.addIN(j)
                                        if entities[j].NW_Out[color] == 0:
                                            entities[j].NW_Out[color] = instance.id
                                            expand = True
                                    elif i in [tup[0] for tup in entities[j].connections.get('1', {}).get(color, [])]:
                                        instance.addOUT(j)
                                        if entities[j].NW_In[color] == 0:
                                            entities[j].NW_In[color] = instance.id
                                            expand = True
                                    else:
                                        print 'error creating network #{}'.format(instance.id)


                        Networks.update({instance.id: instance})


            if entities[i].NW_Out[color] == 0:
                conOUTt = [tup for tup in entities[i].connections.get('2', {}).get(color, ())]
                if len(conOUTt) > 0:
                    conOUT = [tup[0] for tup in conOUTt]
                    for j in conOUT:
                        if i in [tup[0] for tup in entities[j].connections.get('1', {}).get(color, ())]:
                            if entities[j].NW_In[color] != 0:
                                nwid = entities[j].NW_In[color]
                                entities[i].NW_Out[color] = nwid
                                Networks[nwid].addIN(i)
                    if entities[i].NW_Out[color] == 0:
                        for j in conOUT:
                            if i in [tup[0] for tup in entities[j].connections.get('2', {}).get(color, ())]:
                                if entities[j].NW_Out[color] != 0:
                                    nwid = entities[j].NW_Out[color]
                                    entities[i].NW_Out[color] = nwid
                                    Networks[nwid].addIN(i)

                    if entities[i].NW_Out[color] == 0:
                        for j in conOUTt:
                            if j[1]== 1:
                                if entities[j[0]].NW_In[color] != 0:
                                    nwid = entities[j[0]].NW_In[color]
                                    entities[i].NW_Out[color] = nwid
                                    Networks[nwid].addIN(i)
                            elif j[1] == 2:
                                if entities[j[0]].NW_Out[color] != 0:
                                    nwid = entities[j[0]].NW_Out[color]
                                    entities[i].NW_Out[color] = nwid
                                    Networks[nwid].addIN(i)

                    if entities[i].NW_Out[color] == 0:
                        instance = Network(color)
                        instance.addIN(i)
                        entities[i].NW_Out[color] = instance.id
                        for j in conOUT:
                            if i in [tup[0] for tup in entities[j].connections.get('1', {}).get(color, ())]:
                                instance.addOUT(j)
                                entities[j].NW_In[color] = instance.id
                            if i in [tup[0] for tup in entities[j].connections.get('2', {}).get(color, ())]:
                                instance.addIN(j)
                                entities[j].NW_Out[color] = instance.id
                        expand = True
                        while expand:
                            expand = False
                            for i in instance.memberlist['IN']:
                                conn = entities[i].connections.get('2', {}).get(color, [])
                                conn = [tup[0] for tup in conn]
                                for j in conn:
                                    if i in [tup[0] for tup in entities[j].connections.get('2', {}).get(color, [])]:
                                        instance.addIN(j)
                                        if entities[j].NW_Out[color] == 0:
                                            entities[j].NW_Out[color] = instance.id
                                            expand = True
                                    elif i in [tup[0] for tup in entities[j].connections.get('1', {}).get(color, [])]:
                                        instance.addOUT(j)
                                        if entities[j].NW_In[color] == 0:
                                            entities[j].NW_In[color] = instance.id
                                            expand = True
                                    else:
                                        print 'error creating network #{}'.format(instance.id)

                            for i in instance.memberlist['OUT']:
                                conn = entities[i].connections.get('1', {}).get(color, [])
                                conn = [tup[0] for tup in conn]
                                for j in conn:
                                    if i in [tup[0] for tup in entities[j].connections.get('2', {}).get(color, [])]:
                                        instance.addIN(j)
                                        if entities[j].NW_Out[color] == 0:
                                            entities[j].NW_Out[color] = instance.id
                                            expand = True
                                    elif i in [tup[0] for tup in entities[j].connections.get('1', {}).get(color, [])]:
                                        instance.addOUT(j)
                                        if entities[j].NW_In[color] == 0:
                                            entities[j].NW_In[color] = instance.id
                                            expand = True
                                    else:
                                        print 'error creating network #{}'.format(instance.id)
                        Networks.update({instance.id: instance})

        for j in Networks.keys():
            Networks[j].getmembers(entities)
        for ent in entities.values():
            if ent.NW_In[color] != 0:
                ent.NW_In[color] = Networks[ent.NW_In[color]]
            if ent.NW_Out[color] != 0:
                ent.NW_Out[color] = Networks[ent.NW_Out[color]]

    def printNetworks(self):
        for i in self.Networks.keys():
            print '{} Networks'.format(i)
            for j in self.Networks[i].keys():
                print 'Network {} - List of members In  {}'.format(j, self.Networks[i][j].memberlist.get('IN'))
                print '            List of members Out {}'.format(self.Networks[i][j].memberlist.get('OUT'))
                print '            members In  {}'.format([member.Entity.id for member in
                                                                    self.Networks[i][j].members.get('IN').values()])
                print '            members Out {}'.format([member.Entity.id for member in
                                                                    self.Networks[i][j].members.get('OUT').values()])

    def setupsim(self):
        self.buildNetworks('red')
        self.buildNetworks('green')

    def runsim(self, nticks):
        """To run the simulation, the networks will be solved first, then all the connected entities"""
        end = nticks + self.globaltick
        while self.globaltick <= end:
            for i in self.Networks.keys():
                for j in self.Networks[i].keys():
                    self.Networks[i][j].getFactsimOutput(self.globaltick)
            for i in self.activedict.values():
                if i.tick < self.globaltick:
                    i.getFactsimOutput(self.globaltick)
            self.globaltick += 1
        self.globaltick -= 1

    def printresults(self, t=('', ''), e=True, n=False):
        if t == ('', ''):
            t = (0, self.globaltick)
        if e:
            print '########################################\n'+\
                  'Entities activity during simulation\n'+\
                  '########################################\n'
            print '|{:40}'.format('OUTPUT'),
            w = 50
            for time in range(t[0], t[1]):
                dt = '{:04d}'.format(time)
                print '|'+'{:^{w}}'.format(dt,w=w),
            print '|'
            for ent in self.activeEntities:
                print '|{:40}'.format(ent.name),
                for time in range(t[0], t[1]):
                    print '|'+'{:^{w}}'.format(ent.getFactsimOutput(time), w=w),
                print '|'

            print '---------------------------------------------------------------'
            print '|{:40}'.format('INPUT'),
            for time in range(t[0], t[1]):
                dt = '{:04d}'.format(time)
                print '|'+'{:^{w}}'.format(dt, w=w),
            print '|'
            for ent in self.activeEntities:
                onlyOUT = 'constant' in ent.name or 'cargo' in ent.name or 'chest' in ent.name
                if not onlyOUT and ent.name is not None:
                    print '|{:40}'.format(ent.name),
                    for time in range(t[0], t[1]-1):
                        print '|'+'{:^{w}}'.format(ent.FSignalIN.ontick(time), w=w),
                    print '|'

        if n:
            print '########################################\n'+\
                  'Network output during simulation\n'+\
                  '########################################\n'
            print '|{:40}'.format(''),
            w = 50
            for time in range(t[0], t[1]):
                dt = '{:04d}'.format(time)
                print '|'+'{:^{w}}'.format(dt,w=w),
            print '|'
            for color in self.Networks.keys():
                for nw in self.Networks[color].values():
                    aux = '|Factsim Network        N{:04d}'.format(nw.id)
                    print aux + '{}'.format(' '*(41-len(aux))),
                    for time in range(t[0], t[1]):
                        print '|'+'{:^{w}}'.format(nw.getFactsimOutput(time), w=w),
                    print '|'

    def writeresults(self, t=('', ''), e=True, n=True, efilters=(), nfilters = ()):

        name = self.bprfilename[:-4] + '-results.txt'
        rsf = open(name, 'w')
        if t == ('', ''):
            t = (0, self.globaltick)
        if e:
            print >> rsf, '########################################\n'+\
                  'Entities activity during simulation\n'+\
                  '########################################\n'
            print >> rsf, '|{:40}'.format('OUTPUT'),
            w = 50
            for time in range(t[0], t[1]):
                dt = '{:04d}'.format(time)
                print >> rsf, '|'+'{:^{w}}'.format(dt,w=w),
            print >> rsf, '|'

            for ent in self.activeEntities:
                print >> rsf,'|{:40}'.format(ent.name),
                for time in range(t[0], t[1]):
                    print >> rsf, '|'+'{:^{w}}'.format(ent.getFactsimOutput(time), w=w),
                print >> rsf, '|'

            print >> rsf, '---------------------------------------------------------------'
            print >> rsf, '|{:40}'.format('INPUT'),
            for time in range(t[0], t[1]):
                dt = '{:04d}'.format(time)
                print >> rsf, '|'+'{:^{w}}'.format(dt, w=w),
            print >> rsf, '|'
            for ent in self.activeEntities:
                onlyOUT = 'constant' in ent.name or 'cargo' in ent.name or 'chest' in ent.name
                if not onlyOUT and ent.name is not None:
                    print >> rsf, '|{:40}'.format(ent.name),
                    for time in range(t[0], t[1]-1):
                        print >> rsf, '|'+'{:^{w}}'.format(ent.FSignalIN.ontick(time), w=w),
                    print >> rsf, '|'

        if n:
            print >> rsf, '########################################\n'+\
                  'Network output during simulation\n'+\
                  '########################################\n'
            print >> rsf, '|{:40}'.format(''),
            w = 50
            for time in range(t[0], t[1]):
                dt = '{:04d}'.format(time)
                print >> rsf, '|'+'{:^{w}}'.format(dt,w=w),
            print >> rsf, '|'
            for color in self.Networks.keys():
                for nw in self.Networks[color].values():
                    aux = '|Factsim Network        N{:04d}'.format(nw.id)
                    print >> rsf, aux + '{}'.format(' '*(41-len(aux))),
                    for time in range(t[0], t[1]):
                        print >> rsf, '|'+'{:^{w}}'.format(nw.getFactsimOutput(time), w=w),
                    print >> rsf, '|'
        rsf.close()

    def printreport(self):

        print '###############################\n' +\
              '  Statistics of the model run\n' + \
              '###############################\n'
        countpnw = 0
        out_of_tick = 0
        for i in self.Networks['red'].values():
            if len(i.poles) > 0:
                countpnw += 1
            if i.tick < self.globaltick:
                out_of_tick += 1
        for i in self.Networks['green'].values():
            if len(i.poles) > 0:
                countpnw += 1
            if i.tick < self.globaltick:
                out_of_tick += 1
        totalnw = len(self.Networks['red'].values()) + len(self.Networks['green'].values())
        print '{:04d} networks created from poles'.format(countpnw)
        print '{:04d} total networks created'.format(totalnw)
        if out_of_tick > 0:
            print '{:04d} networks out of tick'.format(out_of_tick)

        nonwin = []
        nonwout = []
        constn = 0
        aritm = 0
        decid = 0
        for i in self.activedict.keys():
            if self.activedict[i].NW_In['red'] == 0 and self.activedict[i].NW_In['green'] == 0:
                if 'constant' not in self.activedict[i].name:
                    nonwin += [i]
            if self.activedict[i].NW_Out['red'] == 0 and self.activedict[i].NW_Out['green'] == 0:
                nonwout += [i]
            if 'constant' in self.activedict[i].name:
                constn += 1
            elif 'arithmetic' in self.activedict[i].name:
                aritm += 1
            elif 'decider' in self.activedict[i].name:
                decid += 1
        print '{:04d} Active entities'.format(len(self.activeEntities))
        print '{:04d} Decider combinators'.format(decid)
        print '{:04d} Arithmetic combinators'.format(aritm)
        print '{:04d} Constant combinators'.format(constn)
        print '{:04d} entities with no input {}'.format(len(nonwin), nonwin)
        print '{:04d} entities with no output {}'.format(len(nonwout), nonwout)



    def getrwentities(self, data):
        opened = 0
        closed = 0
        istart = data.find('entities') + 11
        i = data.find('entities') + 10
        while i < len(data):
            if data[i] is '[':
                opened += 1
            elif data[i] is ']':
                closed += 1
            if opened == closed:
                return data[istart:i]
            else:
                i += 1

    def printallEntities(self):
        for i in self.Entities:
            print i
            print i.proporder
            print i.properties

    def getEntity(self, pos):
        return self.Entities[pos-1]

    def getCNEntities(self):
        result = []
        for i in self.Entities:
            if 'connections' in i.properties.keys():
                result += [i]
        return result

    def getActiveEntities(self):
        result = []
        for i in self.activeEntities:
            result += [i.Entity.id]
        return result


factsim = Factsimcmd()
factsim.openbpr()
start_time = time.time()
factsim.printallEntities()

print '\n'+'##################################################'+'\n'
CNE = factsim.activeEntities
for i in CNE:
    print i.name
    print i.connections
    if hasattr(i, 'controlbehavior'):
        print i.controlbehavior
factsim.setupsim()

factsim.printNetworks()

'''
for i in factsim.activedict.values():
    if 'constant' in i.name:
        i.is_on = True
'''

factsim.runsim(1000)

'''
for i in factsim.activedict.values():
    if 'constant' in i.name:
        i.is_on = False
factsim.runsim(10)
for i in factsim.activedict.values():
    if 'constant' in i.name:
        i.is_on = True
factsim.runsim(20)
for i in factsim.activedict.values():
    if 'constant' in i.name:
        i.is_on = False
factsim.runsim(10)
for i in factsim.activedict.values():
    if 'constant' in i.name:
        i.is_on = True
factsim.runsim(20)


factsim.printresults(n=True)
'''

factsim.writeresults()

factsim.printreport()

if __name__ == '__main__':
    print '-------------------------------------------'
    print '                                           '
    print("--- %s seconds ---" % (time.time() - start_time))
