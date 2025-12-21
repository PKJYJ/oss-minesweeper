# -*- coding: utf-8 -*-
"""
Pygame presentation layer for Minesweeper.

This module owns:
- Renderer: all drawing of cells, header, and result overlays
- InputController: translate mouse input to board actions and UI feedback
- Game: orchestration of loop, timing, state transitions, and composition

The logic lives in components.Board; this module should not implement rules.
"""

import sys

import pygame

import config
from components import Board
from pygame.locals import Rect


class Renderer:
    """Draws the Minesweeper UI.

    Knows how to draw individual cells with flags/numbers, header info,
    and end-of-game overlays with a semi-transparent background.
    """

    def __init__(self, screen: pygame.Surface, board: Board):
        self.screen = screen
        self.board = board
        self.font = pygame.font.Font(config.font_name, config.font_size)
        self.header_font = pygame.font.Font(config.font_name, config.header_font_size)
        self.result_font = pygame.font.Font(config.font_name, config.result_font_size)

    def cell_rect(self, col: int, row: int) -> Rect:
        """Return the rectangle in pixels for the given grid cell."""
        x = config.margin_left + col * config.cell_size
        y = config.margin_top + row * config.cell_size
        return Rect(x, y, config.cell_size, config.cell_size)

    def draw_cell(self, col: int, row: int, highlighted: bool) -> None:
        """Draw a single cell, respecting revealed/flagged state and highlight."""
        cell = self.board.cells[self.board.index(col, row)]
        rect = self.cell_rect(col, row)
        if cell.state.is_revealed:
            pygame.draw.rect(self.screen, config.color_cell_revealed, rect)
            if cell.state.is_mine:
                pygame.draw.circle(self.screen, config.color_cell_mine, rect.center, rect.width // 4)
            elif cell.state.adjacent > 0:
                color = config.number_colors.get(cell.state.adjacent, config.color_text)
                label = self.font.render(str(cell.state.adjacent), True, color)
                label_rect = label.get_rect(center=rect.center)
                self.screen.blit(label, label_rect)
        else:
            base_color = config.color_highlight if highlighted else config.color_cell_hidden
            pygame.draw.rect(self.screen, base_color, rect)
            if cell.state.is_flagged:
                flag_w = max(6, rect.width // 3)
                flag_h = max(8, rect.height // 2)
                pole_x = rect.left + rect.width // 3
                pole_y = rect.top + 4
                pygame.draw.line(self.screen, config.color_flag, (pole_x, pole_y), (pole_x, pole_y + flag_h), 2)
                pygame.draw.polygon(
                    self.screen,
                    config.color_flag,
                    [
                        (pole_x + 2, pole_y),
                        (pole_x + 2 + flag_w, pole_y + flag_h // 3),
                        (pole_x + 2, pole_y + flag_h // 2),
                    ],
                )
        pygame.draw.rect(self.screen, config.color_grid, rect, 1)

    def draw_header(self, remaining_mines: int, time_text: str, hints_left: int) -> None:
        pygame.draw.rect(self.screen, config.color_header, (0, 0, config.width, config.margin_top))

        # 1. 지뢰 개수 / 시간 표시
        mines_label = self.header_font.render(f"Mines: {remaining_mines}", True, config.color_header_text)
        self.screen.blit(mines_label, (20, 12))

        time_label = self.header_font.render(time_text, True, config.color_header_text)
        self.screen.blit(time_label, (150, 12))

        # 2. [Issue #4] 힌트 버튼 (중앙) - 추가된 부분
        hint_btn_rect = Rect(config.width // 2 - 40, 10, 80, 30)
        # 힌트가 남았으면 연한 노랑, 없으면 회색
        btn_color = (255, 255, 200) if hints_left > 0 else (100, 100, 100)
        
        pygame.draw.rect(self.screen, btn_color, hint_btn_rect)
        pygame.draw.rect(self.screen, (50, 50, 50), hint_btn_rect, 2)

        hint_text = self.font.render(f"Hint: {hints_left}", True, (0, 0, 0))
        text_rect = hint_text.get_rect(center=hint_btn_rect.center)
        self.screen.blit(hint_text, text_rect)

        # 3. 난이도 버튼 (Beg, Int, Adv) - 기존 유지
        buttons = [("Beg", 10, 8, 10), ("Int", 18, 14, 40), ("Adv", 24, 20, 99)]
        start_x = config.width - 160 

        for i, (name, c, r, m) in enumerate(buttons):
            btn_rect = Rect(start_x + (i * 50), 10, 45, 30)
            pygame.draw.rect(self.screen, (200, 200, 200), btn_rect)
            pygame.draw.rect(self.screen, (50, 50, 50), btn_rect, 2)
            text = self.font.render(name, True, (0, 0, 0))
            self.screen.blit(text, text.get_rect(center=btn_rect.center))

    def draw_result_overlay(self, text: str | None) -> None:
        """Draw a semi-transparent overlay with centered result text and a Restart button."""
        if not text:
            return

        # 1. 반투명 검은 배경
        overlay = pygame.Surface((config.width, config.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, config.result_overlay_alpha))
        self.screen.blit(overlay, (0, 0))

        # 2. 결과 텍스트 (GAME OVER 등)
        label = self.result_font.render(text, True, config.color_result)
        # 텍스트를 화면 중앙보다 약간 위로 올림 (-30)
        rect = label.get_rect(center=(config.width // 2, config.height // 2 - 30))
        self.screen.blit(label, rect)

        # 3. 재시작 버튼 그리기 (추가된 부분)
        # 버튼 크기 설정 (너비 140, 높이 50)
        btn_rect = Rect(0, 0, 140, 50)
        # 버튼 위치 설정 (화면 중앙, 텍스트 아래 +50)
        btn_rect.center = (config.width // 2, config.height // 2 + 50)

        # 버튼 배경 (회색)
        pygame.draw.rect(self.screen, (200, 200, 200), btn_rect)
        # 버튼 테두리 (진한 회색)
        pygame.draw.rect(self.screen, (50, 50, 50), btn_rect, 3)

        # 버튼 텍스트 ("RESTART")
        btn_label = self.font.render("RESTART", True, (0, 0, 0))
        btn_label_rect = btn_label.get_rect(center=btn_rect.center)
        self.screen.blit(btn_label, btn_label_rect)


class InputController:
    """Translates input events into game and board actions."""

    def __init__(self, game: "Game"):
        self.game = game

    def pos_to_grid(self, x: int, y: int):
        """Convert pixel coordinates to (col,row) grid indices or (-1,-1) if out of bounds."""
        if not (config.margin_left <= x < config.width - config.margin_right):
            return -1, -1
        if not (config.margin_top <= y < config.height - config.margin_bottom):
            return -1, -1
        col = (x - config.margin_left) // config.cell_size
        row = (y - config.margin_top) // config.cell_size
        if 0 <= col < self.game.board.cols and 0 <= row < self.game.board.rows:
            return int(col), int(row)
        return -1, -1

    def handle_mouse(self, pos, button) -> None:
        # 1. 상단 바 클릭 처리
        if pos[1] < config.margin_top and button == config.mouse_left:
            # [Issue #4] 힌트 버튼 클릭 확인
            hint_btn_rect = Rect(config.width // 2 - 40, 10, 80, 30)
            if hint_btn_rect.collidepoint(pos):
                # 힌트 사용 조건: 횟수 남음, 게임 시작됨, 게임 안 끝남
                if self.game.hints_left > 0 and self.game.started and not self.game.board.game_over:
                    target = self.game.board.get_safe_cell()
                    if target:
                        self.game.hint_target = target
                        self.game.hints_left -= 1
                return

            # [Issue #3] 난이도 버튼 클릭
            buttons = [(10, 8, 10), (18, 14, 40), (24, 20, 99)]
            start_x = config.width - 160
            for i, (cols, rows, mines) in enumerate(buttons):
                btn_rect = Rect(start_x + (i * 50), 10, 45, 30)
                if btn_rect.collidepoint(pos):
                    config.cols, config.rows, config.num_mines = cols, rows, mines
                    config.width = config.margin_left + config.cols * config.cell_size + config.margin_right
                    config.height = config.margin_top + config.rows * config.cell_size + config.margin_bottom
                    self.game.screen = pygame.display.set_mode((config.width, config.height))
                    self.game.reset()
                    return

        # 2. 게임 종료 재시작 버튼
        if self.game.board.game_over or self.game.board.win:
            if button == config.mouse_left:
                btn_rect = Rect(0, 0, 140, 50)
                btn_rect.center = (config.width // 2, config.height // 2 + 50)
                if btn_rect.collidepoint(pos):
                    self.game.reset()
            return

        # 3. 보드 클릭
        col, row = self.pos_to_grid(pos[0], pos[1])
        if col == -1: return
            
        game = self.game
        if button == config.mouse_left:
            # [Issue #4] 만약 힌트로 알려준 칸을 직접 열었다면 하이라이트 제거
            if game.hint_target == (col, row):
                game.hint_target = None

            game.highlight_targets.clear()
            if not game.started:
                game.started = True
                game.start_ticks_ms = pygame.time.get_ticks()
            game.board.reveal(col, row)
            
        elif button == config.mouse_right:
            game.highlight_targets.clear()
            game.board.toggle_flag(col, row)
            
        elif button == config.mouse_middle:
            neighbors = game.board.neighbors(col, row)
            game.highlight_targets = {
                (nc, nr) for (nc, nr) in neighbors
                if not game.board.cells[game.board.index(nc, nr)].state.is_revealed
            }
            game.highlight_until_ms = pygame.time.get_ticks() + config.highlight_duration_ms



class Game:
    """Main application object orchestrating loop and high-level state."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(config.title)
        self.screen = pygame.display.set_mode(config.display_dimension)
        self.clock = pygame.time.Clock()
        
        # [Issue #4] 힌트 변수 초기화
        self.max_hints = 2
        self.hints_left = self.max_hints
        self.hint_target = None
        
        self.reset()

    def reset(self):
        """Reset the game state and start a new board."""
        self.board = Board(config.cols, config.rows, config.num_mines)
        # Renderer를 새로 만드는 대신 board만 갈아끼워도 됩니다.
        self.renderer = Renderer(self.screen, self.board)
        self.input = InputController(self)
        
        self.highlight_targets = set()
        self.highlight_until_ms = 0
        self.started = False
        self.start_ticks_ms = 0
        self.end_ticks_ms = 0
        
        # [Issue #4] 힌트 초기화
        self.hints_left = self.max_hints
        self.hint_target = None

    def _elapsed_ms(self) -> int:
        """Return elapsed time in milliseconds (stops when game ends)."""
        if not self.started:
            return 0
        if self.end_ticks_ms:
            return self.end_ticks_ms - self.start_ticks_ms
        return pygame.time.get_ticks() - self.start_ticks_ms

    def _format_time(self, ms: int) -> str:
        """Format milliseconds as mm:ss string."""
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _result_text(self) -> str | None:
        """Return result label to display, or None if game continues."""
        if self.board.game_over:
            return "GAME OVER"
        if self.board.win:
            return "GAME CLEAR"
        return None

    def draw(self):
        """Render one frame: header, grid, result overlay."""
        if pygame.time.get_ticks() > self.highlight_until_ms and self.highlight_targets:
            self.highlight_targets.clear()
        
        self.screen.fill(config.color_bg)
        
        # 상단 바 그리기 (hints_left 전달)
        remaining = max(0, config.num_mines - self.board.flagged_count())
        time_text = self._format_time(self._elapsed_ms())
        self.renderer.draw_header(remaining, time_text, self.hints_left)
        
        # 보드 그리기
        now = pygame.time.get_ticks()
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                highlighted = (now <= self.highlight_until_ms) and ((c, r) in self.highlight_targets)
                self.renderer.draw_cell(c, r, highlighted)
        
        # [Issue #4] 힌트 타겟 하이라이트 (초록색 테두리) - 보드 위에 덧그리기
        if self.hint_target:
            hc, hr = self.hint_target
            rect = self.renderer.cell_rect(hc, hr)
            pygame.draw.rect(self.screen, (0, 255, 0), rect, 3) # 두께 3의 초록색 테두리

        self.renderer.draw_result_overlay(self._result_text())
        pygame.display.flip()

    def run_step(self) -> bool:
        """Process inputs, update time, draw, and tick the clock once."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
                # [Issue #4] H키 입력 시 힌트 사용
                elif event.key == pygame.K_h:
                    if self.hints_left > 0 and self.started and not self.board.game_over:
                        target = self.board.get_safe_cell()
                        if target:
                            self.hint_target = target
                            self.hints_left -= 1

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.input.handle_mouse(event.pos, event.button)
                
        if (self.board.game_over or self.board.win) and self.started and not self.end_ticks_ms:
            self.end_ticks_ms = pygame.time.get_ticks()
        self.draw()
        self.clock.tick(config.fps)
        return True


def main() -> int:
    """Application entrypoint: run the main loop until quit."""
    game = Game()
    running = True
    while running:
        running = game.run_step()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())