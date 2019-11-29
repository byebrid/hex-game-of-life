"""hex_game_of_life.py

Author: Byebrid

It's like Conway's game of life, but with a hexagonal grid instead!

Example
-------
>>> Grid()
And you're all good to go! Too easy.

Possible changes
----------------
- I think I need to implement threading (oh no) to make this work the way I 
  want so GUI doesn't constantly freeze up.
"""
import os
import logging
import tkinter as tk
from math import cos, sin, floor, sqrt, pi
import random
import time
import threading
import queue
import concurrent.futures

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
        'alive': 'black',
        'dead': 'green'
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
    """Grid is a container for a grid of Hexagon objects as well as an 
    associated GUI for interacting with these Hexagons.
    
    When a Grid is instantiated, it will automatically display itself.
    """
    def __init__(self):
        """Sets up the window and all its frames, as well as drawing all the 
        Hexagons on the canvas, and calling mainloop() to keep window open."""
        # Keeping track of if currently animating or not
        self.running = False

        # Dict where we will store all hexagons in Grid
        self.hexes = {}

        # Set up window, make widgets and draw the grid of Hexagons to canvas
        self.window = tk.Tk()
        self.window.title("Hexagonal Game of Life")
        self.make_widgets()
        self.canvas.update()
        self.draw_grid()

        self.window.mainloop()

    def resize_grid(self):
        """Delete any Hexagons which are no longer within the window/canvas 
        (window is shrunk) and draw any new Hexagons if they can now fit in the
        window/canvas (window has been made bigger).
        """
        poses_to_pop = []
        for pos, hex in self.hexes.items():
            if hex.is_out_of_bounds():
                hex.delete_from_canvas()
                poses_to_pop.append(pos)
            
        for pos in poses_to_pop:
            self.hexes.pop(pos)

        self.draw_grid()
        self.refresh_counts()
        self.refresh_texts()

    def make_widgets(self):
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
        - self.randomise_p
        - self.r
        - self.fr_limit
        - self.do_show_count
        """
        # Separate window into two frames
        self.top_frame = tk.Frame(self.window)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)
        self.bottom_frame = tk.Frame(self.window)
        self.bottom_frame.pack(side=tk.BOTTOM)
        self.mid_frame = tk.Frame(self.window)
        self.mid_frame.pack(fill=tk.BOTH, expand=True)

        self.menubar = tk.Menu(self.window)
        self.colour_scheme = tk.StringVar()
        self.colour_scheme.set('Default')       

        self.colour_menu = tk.Menu(self.menubar, tearoff = 0)
        for colour_scheme in COLOUR_SCHEMES.keys():
            self.colour_menu.add_radiobutton(
                label=colour_scheme,
                variable=self.colour_scheme,
                value=colour_scheme,
                command=self.refresh_all
                )

        self.menubar.add_cascade(label="Colour", menu = self.colour_menu)
        self.window.config(menu=self.menubar)

        ############# TOP FRAME #############
        # To centre multiple widgets in self.top_frame, put them in their own frame
        self.centre_top_frame = tk.Frame(master=self.top_frame)
        tk.Label(master=self.centre_top_frame, text="Number of alive hexagons:",
            ).pack(side=tk.LEFT)
        self.living_count = tk.IntVar()
        tk.Label(master=self.centre_top_frame, 
            textvariable=self.living_count).pack(side=tk.LEFT)
        self.centre_top_frame.pack()

        # Help text
        def help_box():
            help_window = tk.Toplevel(self.window)
            help_window.maxsize(width=600, height=0)
            help_str = (
                "This is my take on Conway's game of life. It replaces "
                "the classic square grid with a Hexagonal version. The rules of "
                "the system are simple:\n"
                "1) If a cell is 'alive' and it has <2 "
                "or >3 live cells around it, then it dies    as of under/over-population.\n"
                "2) If a cell is 'dead' and it has exactly 3 live neighbours, "
                "then it comes to    life.\n\nClick on a Hexagon to switch its state "
                "or use the Randomise button with the selected probability below to "
                "randomly select hexagons to become alive.\n"
                "If you adjust the window's size, you can fix up the grid with the "
                "Resize button.\nChange the hexagons' 'radii' with the 'r' slider.\n"
                "Change the colour scheme in the menu at the top of the screen (if "
                "on Mac OS)."
            )
            scrollbar = tk.Scrollbar(help_window)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            help_text = tk.Text(help_window, yscrollcommand=scrollbar.set, wrap=tk.WORD)
            help_text.insert(tk.END, help_str)
            help_text.pack()

            scrollbar.config(command=help_text.yview)

        tk.Button(master=self.top_frame, text="Help", command=help_box).pack(side=tk.RIGHT)

        ############# MID FRAME #############
        # Adding canvas to mid frame
        self.canvas = tk.Canvas(master=self.mid_frame, highlightthickness=0, height=700) # f*** highlightthickness
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.update()

        ############# BOTTOM FRAME #############
        # Button to start/stop animation
        self.toggle_animation_text = tk.StringVar()
        self.toggle_animation_text.set("Start")
        tk.Button(self.bottom_frame, 
            textvariable=self.toggle_animation_text,
            command=self.toggle_animation).pack(side=tk.LEFT)

        # Button to randomise states of Hexagons
        tk.Button(self.bottom_frame, 
            text="Randomise", 
            command=self.randomise).pack(side=tk.LEFT)
        
        # Label for changing probability
        tk.Label(self.bottom_frame, text="Probability: ").pack(side=tk.LEFT)
        
        # Slider to change probability
        self.randomise_p = tk.Scale(
            self.bottom_frame, 
            from_=0, to=1,
            resolution=0.01, 
            orient=tk.HORIZONTAL,
            )
        self.randomise_p.pack(side=tk.LEFT)
        # Default p=0.4
        self.randomise_p.set(0.4)

        # Button to set all Hexagons to dead
        tk.Button(self.bottom_frame, 
            text="Clear",
            command=self.clear).pack(side=tk.LEFT)

        # Button to toggle whether to show live neighbour counts of hexagons
        self.do_show_count = tk.BooleanVar() # Default=False
        tk.Checkbutton(
            master=self.bottom_frame,
            text="Show count",
            variable=self.do_show_count,
            command=self.refresh_texts
            ).pack(side=tk.LEFT)

        # Button to reset grid if window has been resized
        tk.Button(master=self.bottom_frame, 
            text="Resize",
            command=self.resize_grid).pack(side="left")

        # Label for 'r' slider
        tk.Label(self.bottom_frame, text="'r': ").pack(side=tk.LEFT)

        def change_r(event):
            """Scales all the Hexagons to new radius"""
            old_r = self.previous_r
            new_r = self.r.get()
            scale_factor = new_r / old_r
            self.canvas.scale("all", 0, 0, scale_factor, scale_factor)
            self.previous_r = new_r

        # Slider to adjust r of Hexagons
        self.previous_r = 20 # For use when resizing Hexes
        self.r = tk.Scale(master=self.bottom_frame,
            from_=10, to=50,
            resolution=1,
            orient=tk.HORIZONTAL,
            command=change_r)
        self.r.pack(side=tk.LEFT)
        self.r.set(self.previous_r)

        # Framerate limit Entry field
        self.fr_limit = tk.DoubleVar()
        self.fr_limit.set(5)
        tk.Entry(self.bottom_frame, 
            textvariable=self.fr_limit,
            width=6).pack(side=tk.RIGHT)

        # Frame rate limit label
        tk.Label(self.bottom_frame, text="Framerate Limit: ").pack(side=tk.RIGHT)

    def draw_grid(self):
        """Draws grid of dead hexagons to start off with.
        """
        for y in range(self.max_y_coord + 1):
            for x in range(self.max_x_coord + 1):
                if (x, y) not in self.hexes.keys(): # Only draw if not already drawn
                    self.hexes[(x, y)] = Hexagon(grid=self, x=x, y=y)

    def toggle_animation(self):
        """Switches animation from off to on and vice versa."""
        if self.running == False:
            self.animate()
        elif self.running == True:
            self.stop()

    def animate(self):
        """Animates the grid."""
        self.running = True
        self.toggle_animation_text.set("Stop")

        # Getting duration of each frame at framerate
        expected_frame_length = 1 / self.fr_limit.get()

        # In case any cells have changed states
        while self.running:
            frame_start = time.time()
            self.update()
            frame_end = time.time()
            actual_frame_length = frame_end - frame_start
            if actual_frame_length < expected_frame_length:
                self.window.after(floor(1000 * (expected_frame_length - actual_frame_length))) # stops input annoyingly

    def stop(self):
        """Stops animation and resets text on start/stop button."""
        self.running = False
        self.toggle_animation_text.set("Start")

    def randomise(self):
        """Randomly sets hexes to being alive.

        Parameters
        ----------
        p: floats between 0 & 1, inclusive; default=0.1
            Probability any given hexagon is set to be alive. Note this is not
            necessarily equivalent to the exact proportion of hexagons in Grid
            that will become alive.
        """
        self.stop()
        for hex in self.hexes.values():
            dice_roll = random.random()
            if dice_roll <= self.randomise_p.get():
                hex.state = 1
            else:
                hex.state = 0

    def clear(self):
        """Clears grid of living hexagons; resets all hexagons to dead."""
        for hex in self.hexes.values():
            hex.state = 0

    def update(self):
        """Updates self by one frame according to the game's logic. To be used
        in self.animate().
        """       
        altered_hexes = self.get_altered_hexes() 

        # Stop animation if no more changes of state will occur
        if len(altered_hexes) == 0:
            self.stop()
        else:
            for hex in altered_hexes:
                hex.switch_state()

        self.canvas.update()

    def wrap_coords(self, x, y):
        """Returns tuple of wrapped coordinates. I.e. if something goes out 
        left of screen, it should come back out on the right, etc..
        
        Parameters
        ----------
        x, y: int
            Coordinates of hexagon in Grid. This is NOT the pixel coordinates
            of the hexagon's centre.
        """
        # Get actual max coords used, in case screen has resized
        current_max_x_coord = max([pos[0] for pos in self.hexes])
        current_max_y_coord = max([pos[1] for pos in self.hexes])
        if x > current_max_x_coord:
            new_x = 0
        elif x < 0:
            new_x = current_max_x_coord
        else:
            new_x = x
        if y > current_max_y_coord:
            new_y = 0
        elif y < 0:
            new_y = current_max_y_coord
        else:
            new_y = y

        return (new_x, new_y)

    def refresh_all(self):
        for hex in self.hexes.values():
            hex.refresh()

    def refresh_texts(self):
        """Refreshes the labels on the hexagons showing how many live 
        neighbours they have.
        """
        for hex in self.hexes.values():
            hex.refresh_text()

    def refresh_counts(self):
        for hex in self.hexes.values():
            hex.refresh_count()

    def get_altered_hexes(self):
        """Returns list of hexes that will change state from this frame to the 
        next.
        """
        altered_hexes = []
        for hex in self.hexes.values():
            count = hex.count
            # Really the main logic of the game
            if (count < 2 or count > 3) and hex.state == 1:
                altered_hexes.append(hex)
            elif count == 3 and hex.state == 0:
                altered_hexes.append(hex)

        return altered_hexes

    @property
    def max_x_coord(self):
        """The maximum allowable x coordinate of a Hexagon on this Grid. Note,
        this is NOT the maximum pixel coordinate."""
        l = Hexagon.get_second_r(r=self.r.get())
        return int((self.canvas.winfo_width()) / (2 * l) - 1)

    @property
    def max_y_coord(self):
        """The maximum allowable y coordinate of a Hexagon on this Grid. Note,
        this is NOT the maximum pixel coordinate.
        
        How it's calculated
        -------------------
        Total height for n canvases given by:
            t0 = 2r
            d = 0.5l + r
            Therefore,
            tn = 2r + n(0.5l + r)
            Therefore,
            n = (tn - 2r) ÷ (0.5l + r)
        """
        r = self.r.get()
        l = Hexagon.get_second_r(r=self.r.get())
        h = self.canvas.winfo_height()
        y = floor((h - 2*r) / (0.5*l + r))

        # Prevents error when wrapping coordinates vertically. Imagine you have
        # 3 rows. The bottom row will take up the same horizontal positions as
        # the first. When wrapping, the bottom row's neighbours will somehow
        # become part of the top row, even though they would not really be 
        # adjacent, leading to negative live neighbour counts.
        if y % 2 == 0:
            return y - 1
        return y   


class Hexagon():
    """A hexagon which is drawn on the given Grid object.

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
        # self.r = grid.r.get()
        self.canvas = grid.canvas
        self.count = 0 # The number of neighbours that are alive
        self.draw()

    def __repr__(self):
        return f"Hexagon{self.x, self.y, self.state}"

    @property
    def r(self):
        return self.grid.r.get()

    def draw(self):
        """Draws Hexagon on canvas and makes it clickable.

        Sets
        ----
        self.item_handle: tkinter.Canvas() item
            A reference to the Hexagon on the canvas so we can call 
            .itemconfig() with self.item_handle to change the Hex's colour, etc.
        self.text_handle: tkinter.Canvas() item
            Similarly, a reference to the text displaying how many live 
            neighbours a Hexagon has.
        """
        points = []
        for angle_index in range(7): 
            angle = pi/6 + angle_index * pi/3 # + pi/6 to rotate slightly
            point = [self.pixel_x + self.r * cos(angle), self.pixel_y + self.r * sin(angle)] 
            points.extend(point)

        # Just to handle the event parameter
        def switch_state_cb(event):
            self.switch_state()

        fill_colour = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['dead']
        outline_colour = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['alive']

        # Draw hexagon and bind mouse click on it to switch state
        self.item_handle = self.canvas.create_polygon(*points, fill=fill_colour, outline=outline_colour)
        self.canvas.tag_bind(self.item_handle, '<Button-1>', switch_state_cb)
        self.refresh_fill() # In case of different colour scheme

        # Draw text displaying live neighbour count and also bind it
        self.text_handle = self.canvas.create_text((self.pixel_x, self.pixel_y), text="")
        self.canvas.tag_bind(self.text_handle, '<Button-1>', switch_state_cb)
        # In case text should be displayed (for Hexagons created after __init__)
        self.refresh_text() 

    def refresh(self):
        """Refreshes fill of Hexagon and its text."""
        self.refresh_fill()
        self.refresh_text()

    def refresh_fill(self):
        """Refreshes fill of Hexagon based on colour scheme."""
        fill_colour, _ = self.get_colours_from_state()
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
        else:
            # Ignore first value returned in tuple
            _, label_colour = self.get_colours_from_state()
        self.canvas.itemconfig(self.text_handle, fill=label_colour, text=self.count)

    def refresh_count(self):
        """Refreshes count of live neighbours. Useful when canvas is resized."""
        count = 0
        for neighbour in self.neighbours:
            count += neighbour.state
        self.count = count

    def delete_from_canvas(self):
        """Deletes the Hexagon and its associated text from canvas"""
        self.grid.canvas.delete(self.item_handle) # Delete Hexagon from canvas
        self.grid.canvas.delete(self.text_handle) # Delete text from canvas

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

        # Refresh visuals of Hexagon if req.
        if new_state != current_state:
            self.refresh()

        # Update global living count
        increment = new_state - current_state
        self.grid.living_count.set(self.grid.living_count.get() + increment)

        # Update neighbours `count`s
        for neighbour in self.neighbours:
            neighbour.count += increment
            neighbour.refresh_text() # Needed to ensure accurate counts for all Hexes

    def switch_state(self):
        """Switches state from dead to alive and vice versa"""
        if self.state == 0:
            self.state = 1
        elif self.state == 1:
            self.state = 0

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
            return self.second_r * (2 * self.x + 2)

    @property
    def pixel_y(self):
        """Returns pixel y coordinate based on hex's grid coordinates"""
        return self.r + self.y * (self.r + 0.5 * self.side_length)

    @property
    def neighbours(self):
        """Returns list of references to hex's neighbours in Grid."""
        x, y = self.x, self.y
        if y % 2 == 1:
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

        # Gets references to Hexagons in grid, wrapping coords if necessary
        return [self.grid.hexes[self.grid.wrap_coords(*i)] for i in neighbour_indices]

    def is_out_of_bounds(self):
        """Return True if Hexagon cannot fit on Canvas, False if not"""
        if self.x > self.grid.max_x_coord or self.y > self.grid.max_y_coord:
            return True

    @staticmethod
    def get_second_r(r):
        """The perpendciular distance from the centre to any of the hex's edges."""
        return r * sin(pi/3)

    @staticmethod
    def get_side_length(r):
        a = pi/3
        return sqrt((r - cos(a))**2 + (0 - sin(a))**2)

    def get_colours_from_state(self):
        """Returns tuple of (fill_colour, label_colour) based on state"""
        alive = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['alive']
        dead = COLOUR_SCHEMES[self.grid.colour_scheme.get()]['dead']
        if self.state == 0:
            return (dead, alive)
        elif self.state == 1:
            return (alive, dead)


if __name__ == '__main__':
    grid = Grid()

############################## MAIN CODE ENDS HERE ##############################
logger.info(msg=f"Finished running {os.path.basename(__file__)}")