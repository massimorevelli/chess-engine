# Testing

This folder contains the scripts, benchmark results, figures, and PGN files used to evaluate version 1.1 of the chess engine.


## Benchmark setup

The benchmark requires **Stockfish 18** as an external UCI engine.

Download the appropriate Stockfish 18 executable and place it at:

```text
testing/stockfish.exe
```


## Running the benchmark

From the repository root, run:

```bash
python testing/run_benchmark.py
```


## Generating the figures

Run:

```bash
python testing/analyze_results.py
```