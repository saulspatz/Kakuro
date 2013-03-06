# kakuro.py

# Enter and solve kakuro puzzles, both manually and programmatically.
# The main window contains a canvas that will be configured either for
# entering and programmatically solving puzzles (Solver mode), or for
# solving them manually (Player mode).  There will be a two different
# control boxes, one for each mode, but only one will be displayed at a
# time.  There will also be a clock.

from Tkinter import *
from tkMessageBox import *                    # get standard dialogs
from tkFileDialog import *
import tkFont
import thread
import time, os.path, re
from solver import Solver
from player import Player
from utilities import displayDialog, StopWatch
import kakuroCSP

class Kakuro(Frame):

  def __init__(self, master):
    Frame.__init__(self, master)
    self.pack(expand = YES, fill = BOTH)
    self.timer = StopWatch(self)
    self.solver = Solver(self, self.timer)
    self.player = Player(self)
    self.timer.grid(row = 0, column = 0, sticky = 'ew')
    self.player.grid(row = 1, column = 0, sticky = 'news')
    self.player.grid_remove()
    self.solver.grid(row = 1, column = 0, sticky = 'news')
    self.rowconfigure(0, weight = 0)
    self.rowconfigure(1, weight = 1)
    self.columnconfigure(0, weight = 1)
    self.fileSaveDir = '.'        # directory for saving puzzles
    self.fileOpenDir = '.'        # directory for saved puzzles
    self.menu = self.makeMenu()
    self.solver.menu = self.menu
    self.enableSolver()

  def makeMenu(self):
    def notdone():
      showerror('Not implemented', 'Not yet available')

    win = self.winfo_toplevel()
    top = Menu(win)
    win.config(menu=top)

    file = top.file = Menu(top, tearoff = 0)
    file.add_command(label='New', command=self.dimensionDialog, underline=0)
    file.add_command(label='Open', command = self.openFile, underline = 0)
    file.add_command(label='Save', command=self.savePuzzleKro, underline=0)
    file.add_command(label='Clear',command = self.clearSolution, underline=0)
    file.add_command(label='Print', command=self.solver.printBoard, underline=0)
    file.add_command(label='Exit', command=self.wrapup, underline=1)
    file.entryconfigure('Save', state = DISABLED)

    puzzle = top.puzzle = Menu(top, tearoff = 0)
    puzzle.add_command(label='Open',command = self.loadPuzzle,underline = 0)
    puzzle.add_command(label='Save',command=self.savePuzzleKak,underline=0)
    puzzle.add_command(label='Clear',command = notdone, underline=0)
    puzzle.entryconfigure('Save', state = DISABLED)
    puzzle.entryconfigure('Clear', state = DISABLED)

    top.add_cascade(label='File', menu=file, underline=0)
    top.add_cascade(label='Puzzle', menu=puzzle, underline=0)
    return top

  def dimensionDialog(self):
    win = self.winDim = Toplevel()
    win.withdraw()  # Remain invisible while we figure out the geometry

    self.rowVar = StringVar()
    self.colVar = StringVar()
    rowFrame = LabelFrame(win, text = "Rows")
    colFrame = LabelFrame(win, text = "Columns")
    rowEntry = Scale(rowFrame, variable=self.rowVar, orient = VERTICAL,
                     from_ = 4, to = 40)
    colEntry = Scale(colFrame, variable = self.colVar, orient = VERTICAL,
                     from_ = 4, to = 40)
    rowEntry.set(self.solver.rows-1)
    colEntry.set(self.solver.cols-1)
    rowEntry.pack()
    colEntry.pack()

    ok = Button(win, text = 'Okay', command = self.okayDim)
    cancel = Button(win, text = 'Cancel', command = win.destroy)
    ok.grid(row = 1, column = 0)
    rowFrame.grid(row = 0, column = 0)
    colFrame.grid(row = 0, column = 1)
    cancel.grid(row = 1, column = 1)

    displayDialog(win, self.winfo_toplevel(), 'Dimension', True)

  def okayDim(self):
    self.winDim.destroy()
    rows = int(self.rowVar.get())
    cols = int(self.colVar.get())
    self.drawNew(rows, cols, 'Solver')
    self.timer.pause(reset=True)

  def drawNew(self, rows, cols, mode):
    self.menu.file.entryconfigure('Save', state = DISABLED)
    if mode == 'Solver':
      self.solver.drawNew(rows, cols)
      self.enableSolver()
    else:
      self.player.drawNew(rows, cols)
      self.enablePlayer()

  def openFile(self):
    # Mainly for development, to avoid having to enter puzzles
    # over and over
    fname = askopenfile( filetypes = [('Kakuro Files', '.kro')],
                         title = 'Open Puzzle File',
                         defaultextension = 'kro',
                        initialdir = self.fileOpenDir)
    if not fname:
        return
    self.timer.pause(reset = True)
    self.fileOpenDir = os.path.dirname(fname.name)
    text = fname.read()

    dimPattern = re.compile(r'(\d+) by (\d+)')
    rows, cols = dimPattern.search(text).groups()
    self.drawNew(int(rows), int(cols), 'Solver')
    cluePattern = re.compile(r'\d+ +\d+ +\d+ +\d+.*\n')
    clues = cluePattern.findall(text)
    self.solver.displayClues(clues)

  def savePuzzleKro(self):
    # Save puzzle in .kro format
    # Menu item is enabled if and only if the puzzle has been solved
    # and has exactly one solution.
    # If there are more rows than columns, the puzzle is transposed to
    # better fit a computer screen.

    board = self.solver
    rows = board.rows
    cols = board.cols
    fname = asksaveasfilename( filetypes = [('Kakuro Files', '.kro')],
                               title = 'Save Puzzle',
                               defaultextension = 'kro',
                               initialdir = self.fileSaveDir)
    if not fname: return
    # Force a .kro extension in linux
    if not fname.endswith('.kro'):
      fname = fname[:-3] + '.kro'
    self.fileSaveDir = os.path.split(fname[0])
    fout = file(fname, 'w')
    fout.write('# %s\n' % os.path.split(fname)[1])
    fout.write('# %s\n' % time.strftime("%A, %d %B %Y %H:%M:%S"))
    if rows <= cols:
      fout.write('dim %d by %d\n' % (rows-1, cols-1))
    else:
      fout.write('#Transposed from data entry.\n')
      fout.write('dim %d by %d\n' % (cols-1, rows-1))
    fout.write('\nBlack Squares\n')
    fout.write('Row Col Acr Dwn\n\n')

    blacks = board.getClues()
    for b in sorted(blacks):
      clues = blacks[b]
      fout.write('%3s %3s %3s %3s\n' % (b[0], b[1], clues[0], clues[1]))
    fout.write('\nSolution\n')
    fout.write('Row Col Ans\n\n')
    soln = self.solver.getSolution()
    if rows > cols:
      soln = {(k[1], k[0]):soln[k] for k in soln}
    for white in sorted(soln):
      fout.write('%3s %3s %3s\n' % (white[0], white[1], soln[white]))
    fout.close()
    self.menu.file.entryconfigure('Save', state = DISABLED)

  def loadPuzzle(self):
    fname = askopenfile( filetypes = [('Kakuro Files', '.kro')],
                         title = 'Open Puzzle File',
                         defaultextension = 'kro',
                        initialdir = self.fileOpenDir)
    if not fname:
        return
    self.fileOpenDir = os.path.dirname(fname.name)
    text = fname.read()

    dimPattern = re.compile(r'(\d+) by (\d+)')
    rows, cols = dimPattern.search(text).groups()
    self.drawNew(int(rows), int(cols), 'Player')
    cluePattern = re.compile(r'\d+ +\d+ +\d+ +\d+.*\n')
    clues = cluePattern.findall(text)
    self.player.displayClues(clues)
    self.timer.pause(reset = True)

  def savePuzzleKak(self):
    pass

  def clearSolution(self):
    self.solver.clearSolution()
    self.menu.file.entryconfigure('Clear', state = DISABLED)

  def wrapup(self):
    if self.menu.file.entrycget('Save', 'state') == NORMAL:
      if askyesno('Puzzle Not Saved', "Save Current Puzzle?"):
        self.savePuzzleKro()
    self.master.destroy()

  def enableSolver(self):
    if self.player.winfo_ismapped():
      self.player.grid_remove()
      self.player.disable()
      self.solver.grid()
    self.solver.enable()

  def enablePlayer(self):
    if self.solver.winfo_ismapped():
      self.solver.grid_remove()
      self.solver.disable()
      self.player.grid()
    self.player.enable()

def main():
  root = Tk()
  root.wm_geometry('615x650')
  app = Kakuro(root)
  root.wm_protocol('WM_DELETE_WINDOW', app.wrapup)
  root.mainloop()

if __name__ == '__main__':
  main()
