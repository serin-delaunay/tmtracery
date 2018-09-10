# Turing Machine Tracery

This project implements a [Turing Machine](https://en.wikipedia.org/wiki/Turing_Machine) - to - [Tracery](http://tracery.io) compiler. The compiler relies on a bug in some Tracery versions which allows delayed expansion of variables, and shows that these versions of Tracery are Turing-complete

To convert a Turing machine defined in `machine.json` to Tracery, run the following command:

```
python tmtracery.py machine.json
```

The resulting Tracery grammar will be written to `machine.json.tracery.json`.

You can specify a different output filename using a command line argument:

```
python tmtracery.py machine.json -o machine.t.json
```

You can add initial tape data from `input.txt`, using another command line argument:

```
python tmtracery.py machine.json -i input.txt
```

# Turing machine file format

TMT uses a JSON encoding of Turing machines.
The machine must be encoded as a single object containing seven keys:

* `states`: an array of unique strings naming all of the machine's states, including an accepting and rejecting state.
* `symbols`: an array of unique single-character strings naming all of the machine's symbols, including a blank symbol.
* `blank_symbol`: a string equal to one of the items in `symbols`. The machine's tape will initially be filled with this, apart from the input data.
* `start_state`: a string equal to one of the items in `states`. This will be the machine's initial state.
* `accept_state`: a string equal to one of the items in `states`. The machine will halt and accept on reaching this state.
* `reject_state`: a string equal to one of the items in `states`. The machine will halt and reject on reaching this state.
* `delta`: a complete array of transitions for all symbols and all states except the accept and reject state.

Any other keys are ignored.

## Transition format

Each transition in `delta` is an array containing two arrays.
The first identifies the state and symbol under the tape head which will prompt this transition.
The second identifies the new state, the symbol to write at the tape head, and the direction to move the tape head after writing.
Valid tape head directions are `<` (left), `>` (right), and `_` (remain).

## Example machine

```
{
    "function": "Accepts a string iff it is empty, or starts with 0 and consists of alternating 1s and 0s."
    "states": ["A", "B", "Y", "N"],
    "symbols": ["0", "1", "_"],
    "blank_symbol": "_",
    "start_state": "A",
    "accept_state": "Y",
    "reject_state": "N",
    "delta": [
		[["A", "0"], ["B", "0", ">"]],
		[["A", "1"], ["N", "1", "_"]],
		[["A", "_"], ["Y", "_", "_"]],
		[["B", "0"], ["N", "0", "_"]],
		[["B", "1"], ["A", "1", ">"]],
		[["B", "_"], ["Y", "_", "_"]]
	]
}
```

# Execution model

The simulated machine has one double-sided infinite tape, implemented as a pair of stacks.
When either end of the tape is reached, an additional blank symbol is automatically appended to that side.

