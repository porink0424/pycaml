# Pycaml Compiler

'Pycaml Compiler' is a compiler for min-caml, which has a two-tiered structure: Ocaml parts first performs the process up to a closure transformation, and then Python parts performs the process left. 

## Getting Started

### Prerequisites

- ocaml
- python3

### Usage

To use Pycaml Compiler, run following steps.

1. Make an executable file of min-caml.

> `make`

2. To run two parts in succession, run ```pycaml.sh```:

> `sh pycaml.sh filename`

You can compile any file in ```test``` directory by specifying **the filename without an extension**. If you do not specify a file, ```test/test.ml``` will be compiled.

