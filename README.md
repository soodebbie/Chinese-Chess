# Chinese Chess (Xiangqi)

A simple command-line Chinese Chess (Xiangqi) game written in Python.

## Getting Started

### Requirements
- Python 3.11+

### Install

```bash
python -m pip install -e .
```

### Run

```bash
python -m chinese_chess
```

### Play in the browser
Start the tiny web server and open http://127.0.0.1:5000 in your browser:

```bash
python -m pip install -e .
python -m chinese_chess.web
```

Use click-to-select squares to move (first click = from, second = to). `Reset` restarts the game.

Tips:
- Keep the PowerShell window running; close it to stop the server.
- To change port/host: `set PORT=8000` (and optionally `set HOST=0.0.0.0`) before running the command.

### Controls
- Enter moves using algebraic coordinates: e.g. `a0 a3` (from `a0` to `a3`).
- `quit` or `exit` to stop the game.

## Notes
- This is a basic implementation focused on piece movement rules and turn-taking.
- It does not currently enforce check/checkmate rules.
