# -*- coding: utf-8 -*-
"""
Pygame presentation layer for Minesweeper.
"""

import sys
import os
import pygame
import config
from components import Board
from pygame.locals import Rect


class Renderer:
    """Draws the Minesweeper UI."""

    def __init__(self, screen: pygame.Surface, board: Board):
        self.screen = screen
        self.board = board
        self.font = pygame.font.Font(config.font_name, config.font_size)
        self.header_font = pygame.font.Font(config.font_name, config.header_font_size)
        self.result_font = pygame.font.Font(config.font_name, config.result_font_size)

    def get_board_offset(self):
        grid_width = self.board.cols * config.cell_size
        grid_height = self.board.rows * config.cell_size
        offset_x = (config.width - grid_width) // 2
        offset_y = 60 + (config.height - 60 - grid_height) // 2
        return offset_x, offset_y

    def cell_rect(self, col: int, row: int) -> Rect:
        off_x, off_y = self.get_board_offset()
        x = off_x + col * config.cell_size
        y = off_y + row * config.cell_size
        return Rect(x, y, config.cell_size, config.cell_size)

    def draw_cell(self, col: int, row: int, highlighted: bool) -> None:
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

    def draw_header(self, remaining_mines: int, time_text: str, hints_left: int, high_score_text: str) -> None:
        pygame.draw.rect(self.screen, config.color_header, (0, 0, config.width, 60))

        # [수정됨] 텍스트 간격 좁히기
        
        # 1. 지뢰 (왼쪽)
        mines_label = self.header_font.render(f"Mines: {remaining_mines}", True, config.color_header_text)
        self.screen.blit(mines_label, (20, 12))

        # 2. 시간 (150 -> 125로 당김)
        time_label = self.header_font.render(f"Time: {time_text}", True, config.color_header_text)
        self.screen.blit(time_label, (125, 12))

        # 3. 최고 기록 (300 -> 245로 당김)
        hs_label = self.header_font.render(f"Best: {high_score_text}", True, (255, 215, 0))
        self.screen.blit(hs_label, (245, 12))

        # 4. 힌트 버튼 (정중앙)
        hint_btn_rect = Rect(0, 0, 80, 30)
        hint_btn_rect.centerx = config.width // 2
        hint_btn_rect.top = 10
        
        btn_color = (255, 255, 200) if hints_left > 0 else (100, 100, 100)
        pygame.draw.rect(self.screen, btn_color, hint_btn_rect)
        pygame.draw.rect(self.screen, (50, 50, 50), hint_btn_rect, 2)

        hint_text = self.font.render(f"Hint: {hints_left}", True, (0, 0, 0))
        text_rect = hint_text.get_rect(center=hint_btn_rect.center)
        self.screen.blit(hint_text, text_rect)

        # 5. 난이도 버튼 (오른쪽 끝 고정)
        buttons = [("Beg", 10, 8, 10), ("Int", 18, 14, 40), ("Adv", 24, 20, 99)]
        start_x = config.width - 160 

        for i, (name, c, r, m) in enumerate(buttons):
            btn_rect = Rect(start_x + (i * 50), 10, 45, 30)
            pygame.draw.rect(self.screen, (200, 200, 200), btn_rect)
            pygame.draw.rect(self.screen, (50, 50, 50), btn_rect, 2)
            text = self.font.render(name, True, (0, 0, 0))
            self.screen.blit(text, text.get_rect(center=btn_rect.center))

    def draw_result_overlay(self, text: str | None) -> None:
        if not text:
            return

        overlay = pygame.Surface((config.width, config.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, config.result_overlay_alpha))
        self.screen.blit(overlay, (0, 0))

        label = self.result_font.render(text, True, config.color_result)
        rect = label.get_rect(center=(config.width // 2, config.height // 2 - 30))
        self.screen.blit(label, rect)

        btn_rect = Rect(0, 0, 140, 50)
        btn_rect.center = (config.width // 2, config.height // 2 + 50)
        pygame.draw.rect(self.screen, (200, 200, 200), btn_rect)
        pygame.draw.rect(self.screen, (50, 50, 50), btn_rect, 3)

        btn_label = self.font.render("RESTART", True, (0, 0, 0))
        btn_label_rect = btn_label.get_rect(center=btn_rect.center)
        self.screen.blit(btn_label, btn_label_rect)


class InputController:
    """Translates input events into game and board actions."""

    def __init__(self, game: "Game"):
        self.game = game

    def pos_to_grid(self, x: int, y: int):
        off_x, off_y = self.game.renderer.get_board_offset()
        
        grid_width = self.game.board.cols * config.cell_size
        grid_height = self.game.board.rows * config.cell_size
        
        if not (off_x <= x < off_x + grid_width):
            return -1, -1
        if not (off_y <= y < off_y + grid_height):
            return -1, -1
            
        col = (x - off_x) // config.cell_size
        row = (y - off_y) // config.cell_size
        
        if 0 <= col < self.game.board.cols and 0 <= row < self.game.board.rows:
            return int(col), int(row)
        return -1, -1

    def handle_mouse(self, pos, button) -> None:
        if pos[1] < 60 and button == config.mouse_left:
            # 힌트 버튼 클릭
            hint_btn_rect = Rect(0, 0, 80, 30)
            hint_btn_rect.centerx = config.width // 2
            hint_btn_rect.top = 10
            
            if hint_btn_rect.collidepoint(pos):
                if self.game.hints_left > 0 and self.game.started and not self.game.board.game_over:
                    target = self.game.board.get_safe_cell()
                    if target:
                        self.game.hint_target = target
                        self.game.hints_left -= 1
                return

            # 난이도 버튼 클릭
            buttons = [(10, 8, 10), (18, 14, 40), (24, 20, 99)]
            start_x = config.width - 160
            for i, (cols, rows, mines) in enumerate(buttons):
                btn_rect = Rect(start_x + (i * 50), 10, 45, 30)
                if btn_rect.collidepoint(pos):
                    config.cols, config.rows, config.num_mines = cols, rows, mines
                    self.game.reset()
                    return

        if self.game.board.game_over or self.game.board.win:
            if button == config.mouse_left:
                btn_rect = Rect(0, 0, 140, 50)
                btn_rect.center = (config.width // 2, config.height // 2 + 50)
                if btn_rect.collidepoint(pos):
                    self.game.reset()
            return

        col, row = self.pos_to_grid(pos[0], pos[1])
        if col == -1: return
            
        game = self.game
        if button == config.mouse_left:
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
    """Main application object."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(config.title)
        
        # 윈도우 크기를 '상급(Adv)' 기준으로 고정
        config.width = 20 + 24 * config.cell_size + 20
        config.height = 60 + 20 * config.cell_size + 20
        
        config.cols = 18
        config.rows = 14
        config.num_mines = 40
        
        self.screen = pygame.display.set_mode((config.width, config.height))
        self.clock = pygame.time.Clock()
        
        self.max_hints = 2
        self.hints_left = self.max_hints
        self.hint_target = None
        self.high_score = self.load_highscore()
        
        self.reset()

    def load_highscore(self) -> int | None:
        try:
            if os.path.exists("highscore.txt"):
                with open("highscore.txt", "r") as f:
                    return int(f.read().strip())
        except:
            pass
        return None

    def save_highscore(self, score: int):
        try:
            with open("highscore.txt", "w") as f:
                f.write(str(score))
        except:
            pass

    def reset(self):
        self.board = Board(config.cols, config.rows, config.num_mines)
        self.renderer = Renderer(self.screen, self.board)
        self.input = InputController(self)
        self.highlight_targets = set()
        self.highlight_until_ms = 0
        self.started = False
        self.start_ticks_ms = 0
        self.end_ticks_ms = 0
        self.hints_left = self.max_hints
        self.hint_target = None

    def _elapsed_ms(self) -> int:
        if not self.started:
            return 0
        if self.end_ticks_ms:
            return self.end_ticks_ms - self.start_ticks_ms
        return pygame.time.get_ticks() - self.start_ticks_ms

    def _format_time(self, ms: int) -> str:
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _result_text(self) -> str | None:
        if self.board.game_over:
            return "GAME OVER"
        if self.board.win:
            if self.high_score and self._elapsed_ms() == self.high_score:
                return "NEW RECORD!"
            return "GAME CLEAR"
        return None

    def draw(self):
        if pygame.time.get_ticks() > self.highlight_until_ms and self.highlight_targets:
            self.highlight_targets.clear()
        
        self.screen.fill(config.color_bg)
        
        remaining = max(0, config.num_mines - self.board.flagged_count())
        time_text = self._format_time(self._elapsed_ms())
        
        hs_text = "00:00"
        if self.high_score is not None:
            hs_text = self._format_time(self.high_score)
            
        self.renderer.draw_header(remaining, time_text, self.hints_left, hs_text)
        
        now = pygame.time.get_ticks()
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                highlighted = (now <= self.highlight_until_ms) and ((c, r) in self.highlight_targets)
                self.renderer.draw_cell(c, r, highlighted)
        
        if self.hint_target:
            hc, hr = self.hint_target
            rect = self.renderer.cell_rect(hc, hr)
            pygame.draw.rect(self.screen, (0, 255, 0), rect, 3)

        self.renderer.draw_result_overlay(self._result_text())
        pygame.display.flip()

    def run_step(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
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
            
            if self.board.win:
                elapsed = self.end_ticks_ms - self.start_ticks_ms
                if self.high_score is None or elapsed < self.high_score:
                    self.high_score = elapsed
                    self.save_highscore(self.high_score)

        self.draw()
        self.clock.tick(config.fps)
        return True


def main() -> int:
    game = Game()
    running = True
    while running:
        running = game.run_step()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())