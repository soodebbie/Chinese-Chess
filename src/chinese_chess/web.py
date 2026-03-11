"""Lightweight Flask web UI for Chinese Chess (Xiangqi).

Run locally:
    python -m chinese_chess.web

Serves a single-page app at http://127.0.0.1:5000/
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

import os

from flask import Flask, jsonify, render_template_string, request

from .game import ChineseChessGame, Color, Piece


app = Flask(__name__)

# Single, in-memory game instance for the demo server.
GAME = ChineseChessGame()
COMPUTER_COLOR: Optional[Color] = None


def _piece_to_dict(p: Optional[Piece]) -> Optional[Dict[str, str]]:
    if p is None:
        return None
    return {"kind": p.kind, "color": p.color.value, "symbol": p.symbol}


def _board_state() -> Dict[str, Any]:
    return {
        "board": [[_piece_to_dict(p) for p in row] for row in GAME.board],
        "turn": GAME.get_turn(),
        "computer": COMPUTER_COLOR.value if COMPUTER_COLOR else None,
    }


@app.get("/state")
def state() -> Any:
    return jsonify(_board_state())


@app.post("/move")
def move() -> Any:
    global GAME
    data = request.get_json(force=True) or {}
    src = data.get("from")
    dst = data.get("to")
    if not src or not dst:
        return jsonify({"error": "from/to required"}), 400
    try:
        msg = GAME.move(src, dst)
        response: Dict[str, Any] = {"message": msg, **_board_state()}
        # If playing vs computer and it's computer's turn, auto move
        if COMPUTER_COLOR and GAME.turn == COMPUTER_COLOR and "Checkmate" not in msg and "Draw" not in msg:
            comp_move = GAME.random_move(COMPUTER_COLOR)
            if comp_move is None:
                response["computer_move"] = None
                response["computer_message"] = "Computer has no legal moves"
            else:
                cmsg = GAME.move(*comp_move)
                response["computer_move"] = comp_move
                response["computer_message"] = cmsg
                response.update(_board_state())
        return jsonify(response)
    except Exception as exc:  # noqa: BLE001 - surface validation errors
        return jsonify({"error": str(exc), **_board_state()}), 400


@app.post("/reset")
def reset() -> Any:
    global GAME
    GAME = ChineseChessGame()
    return jsonify({"message": "Reset", **_board_state()})


@app.post("/mode")
def mode() -> Any:
    """Set computer mode: payload {"computer": "black"} or null."""
    global GAME, COMPUTER_COLOR
    data = request.get_json(force=True) or {}
    comp = data.get("computer")
    if comp is None:
        COMPUTER_COLOR = None
    elif comp == "black":
        COMPUTER_COLOR = Color.BLACK
    elif comp == "red":
        COMPUTER_COLOR = Color.RED
    else:
        return jsonify({"error": "computer must be null, 'red', or 'black'"}), 400
    GAME = ChineseChessGame()
    return jsonify({"message": "Mode updated", **_board_state()})


INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Chinese Chess</title>
  <style>
    :root {
      --board-bg: #f6e8d5;
      --grid-line: #a67c52;
      --line-w: 1px;
      --border: 4px;
      --river: #dfeaf4;
      --red: #c0392b;
      --black: #2c3e50;
      --select: #f1c40f55;
      --cell: 54px;
      font-family: "Segoe UI", sans-serif;
    }
    body { margin: 0; display: flex; justify-content: center; background: #f4f4f4; }
    main { margin: 24px; display: flex; flex-direction: column; align-items: center; gap: 12px; }
    h1 { margin: 0 0 4px 0; font-size: 44px; text-align: center; }
    #turn-row { width: calc(var(--cell) * 9); text-align: left; margin: 0 0 18px 0; font-weight: 600; }
    #panel { width: calc(var(--cell) * 9); margin: 18px 0 0 0; display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 15px; }
    #modes { display: flex; gap: 8px; align-items: center; }
    #status { min-height: 20px; }
    #board {
      position: relative;
      width: calc(var(--cell) * 9);
      height: calc(var(--cell) * 10);
      background: var(--board-bg);
      box-shadow: 0 6px 20px #0002;
      border: var(--border) solid var(--grid-line);
      box-sizing: border-box;
    }
    #overlay {
      position: absolute;
      inset: 0;
      background: #fffefc;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 14px;
      z-index: 3;
      text-align: center;
      padding: 16px;
      box-sizing: border-box;
    }
    #overlay h2 { margin: 0; font-size: 40px; }
    #overlay p { margin: 0; color: #555; }
    #grid {
      position: absolute;
      inset: 0;
      pointer-events: none;
    }
    .diag-svg {
      position: absolute;
      inset: 0;
      pointer-events: none;
    }
    .vline {
      position: absolute;
      top: 0;
      bottom: 0;
      width: var(--line-w);
      background: var(--grid-line);
    }
    .hline {
      position: absolute;
      left: 0;
      right: 0;
      height: var(--line-w);
      background: var(--grid-line);
    }
    #river {
      position: absolute;
      top: 45%;
      height: 10%;
      left: 0;
      right: 0;
      border-left: var(--border) solid var(--grid-line);
      border-right: var(--border) solid var(--grid-line);
      box-sizing: border-box;
      background: var(--river);
      opacity: 0.7;
      pointer-events: none;
    }
    .cell {
      position: absolute;
      width: var(--cell);
      height: var(--cell);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: background 120ms;
      user-select: none;
      transform: translate(-50%, -50%);
    }
    .cell:hover { background: #00000010; }
    .cell.selected { background: var(--select); }
    .piece {
      width: 80%;
      height: 80%;
      border-radius: 50%;
      border: 2px solid currentColor;
      color: currentColor;
      background: #fffdfa;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 18px;
      box-shadow: inset 0 0 0 2px #00000010, 0 1px 2px #0002;
      pointer-events: none;
    }
    .red { color: var(--red); }
    .black { color: var(--black); }
    button { padding: 8px 12px; border: none; background: #2d89ef; color: white; cursor: pointer; border-radius: 6px; }
    button:hover { background: #1b6fcc; }
    #status { min-width: 140px; font-weight: 600; }
    @media (max-width: 560px) {
      :root { --cell: 40px; }
      h1 { font-size: 18px; }
    }
  </style>
</head>
  <body>
  <main>
    <h1>Chinese Chess 象棋</h1>
    <div id="turn-row">Turn: <span id="turn">-</span></div>
    <div id="board">
      <div id="overlay">
        <h2>Chinese Chess 象棋</h2>
        <p>Select game mode to begin.</p>
        <div id="overlay-modes">
          <button data-mode="none">Two players</button>
          <button data-mode="black">Vs computer (Black)</button>
        </div>
      </div>
      <div id="river"></div>
      <div id="grid"></div>
    </div>
    <div id="panel">
      <div id="status">Loading...</div>
      <div id="modes">
        <button data-mode="none">Two players</button>
        <button data-mode="black">Vs computer</button>
      </div>
      <button id="reset">Reset</button>
    </div>
  </main>
  <script>
    const boardEl = document.getElementById("board");
    const statusEl = document.getElementById("status");
    const turnEl = document.getElementById("turn");
    const gridEl = document.getElementById("grid");
    const modeButtons = document.querySelectorAll("#modes button");
    const overlayButtons = document.querySelectorAll("#overlay button");
    const overlay = document.getElementById("overlay");
    let selected = null;
    let modeChosen = false;

    function buildGrid() {
      gridEl.innerHTML = "";
      const riverStart = 45; // percent from top
      const riverEnd = 55;
      // Vertical lines (9 files, 0..8)
      for (let c = 0; c < 9; c++) {
        const leftPct = `${c * 100/8}%`;
        // top segment
        const vt = document.createElement("div");
        vt.className = "vline";
        vt.style.left = leftPct;
        vt.style.top = "0";
        vt.style.bottom = `${100 - riverStart}%`;
        gridEl.appendChild(vt);
        // bottom segment
        const vb = document.createElement("div");
        vb.className = "vline";
        vb.style.left = leftPct;
        vb.style.top = `${riverEnd}%`;
        vb.style.bottom = "0";
        gridEl.appendChild(vb);
      }
      // Horizontal lines (10 ranks, 0..9) – no extra lines inside river band
      for (let r = 0; r < 10; r++) {
        const h = document.createElement("div");
        h.className = "hline";
        h.style.top = `${r * 100/9}%`;
        gridEl.appendChild(h);
      }
      // Palace diagonals via SVG overlay in pixel coordinates for exact alignment
      const w = boardEl.clientWidth;
      const h = boardEl.clientHeight;
      const stepX = w / 8;
      const stepY = h / 9;
      const lx = c => c * stepX;
      const ly = r => r * stepY;
      const lineW = getComputedStyle(boardEl).getPropertyValue("--line-w").trim() || "1px";
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
      svg.setAttribute("width", w);
      svg.setAttribute("height", h);
      svg.classList.add("diag-svg");
      const diagCoords = [
        [3, 0, 5, 2],
        [5, 0, 3, 2],
        [3, 7, 5, 9],
        [5, 7, 3, 9],
      ];
      diagCoords.forEach(([x1, y1, x2, y2]) => {
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", lx(x1));
        line.setAttribute("y1", ly(y1));
        line.setAttribute("x2", lx(x2));
        line.setAttribute("y2", ly(y2));
        line.setAttribute("stroke", "var(--grid-line)");
        line.setAttribute("stroke-width", lineW);
        line.setAttribute("stroke-linecap", "butt");
        line.setAttribute("shape-rendering", "geometricPrecision");
        svg.appendChild(line);
      });
      gridEl.appendChild(svg);
    }

    function cellId(r, c) { return `r${r}c${c}`; }

    function render(board) {
      boardEl.querySelectorAll(".cell").forEach(el => el.remove());
      for (let r = 0; r < 10; r++) {
        for (let c = 0; c < 9; c++) {
          const cell = document.createElement("div");
          cell.className = "cell";
      cell.style.left = `${c * 100/8}%`;
      cell.style.top = `${r * 100/9}%`;
          cell.style.width = `var(--cell)`;
          cell.style.height = `var(--cell)`;
          cell.dataset.r = r;
          cell.dataset.c = c;
          cell.id = cellId(r,c);
          const p = board[r][c];
          if (p) {
            const piece = document.createElement("div");
            piece.className = `piece ${p.color}`;
            piece.textContent = p.symbol;
            cell.appendChild(piece);
          }
          cell.onclick = onCellClick;
          boardEl.appendChild(cell);
        }
      }
    }

    function algebraic(r, c) {
      return String.fromCharCode("a".charCodeAt(0) + c) + r;
    }

    function clearSelection() {
      if (selected) {
        document.getElementById(cellId(selected.r, selected.c))?.classList.remove("selected");
      }
      selected = null;
    }

    function onCellClick(e) {
      if (!modeChosen) return;
      const r = Number(e.currentTarget.dataset.r);
      const c = Number(e.currentTarget.dataset.c);
      if (!selected) {
        selected = {r, c};
        e.currentTarget.classList.add("selected");
      } else {
        const from = algebraic(selected.r, selected.c);
        const to = algebraic(r, c);
        move(from, to);
        clearSelection();
      }
    }

    async function fetchState() {
      const res = await fetch("/state");
      const data = await res.json();
      render(data.board);
      turnEl.textContent = data.turn;
      highlightMode(data.computer);
    }

    async function move(from, to) {
      const res = await fetch("/move", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({from, to})
      });
      const data = await res.json();
      if (res.ok) {
        render(data.board);
        statusEl.textContent = data.message || "OK";
        turnEl.textContent = data.turn;
        if (data.computer_move) {
          statusEl.textContent += ` | Computer: ${data.computer_move[0]}→${data.computer_move[1]} (${data.computer_message})`;
          turnEl.textContent = data.turn; // updated after computer move
        }
      } else {
        statusEl.textContent = data.error;
      }
    }

    document.getElementById("reset").onclick = async () => {
      await fetch("/reset", {method: "POST"});
      clearSelection();
      fetchState();
      statusEl.textContent = "Reset";
    };

    function setMode(comp) {
      return fetch("/mode", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({computer: comp})
      }).then(() => {
        clearSelection();
        fetchState();
        statusEl.textContent = comp ? "Vs computer (Black)" : "Two players";
        modeChosen = true;
        overlay.style.display = "none";
      });
    }

    modeButtons.forEach(btn => {
      btn.onclick = async () => {
        const comp = btn.dataset.mode === "none" ? null : btn.dataset.mode;
        await setMode(comp);
      };
    });
    overlayButtons.forEach(btn => {
      btn.onclick = async () => {
        const comp = btn.dataset.mode === "none" ? null : btn.dataset.mode;
        await setMode(comp);
      };
    });

    function highlightMode(comp) {
      modeButtons.forEach(btn => {
        const active = (btn.dataset.mode === "none" && !comp) || (btn.dataset.mode === comp);
        btn.style.background = active ? "#1b6fcc" : "#2d89ef";
      });
      if (modeChosen) overlay.style.display = "none";
    }

    buildGrid();
    fetchState();
  </script>
</body>
</html>
"""


@app.get("/")
def index() -> Any:
    return render_template_string(INDEX_HTML)


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
