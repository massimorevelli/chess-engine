## Chess Engine


### Overview


This project implements a classical chess engine written in Python. It evaluates positions, explores possible move sequences, and selects the best continuation using a search-and-evaluation framework built on the `python-chess` library.

The engine includes:

- A static evaluation function combining material balance, piece–square tables (PSTs), and heuristic bonuses/penalties
- A minimax search algorithm with alpha-beta pruning, quiescence search, and transposition table caching

It supports command-line play, self-play with PGN export, and UCI (Universal Chess Interface) mode for chess GUIs and engine-to-engine communication.

See the [technical report](technical_report.pdf) for a full explanation of the engine's architecture, algorithms, and design choices.

### Testing

The engine’s performance was evaluated both in matches against Stockfish (a leading open-source chess engine) and through self-play analysis.  See the [testing report](testing_report.pdf) for detailed methodology, metrics, and results.

<p  align="center">
<img  src="testing_data/images/01.png"  alt="Sample checkmate 1"  width="48%">
<img  src="testing_data/images/02.png"  alt="Sample checkmate 2"  width="48%">
</p>


### Usage

#### Command-line play

Play interactively against the engine in the terminal by entering moves in standard algebraic notation (SAN):

```bash
python chess_engine.py cli
```

#### UCI mode

The engine can be loaded into any UCI-compatible GUI (e.g. Arena) to play against it with a visual board and more intuitive controls.

The UCI interface can also be used to run benchmark matches against Stockfish:

1.  Download the latest [Stockfish executable](https://stockfishchess.org/download/).
    
2.  Place it inside `chess-engine/testing/stockfish.exe`.
    
3.  Run the match script (`match_vs_stockfish.py`)

#### Self-play mode

For testing and analysis, the self-play mode runs a game where the engine competes against itself, automatically saving the complete game in PGN format with move-by-move evaluations:

```bash
python chess_engine.py selfplay
```



### Changelog

- **v1.0 (current) - Initial release**
  - Static board evaluation (material balance + positional advantage)
  - Minimax search algorithm with alpha-beta pruning
  - Search optimization features (move ordering, memory caching)
  - Command-line play mode
  - Self-play mode with PGN export
  - UCI support

- **v1.1 (WIP)**
   - Phase-dependent PSTs (opening, middlegame, endgame)
   - Opening book and endgame tablebases
   - Iterative deepening with time management
   - Additional search optimizations (e.g. null move pruning)
