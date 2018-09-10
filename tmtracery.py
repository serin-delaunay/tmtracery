import argparse
import json
from typing import NamedTuple, Set, Dict, Tuple
from enum import Enum
from itertools import product
from collections import OrderedDict

# Forward, Back, Stay
directions = "><_"
# Tracery special characters, JSON special characters, CBDQ special characters, and *
reserved_characters = '[],{}#"*\n \t'

class StateSymbol(NamedTuple):
    """
    Next action of a Turing machine depends only on current state and symbol under tape head
    """
    state: str
    symbol: str
    def code(self):
        return '*{0}*{1}'.format(self.state, self.symbol)

class Action(NamedTuple):
    """
    Depending on state and symbol, the action can be to transition to any state, write any symbol under the tape head, and optionally move in either direction.
    """
    state: str
    symbol: str
    direction: str
    def code(self, accept, reject):
        if self.state == accept or self.state == reject:
            run_next = ""
        else:
            run_next = "[run_next:#activate_next#]"
        return "[state:{0}][tape_right:POP][tape_right:{1}][direction:{2}]{3}".format(self.state, self.symbol, self.direction, run_next)

TransitionFunction = Dict[StateSymbol, Action]

class TuringMachine(NamedTuple):
    states: Set[str]
    symbols: Set[str]
    blank_symbol: str
    start_state: str
    accept_state: str
    reject_state: str
    delta: TransitionFunction
    
    @classmethod
    def from_json(cls, mj):
        states = set(mj['states'])
        assert len(states) == len(mj['states']), "State names not unique"
        symbols = set(mj['symbols'])
        assert len(symbols) == len(mj['symbols']), "Symbols not unique"
        delta = {StateSymbol(*state_symbol): Action(*action) for (state_symbol, action) in mj['delta']}
        assert len(delta) == len(mj['delta'])
        return TuringMachine(states, symbols, mj['blank_symbol'], mj['start_state'], mj['accept_state'], mj['reject_state'], delta)
    
    def validate(self):
        for state in self.states:
            assert self.string_is_valid(state), 'state name "{}" contains reserved character'.format(state)
        for symbol in self.symbols:
            assert self.symbol_is_valid(symbol), 'symbol "{}" is reserved'.format(symbol)
        assert len(self.blank_symbol) == 1, 'blank symbol "{}" must be a single symbol'.format(self.blank_symbol)
        assert self.blank_symbol in self.symbols, 'blank symbol "{}" not in symbols'.format(self.blank_symbol)
        assert self.start_state in self.states, 'start state "{}" not in states'.format(self.start_state)
        assert self.accept_state in self.states, 'accept state "{}" not in states'.format(self.accept_state)
        assert self.reject_state in self.states, 'reject state "{}" not in states'.format(self.reject_state)
        for (state_symbol, action)  in self.delta.items():
            assert state_symbol.state in self.states, 'transition starts in nonexistent state "{}"'.format(state_symbol.state)
            assert state_symbol.symbol in self.symbols, 'transition requires nonexistent symbol "{}"'.format(state_symbol.symbol)
            assert state_symbol.state != self.accept_state, 'transition starts in accepting state "{}"'.format(state_symbol.state)
            assert state_symbol.state != self.reject_state, 'transition starts in rejecting state "{}"'.format(state_symbol.state)
            assert action.state in self.states, 'transition goes to nonexistent state "{}"'.format(action.state)
            assert action.symbol in self.symbols, 'transition writes nonexistent symbol "{}"'.format(action.symbol)
            assert action.direction in directions, 'transition goes in invalid direction "{}"'.format(action.direction)
        return True
        
    
    @staticmethod
    def string_is_valid(string):
        return all(c  not in string for c in reserved_characters)
    
    @staticmethod
    def symbol_is_valid(symbol):
        return len(symbol) == 1 and symbol not in reserved_characters
    
    def as_tracery(self):
        raise NotImplemented

def validate_input(machine, input):
    for symbol in input:
        assert symbol in machine.symbols

def main():
    parser = argparse.ArgumentParser(description='Compile Turing machines to Tracery grammars.')
    parser.add_argument('machine', type=str,
                        help='the Turing machine to compile')
    parser.add_argument('--input', metavar='i', type=str,
                        help='optional input tape file for the machine')
    parser.add_argument('--output', metavar='o', type=str,
                        help='optional output filename')
    parser.add_argument('--verbose', dest='verbose', action='store_true')
    parser.set_defaults(verbose=False)
    args = parser.parse_args()
    with open(args.machine) as machine_file:
        machine_json = json.load(machine_file)
    if args.input is not None:
        with open(args.input) as input_file:
            input = input_file.read()
    else:
        input = ""
    if args.output is not None:
        out_filename = args.output
    else:
        out_filename = args.machine+'.tracery.json'
    
    machine = TuringMachine.from_json(machine_json)
    machine.validate()
    validate_input(machine, input)
    with open('tmtracery.json') as tracery_base_file:
        machine_tracery = json.load(tracery_base_file, object_pairs_hook=OrderedDict)
    machine_tracery['init_tape'] = ''.join('[tape_right:{}]'.format(symbol) for symbol in reversed(input))
    machine_tracery['init_state'] = "[state:{}]".format(machine.start_state)
    if args.verbose:
        machine_tracery['run'] = "#state##tape_right# " + machine_tracery['run']
        for k,v in machine_tracery.items():
            if 'activate' not in k and not k.startswith('tape'):
                machine_tracery[k] = "\n*{}*".format(k) + v
    machine_tracery['blank'] = machine.blank_symbol
    for symbol in machine.symbols:
        machine_tracery["padder_left{}".format(symbol)] = ""
        machine_tracery["padder_right{}".format(symbol)] = ""
    for state in machine.states:
        if state == machine.accept_state:
            continue
        if state == machine.reject_state:
            continue
        for symbol in machine.symbols:
            state_symbol = StateSymbol(state, symbol)
            machine_tracery[state_symbol.code()] = machine.delta[state_symbol].code(machine.accept_state, machine.reject_state)
    with open(out_filename, 'w') as out_file:
        json.dump(machine_tracery, out_file, indent='\t')

if __name__ == '__main__':
    main()
