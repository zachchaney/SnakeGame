import pygame
import numpy as np
import random
import time

# Color Variables
color_grid_lines = (255, 255, 255)
color_empty_cell = (20, 20, 20)
color_path_lines = (255, 255, 215)
#color_path_lines = (20, 20, 20)
color_apple = (255, 0, 0)
color_snake = (0, 255, 0)

# Game variables
rows = 20
columns = 20
cellsize = int(1000 / rows)
grid_line_size = 0


# Generate an initial Hamiltonian cycle on an N x M grid starting at cell
# For example, given N = 4 and M = 4, and cell = 1 then
#   grid = [[0 , 1, 2, 3],
#           [4, 5, 6, 7],
#           [8, 9, 10, 11],
#           [12, 13, 14, 15]]
# The output path is then
#   path = [1, 2, 3, 7, 6, 5, 9, 10, 11, 15, 14, 13, 12, 8, 4, 0]
def initial_path(N, M, cell):
    grid = np.arange(N * M).reshape((N, M))
    grid[1::2, 1:] = grid[1::2, :0:-1]
    path = np.concatenate((grid[:, 1:].reshape((1, N * M - N))[0], grid[::-1, 0]))
    path = np.concatenate((path[np.where(path == cell[0])[0][0]:], path[:np.where(path == cell[0])[0][0]]))
    return path


# Returns a new random position for the apple. Possible positions are any cell that does not contain the snake.
def new_apple_position(snake):
    open_cells = [x for x in range(rows * columns) if x not in snake]
    if len(open_cells) == 0:
        return None
    else:
        return random.choice(open_cells)


# Function that updates the surface with the path, snake, and apple
def update_surface(surface, path, snake, apple):
    surface.fill(color_empty_cell)

    # Draw the path, including the ends of the snake
    path_and_snake = np.append(np.insert(path, 0, snake[-1]), snake[0])
    for line in range(len(path_and_snake) - 1):
        pygame.draw.line(surface, color_path_lines, (
            (path_and_snake[line] % columns) * cellsize + cellsize / 2,
            (path_and_snake[line] // rows) * cellsize + cellsize / 2), (
                             (path_and_snake[line + 1] % columns) * cellsize + cellsize / 2,
                             (path_and_snake[line + 1] // rows) * cellsize + cellsize / 2))

    # Draw the snake cells
    for cell in snake:
        pygame.draw.rect(surface, color_snake, ((cell % columns) * cellsize, (cell // rows) * cellsize, cellsize - grid_line_size, cellsize - grid_line_size))

    # Draw the apple
    if apple is not None:
        pygame.draw.rect(surface, color_apple, (
            (apple % columns) * cellsize, (apple // rows) * cellsize, cellsize - grid_line_size, cellsize - grid_line_size))

    pygame.display.update()


# Returns a list of all neighboring cells to 'cell' that lie on 'path'
def neighbors_on_path(cell, path):
    neighbors = []
    if np.any(path == ((cell // columns) - 1) * columns + cell % columns):
        neighbors += [((cell // columns) - 1) * columns + cell % columns]
    if np.any(path == ((cell // columns) + 1) * columns + cell % columns):
        neighbors += [((cell // columns) + 1) * columns + cell % columns]
    if np.any(path == cell + 1) and (cell + 1) % columns != 0:
        neighbors += [cell + 1]
    if np.any(path == cell - 1) and cell % columns != 0:
        neighbors += [cell - 1]
    return neighbors


# Update the Hamiltonian path to decrease the distance from the snake's head to the apple
def update_path(path, snake, apple):

    best_path = path

    # possible_moves is a list of all possible cells that the snake could move to next
    #  - we use path[3:] to avoid re-calculating the given path
    possible_moves = neighbors_on_path(snake[-1], path[3:])

    # Loop through each possible_move
    for next_move in possible_moves:

        # If the snake moves to next_move, then its old path is cut into two:
        #   short_path = the path taken by moving to next_move then continuing on the old path
        #   rem_path = the removed piece of the old path that was 'jumped' by moving to next_move
        short_path = np.concatenate(([path[0]], path[np.where(path == next_move)[0][0]:]))
        rem_path = path[1:np.where(path == next_move)[0][0]]

        # Our goal is to insert rem_path into short_path to create a new hamiltonian cycle
        for i in range(len(rem_path)):

            # possible_breaks is a list of all cells that rem_path[0] could connect back to in short_path
            possible_breaks = neighbors_on_path(rem_path[0], short_path[2:])

            # Loop through each one and determine if we can break short_path at that neighboring cell
            for break_cell_before in possible_breaks:

                # break_cell_after is the next cell in short_path after break_cell_before
                # If the break_cell_before is the last cell in short_path, there's no break_cell_after, so continue
                if np.where(short_path == break_cell_before)[0][0] + 1 < len(short_path):
                    break_cell_after = short_path[np.where(short_path == break_cell_before)[0][0] + 1]
                else:
                    continue

                # If there's a neighboring cell to break_cell_after and rem_path[-1], then we can stitch everything up
                if rem_path[-1] in neighbors_on_path(break_cell_after, path):

                    index = np.where(short_path == break_cell_after)[0][0]
                    new_path = np.concatenate((short_path[:index], rem_path, short_path[index:]))

                    if np.where(new_path == apple) < np.where(path == apple):
                        best_path = new_path

            # If the rem_path is a cycle (i.e. the first and last elements are neighboring), then shift the rem_path
            # and loop len(rem_path) times
            if rem_path[-1] in neighbors_on_path(rem_path[0], path):
                rem_path = np.concatenate((rem_path[1:], [rem_path[0]]))
            else:
                break

    return best_path


def main():
    pygame.init()
    surface = pygame.display.set_mode((columns * cellsize, rows * cellsize))
    pygame.display.set_caption("Deterministic Snake Game")
    surface.fill(color_grid_lines)

    # Initial position of the snake, anywhere on the board
    snake = [random.randint(0, rows * columns)]

    # Initial hamiltonian cycle for the snake
    path = initial_path(rows, columns, snake)

    # Define the initial position of the apple, anywhere but on the snake
    apple = new_apple_position(snake)

    # Draws the path, snake, and apple onto the surface
    update_surface(surface, path, snake, apple)

    # Start a timer
    start_time = time.time()
    end_time = None

    # Count the moves
    moves = 0

    while True:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        # As long as the hamiltonian path is greater than zero, the snake can make a move
        if len(path) > 1:

            # Update the hamiltonian path
            path = update_path(path, snake, apple)

            # Move across the path
            snake.append(path[1])
            path = np.delete(path, 0)
            moves += 1

            # Check to see if the snake has hit the apple
            if snake[-1] == apple:
                apple = new_apple_position(snake)
            else:
                path = np.append(path, snake[0])
                snake.pop(0)

            update_surface(surface, path, snake, apple)

        else:
            if end_time is None:
                end_time = time.time()
                print("Elapsed Time: {}".format(end_time - start_time))
                print("Total Moves: {}".format(moves))

        #time.sleep(0.2)


if __name__ == "__main__":
    main()
