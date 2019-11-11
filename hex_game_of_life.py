"""hex_game_of_life.py

Author: Byebrid

It's like Conway's game of life, but with a hexagonal grid instead!


Example
-----
>>> grid = Grid(width=500, height=500, r=20)
And you're all good to go!

Possible changes
-----
- Make it so we can adjust r value while in the GUI.
- Make it so resizing the screen readjusts all the frames, etc.
"""
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

COLOUR_SCHEMES = {
    'Default': {
        'alive': 'black',
        'dead': 'white'
    },
    'Christmas': {
        'alive': '#d92726', # red
        'dead': '#66b649' # green
    },
    'Neon': {
        'alive': 'green',
        'dead': 'black'
    },
    'Dark': {
        'alive': 'gray',
        'dead': 'black'
    },
    'Greenish purple': {
        'alive': '#9949B6', # purple
        'dead': '#66b649' # green
    }
}


class Grid():
    def __init__(self, width, height, r):
        """Sets up the window and all its frames, as well as drawing all the 
        Hexagons on the canvas, and calling mainloop() to keep window open."""
        # Keeping track of if currently animating or not
        self.running = False
    
        # 'Radius' of hexagons in Grid
        self.r = r

        # Dict where we will store all hexagons in Grid
        self.hexes = {}

        # Set up window, make widgets and draw the grid of Hexagons to canvas
        self.window = tk.Tk()
        self.window.title("Lex's Hexagonal Game of Life")
        self.make_widgets(width=width, height=height)
        self.init_draw()

        self.window.mainloop()

    def make_widgets(self, width, height):
        """Makes:
        - Menubar with colour theme selection
        - Display of count of living Hexagons
        - Main canvas
        - Start/stop button
        - Randomise button (with adjustable probability)
        - Clear button
        - Checkbox to hide/show neighbour counts
        - Framerate limit entry field

        Important things this func creates (also creates others):
        - self.canvas
        - self.top_frame, mid_frame, bottom_frame, centre_top_frame
        - self.colour_scheme
        - self.canvas_init_width
        - self.canvas_init_height
        - self.randomise_p
        - self.fr_limit
        - self.do_show_count
        """
        # Separate window into two frames
        self.top_frame = tk.Frame(self.window)
        self.top_frame.pack(side=tk.TOP)
        self.mid_frame = tk.Frame(self.window)
        self.mid_frame.pack()
        self.bottom_frame = tk.Frame(self.window)
        self.bottom_frame.pack(side=tk.BOTTOM)

        ############# TOP FRAME #############
        def change_colour_scheme():
            self.refresh_fills()
            self.refresh_texts()

        self.menubar = tk.Menu(self.window)
        self.colour_scheme = tk.StringVar()
        self.colour_scheme.set('Default')       

        self.colour_menu = tk.Menu(self.menubar, tearoff = 0)
        for colour_scheme in COLOUR_SCHEMES.keys():
            self.colour_menu.add_radiobutton(
                label=colour_scheme,
                variable=self.colour_scheme,
                value=colour_scheme,
                command=change_colour_scheme
                )

        self.colour_menu.add_separator()
        self.menubar.add_cascade(label="Colour", menu = self.colour_menu)
        self.window.config(menu=self.menubar)

        # To centre multiple widgets in self.top_frame, put them in their own frame
        self.centre_top_frame = tk.Frame(master=self.top_frame)
        tk.Label(master=self.centre_top_frame, text="Number of alive hexagons:",
            ).pack(side=tk.LEFT)
        self.living_count = tk.IntVar()
        self.living_label = tk.Label(master=self.centre_top_frame, 
            textvariable=self.living_count,)
        self.living_label.pack(side=tk.LEFT)
        self.centre_top_frame.pack()

        ############# MID FRAME #############
        # Adding canvas to mid frame
        self.canvas = tk.Canvas(self.mid_frame, width=width, height=height)
        self.canvas.pack(fill=tk.BOTH)
        self.canvas.update()

        self.canvas_init_width = self.canvas.winfo_width()
        self.canvas_init_height = self.canvas.winfo_height()

        ############# BOTTOM FRAME #############
        # Creating button to start/stop animation
        self.start_stop_text = tk.StringVar()
        self.start_stop_text.set("Start")
        tk.Button(self.bottom_frame, 
            textvariable=self.start_stop_text,
            command=self.start_stop).pack(side=tk.LEFT)

        # Button + Entry for probability to randomise states of hexagons
        tk.Button(self.bottom_frame, 
            text="Randomise", 
            command=self.randomise).pack(side=tk.LEFT)
        tk.Label(self.bottom_frame, text="Probability: ").pack(side=tk.LEFT)
        self.randomise_p = tk.Scale(
            self.bottom_frame, 
            from_=0, to=1,
            resolution=0.01, 
            orient=tk.HORIZONTAL,
            )
        self.randomise_p.pack(side=tk.LEFT)
        # Default p=0.4
        self.randomise_p.set(0.4)

        # Button to reset grid to empty/all dead
        tk.Button(self.bottom_frame, 
            text="Clear",
            command=self.clear).pack(side=tk.LEFT)

        # Button to toggle whether to show live neighbour counts of hexagons
        self.do_show_count = tk.BooleanVar()
        tk.Checkbutton(
            master=self.bottom_frame,
            text="Show count",
            variable=self.do_show_count,
            command=self.refresh_texts
            ).pack(side=tk.LEFT)

        # Framerate limit Entry field
        self.fr_limit = tk.DoubleVar()
        self.fr_entry = tk.Entry(self.bottom_frame, 
            textvariable=self.fr_limit,
            width=6)
        self.fr_entry.pack(side=tk.RIGHT)
        # Default to 5 frames/sec
        self.fr_limit.set(5)

        # Frame rate limit label
        tk.Label(self.bottom_frame, text="Framerate Limit: ").pack(side=tk.RIGHT)

    def init_draw(self):
        """To be used in self.__init__(). Draws grid of dead hexagons to start 
        off with.
        """
        for y in range(self.max_y_coord + 1):
            for x in range(self.max_x_coord + 1):
                self.hexes[(x, y)] = Hexagon(grid=self, x=x, y=y)

    def start_stop(self):
        """Switches animation from off to on and vice versa."""
        if self.running == False:
            self.animate()
        elif self.running == True:
            self.stop()

    def animate(self, n=1000):
        """Animates the grid.
        
        Parameters
        ----------
        n: int; default=1000
            Number of frames to animate.
        """
        self.running = True
        self.start_stop_text.set("Stop")

        delay = 1 / self.fr_limit.get()
        # In case any cells have changed states
        # self.refresh_neighbour_counts()
        while n >= 0 and self.running:
            start = time.time()
            self.update()
            n -= 1
            end = time.time()
            if end - start < delay:
                time.sleep(delay - (end-start)) # stops input annoyingly

    def randomise(self):
        """Randomly sets hexes to being alive.

        Parameters
        ----------
        p: floats between 0 & 1, inclusive; default=0.1
            Probability any given hexagon is set to be alive. Note this is not
            neccessarily equivalent to the exact proportion of hexagons in Grid
            that will become alive.
        """
        self.stop()
        for hex in self.hexes.values():
            dice_roll = random.random()
            if dice_roll <= self.randomise_p.get():
                hex.state = 1
            else:
                hex.state = 0
        
        self.refresh_texts()

    def clear(self):
        """Clears grid of living hexagons; resets all hexagons to dead."""
        for hex in self.hexes.values():
            hex.state = 0
        # self.re
        self.refresh_texts()

    def update(self):
        """Updates self by one frame according to the game's logic. To be used
        in self.animate().
        """        
        for hex in self.get_altered_hexes():
            hex.switch_state()

        # Needed because some neighbours don't change state but their count will change
        self.refresh_texts()
     
        self.canvas.update()

        # Stop animation if no more changes of state will occur
        if len(self.get_altered_hexes()) == 0:
            self.stop()

    def wrap_coords(self, x, y):
        """Returns tuple of wrapped coordinates. I.e. if something goes out 
        left of screen, it should come back out on the right, etc..
        
        Parameters
        ----------
        x, y: int
            Coordinates of hexagon in Grid. This is NOT the pixel coordinates
            of the hexagon's centre.
        """
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

    def stop(self):
        """Stops animation and resets text on start/stop button."""
        self.start_stop_text.set("Start")
        self.running = False

    def refresh_fills(self):
        """Resets fills of all Hexagons in Grid"""
        for hex in self.hexes.values():
            hex.refresh_fill()

    def refresh_neighbour_counts(self):
        """Refreshed all Hexagons' live neighbour counts in case they may have
        become innacurate (i.e. when lots of states are changed at once.)."""
        for hex in self.hexes.values():
            hex.refresh_neighbour_count()

    def refresh_texts(self):
        """Refreshes the labels on the hexagons showing how many live 
        neighbours they have.
        """
        for hex in self.hexes.values():
            hex.refresh_text()

    def get_altered_hexes(self):
        """Returns list of hexes that will change state from this frame to the 
        next.
        """
        altered_hexes = []
        for hex in self.hexes.values():
            count = hex.count
            if (count < 2 or count > 3) and hex.state == 1:
                altered_hexes.append(hex)
            elif count == 3 and hex.state == 0:
                altered_hexes.append(hex)

        return altered_hexes

    @property
    def max_x_coord(self):
        """The maximum allowable x coordinate of a Hexagon on this Grid. Note,
        this is NOT the maximum pixel coordinate."""
        l = Hexagon.get_second_r(r=self.r)
        return int(self.canvas_init_width / (2 * l) - 1)

    @property
    def max_y_coord(self):
        """The maximum allowable y coordinate of a Hexagon on this Grid. Note,
        this is NOT the maximum pixel coordinate."""
        # God I need to change this
        l = Hexagon.get_second_r(r=self.r)
        
        def total_height(y_coord):
            return self.r * (2 + y_coord) + y_coord * 0.5 * l
        
        y = 0
        while total_height(y) <= self.canvas_init_height:
            y += 1
        return y        


class Hexagon():
    """A hexagon which is drawn on the given Grid object.
    
    There's only really one method to concern yourself with and that is:
        switch_state(self): This simply switches a cell's state and recolours
        it based on its new state.

    I may move the logic of how a cell changes state from the Grid object to
    this class but not just now.

    Parameters
    ----------
    grid: Grid
        A Grid object which will contain many Hexagons
    x, y: int
        The coordinates of the Hexagon in `grid`. NOT its literal pixel 
        coordinates in the tkinter canvas.
    """
    def __init__(self, grid, x, y):
        self.x = x
        self.y = y
        self.grid = grid
        self.r = grid.r
        self.canvas = grid.canvas
        self.item_handle, self.text = self.init_draw()
        self.count = 0 # The number of neighbours that are alive

    def __repr__(self):
        return f"Hexagon{self.x, self.y, self.state}"
    
    def init_draw(self):
        """Returns tuple of (item_handle, label).

        Actually draws the Hexagon on the canvas, assuming it is dead.

        Also binds self.switch_state() to when we use the mouse to click the 
        Hexagon or its label. 

        Returns
        -------
        (item_handle, label):
        `item_handle` is the reference to the Hexagon in its canvas. This can
        later be used to adjust its fill, etc. using tkinter's .itemconfig().

        `label` is the reference to the text displaying how many live 
        neighbours this Hexagon has.
        """
        points = []
        for angle_index in range(7): 
            angle = pi/6 + angle_index * pi/3 # + pi/6 to rotate slightly
            point = [self.pixel_x + self.r * cos(angle), self.pixel_y + self.r * sin(angle)] 
            points.extend(point)
        
        def switch_state_callback(event):
            self.switch_state()
            self.grid.refresh_texts()

        # Draw hexagon and bind mouse click on it to switch state
        item_handle = self.canvas.create_polygon(*points, fill="white", outline="black")
        self.canvas.tag_bind(item_handle, '<Button-1>', switch_state_callback)

        # Draw text displaying live neighbour count and also bind it
        label = self.canvas.create_text((self.pixel_x, self.pixel_y), text="")
        self.canvas.tag_bind(label, '<Button-1>', switch_state_callback)

        return (item_handle, label)

    def refresh_fill(self):
        """Refreshes fill of Hexagon based on colour scheme."""
        if self.state == 1:
            fill_colour = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['alive']
            outline_colour = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['dead']
        elif self.state == 0:
            fill_colour = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['dead']
            outline_colour = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['alive']
        
        self.canvas.itemconfig(self.item_handle, fill=fill_colour, outline=outline_colour)

    def refresh_text(self):
        """Refreshes the label showing how many live neighbours there are.
        
        Note, this does NOT update the canvas or check that the current
        neighbour count is accurate (which may not be so when clearing, 
        randomising grid, etc.).
        """
        if self.grid.do_show_count.get() == False:
            label_colour = ""
        elif self.state == 0:
            label_colour = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['alive']
        elif self.state == 1:
            label_colour = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['dead']
    
        self.canvas.itemconfig(self.text, fill=label_colour, text=self.count)

    @property
    def state(self):
        """Whether hexagon is alive (1) or dead (0). Defaults to 0."""
        try:
            return self.__state
        except AttributeError:
            # Defaults to 0
            self.__state = 0
            return self.__state

    @state.setter
    def state(self, new_state):
        """Sets self.__state and adjusts fill colour of hexagon accordingly.
        Also updates the `count`s of neighbours, as well as the global count
        of how many living Hexagons there are.
        """
        # Get current state, then set to `new_state`
        current_state = self.state
        self.__state = new_state
        fill_colour = None
        increment = 0
        if new_state == 1 and current_state == 0:
            fill_colour = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['alive']
            label_colour = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['dead']
            increment = 1
        elif new_state == 0 and current_state == 1:
            fill_colour = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['dead']
            label_colour = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['alive']
            increment = -1

        # Update global living count
        self.grid.living_count.set(self.grid.living_count.get() + increment)

        # Update neighbours `count`s
        for neighbour in self.neighbours:
            neighbour.count += increment

        # Colour in hexagon if needed
        if fill_colour:
            self.canvas.itemconfig(self.item_handle, fill=fill_colour, outline=label_colour)
            self.refresh_text()

    def switch_state(self):
        """Switches state from dead to alive and vice versa"""
        if self.state == 0:
            self.state = 1
        elif self.state == 1:
            self.state = 0
        
    def refresh_neighbour_count(self):
        """Resets self.count to correct count. To be used in case lots of 
        states are changed at once.
        """
        self.count = sum([n.state for n in self.neighbours])

    @property
    def second_r(self):
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
        """Returns list of references to hex's neighbours in Grid."""
        x, y = self.x, self.y
        if y % 2 == 0:
            neighbour_indices = [
                (x-1, y  ),
                (x  , y-1),
                (x  , y+1),
                (x+1, y-1),
                (x+1, y  ),
                (x+1, y+1)
            ]
        else:
            neighbour_indices = [
                (x-1, y-1),
                (x-1, y  ),
                (x-1, y+1),
                (x  , y-1),
                (x  , y+1),
                (x+1, y  )
            ]

        # Gets references to Hexagons in grid, wrapping coords if neccessary
        return [self.grid.hexes[self.grid.wrap_coords(*i)] for i in neighbour_indices]

    @staticmethod
    def get_second_r(r):
        """The perpendciular distance from the centre to any of the hex's edges."""
        return r * sin(pi/3)

    @staticmethod
    def get_side_length(r):
        a = pi/3
        return sqrt((r - cos(a))**2 + (0 - sin(a))**2)


if __name__ == '__main__':
    grid = Grid(width=500, height=500, r=25)

############################## MAIN CODE ENDS HERE ##############################
logger.info(msg=f"Finished running {os.path.basename(__file__)}")