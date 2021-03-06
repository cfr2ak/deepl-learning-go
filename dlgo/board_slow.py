import copy
from dlgo.types import Player


class Move:
    def __init__(self, point=None, is_pass=False, is_resign=False):
        assert (point is not None) ^ is_pass ^ is_resign
        self.point = point
        self.is_play = (self.point is not None)
        self.is_pass = is_pass
        self.is_resign = is_resign

    @classmethod
    def play(cls, point):
        return Move(point=point)

    @classmethod
    def pass_turn(cls):
        return Move(is_pass=True)

    @classmethod
    def resign(cls):
        return Move(is_resign=True)


class GoString:
    def __init__(self, color, stones, liberties):
        self.color = color
        self.stones = set(stones)
        self.liberties = set(liberties)

    def remove_liberty(self, point):
        self.liberties.remove(point)

    def add_liberty(self, point):
        self.liberties.add(point)

    def merged_with(self, go_string):
        assert go_string.color == self.color
        combined_stones = self.stones | go_string.stones
        return GoString(
            self.color,
            combined_stones,
            (self.liberties | go_string.liberties) - combined_stones
        )

    @property
    def num_liberties(self):
        return len(self.liberties)

    def __eq__(self, other):
        return isinstance(other, GoString) and \
            self.color == other.color and \
            self.stones == other.stones and \
            self.liberties == other.liberties


class Board:
    def __init__(self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid = {}

    def place_stone(self, player, point):
        self._check_point_validity(point)
        point_info = {
            'adjacent_same_color': [],
            'adjacent_opposite_color': [],
            'liberties': []
        }

        for neighbor in point.neighbors():
            if not self.is_point_on_grid(neighbor):
                continue
            self._update_point_info(player, neighbor, point_info)

        new_string = GoString(player, [point], point_info['liberties'])

        self._merge_with_adjacent_same_string(new_string, point_info)
        self._remove_liberty_of_opposite_string(point, point_info)
        self._remove_string_with_zero_liberty(point_info)

    def is_point_on_grid(self, point):
        return 1 <= point.row <= self.num_rows and \
            1 <= point.col <= self.num_cols

    def get_color_on_point(self, point):
        string = self._grid.get(point)
        if string is None:
            return None
        return string.color

    def get_go_string_on_point(self, point):
        string = self._grid.get(point)
        if string is None:
            return None
        return string

    def _check_point_validity(self, point):
        assert self.is_point_on_grid(point)
        assert self._grid.get(point) is None

    def _update_point_info(self, player, neighbor, point_info):
        neighbor_string = self._grid.get(neighbor)
        if neighbor_string is None:
            point_info['liberties'].append(neighbor)
        elif neighbor_string.color == player:
            self._append_neighbor(neighbor_string, point_info['adjacent_same_color'])
        else:
            self._append_neighbor(neighbor_string, point_info['adjacent_opposite_color'])

    @staticmethod
    def _append_neighbor(neighbor_string, adjacent_list):
        if neighbor_string not in adjacent_list:
            adjacent_list.append(neighbor_string)

    def _merge_with_adjacent_same_string(self, new_string, point_info):
        for same_color_string in point_info['adjacent_same_color']:
            new_string = new_string.merged_with(same_color_string)
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string

    @staticmethod
    def _remove_liberty_of_opposite_string(point, point_info):
        for other_color_string in point_info['adjacent_opposite_color']:
            other_color_string.remove_liberty(point)

    def _remove_string_with_zero_liberty(self, point_info):
        for other_color_string in point_info['adjacent_opposite_color']:
            if other_color_string.num_liberties == 0:
                self._remove_string(other_color_string)

    def _remove_string(self, string):
        for point in string.stones:
            for neighbor in point.neighbors():
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                    neighbor_string.add_liberty(point)
            self._grid[point] = None


class GameState:
    def __init__(self, board, next_player, previous_state, last_move):
        self.board = board
        self.next_player = next_player
        self.previous_state = previous_state
        self.last_move = last_move

    def apply_move(self, move):
        """
        :param move: move applied to Board
        :return: new GameState after applying the move
        """
        if move.is_play:
            next_board = self._get_next_board(move, self.next_player)
        else:
            next_board = self.board

        return GameState(next_board, self.next_player.other, self, move)

    @classmethod
    def new_game(cls, board_size):
        if isinstance(board_size, int):
            board_size = (board_size, board_size)
        board = Board(*board_size)
        return GameState(board, Player.black, None, None)

    def _does_both_sides_passed(self):
        second_last_move = self.previous_state.last_move
        if second_last_move is None:
            return False
        return self.last_move.is_pass and second_last_move.is_pass

    def is_over(self):
        if self.last_move is None:
            return False
        if self.last_move.is_resign:
            return True

        return self._does_both_sides_passed()

    def is_move_self_capture(self, player, move):
        if not move.is_play:
            return False
        next_board = self._get_next_board(move, player)
        new_string = next_board.get_go_string_on_point(move.point)
        return new_string.num_liberties == 0

    def _get_next_board(self, move, player):
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        return next_board

    @property
    def state(self):
        return self.next_player, self.board

    def does_move_violate_ko(self, player, move):
        if not move.is_play:
            return False
        next_board = self._get_next_board(move, player)
        next_state = player.other, next_board
        past_state = self.previous_state
        return self._check_state_exist_ever_before(next_state, past_state)

    @staticmethod
    def _check_state_exist_ever_before(next_state, past_state):
        while past_state is not None:
            if past_state.state == next_state:
                return True
            past_state = past_state.previous_state
        return False

    def is_valid_move(self, move):
        if self.is_over():
            return False
        if move.is_pass or move.is_resign:
            return True
        return (
            self.board.get_color_on_point(move.point) is None and
            not self.is_move_self_capture(self.next_player, move) and
            not self.does_move_violate_ko(self.next_player, move)
        )



