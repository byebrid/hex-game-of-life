'''hex_game_of_life.py

Author: Byebrid

It's like Conway's game of life, but with a hexagonal grid instead!

Notes
-----
- You can view the coordinate system for the hexagonal grid if you set
  `label` to True when you draw each Hexagon. Basically, the coordinates are
  (column, row), with the top left as (0, 0). Because the hexagons are arranged
  the way they are, 'column' may be a slight misnomer but it works well enough
  (though it does lead to some slight inconsistency with parity).
'''
import os
import logging
import tkinter as tk
from math import cos, sin, floor, sqrt, pi
import random
import time

# Change cwd to that of script
path_to_script = os.path.abspath(__file__)
name_of_script = os.path.basename(__file__)
os.chdir(os.path.dirname(path_to_script))

# Setting up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
basename, ext = os.path.splitext(name_of_script) # Separates basename and extension (i.e. '.py')
file_handler = logging.FileHandler(basename + '.log') # Naming log file same as script
formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.info(msg=f"Started running {name_of_script}")
############################# MAIN CODE STARTS HERE #############################

class Grid():
    def __init__(self, width, height, r):
        self.window = tk.Tk()
        self.canvas = tk.Canvas(self.window, width=width, height=height)
        self.canvas.pack()
        self.canvas.update()

        self.r = r

        self.hexes = {}

        self.init_draw()

    def update(self):
        altered_hexes = []
        for hex in self.hexes.values():
            count = hex.live_neighbours_count()
            if (count < 2 or count > 3) and hex.state == 1:
                altered_hexes.append(hex)
            elif count == 3 and hex.state == 0:
                altered_hexes.append(hex)
        
        for hex in altered_hexes:
            hex.switch_state()
        self.canvas.update()

    def animate(self, n=1000):
        while n >= 0:
            self.update()
            n -= 1


    @property
    def max_x_coord(self):
        l = Hexagon.get_second_r(r=self.r)
        return int(self.canvas.winfo_width() / (2 * l) - 1)

    @property
    def max_y_coord(self):
        l = Hexagon.get_second_r(r=self.r)
        
        def total_height(y_coord):
            return self.r * (2 + y_coord) + y_coord * 0.5 * l
        
        y = 0
        while total_height(y) <= self.canvas.winfo_height():
            y += 1
        return y

    def init_draw(self):
        for y in range(self.max_y_coord + 1):
            for x in range(self.max_x_coord + 1):
                self.hexes[(x, y)] = Hexagon(grid=self, x=x, y=y)

    def switch_state(self, x, y):
        self.hexes[(x, y)].switch_state()

    def set_random_states(self, p=0.1):
        """Randomly sets hexes to being alive.

        Note: Actually calls switch_state() so cell will become dead if it was
        previously alive.
        """
        for hex in self.hexes.values():
            dice_roll = random.random()
            if dice_roll <= p:
                hex.switch_state()
        
    def wrap_coords(self, x, y):
        """Returns tuple of wrapped coordinates"""
        if x > self.max_x_coord:
            new_x = 0
        elif x < 0:
            new_x = self.max_x_coord
        else:
            new_x = x
        if y > self.max_y_coord:
            new_y = 0
        elif y < 0:
            new_y = self.max_y_coord
        else:
            new_y = y

        return (new_x, new_y)


class Hexagon():
    """A hexagon which is drawn on the given Grid object.
    
    There's only really one method to convern yourself with and that is:
        switch_state(self): This simply switches a cell's state and recolours
        it based on its new state.

    I may move the logic of how a cell changes state from the Grid object to
    this class but not just now.
    """
    def __init__(self, grid, x, y, state=0):
        self.x = x
        self.y = y
        self.grid = grid
        self.r = grid.r
        self.state = state
        self.canvas = grid.canvas

        self.item_handle = self.init_draw()

    def __repr__(self):
        return f"Hexagon{self.x, self.y, self.state}"
    
    def init_draw(self):
        """Returns canvas item of Hexagon so we can make changes to it using
        itemconfig later on.
        """
        points = []
        for angle_index in range(7): 
            angle = pi/6 + angle_index * pi/3 # + pi/6 to rotate slightly
            point = [self.pixel_x + self.r * cos(angle), self.pixel_y + self.r * sin(angle)] 
            points.extend(point)
        
        return self.canvas.create_polygon(*points, fill="white", outline="black")

    def switch_state(self):
        """Switches state from dead to alive and vice versa"""
        if self.state == 0:
            self.state = 1
            fill_colour = "black"
        elif self.state == 1:
            self.state = 0
            fill_colour = "white"
        
        self.canvas.itemconfig(self.item_handle, fill=fill_colour)

    @property
    def second_r(self):
        """The perpendicular distance from the centre to any edge of the hex."""
        return Hexagon.get_second_r(r=self.r)

    @property
    def side_length(self):
        return Hexagon.get_side_length(r=self.r)

    @property
    def pixel_x(self):
        """Returns pixel x coordinate based on hex's grid coordinates"""
        if self.y % 2 == 0:
            return self.second_r * (2 * self.x + 1)
        else:
            return self.second_r * (2 * self.x)

    @property
    def pixel_y(self):
        """Returns pixel y coordinate based on hex's grid coordinates"""
        return self.r + self.y * (self.r + 0.5 * self.side_length)

    @property
    def neighbours(self):
        """Returns list of coordinates of hex's neighbours in Grid.
        
        These coordinates depend on the parity of hex's y coord.
        """
        x, y = self.x, self.y
        if y % 2 == 0:
            neighbours = [
                (x-1, y  ),
                (x  , y-1),
                (x  , y+1),
                (x+1, y-1),
                (x+1, y  ),
                (x+1, y+1)
            ]
        else:
            neighbours = [
                (x-1, y-1),
                (x-1, y  ),
                (x-1, y+1),
                (x  , y-1),
                (x  , y+1),
                (x+1, y  )
            ]
        
        return neighbours

    def live_neighbours_count(self):
        """Returns how many adjacent hexagons are alive"""
        count = 0
        for x, y in self.neighbours:
            new_x, new_y = self.grid.wrap_coords(x, y)
            neighbour_state = self.grid.hexes[(new_x, new_y)].state
            count += neighbour_state

        return count

    @staticmethod
    def get_second_r(r):
        return r * sin(pi/3)

    @staticmethod
    def get_side_length(r):
        a = pi/3
        return sqrt((r - cos(a))**2 + (0 - sin(a))**2)


grid = Grid(width=1080, height=720, r=40)
grid.set_random_states(p=0.5)
grid.animate()

############################## MAIN CODE ENDS HERE ##############################
logger.info(msg=f"Finished running {os.path.basename(__file__)}")