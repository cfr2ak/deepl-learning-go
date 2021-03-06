from dlgo import types

COLS = 'ABCDEFGHJKLMNOPQRST'
STONE_TO_CHAR = {
    None: ' . ',
    types.Player.black: ' x ',
    types.Player.white: ' o '
}


def print_move(player, move):
    if move.is_pass:
        move_string = 'passes'
    elif move.is_resign:
        move_string = 'resigns'
    else:
        move_string = '%s%d' % (COLS[move.point.col - 1], move.point.row)
    print('%s %s' % (player, move_string))


def print_board(board):
    for row in range(board.num_rows, 0, -1):
        bump = " " if row <= 9 else ""
        line = []
        for col in range(1, board.num_cols + 1):
            stone = board.get_color_on_point(types.Point(row=row, col=col))
            line.append(STONE_TO_CHAR[stone])
        print('%s%d %s' % (bump, row, ''.join(line)))
    print('    ' + '  '.join(COLS[:board.num_cols]))


def point_from_coords(coord):
    column = COLS.index(coord[0]) + 1
    row = int(coord[1:])
    return types.Point(row=row, col=column)


def coords_from_point(point):
    return '%s%d' % (
        COLS[point.col - 1],
        point.row
    )



