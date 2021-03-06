from __future__ import absolute_import
from collections import namedtuple
from dlgo.types import Player, Point


class Territory:
    def __init__(self, territory_map):
        self.num_black_territory = 0
        self.num_white_territory = 0
        self.num_black_stones = 0
        self.num_white_stones = 0
        self.num_dame = 0
        self.dame_points = []
        for point, status in territory_map.items():
            if status == Player.black:
                self.num_black_stones += 1
            elif status == Player.white:
                self.num_white_stones += 1
            elif status == 'territory_b':
                self.num_black_territory += 1
            elif status == 'territory_w':
                self.num_white_territory += 1
            elif status == 'dame':
                self.num_dame += 1
                self.dame_points.append(point)


class GameResult(namedtuple('GameResult', 'b w komi')):
    @property
    def winner(self):
        if self.b > self.w + self.komi:
            return Player.black
        else:
            return Player.white

    @property
    def winning_margin(self):
        w = self.w + self.komi
        return abs(self.b - w)

    def __str__(self):
        w = self.w + self.komi
        if self.b > w:
            return 'B+%.1f' % (self.b - w)
        else:
            return 'W+%.1f' % (w - self.b)


def evaluate_territory(board):
    status = {}
    for r in range(1, board.num_rows + 1):
        for c in range(1, board.num_cols + 1):
            point = Point(row=r, col=c)
            if point in status:
                continue
            stone = board.get_color_on_point(point)
            if stone is not None:
                status[point] = stone
            else:
                group, neighbors = _collect_region(point, board)
                if len(neighbors) == 1:
                    neighbor_stone = neighbors.pop()
                    stone_str = 'b' if neighbor_stone == Player.black else 'w'
                    fill_with = 'territory_' + stone_str
                else:
                    fill_with = 'dame'

                for pos in group:
                    status[pos] = fill_with

    return Territory(status)


def _collect_region(start_position, board, visited=None):
    if visited is None:
        visited = {}
    if start_position in visited:
        return [], set()
    all_points = {start_position}
    all_borders = set()
    visited[start_position] = True
    here = board.get_color_on_point(start_position)
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for delta_r, delta_c in deltas:
        next_point = Point(row=start_position.row + delta_r, col=start_position.col + delta_c)
        if not board.is_point_on_grid(next_point):
            continue
        neighbor = board.get_color_on_point(next_point)
        if neighbor == here:
            points, borders = _collect_region(next_point, board, visited)
            all_points += points
            all_borders |= borders
        else:
            all_borders.add(neighbor)
    return all_points, all_borders


def compute_game_result(game_state):
    territory = evaluate_territory(game_state.board)
    return GameResult(
        territory.num_black_territory + territory.num_black_stones,
        territory.num_white_territory + territory.num_white_stones,
        komi=7.5
    )
