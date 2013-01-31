# kakuro.py

# Enter and solve kakuro puzzles, boyth manually and programmatically.
# The main window contains both a Solver (for enetering puzzles) and a
# Player, for solving them manually, but only one is displayed at any
# given time.

from Tkinter import *
from tkMessageBox import *                    # get standard dialogs
from tkFileDialog import *
import tkFont
import time, os.path, re
