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


class Hexagon():
    def __init__(self, canvas, x, y, r, state=0, visible=True, label=False):
        """
        Parameters
        ----------
        canvas: tkinter.Canvas()
            Canvas to draw hexagon on
        x: int
            The x-coordinate of the hexagon. Not its literal pixel position
        y: int
            The y-coordinate of the hexagon. Not its literal pixel position
        r: int
            The 'radius' of the hexagon; the distance from its centre to any
            one of its vertices
        state: 1 or 0; default=0
            If 1, then the hexagon is alive. If 0, then the hexagon is dead.
            Note: choosing 1 as the alive state makes counting the number of
            alive neighbours slightly easier
        visible: boolean; default=True
            Whether to draw this hexagon on the canvas or not
        label: boolean; default=False
            Whether to label hexagon with its coordinates in the grid.
            Note: Only has an effect if `draw` == True.
        """ 
        self.canvas = canvas
        self.x = x
        self.y = y
        self.r = r
        self.label = label
        self.visible = visible
        self.state = state
        # Draw self and get its item ID so we can call it back later
        self.canvas_ref = self.draw()

    def __repr__(self):
        return f"Hexagon@({self.x}, {self.y})"

    def draw(self):
        """Returns canvas item, drawn as a hexagon."""
        if not self.visible:
            return

        points = []
        for angle_index in range(7): 
            angle = pi/6 + angle_index * pi/3 # + pi/6 to rotate slightly
            point = [self.pixel_x + self.r * cos(angle), self.pixel_y + self.r * sin(angle)] 
            points.extend(point)
        
        if self.label:
            if self.state == 0:
                label_colour = "black"
            elif self.state == 1:
                label_colour = "white"
            
            self.canvas.create_text(self.pixel_x, self.pixel_y, 
                text=(self.x, self.y), 
                fill=label_colour)

        # Store current colour before changing back to default
        hex_colour = self.colour
        self.colour = self.get_colour_from_state()
        return self.canvas.create_polygon(*points, fill=hex_colour, outline="black", tag=self.tag)

    @property
    def tag(self):
        """The tag this hexagon has on the canvas. To be used in redrawing when
        hexagon changes state.
        """
        # Note, tag can NOT have whitespace
        return f"({self.x},{self.y})"
       
    @property
    def pixel_x(self):
        """Returns pixel's x coordinate of hexagon's centre based off of hex map
        coordinates and its radius
        """
        if self.y % 2 == 0:
            return self.dist_to_edge * (2 * self.x + 1)
        else:
            return self.dist_to_edge * (2 * self.x)

    @property
    def pixel_y(self):
        """Returns pixel's y coordinate of hexagon's centre based off of hex map
        coordinates and its radius
        """
        return self.r + self.y * (self.r + 0.5 * self.side_length)

    @property
    def side_length(self):
        """The side length of the hexagon."""
        a = pi/3
        return sqrt((self.r - cos(a))**2 + (0 - sin(a))**2)

    @property
    def dist_to_edge(self):
        """Returns perpendicular distance of centre to any of the hexagon's 
        edges.
        """
        return self.r * sin(pi/3)

    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, state):
        self.__state = state
        self.draw()
            
    @property
    def colour(self):
        try:
            return self.__colour
        except:
            return self.get_colour_from_state()
    
    @colour.setter
    def colour(self, colour):
        self.__colour = colour

    def get_colour_from_state(self):
        if self.state == 0:
            return "white"
        elif self.state == 1:
            return "black"

    @property
    def neighbours(self):
        """Returns coordinates of hex's neighbours in Grid.
        
        These coordinates depend on the parity of hex's y coord.
        """
        x, y = self.x, self.y
        if self.y % 2 == 0:
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


class Grid():
    """Object which stores a grid of Hexagons and can update them according to
    the rules of Lex's game of life.
    """
    def __init__(self, canvas, r):
        self.r = r
        self.canvas = canvas
        self.canvas.update()

        self.example_hex = Hexagon(canvas, 0, 0, r=r, visible=False)

        self.hexes = {}
        
        self.draw()

        print(f"Max coords: {(self.max_x_coord, self.max_y_coord)}")

    def start(self, forever=True):
        """Starts animation of grid
        
        Parameters
        ----------
        forever: True or positive int; default=True
            The number of updates to perform in total. If set to True, then 
            will animate until manually interrupted by user.
        """
        while 0 < forever:
            self.update()

    @property
    def max_x_coord(self):
        """Returns maximum allowable y coordinate for the given `r` and `canvas`"""
        return int(self.canvas.winfo_width() / (2 * self.example_hex.dist_to_edge) - 1)

    @property
    def max_y_coord(self):
        """Returns maximum allowable y coordinate for the given `r` and `canvas`
        
        E.g.
        y | height
        --------
        0 | 2r
        1 | 3r + 1 * 0.5*side_length
        2 | 4r + 2 * 0.5*side_length
        3 | 5r - 3 * 0.5*side_length

        Could definitely be refactored if we consider the total height as an
        arithmetic series.
        """
        r = self.example_hex.r
        l = self.example_hex.side_length
        
        def total_height(y_coord):
            return r * (2 + y_coord) + y_coord * 0.5 * l
        
        y = 0
        while total_height(y) <= self.canvas.winfo_height():
            y += 1
        return y

    def wrap_coords(self, x, y):
        """Returns tuple of (x, y) adjusted if either/both coordinates were
        out of bounds.
        I.e. this means if something moves off the left edge of the screen, it
        will reemerge on the right.
        """
        new_x, new_y = x, y
        if x < 0:
            new_x = self.max_x_coord
        elif x > self.max_x_coord:
            new_x = 0
            
        if y < 0:
            new_y = self.max_y_coord
        elif y > self.max_y_coord:
            new_y = 0

        return (new_x, new_y)

    def draw(self):
        """Draw grid of hexagons"""
        start = time.time()

        for i in range(self.max_x_coord + 1):
            for j in range(self.max_y_coord + 1):
                hexagon = Hexagon(self.canvas, i, j, self.r)
                # hexagon.draw()
                self.hexes[(i, j)] = hexagon

        stop = time.time()
        print(f"Grid draw() took {stop-start} seconds")
        
    def set_random_states(self, p=0.1):
        """Randomly sets all hexagons in grid to either alive or dead.

        Parameters
        ----------
        p: float between 0-1; default=0.1
            The probability of any given cell being set to alive
        """
        for hex in self.hexes.values():
            if random.random() <= p:
                hex.state = 1
                hex.colour = "red"

    def update(self):
        """Updates all hexagons in the grid according to a particular set of
        rules (see below for implementation).

        Basic rules (subject to change in actual code)
        ----------------------------------------------
        If cell is alive:
            If cell has <2 or >3 neighbours, it dies
        If cell is dead:
            If cell has 2 neighbours, it comes to life
        """
        start = time.time()

        # Keep track of altered hexes but DON'T change their state until we've
        # checked all of them
        altered_hexes = []
        for (x, y), hex in self.hexes.items(): 
            count = 0
            for x_key, y_key in hex.neighbours:
                # Wrap around edges if required (i.e. go through left edge, come out right)
                new_x, new_y = self.wrap_coords(x_key, y_key)
                count += self.hexes[(new_x, new_y)].state

            if hex.state == 1:
                if count < 2 or count > 3:
                    altered_hexes.append(hex)

            if hex.state == 0:
                if count == 2:
                    altered_hexes.append(hex)

        # Only delete and redraw hexes that have changed state
        for hex in altered_hexes:
            # Swap the hex's state, delete it from canvas, then redraw
            hex.state = 1 if hex.state == 0 else 0
            # Change hex's colour based on its state
            self.canvas.itemconfig(hex.canvas_ref, fill=hex.get_colour_from_state())
            # self.canvas.delete(self.canvas.find_withtag(hex.tag))
            # hex.draw()
       
        self.canvas.update()
        print(len(self.canvas.find_all()))
        
        stop = time.time()
        print(f"update() took {stop-start} seconds")
        
        
# Creating window and attaching canvas to it
window = tk.Tk()
window.title("Lex's game of life")
canvas = tk.Canvas(window, width=1000, height=1000)
canvas.pack()

# Initialising Grid object
grid = Grid(canvas, r=10)

# Setting some cells to be alive
# grid.set_random_states()
grid.hexes[(20, 10)].state = 1
grid.hexes[(20, 10)].colour = "red"
grid.hexes[(20, 10)].draw()

grid.hexes[(21, 10)].state = 1
grid.hexes[(21, 10)].colour = "red"
grid.hexes[(21, 10)].draw()

grid.hexes[(22, 10)].state = 1
grid.hexes[(22, 10)].colour = "red"
grid.hexes[(22, 10)].draw()

grid.hexes[(23, 10)].state = 1
grid.hexes[(23, 10)].colour = "red"
grid.hexes[(23, 10)].draw()

grid.canvas.update()

# Starting animation of Grid
grid.start()

############################## MAIN CODE ENDS HERE ##############################
logger.info(msg=f"Finished running {os.path.basename(__file__)}")