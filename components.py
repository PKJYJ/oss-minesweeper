"""
Core game logic for Minesweeper.
"""

import random
from typing import List, Tuple


class CellState:
    """Mutable state of a single cell."""
    def __init__(self, is_mine: bool = False, is_revealed: bool = False, is_flagged: bool = False, adjacent: int = 0):
        self.is_mine = is_mine
        self.is_revealed = is_revealed
        self.is_flagged = is_flagged
        self.adjacent = adjacent


class Cell:
    """Logical cell positioned on the board by column and row."""
    def __init__(self, col: int, row: int):
        self.col = col
        self.row = row
        self.state = CellState()


class Board:
    """Minesweeper board state and rules."""

    def __init__(self, cols: int, rows: int, mines: int):
        self.cols = cols
        self.rows = rows
        self.num_mines = mines
        self.cells: List[Cell] = [Cell(c, r) for r in range(rows) for c in range(cols)]
        self._mines_placed = False
        self.revealed_count = 0
        self.game_over = False
        self.win = False

    def get_safe_cell(self) -> tuple[int, int] | None:
        #"""[Issue #4] 아직 열리지 않은 안전한 칸 하나를 반환"""
        candidates = []
        for cell in self.cells:
            # 열리지 않았고, 지뢰가 아닌 칸
            if not cell.state.is_revealed and not cell.state.is_mine:
                candidates.append((cell.col, cell.row))
        
        if candidates:
            return random.choice(candidates)
        return None

    # [Issue #6] 숫자 칸 자동 열기 로직 추가
    def auto_reveal(self, col: int, row: int) -> None:
        #"""Shift+우클릭 시 주변 깃발 개수가 맞으면 나머지 칸 오픈"""
        if not self.is_inbounds(col, row):
            return
            
        idx = self.index(col, row)
        cell = self.cells[idx]
        
        # 1. 이미 열린 칸이어야 하고, 숫자가 있어야 함 (0이 아니어야 함)
        if not cell.state.is_revealed or cell.state.adjacent == 0:
            return
            
        # 2. 주변 깃발 개수 세기
        neighbors = self.neighbors(col, row)
        flag_count = 0
        for (nc, nr) in neighbors:
            if self.cells[self.index(nc, nr)].state.is_flagged:
                flag_count += 1
                
        # 3. 깃발 개수와 숫자가 같으면 -> 깃발이 아닌 나머지 칸들 열기
        if flag_count == cell.state.adjacent:
            for (nc, nr) in neighbors:
                target = self.cells[self.index(nc, nr)]
                # 깃발이 아니고 닫혀있는 칸만 열기 (함정 발동 가능)
                if not target.state.is_flagged and not target.state.is_revealed:
                    self.reveal(nc, nr)

    def index(self, col: int, row: int) -> int:
        return row * self.cols + col

    def is_inbounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows

    def neighbors(self, col: int, row: int) -> List[Tuple[int, int]]:
        deltas = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0),            (1, 0),
            (-1, 1),  (0, 1),  (1, 1),
        ]
        result: List[Tuple[int, int]] = []
        for dc, dr in deltas:
            nc, nr = col + dc, row + dr
            if self.is_inbounds(nc, nr):
                result.append((nc, nr))
        return result

    def place_mines(self, safe_col: int, safe_row: int) -> None:
        all_positions = [(c, r) for r in range(self.rows) for c in range(self.cols)]
        forbidden = {(safe_col, safe_row)} | set(self.neighbors(safe_col, safe_row))
        pool = [p for p in all_positions if p not in forbidden]
        random.shuffle(pool)

        for (c, r) in pool[: self.num_mines]:
            cell = self.cells[self.index(c, r)]
            cell.state.is_mine = True

        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[self.index(c, r)]
                if cell.state.is_mine:
                    cell.state.adjacent = 0
                    continue
                count = 0
                for (nc, nr) in self.neighbors(c, r):
                    neighbor_cell = self.cells[self.index(nc, nr)]
                    if neighbor_cell.state.is_mine:
                        count += 1
                cell.state.adjacent = count

        self._mines_placed = True

    def reveal(self, col: int, row: int) -> None:
        if not self.is_inbounds(col, row):
            return
        if self.game_over:
            return

        if not self._mines_placed:
            self.place_mines(col, row)

        start_cell = self.cells[self.index(col, row)]

        if start_cell.state.is_flagged:
            return

        if start_cell.state.is_mine:
            start_cell.state.is_revealed = True
            self.game_over = True
            self._reveal_all_mines()
            return

        stack = [(col, row)]
        while stack:
            c, r = stack.pop()
            if not self.is_inbounds(c, r):
                continue
            cell = self.cells[self.index(c, r)]

            if cell.state.is_revealed or cell.state.is_flagged:
                continue
            if cell.state.is_mine:
                continue

            cell.state.is_revealed = True
            self.revealed_count += 1

            if cell.state.adjacent == 0:
                for (nc, nr) in self.neighbors(c, r):
                    neighbor_cell = self.cells[self.index(nc, nr)]
                    if not neighbor_cell.state.is_revealed and not neighbor_cell.state.is_mine:
                        stack.append((nc, nr))

        self._check_win()

    def toggle_flag(self, col: int, row: int) -> None:
        if not self.is_inbounds(col, row):
            return
        if self.game_over:
            return

        cell = self.cells[self.index(col, row)]
        if cell.state.is_revealed:
            return

        cell.state.is_flagged = not cell.state.is_flagged

    def flagged_count(self) -> int:
        return sum(1 for cell in self.cells if cell.state.is_flagged)

    def _reveal_all_mines(self) -> None:
        for cell in self.cells:
            if cell.state.is_mine:
                cell.state.is_revealed = True

    def _check_win(self) -> None:
        total_cells = self.cols * self.rows
        if self.revealed_count == total_cells - self.num_mines and not self.game_over:
            self.win = True
            for cell in self.cells:
                if not cell.state.is_revealed and not cell.state.is_mine:
                    cell.state.is_revealed = True