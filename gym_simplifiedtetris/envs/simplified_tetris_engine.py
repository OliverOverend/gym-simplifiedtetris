import time
from typing import Dict, List, Optional, Sequence, Tuple, Union

import cv2.cv2 as cv
import imageio
import numpy as np
from gym_simplifiedtetris.utils.pieces import PieceCoords
from matplotlib import colors
from PIL import Image

Coords = List[List[Tuple[int, int]]]
Piece_info = Dict[str, Union[Coords, str]]

PIECES_DICT: Dict[int, Dict[int, Piece_info]] = {
    1: {
        0: {
            "coords": [
                [(0, 0)],
            ],
            "name": "O",
        }
    },
    2: {
        0: {
            "coords": [
                [(0, 0), (0, -1)],
                [(0, 0), (1, 0)],
            ],
            "name": "I",
        }
    },
    3: {
        0: {
            "coords": [
                [(0, 0), (0, -1), (0, -2)],
                [(0, 0), (1, 0), (2, 0)],
                [(0, 0), (0, -1), (0, -2)],
                [(0, 0), (1, 0), (2, 0)],
            ],
            "name": "I",
        },
        1: {
            "coords": [
                [(0, 0), (1, 0), (0, -1)],
                [(0, 0), (0, 1), (1, 0)],
                [(0, 0), (-1, 0), (0, 1)],
                [(0, 0), (0, -1), (-1, 0)],
            ],
            "name": "L",
        },
    },
    4: {
        0: {
            "coords": [
                [(0, 0), (0, -1), (0, -2), (0, -3)],
                [(0, 0), (1, 0), (2, 0), (3, 0)],
                [(0, 0), (0, -1), (0, -2), (0, -3)],
                [(0, 0), (1, 0), (2, 0), (3, 0)],
            ],
            "name": "I",
        },
        1: {
            "coords": [
                [(0, 0), (1, 0), (0, -1), (0, -2)],
                [(0, 0), (0, 1), (1, 0), (2, 0)],
                [(0, 0), (-1, 0), (0, 1), (0, 2)],
                [(0, 0), (0, -1), (-1, 0), (-2, 0)],
            ],
            "name": "L",
        },
        2: {
            "coords": [
                [(0, 0), (0, -1), (-1, 0), (-1, -1)],
                [(0, 0), (0, -1), (-1, 0), (-1, -1)],
                [(0, 0), (0, -1), (-1, 0), (-1, -1)],
                [(0, 0), (0, -1), (-1, 0), (-1, -1)],
            ],
            "name": "O",
        },
        3: {
            "coords": [
                [(0, 0), (-1, 0), (1, 0), (0, -1)],
                [(0, 0), (0, -1), (0, 1), (1, 0)],
                [(0, 0), (1, 0), (-1, 0), (0, 1)],
                [(0, 0), (0, 1), (0, -1), (-1, 0)],
            ],
            "name": "T",
        },
        4: {
            "coords": [
                [(0, 0), (-1, 0), (0, -1), (0, -2)],
                [(0, 0), (0, -1), (1, 0), (2, 0)],
                [(0, 0), (1, 0), (0, 1), (0, 2)],
                [(0, 0), (0, 1), (-1, 0), (-2, 0)],
            ],
            "name": "J",
        },
        5: {
            "coords": [
                [(0, 0), (-1, 0), (0, -1), (1, -1)],
                [(0, 0), (0, -1), (1, 0), (1, 1)],
                [(0, 0), (-1, 0), (0, -1), (1, -1)],
                [(0, 0), (0, -1), (1, 0), (1, 1)],
            ],
            "name": "S",
        },
        6: {
            "coords": [
                [(0, 0), (-1, -1), (0, -1), (1, 0)],
                [(0, 0), (1, -1), (1, 0), (0, 1)],
                [(0, 0), (-1, -1), (0, -1), (1, 0)],
                [(0, 0), (1, -1), (1, 0), (0, 1)],
            ],
            "name": "Z",
        },
    },
}


class SimplifiedTetrisEngine:
    """
    A class representing a simplified Tetris engine containing methods
    that retrieve the actions available for each of the pieces in use, drop
    pieces vertically downwards, having identified the correct location to
    drop them, clear full rows, and render a game of Tetris.

    :param grid_dims: the grid dimensions; height, width.
    :param piece_size: the size of the pieces in use.
    :param num_pieces: the number of pieces in use.
    :param num_actions: the number of available actions in each state.
    """

    def __init__(
        self,
        grid_dims: Sequence[int],
        piece_size: int,
        num_pieces: int,
        num_actions: int,
    ):
        self._height, self._width = grid_dims
        self._piece_size = piece_size
        self._num_pieces = num_pieces
        self._num_actions = num_actions

        # Create empty grid and anchor.
        self._grid = np.zeros((grid_dims[1], grid_dims[0]), dtype=int)
        self._anchor = [grid_dims[1] / 2 - 1, piece_size - 1]

        # Initialise render attributes.
        self._final_scores = np.array([], dtype=int)
        self._sleep_time = 500
        self._show_agent_playing = True
        self._cell_size = int(min(0.8 * 1000 / grid_dims[0], 0.8 * 2000 / grid_dims[1]))
        self._LEFT_SPACE = 400
        self._BLACK: tuple = self._get_bgr_code("black")
        self._WHITE: tuple = self._get_bgr_code("white")
        self._RED: tuple = self._get_bgr_code("red")
        self._GRID_COLOURS: list = [
            self._WHITE,  # Empty.
            self._get_bgr_code("cyan"),  # 'I'.
            self._get_bgr_code("orange"),  # 'L'.
            self._get_bgr_code("yellow"),  #  'O'.
            self._get_bgr_code("purple"),  # 'T'.
            self._get_bgr_code("blue"),  # 'J'.
            self._get_bgr_code("green"),  # 'S'.
            self._RED,  # 'Z'.
        ]

        # Initialise an empty _img array.
        self._img = np.array([])

        # Initialise the piece coordinates.
        self._all_piece_coords = PieceCoords(PIECES_DICT[piece_size])
        (
            self._current_piece_coords,
            self._current_piece_id,
        ) = self._all_piece_coords._get_piece_at_random()

        self._get_all_available_actions()
        self._reset()

        # Initialise attributes for saving GIFs.
        self._image_lst = []
        self._save_frame = False

    @staticmethod
    def _get_bgr_code(colour_name: str) -> Tuple[float, float, float]:
        """
        Gets the BGR code corresponding to the arg provided.

        :param colour_name: a string of the colour name,
        :return: an inverted RGB code of the inputted colour name.
        """
        return tuple(np.array([255, 255, 255]) * colors.to_rgb(colour_name))[::-1]

    @staticmethod
    def _close() -> None:
        """Closes the open windows."""
        cv.waitKey(1)
        cv.destroyAllWindows()
        cv.waitKey(1)

    def _reset(self) -> None:
        """Resets the score, grid, piece coords, piece id and anchor."""
        self._score = 0
        self._grid = np.zeros_like(self._grid)
        self._update_coords_and_anchor()

    def _render(self, mode: Optional[str] = "human") -> np.ndarray:
        """
        Shows an image of the current grid, having dropped the current piece.
        The human has the option to pause (SPACEBAR), speed up (RIGHT key),
        slow down (LEFT key) or quit (ESC) the window.

        :param mode: the render mode.
        :return: the image pixel values.
        """

        # Get the grid after dropping the current piece.
        grid = self._get_grid()

        # Convert grid into Image object then into an array.
        self._resize_grid(grid)

        # Draw horizontal and vertical lines between the cells.
        self._draw_separating_lines()

        # Add image to the left.
        self._add_img_left()

        # Draws a horizontal red line to indicate the top of the playfield.
        self._draw_boundary()

        if mode == "human":
            if self._show_agent_playing:

                if self._save_frame:
                    frame_rgb = cv.cvtColor(self._img, cv.COLOR_BGR2RGB)
                    self._image_lst.append(frame_rgb)

                    if len(self._final_scores) == 5:
                        imageio.mimsave(
                            f"assets/{self._height}x{self._width}_{self._piece_size}.gif",
                            self._image_lst,
                            fps=60,
                            duration=0.5,
                        )
                        self._save_frame = False

                cv.imshow("Simplified Tetris", self._img)
                k = cv.waitKey(self._sleep_time)

                # Escape to exit, spacebar to pause and resume.
                if k == 3:  # right arrow
                    self._sleep_time -= 100

                    if self._sleep_time < 100:
                        self._sleep_time = 1

                    time.sleep(self._sleep_time / 1000)
                elif k == 2:  # Left arrow.
                    self._sleep_time += 100
                    time.sleep(self._sleep_time / 1000)
                elif k == 27:  # Esc.
                    self._show_agent_playing = False
                    self._close()
                elif k == 32:  # Spacebar.
                    while True:
                        j = cv.waitKey(30)

                        if j == 32:  # Spacebar.
                            break

                        if j == 27:  # Esc.
                            self._show_agent_playing = False
                            self._close()
                            break

            return self._img

        raise ValueError('Mode should be "human".')

    def _draw_boundary(self) -> None:
        """Draws a horizontal red line to indicate the cut off point."""
        vertical_position = self._piece_size * self._cell_size
        self._img[
            vertical_position
            - int(self._cell_size / 40) : vertical_position
            + int(self._cell_size / 40)
            + 1,
            self._LEFT_SPACE :,
            :,
        ] = self._RED

    def _get_grid(self) -> np.ndarray:
        """
        Gets the array of the current grid containing the colour tuples.

        :return: the array of the current grid.
        """
        grid = [
            [self._GRID_COLOURS[self._grid[j][i]] for j in range(self._width)]
            for i in range(self._height)
        ]
        return np.array(grid)

    def _resize_grid(self, grid: np.ndarray) -> None:
        """
        Reshape the grid, convert it to an Image and resize it, then convert it
        to an array.

        :param grid: the grid to be resized.
        """
        self._img = grid.reshape((self._height, self._width, 3)).astype(np.uint8)
        self._img = Image.fromarray(self._img, "RGB")
        self._img = self._img.resize(
            (self._width * self._cell_size, self._height * self._cell_size)
        )
        self._img = np.array(self._img)

    def _draw_separating_lines(self) -> None:
        """Draws the horizontal and vertical _BLACK lines to separate the grid's cells."""
        for j in range(-int(self._cell_size / 40), int(self._cell_size / 40) + 1):
            self._img[
                [i * self._cell_size + j for i in range(self._height)], :, :
            ] = self._BLACK
            self._img[
                :, [i * self._cell_size + j for i in range(self._width)], :
            ] = self._BLACK

    def _add_img_left(self) -> None:
        """
        Adds the image that will appear to the left of the grid.
        """
        img_array = np.zeros(
            (self._height * self._cell_size, self._LEFT_SPACE, 3)
        ).astype(np.uint8)

        # Calculate the mean score.
        mean_score = (
            0.0 if len(self._final_scores) == 0 else np.mean(self._final_scores)
        )

        # Add statistics.
        self._add_statistics(
            img_array=img_array,
            items=[
                [
                    "Height",
                    "Width",
                    "",
                    "Current score",
                    "Mean score",
                    "",
                    "Current piece",
                ],
                [
                    f"{self._height}",
                    f"{self._width}",
                    "",
                    f"{self._score}",
                    f"{mean_score:.1f}",
                    "",
                    f"{PIECES_DICT[self._piece_size][self._current_piece_id]['name']}",
                ],
            ],
            x_offsets=[50, 300],
        )
        self._img = np.concatenate((img_array, self._img), axis=1)

    def _add_statistics(
        self,
        img_array: np.ndarray,
        items: List[List[str]],
        x_offsets: List[int],
    ) -> None:
        """
        Adds statistics to the array provided.

        :param img_array: the array to be edited.
        :param items: the lists to be added to the array.
        :param x_offsets: the horizontal positions where the statistics should be added.
        """
        for i, item in enumerate(items):
            for count, j in enumerate(item):
                cv.putText(
                    img_array,
                    j,
                    (x_offsets[i], 60 * (count + 1)),
                    cv.FONT_HERSHEY_SIMPLEX,
                    1,
                    self._WHITE,
                    2,
                    cv.LINE_AA,
                )

    def _update_coords_and_anchor(self) -> None:
        """Updates the current piece's coords and ID, and resets the anchor."""
        (
            self._current_piece_coords,
            self._current_piece_id,
        ) = self._all_piece_coords._get_piece_at_random()
        self._anchor = [self._width / 2 - 1, self._piece_size - 1]

    def _is_illegal(self) -> bool:
        """
        Checks if the piece's current position is illegal by looping over each
        of its square blocks.

        Author:
        > Andrean Lay
        Source:
        > https://github.com/andreanlay/tetris-ai-deep-reinforcement-learning/blob/master/src/
        engine.py

        :return: whether the piece's current position is legal.
        """

        # Loop over each of the piece's blocks.
        for i, j in self._piece:
            x_pos, y_pos = int(self._anchor[0] + i), int(self._anchor[1] + j)

            # Don't check if illegal move if block is too high.
            if y_pos < 0:
                continue

            # Check if illegal move. Last condition must come after previous conditions.
            if (
                x_pos < 0
                or x_pos >= self._width
                or y_pos >= self._height
                or self._grid[x_pos, y_pos] > 0
            ):
                return True

        return False

    def _hard_drop(self) -> None:
        """
        Finds the position to place the piece (the anchor) by hard dropping the current piece.

        Author:
        > Andrean Lay
        Source:
        > https://github.com/andreanlay/tetris-ai-deep-reinforcement-learning/blob/master/src/
        engine.py
        """
        while True:
            # Keep going until current piece occupies a full cell, then backtrack once.
            if not self._is_illegal():
                self._anchor[1] += 1
            else:
                self._anchor[1] -= 1
                break

    def _clear_rows(self) -> int:
        """
        Removes blocks from all rows that are full.

        Author:
        > Andrean Lay
        Source:
        > https://github.com/andreanlay/tetris-ai-deep-reinforcement-learning/blob/master/src/
        engine.py

        :return: the number of rows cleared.
        """

        can_clear = [
            (self._grid[:, i + self._piece_size] != 0).all()
            for i in range(self._height - self._piece_size)
        ]
        new_grid = np.zeros_like(self._grid)
        j = self._height - 1

        # Starts from bottom row.
        for i in range(self._height - 1, self._piece_size - 1, -1):

            if not can_clear[i - self._piece_size]:  # Unable to clear.
                new_grid[:, j] = self._grid[:, i]
                j -= 1

        self._grid = new_grid
        return sum(can_clear)

    def _update_grid(self, set_piece: bool) -> None:
        """
        Sets the current piece using the anchor.

        Author:
        > Andrean Lay
        Source:
        > https://github.com/andreanlay/tetris-ai-deep-reinforcement-learning/blob/master/src/
        engine.py

        :param set_piece: whether to set the piece.
        """
        # Loop over each block.
        for i, j in self._piece:
            self._grid[int(i + self._anchor[0]), int(j + self._anchor[1])] = (
                self._current_piece_id + 1 if set_piece else 0
            )

    def _get_reward(self) -> Tuple[float, int]:
        """
        Returns the reward, which is the number of rows cleared.

        :return: the reward and the number of rows cleared.
        """
        num_rows_cleared = self._clear_rows()
        return float(num_rows_cleared), num_rows_cleared

    def _get_all_available_actions(self) -> None:
        """Gets the actions available for each of the pieces in use."""
        self._all_available_actions = {}
        for k in range(self._num_pieces):
            self._current_piece_coords = self._all_piece_coords._select_piece(k)
            self._current_piece_id = k
            self._all_available_actions[k] = self._compute_available_actions()

    def _compute_available_actions(self) -> Dict[int, Tuple[int, int]]:
        """
        Computes the actions that are available with the current piece.

        Author:
        > Andrean Lay
        Source:
        > https://github.com/andreanlay/tetris-ai-deep-reinforcement-learning/blob/master/src/
        engine.py

        :return: the available actions.
        """

        available_actions = {}
        count = 0

        for rotation, piece in enumerate(self._current_piece_coords):
            self._piece = piece.copy()

            max_x = int(max([coord[0] for coord in self._piece]))
            min_x = int(min([coord[0] for coord in self._piece]))

            for translation in range(abs(min_x), self._width - max_x):

                # This ensures that no more than self._num_actions are returned.
                if count == self._num_actions:
                    return available_actions

                self._anchor = [translation, 0]

                self._hard_drop()
                self._update_grid(True)

                # Update available_actions with translation/rotation tuple.
                available_actions[count] = (translation, rotation)

                self._update_grid(False)

                count += 1

        return available_actions
