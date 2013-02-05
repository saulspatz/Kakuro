# kakuro.py

# Enter and solve kakuro puzzles, both manually and programmatically.
# The main window contains a canvas that will be configured either for
# entering and programmatically solving puzzles (Solver mode), or for
# solving them manually (Player mode).  There will be a two different
# control boxes, one for each mode, butonly one will be displayed at a
# time.  In Player mode, there will also be a timer.


from Tkinter import *
from tkMessageBox import *                    # get standard dialogs
from tkFileDialog import *
import tkFont
import thread
import time, os.path, re
from board import Board
from utilities import displayDialog
from control import SolverControl
import kakuroCSP

blackFill = 'dark gray'
noticeFont = ('helevetica', 18, 'normal')

class Kakuro(Frame):

  def __init__(self, master, bg = 'white', cursor = 'crosshair'):
    Frame.__init__(self, master)
    self.pack(expand = YES, fill = BOTH)
    self.board = Board(self, bg = bg, cursor=cursor)
    self.control = SolverControl(self)
    self.setTitle()
    self.control.pack(side=BOTTOM, expand=YES, fill = X)
    self.board.pack(side=TOP, expand = YES, fill = BOTH)
    self.menu = self.makeMenu()
    self.fileSaveDir = '.'        # directory for saving puzzles
    self.fileOpenDir = '.'        # directory for saved puzzles

  def setTitle(self):
    b = self.board
    top = self.winfo_toplevel()
    top.title('Kakuro Solver %d-by-%d' %(b.rows-1, b.cols-1))

  def makeMenu(self):
    def notdone():
      showerror('Not implemented', 'Not yet available')

    win = self.winfo_toplevel()
    top = Menu(win)
    win.config(menu=top)

    file = top.file = Menu(top, tearoff = 0)
    file.add_command(label='New', command=self.dimensionDialog, underline=0)
    file.add_command(label='Open', command = self.openFile, underline = 0)
    file.add_command(label='Save', command=self.savePuzzle, underline=0)
    file.add_command(label='Clear',command = self.clearSolution, underline=0)
    file.add_command(label='Print', command=self.board.printBoard, underline=0)
    file.add_command(label='Exit', command=self.wrapup, underline=1)
    file.entryconfigure('Save', state = DISABLED)
    file.entryconfigure('Clear', state = DISABLED)

    top.add_cascade(label='File', menu=file, underline=0)
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
    rowEntry.set(self.board.rows-1)
    colEntry.set(self.board.cols-1)
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
    self.drawNew(rows, cols)

  def drawNew(self, rows, cols):
    self.menu.file.entryconfigure('Save', state = DISABLED)
    self.board.drawNew(rows, cols)
    self.setTitle()

  def openFile(self):
    # Mainly for development, to avoid having to enter puzzles
    # over and over
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
    self.drawNew(int(rows), int(cols))
    cluePattern = re.compile(r'\d+ +\d+ +\d+ +\d+.*\n')
    clues = cluePattern.findall(text)
    self.board.displayClues(clues)

  def savePuzzle(self):
    # Menu item is enabled if and only if the puzzle has been solved
    # and has exactly one solution.
    # If there are more rows than columns, the puzzle is transposed to
    # better fit a computer screen.

    board = self.board
    canvas = board.canvas
    rows = board.rows
    cols = board.cols
    fname = asksaveasfilename( filetypes = [('Kakuro Files', '.kro')],
                               title = 'Save Puzzle',
                               defaultextension = 'kro',
                               initialdir = self.fileSaveDir)
    if not fname: return
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

    blacks = canvas.find_withtag('black')
    blackDict = dict()
    for black in blacks:
      tags = canvas.gettags(black)
      rTag = [t for t in tags if t.startswith('R')][0]
      cTag = [t for t in tags if t.startswith('C')][0]
      clueTag = 'clue' + rTag + cTag
      across = canvas.itemcget(clueTag + 'A', 'text')
      down = canvas.itemcget(clueTag + 'D', 'text')
      if not across: across = 0
      if not down: down = 0
      r = int(rTag[1:])
      c = int(cTag[1:])
      if rows <= cols:
        blackDict[r, c] = (across, down)
      else:
        blackDict[c, r] = (down, across)
    for b in sorted(blackDict):
      clues = blackDict[b]
      fout.write('%3s %3s %3s %3s\n' % (b[0], b[1], clues[0], clues[1]))
    fout.write('\nSolution\n')
    fout.write('Row Col Ans\n\n')
    soln = self.solns[0]
    if rows > cols:
      soln = {(k[1], k[0]):soln[k] for k in soln}
    for white in sorted(soln):
      fout.write('%3s %3s %3s\n' % (white[0], white[1], soln[white]))
    fout.close()
    self.menu.file.entryconfigure('Save', state = DISABLED)

  def clearSolution(self):
    self.board.clearSolution()
    self.menu.file.entryconfigure('Clear', state = DISABLED)

  def wrapup(self):
    if self.menu.file.entrycget('Save', 'state') == NORMAL:
      if askyesno('Puzzle Not Saved', "Save Current Puzzle?"):
        self.savePuzzle()
    self.master.destroy()

  def solve(self):
    board = self.board
    rows = board.rows
    cols = board.cols
    across = dict()
    down = dict()

    # unhighlight any highlighted cell
    board.itemconfigure('highlight', fill=blackFill)
    board.dtag('highlight', 'highlight')

    # add a sentinel black square to the end of each row and column
    for r in range(rows+1):
      across[r, cols] = 0
    for c in range(cols+1):
      down[rows, c] = 0

    for sq in board.find_withtag('black'):
      tags = board.gettags(sq)
      rTag = [t for t in tags if t.startswith('R')][0]
      cTag = [t for t in tags if t.startswith('C')][0]
      r = int(rTag[1:])
      c = int(cTag[1:])
      clueTag = 'clue'+rTag+cTag
      try:
        id = board.find_withtag(clueTag+'A')[0]
        across[r,c] = int(board.itemcget(id, 'text'))
      except (IndexError, ValueError):
        across[r, c] = 0
      try:
        id = board.find_withtag(clueTag+'D')[0]
        down[r, c] = int(board.itemcget(id, 'text'))
      except (IndexError, ValueError):
        down[r, c] = 0

    aSum = sum(across.values())
    dSum = sum(down.values())

    if  aSum == 0:
      showerror('No Puzzle', 'Please enter some clues')
      return []

    if aSum != dSum:
      showerror('Inconsistent Data',
         'Across clues total %d\nDown clues total %d' % (aSum, dSum))
      return []

    bad = kakuroCSP.sanityCheck(rows, cols, across, down)
    if bad:
      errs = ["row %2s col %2s: Can't make %2d in %s\n" % b for b in bad]
      self.errorDialog('\n'.join(errs))
      return []

    left, top, right, bottom = board.bbox('all')
    board.create_text(left+20, top+20, anchor = NW, text = "Solving 00:00",
                                fill = 'yellow', font = noticeFont,
                                tag = 'notice')
    start = time.time()
    kakuroCSP.solverDone = False
    solver = thread.start_new_thread(kakuroCSP.kakuroCSP, ())
    while not kakuroCSP.solverDone:
      elapsed = int(time.time() - start)
      if elapsed >= 3600:
        hours = elapsed // 3600
        elapsed -= 3600*hours
        minutes = elapsed // 60
        seconds = elapsed % 60
        timeText = 'Solving %d:%02d:%02d' % (hours, minutes, seconds)
      else:
        minutes = elapsed // 60
        seconds = elapsed % 60
        timeText = 'Solving %02d:%02d' % (minutes, seconds)
      board.itemconfigure('notice', text = timeText)
      board.update_idletasks()

    self.solns = kakuroCSP.solutions
    self.vars  = kakuroCSP.variables

    self.report()
    board.delete('notice')

def main():
  root = Tk()
  root.wm_geometry('615x650')
  app = Kakuro(root)
  root.wm_protocol('WM_DELETE_WINDOW', app.wrapup)
  root.mainloop()

if __name__ == '__main__':
  main()
