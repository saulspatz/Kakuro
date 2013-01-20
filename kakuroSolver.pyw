# kakuroSolver.pyw
# Allows the user to enter a kakuro puzzle interactively
# Solves the puzzle an saves it in a form that can be used with the client

# Requires constraint.py avaialble from:
#     http://labix.org/python-constraint

from Tkinter import *
from tkMessageBox import *                    # get standard dialogs
from tkFileDialog import *
import tkFont
import time, os.path
from kakuroCSP import kakuroCSP, sanityCheck

clueFont = ('helevetica', 12, 'bold')
blackFill = 'dark gray'
defaultFill = 'white'
currentFill = 'light blue'

class ClueEntry(LabelFrame):
  # for validation documentation, see
  # http://stackoverflow.com/questions/4140437/python-tkinter-interactively-validating-entry-widget-content

  def __init__(self, master, title, val):
    LabelFrame.__init__(self, master, text=title)
    self.intvar = StringVar()
    self.intvar.set(val)
    cmd = (self.register(self.validate), "%P")
    entry = Entry(self, textvariable=self.intvar, validate="key",
                  validatecommand=cmd)
    entry.grid(row=0,column=0,sticky='ew')
    self.columnconfigure(0, weight=1)
    self.entry = entry

  def get(self):
    try:
      value = int(self.intvar.get())
    except ValueError:        # empty string
      return 0
    if not 3 <= value <= 45:
      showerror("Invalid Value", "Value must be between 3 and 45.")
      return None
    self.entry.delete(0, 'end')
    return value

  def validate(self, proposed):
    return proposed == '' or proposed.isdigit()

class ScrolledCanvas(Frame):
  def __init__(self, parent, width, height, bg, cursor):
    Frame.__init__(self, parent)
    self.pack(expand=YES, fill=BOTH)                  # make me expandable
    canv = Canvas(self, bg=bg, relief=SUNKEN)
    canv.config(width=width, height=height)           # display area size
    canv.config(scrollregion=(0, 0, width, 2000))     # canvas size corners
    canv.config(highlightthickness=0)                 # no pixels to border

    sbar = Scrollbar(self)
    sbar.config(command=canv.yview)                   # xlink sbar and canv
    canv.config(yscrollcommand=sbar.set)              # move one moves other
    sbar.pack(side=RIGHT, fill=Y)                     # pack first=clip last
    canv.pack(side=LEFT, expand=YES, fill=BOTH)       # canv clipped first
    self.canvas = canv

class Board(ScrolledCanvas):
  # View

  def __init__(self, win, parent, width = 600, height = 800, bg = 'white',
               cols = 12, rows = 21, cursor = 'crosshair'):
    rows += 1   # Allow for top and left boundaries
    cols += 1
    cw = ( width-10 ) // cols
    height = cw * rows + 10
    ScrolledCanvas.__init__(self, win, width = width, height = height,
                            bg=bg, cursor=cursor)
    self.cellHeight = self.cellWidth = cw
    self.parent = parent
    self.createCells(height, width, rows, cols)

    self.frozen = False       # respond to mouse clicks
    self.rows = rows
    self.cols = cols

  def createCells(self, height, width, rows, cols):
    # Each cell has a tag starting with R for the row number and a tag starting
    # with C for the column number.

    canvas = self.canvas
    cw = self.cellWidth
    ch = self.cellHeight
    self.x0 = ( width - cols * cw ) // 2          # cell origin is (x0, y0)
    self.y0 = ( height - rows * ch ) // 2

    for c, x in enumerate(range(self.x0, self.x0+cols*cw, cw)):
      for r, y in enumerate(range(self.y0,  self.y0+rows*ch, ch)):
        id = canvas.create_rectangle(x, y, x+cw, y+ch, fill = defaultFill,
                                     tags=('cell', 'R%s' % r, 'C%s' % c))
        if r == 0 or c == 0:
          canvas.addtag_withtag('black', id)
        if r == 0:
          canvas.addtag_withtag('top', id)
        if c == 0:
          canvas.addtag_withtag('left', id)
        tags = canvas.gettags(id)
    canvas.itemconfigure('black', fill = blackFill)
    canvas.tag_bind('cell', '<ButtonPress-1>', self.onClick)
    canvas.tag_bind('cell', '<ButtonPress-3>', self.onRightClick)

  def redraw(self, event):
    self.createCells(event.height, event.width, self.rows, self.cols)

  def onClick(self, event):
    if self.frozen:
      return
    canvas = event.widget

    # first unhighlight the current cell

    canvas.itemconfigure('highlight', fill=blackFill)
    canvas.dtag('highlight', 'highlight')

    obj = canvas.find_withtag('current')
    canvas.addtag_withtag('highlight', obj)
    canvas.addtag_withtag('black', obj)
    canvas.itemconfigure(obj, fill = currentFill)

  def onRightClick(self, event):

    # Unselect a black square

    if self.frozen:
      return
    canvas = event.widget

    # first unhighlight the current cell

    canvas.itemconfigure('highlight', fill=blackFill)
    canvas.dtag('highlight', 'highlight')

    tags = canvas.gettags('current')
    if 'top' in tags or 'left' in tags:
      return
    rTag = [t for t in tags if t.startswith('R')][0]
    cTag = [t for t in tags if t.startswith('C')][0]
    clueTag = 'clue' + rTag + cTag
    canvas.delete(clueTag+'A')
    canvas.delete(clueTag+'D')
    canvas.dtag('current', 'black')
    canvas.itemconfigure('current', fill = defaultFill)

  def printBoard(self):
    pass

class Kakuro(object):

  def __init__(self, win, bg = 'white', cursor = 'crosshair'):
    self.win = win
    self.control=Control(self, win)
    self.board = Board(win, self, bg = bg, cursor=cursor)
    self.setTitle()
    self.board.pack(side = TOP, expand=YES, fill=BOTH)
    self.menu = self.makeMenu(win)
    self.fileSaveDir = '.'        # directory for saving puzzles
    global clueFont
    clueFont= tkFont.Font(family = 'Helvetica', size = 12, weight = 'normal')

  def setTitle(self):
    b = self.board
    self.win.title('Kakuro Solver %d-by-%d' %(b.rows-1, b.cols-1))

  def makeMenu(self, win):
    def notdone():
      showerror('Not implemented', 'Not yet available')

    top = Menu(win)                                # win=top-level window
    win.config(menu=top)                           # set its menu option

    file = top.file = Menu(top, tearoff = 0)
    file.add_command(label='New...', command=self.dimensionDialog, underline=0)
    file.add_command(label='Print', command=self.board.printBoard, underline=0)
    file.add_command(label='Save', command=self.savePuzzle, underline=0)
    file.add_command(label='Quit', command=win.quit, underline=0)
    file.entryconfigure('Save', state="disabled")

    top.add_cascade(label='File', menu=file, underline=0)
    return top

  def solve(self):
    canvas = self.board.canvas
    rows = self.board.rows
    cols = self.board.cols
    acrossClues = dict()
    downClues = dict()

    # add a sentinel black square to the end of each row and column
    for r in range(rows+1):
      across[r, cols] = 0
    for c in range(cols+1):
      down[c, rows] = 0
    for sq in canvas.find_withtag('black'):
      tags = canvas.find_withtag(sq)
      rTag = [t for t in tags if t.startswith('R')][0]
      cTag = [t for t in tags if t.startswith('C')][0]
      r = int(rTag[1:])
      c = int(cTag[1:])
      clueTag = 'clue'+rTag+cTag
      try:
        across[r, c] = int(canvas.find_withtag(clueTag+'A')[0].text)
      except IndexError:
        across[r, c] = 0
      try:
        down[r, c] = int(canvas.find_withtag(clueTag+'D')[0].text)
      except IndexError:
        down[r, c] = 0

    aSum = sum(across.values())
    dSum = sum(down.values())
    if aSum != dSum:
      showerror('Inconcistent Data',
         'Across clues total %d\nDown clues total %d' % (aSum, dSum))
      return []

    #  ******************* TODO **********************
    # Replace showerror with a nonmodal dialog here
    # ************************************************

    bad = sanityCheck(rows, cols, across, down)
    if bad:
      errs = ''
      for b in bad:
        errs += "At row %2d column %sd: Can't make %2d in %d\n" % b
      showerror("Invalid Clues", errs)
      return []
    return kakuroCSP()

  def report(self):
    solns = self.solns
    if not solns:
      showerror('Bad Problem', 'No Solution')
    elif len(solns) == 1:
      self.menu.file.entryconfigure('Save', state='normal')
      if askyesno('One Solution', 'Display the solution?', default='no'):
        self.board.printSolution(solns[0])
    else:
      for idx, soln in enumerate(solns):
        if askyesno('%d Solutions' % len(solns), 'Display solution number %d?'
                     %(idx+1)):
          self.board.printSolution(soln)
        else:
          break

  def dimensionDialog(self):

    # **************** TODO ****************************
    # Change this to a reusable class

    win = self.winDim = Toplevel()
    win.withdraw()  # Remain invisible while we figure out the geometry
    relx= .5
    rely = .3
    master = self.win
    win.transient(master)

    self.var = IntVar(value = self.dim)
    for idx, pick in enumerate(range(4,10)):
      rad = Radiobutton(win, text=str(pick), value=pick, variable=self.var)
      rad.grid(row = 0, column = idx)
    ok = Button(win, text = 'Okay', command = self.okayDim)
    cancel = Button(win, text = 'Cancel', command = self.cancelDim)
    ok.grid(row = 1, column = 1)
    cancel.grid(row = 1, column = 4)

    win.update_idletasks() # Actualize geometry information
    if master.winfo_ismapped():
      m_width = master.winfo_width()
      m_height = master.winfo_height()
      m_x = master.winfo_rootx()
      m_y = master.winfo_rooty()
    else:
      m_width = master.winfo_screenwidth()
      m_height = master.winfo_screenheight()
      m_x = m_y = 0
    w_width = win.winfo_reqwidth()
    w_height = win.winfo_reqheight()
    x = m_x + (m_width - w_width) * relx
    y = m_y + (m_height - w_height) * rely
    if x+w_width > master.winfo_screenwidth():
      x = master.winfo_screenwidth() - w_width
    elif x < 0:
      x = 0
    if y+w_height > master.winfo_screenheight():
      y = master.winfo_screenheight() - w_height
    elif y < 0:
      y = 0
    win.geometry("+%d+%d" % (x, y))
    win.title('Dimension')

    win.deiconify()          # Become visible at the desired location
    win.wait_visibility()
    win.grab_set()           # make modal

  def okayDim(self):
    self.winDim.destroy()
    self.board.drawNew()

  def cancelDim(self):
    self.winDim.destroy()

  def savePuzzle(self):
    # Menu item is enabled if and only if the puzzle has been solved
    # and has exactly one solution

    board = self.borad
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
    fout.write('dim %d by %d\n' % (rows, cols))
    fout.write('#\nSolution\n')

    # **********  TODO ***************

    fout.close()

class Control(Frame):
  def __init__(self, parent, win):
    Frame.__init__(self, win)
    self.parent = parent

    self.pack(side = BOTTOM, expand = NO, fill = X)
    self.helpButton = Button(self, text = 'Help')
    self.helpButton.pack(side = LEFT, expand = YES)

    self.across = ClueEntry(self, "Across", '')
    self.across.pack(side = LEFT, expand = YES)
    self.down = ClueEntry(self, "Down", '')
    self.down.pack(side = LEFT, expand = YES)
    self.getReady()

    self.solveButton = Button(self, text = 'Solve', command = self.parent.solve)
    self.solveButton.pack(side = LEFT, expand = YES)

    self.across.entry.bind('<Key-Return>', self.enterAcross)
    self.across.entry.bind('<Key-KP_Enter>', self.enterAcross)
    self.down.entry.bind('<Key-Return>', self.enterDown)
    self.down.entry.bind('<Key-KP_Enter>', self.enterDown)

  def disable(self):
    self.solveButton.configure(state = 'disabled')
    self.across.configure(state = 'disabled')
    self.down.configure(state = 'disabled')
    self.getReady()

  def enable(self):
    self.solveButton.configure(state = 'normal')
    self.across.configure(state = 'normal')
    self.down.configure(state = 'normal')

  def enterAcross(self, event):
    self.enterValue(event, 'A')

  def enterDown(self, event):
    self.enterValue(event, 'D')

  def enterValue(self, event, direction):
      entry = event.widget
      canvas = self.parent.board.canvas
      tags = canvas.gettags('highlight')

      if not tags:
        showerror('No Cell Selected', 'Please select a cell on order to enter a clue')
        return

      tag = [t for t in tags if t.startswith(direction)]
      rTag = [t for t in tags if t.startswith('R')][0]
      cTag = [t for t in tags if t.startswith('C')][0]
      if direction == 'A':
        clue = self.across.get()
        if 'top' in tags:
          showerror('Invalid Clue', 'Cannot have an across clue here')
          return
      else:
        clue = self.down.get()
        if 'left' in tags:
          showerror('Invalid Clue', 'Cannot have a down clue here')
          return
      if clue is None: return

      canvas.dtag('highlight', tag)
      #canvas.addtag_withtag( direction + str(clue), 'highlight')
      canvas.dtag('highlight', tag)

      clueTag = 'clue' + rTag + cTag + direction
      canvas.delete(clueTag)
      left, top, right, bottom = canvas.bbox('highlight')

      if clue == 0 : return

      if direction == 'A':
        y = top + 2
        x = right - 2
        canvas.create_text(x, y, anchor = NE, tag = clueTag, text = str(clue),
                           font = clueFont)
      else:
        y = bottom - 2
        x = left + 2
        canvas.create_text(x, y, anchor = SW, tag = clueTag, text = str(clue),
                           font = clueFont)

  def getReady(self):
      self.across.entry.focus_set()

def main():
  root = Tk()
  root.wm_geometry('615x650')
  Kakuro(root)
  root.mainloop()

if __name__ == "__main__":
  main()