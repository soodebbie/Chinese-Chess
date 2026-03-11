from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional, Tuple
import random


class Color(str, Enum):
    RED = "red"
    BLACK = "black"


@dataclass(frozen=True)
class Piece:
    kind: str
    color: Color

    @property
    def symbol(self) -> str:
        # Chinese characters for each piece type
        red_map = {
            "r": "車",
            "n": "馬",
            "b": "相",
            "a": "仕",
            "k": "帥",
            "c": "炮",
            "p": "兵",
        }
        black_map = {
            "r": "車",
            "n": "馬",
            "b": "象",
            "a": "士",
            "k": "將",
            "c": "炮",
            "p": "卒",
        }
        return (red_map if self.color == Color.RED else black_map)[self.kind.lower()]


Coordinate = Tuple[int, int]  # (row, col)


class ChineseChessGame:
    """A minimal Chinese Chess (Xiangqi) game logic engine."""

    def __init__(self) -> None:
        self.board = self._create_starting_board()
        self.turn = Color.RED
        self.move_history: list[tuple[str, str]] = []
        # Track repeated positions for draw detection (threefold repetition).
        self._position_counts: dict[tuple, int] = {}
        self._game_over: Optional[str] = None
        self._record_position()

    @staticmethod
    def _create_starting_board() -> list[list[Optional[Piece]]]:
        # Board is 10 rows (0..9) x 9 cols (0..8)
        b: list[list[Optional[Piece]]] = [[None] * 9 for _ in range(10)]

        # Black (top, row 0..2)
        b[0] = [
            Piece("r", Color.BLACK),
            Piece("n", Color.BLACK),
            Piece("b", Color.BLACK),
            Piece("a", Color.BLACK),
            Piece("k", Color.BLACK),
            Piece("a", Color.BLACK),
            Piece("b", Color.BLACK),
            Piece("n", Color.BLACK),
            Piece("r", Color.BLACK),
        ]

        b[2][1] = Piece("c", Color.BLACK)
        b[2][7] = Piece("c", Color.BLACK)
        b[3][0] = Piece("p", Color.BLACK)
        b[3][2] = Piece("p", Color.BLACK)
        b[3][4] = Piece("p", Color.BLACK)
        b[3][6] = Piece("p", Color.BLACK)
        b[3][8] = Piece("p", Color.BLACK)

        # Red (bottom, row 9..7)
        b[9] = [
            Piece("r", Color.RED),
            Piece("n", Color.RED),
            Piece("b", Color.RED),
            Piece("a", Color.RED),
            Piece("k", Color.RED),
            Piece("a", Color.RED),
            Piece("b", Color.RED),
            Piece("n", Color.RED),
            Piece("r", Color.RED),
        ]

        b[7][1] = Piece("c", Color.RED)
        b[7][7] = Piece("c", Color.RED)
        b[6][0] = Piece("p", Color.RED)
        b[6][2] = Piece("p", Color.RED)
        b[6][4] = Piece("p", Color.RED)
        b[6][6] = Piece("p", Color.RED)
        b[6][8] = Piece("p", Color.RED)

        return b

    @staticmethod
    def coord_from_algebraic(text: str) -> Coordinate:
        text = text.strip().lower()
        if len(text) != 2:
            raise ValueError("Invalid coordinate: must be 2 characters (file+rank)")

        file = text[0]
        rank = text[1]
        if file < "a" or file > "i":
            raise ValueError("Invalid file: must be a-i")
        if rank < "0" or rank > "9":
            raise ValueError("Invalid rank: must be 0-9")

        col = ord(file) - ord("a")
        row = int(rank)
        return row, col

    @staticmethod
    def algebraic_from_coord(coord: Coordinate) -> str:
        row, col = coord
        return f"{chr(col + ord('a'))}{row}"

    def at(self, coord: Coordinate) -> Optional[Piece]:
        r, c = coord
        return self.board[r][c]

    def set_at(self, coord: Coordinate, piece: Optional[Piece]) -> None:
        r, c = coord
        self.board[r][c] = piece

    def _in_bounds(self, coord: Coordinate) -> bool:
        r, c = coord
        return 0 <= r < 10 and 0 <= c < 9

    def _is_palace(self, coord: Coordinate, color: Color) -> bool:
        r, c = coord
        if color == Color.RED:
            return 7 <= r <= 9 and 3 <= c <= 5
        return 0 <= r <= 2 and 3 <= c <= 5

    def _path_between(self, start: Coordinate, end: Coordinate) -> Iterable[Coordinate]:
        r0, c0 = start
        r1, c1 = end
        if r0 == r1:
            step = 1 if c1 > c0 else -1
            for c in range(c0 + step, c1, step):
                yield (r0, c)
        elif c0 == c1:
            step = 1 if r1 > r0 else -1
            for r in range(r0 + step, r1, step):
                yield (r, c0)

    def _count_between(self, start: Coordinate, end: Coordinate) -> int:
        """Count occupied squares strictly between start and end along rank/file."""
        return sum(1 for p in self._path_between(start, end) if self.at(p) is not None)

    def _is_clear_path(self, start: Coordinate, end: Coordinate) -> bool:
        return all(self.at(p) is None for p in self._path_between(start, end))

    def _attacks(self, piece: Piece, pos: Coordinate, target: Coordinate) -> bool:
        """Return True if `piece` at `pos` attacks the target square."""
        pr, pc = pos
        tr, tc = target
        dr = tr - pr
        dc = tc - pc
        adx = abs(dr)
        ady = abs(dc)
        kind = piece.kind.lower()

        if kind == "r":
            return (dr == 0 or dc == 0) and self._is_clear_path(pos, target)

        if kind == "c":
            if dr != 0 and dc != 0:
                return False
            return self._count_between(pos, target) == 1

        if kind == "n":
            if (adx, ady) not in {(2, 1), (1, 2)}:
                return False
            leg = (pr + (dr // 2), pc) if adx == 2 else (pr, pc + (dc // 2))
            return self.at(leg) is None

        if kind == "b":
            if adx != 2 or ady != 2:
                return False
            if piece.color == Color.RED and tr < 5:
                return False
            if piece.color == Color.BLACK and tr > 4:
                return False
            mid = ((pr + tr) // 2, (pc + tc) // 2)
            return self.at(mid) is None

        if kind == "a":
            return adx == 1 and ady == 1 and self._is_palace(target, piece.color)

        if kind == "k":
            if (adx, ady) in {(1, 0), (0, 1)}:
                return True
            return pc == tc and self._is_clear_path(pos, target)

        if kind == "p":
            forward = -1 if piece.color == Color.RED else 1
            if dr == forward and dc == 0:
                return True
            crossed = (piece.color == Color.RED and pr <= 4) or (piece.color == Color.BLACK and pr >= 5)
            return crossed and dr == 0 and ady == 1

        return False

    def _is_in_check(self, color: Color) -> bool:
        general = self._find_general(color)
        if general is None:
            return True
        attacker_color = Color.BLACK if color == Color.RED else Color.RED
        for r in range(10):
            for c in range(9):
                p = self.board[r][c]
                if p and p.color == attacker_color:
                    if self._attacks(p, (r, c), general):
                        return True
        return False

    def _validate_move(self, start: Coordinate, end: Coordinate) -> None:
        if not self._in_bounds(start) or not self._in_bounds(end):
            raise ValueError("Move out of bounds")

        piece = self.at(start)
        if piece is None:
            raise ValueError("No piece at start coordinate")
        if piece.color != self.turn:
            raise ValueError("Not your turn")

        dest_piece = self.at(end)
        if dest_piece is not None and dest_piece.color == piece.color:
            raise ValueError("Cannot capture your own piece")

        dr = end[0] - start[0]
        dc = end[1] - start[1]
        adx = abs(dr)
        ady = abs(dc)

        kind = piece.kind.lower()

        if kind == "r":
            if dr != 0 and dc != 0:
                raise ValueError("Rook moves in straight lines")
            if not self._is_clear_path(start, end):
                raise ValueError("Rook path is blocked")

        elif kind == "c":
            if dr != 0 and dc != 0:
                raise ValueError("Cannon moves in straight lines")
            between = self._count_between(start, end)
            if dest_piece is None:
                if between != 0:
                    raise ValueError("Cannon must move to an empty square with no intervening pieces")
            else:
                if between != 1:
                    raise ValueError("Cannon captures by jumping over exactly one piece")

        elif kind == "n":
            if (adx, ady) not in [(2, 1), (1, 2)]:
                raise ValueError("Knight moves in an L-shape")
            # leg blocking
            if adx == 2:
                leg = (start[0] + (dr // 2), start[1])
            else:
                leg = (start[0], start[1] + (dc // 2))
            if self.at(leg) is not None:
                raise ValueError("Knight is blocked by a leg")

        elif kind == "b":
            # Elephant (bishop)
            if adx != 2 or ady != 2:
                raise ValueError("Bishop moves exactly two points diagonally")
            # cannot cross river
            if piece.color == Color.RED and end[0] < 5:
                raise ValueError("Red bishop cannot cross the river")
            if piece.color == Color.BLACK and end[0] > 4:
                raise ValueError("Black bishop cannot cross the river")
            # Eye blocking
            mid = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2)
            if self.at(mid) is not None:
                raise ValueError("Bishop is blocked at the mid-point")

        elif kind == "a":
            if adx != 1 or ady != 1:
                raise ValueError("Advisor moves one point diagonally")
            if not self._is_palace(end, piece.color):
                raise ValueError("Advisor must stay inside the palace")

        elif kind == "k":
            if (adx, ady) not in [(1, 0), (0, 1)]:
                raise ValueError("General moves one point orthogonally")
            if not self._is_palace(end, piece.color):
                raise ValueError("General must stay inside the palace")
            # Flying general rule: cannot directly face other general without intervening pieces
            other_general = self._find_general(Color.BLACK if piece.color == Color.RED else Color.RED)
            if other_general and end[1] == other_general[1]:
                path_clear = self._is_clear_path(end, other_general)
                if path_clear:
                    raise ValueError("Generals cannot face each other directly")

        elif kind == "p":
            forward = -1 if piece.color == Color.RED else 1
            if dr == forward and dc == 0:
                return
            # after crossing river can move sideways
            if (piece.color == Color.RED and start[0] <= 4) or (piece.color == Color.BLACK and start[0] >= 5):
                if dr == 0 and ady == 1:
                    return
            raise ValueError("Pawn moves one step forward (and sideways after crossing the river)")

        else:
            raise ValueError(f"Unknown piece type: {piece.kind}")

    def _find_general(self, color: Color) -> Optional[Coordinate]:
        for r in range(10):
            for c in range(9):
                p = self.board[r][c]
                if p and p.kind.lower() == "k" and p.color == color:
                    return (r, c)
        return None

    def move(self, from_text: str, to_text: str) -> str:
        if self._game_over:
            raise ValueError(f"Game over: {self._game_over}")

        start = self.coord_from_algebraic(from_text)
        end = self.coord_from_algebraic(to_text)
        self._validate_move(start, end)

        moved_piece = self.at(start)
        assert moved_piece is not None

        captured = self.at(end)
        self.set_at(end, moved_piece)
        self.set_at(start, None)

        # Reject moves that leave your own general in check.
        if self._is_in_check(moved_piece.color):
            self.set_at(start, moved_piece)
            self.set_at(end, captured)
            raise ValueError("Move would leave your general in check")

        self.move_history.append((from_text, to_text))
        self.turn = Color.BLACK if self.turn == Color.RED else Color.RED
        self._record_position()

        if captured and captured.kind.lower() == "k":
            self._game_over = "Checkmate! General captured."
            return self._game_over

        opponent = Color.BLACK if moved_piece.color == Color.RED else Color.RED
        if self._is_in_check(opponent):
            return "Check!"

        if self._is_draw_by_repetition():
            self._game_over = "Draw by repetition"
            return self._game_over

        if captured:
            return f"{moved_piece.symbol} captures {captured.symbol}"
        return "OK"

    def format_board(self) -> str:
        rows: list[str] = []
        header = "   " + " ".join(chr(ord('a') + i) for i in range(9))
        rows.append(header)
        for r in range(0, 10):
            line = f"{r:2d} "
            for c in range(9):
                p = self.board[r][c]
                line += (p.symbol if p else ".") + " "
            rows.append(line)
        return "\n".join(rows)

    def get_turn(self) -> str:
        return "Red" if self.turn == Color.RED else "Black"

    # ---------------- internal helpers ----------------

    def _record_position(self) -> None:
        key = self._position_key()
        self._position_counts[key] = self._position_counts.get(key, 0) + 1

    def _position_key(self) -> tuple:
        flat = tuple(
            p.symbol if p else "."
            for row in self.board
            for p in row
        )
        return (self.turn, flat)

    def _is_draw_by_repetition(self) -> bool:
        # Three occurrences of same board with same player to move.
        return self._position_counts.get(self._position_key(), 0) >= 3

    # ---------------- AI helpers ----------------

    def legal_moves(self, color: Color) -> list[tuple[str, str]]:
        """Generate all legal moves for the given color."""
        prev_turn = self.turn
        self.turn = color  # ensure validation uses correct side to move
        moves: list[tuple[str, str]] = []
        for r in range(10):
            for c in range(9):
                p = self.board[r][c]
                if not p or p.color != color:
                    continue
                start = (r, c)
                for r2 in range(10):
                    for c2 in range(9):
                        end = (r2, c2)
                        try:
                            self._validate_move(start, end)
                            captured = self.at(end)
                            self.set_at(end, p)
                            self.set_at(start, None)
                            if not self._is_in_check(color):
                                moves.append((self.algebraic_from_coord(start), self.algebraic_from_coord(end)))
                            self.set_at(start, p)
                            self.set_at(end, captured)
                        except Exception:
                            # Not a legal move
                            continue
        self.turn = prev_turn
        return moves

    def random_move(self, color: Color) -> Optional[tuple[str, str]]:
        moves = self.legal_moves(color)
        if not moves:
            return None
        return random.choice(moves)
