"""Command line interface for the Chinese Chess game."""

from __future__ import annotations

from .game import ChineseChessGame, Color


def main() -> None:
    game = ChineseChessGame()

    print("Choose mode:")
    print("1) Two-player (hotseat)")
    print("2) Play vs computer (computer is Black)")
    mode = ""
    while mode not in {"1", "2"}:
        mode = input("Enter 1 or 2: ").strip()
    vs_computer = mode == "2"
    computer_color = Color.BLACK if vs_computer else None

    print("Chinese Chess (Xiangqi)")
    print("Enter moves using algebraic coordinates (e.g. a0 a3). Type 'quit' to exit.")

    while True:
        print()
        print(game.format_board())
        print(f"Turn: {game.get_turn()}")

        raw = input("Move> ").strip()
        if raw.lower() in {"quit", "exit"}:
            print("Goodbye!")
            return
        if raw.lower() in {"help", "h", "?"}:
            print("Examples: 'a0 a3' moves the piece at a0 to a3.")
            print("Coordinates: files a-i, ranks 0-9 (0 is black side, 9 is red side).")
            continue

        if vs_computer and game.turn == computer_color:
            # Let computer move automatically
            mv = game.random_move(computer_color)
            if mv is None:
                print("Computer has no legal moves. You win!")
                return
            print(f"Computer moves: {mv[0]} {mv[1]}")
            result = game.move(mv[0], mv[1])
            print(result)
            if result.startswith(("Checkmate", "Draw")):
                print("Game over!")
                return
            continue

        parts = raw.split()
        if len(parts) != 2:
            print("Please enter moves in the format: from to (e.g. a0 a3)")
            continue

        try:
            result = game.move(parts[0], parts[1])
            print(result)
            if result.startswith(("Checkmate", "Draw")):
                print("Game over!")
                return
        except Exception as exc:
            print(f"Invalid move: {exc}")
