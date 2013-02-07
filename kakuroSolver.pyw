# kakuroSolver.pyw
# Allows the user to enter a kakuro puzzle interactively
# Solves the puzzle an saves it in a form that can be used with the client

# Requires constraint.py avaialble from:
#     http://labix.org/python-constraint

from Tkinter import *
from tkMessageBox import *                    # get standard dialogs
from tkFileDialog import *
import tkFont
import time, os.path, re
import kakuroCSP, thread
from utilities import displayDialog
from board import Board


clueFont = ('helevetica', 12, 'normal')
answerFont = ('helvetica', 24, 'bold')
noticeFont = ('helvetica', 18, 'bold')
blackFill = 'dark gray'
defaultFill = 'white'
currentFill = 'light blue'

class ScrolledCanvas(Frame):
  def __init__(self, master, width, height, bg, cursor):
    Frame.__init__(self, master)
    canv = Canvas(self, bg=bg, relief=SUNKEN)
    canv.config(width=width, height=height)           # display area size
    canv.config(scrollregion=(0, 0, width, height))   # canvas size corners
    canv.config(highlightthickness=0)                 # no pixels to border

    sbar = Scrollbar(self)
    sbar.config(command=canv.yview)                   # xlink sbar and canv
    canv.config(yscrollcommand=sbar.set)              # move one moves other
    sbar.pack(side=RIGHT, fill=Y)                     # pack first=clip last
    canv.pack(side=LEFT, expand=YES, fill=BOTH)       # canv clipped first
    self.canvas = canv


class Board(ScrolledCanvas):
  # View

  def __init__(self, master, width = 600, height = 800, bg = 'white',
               cols = 12, rows = 21, cursor = 'crosshair'):

    ScrolledCanvas.__init__(self, master, width = width, height = height,
                            bg=bg, cursor=cursor)
    self.reset(width, rows, cols)
    self.master = master

  def reset(self, width, rows, cols):
    rows += 1   # Allow for top and left boundaries
    cols += 1
    cw = ( width-10 ) // cols
    height = cw * rows + 10
    self.cellHeight = self.cellWidth = cw
    self.canvas.config(scrollregion=(0, 0, width, height))
    self.createCells(height, width, rows, cols)
    self.rows = rows
    self.cols = cols

  def createCells(self, height, width, rows, cols):
    # Each cell has a tag starting with R for the row number and a tag starting
    # with C for the column number.  It also has a tag of the form row.col to
    # allow direct access.  Black squares have two associated text objects,
    # one for each clue.  These are initially set to empty strings.

    canvas = self.canvas
    cw = self.cellWidth
    ch = self.cellHeight
    self.x0 = ( width - cols * cw ) // 2          # cell origin is (x0, y0)
    self.y0 = ( height - rows * ch ) // 2

    for c, x in enumerate(range(self.x0, self.x0+cols*cw, cw)):
      for r, y in enumerate(range(self.y0,  self.y0+rows*ch, ch)):
        rTag = 'R%s' % r
        cTag = 'C%s' % c
        clueTag = 'clue'+rTag + cTag
        coords = '%d.%d' % (r, c)
        id = canvas.create_rectangle(x, y, x+cw, y+ch, fill = defaultFill,
                                     tags=('cell', rTag, cTag, coords))
        if r == 0 or c == 0:
          canvas.addtag_withtag('black', id)
        if r == 0:
          canvas.addtag_withtag('top', id)
        if c == 0:
          canvas.addtag_withtag('left', id)
        if r == rows-1:
          canvas.addtag_withtag('bottom', id)
        if c == cols-1:
          canvas.addtag_withtag('right', id)
        canvas.create_text(x+cw-2, y+2, anchor = NE, tag = clueTag+'A',
                           text = '', font = clueFont)
        canvas.create_text(x+2, y+ch-2, anchor = SW, tag = clueTag+'D',
                                   text = '', font = clueFont)
    canvas.itemconfigure('black', fill = blackFill)
    canvas.tag_bind('cell', '<ButtonPress-1>', self.onClick)
    canvas.tag_bind('cell', '<ButtonPress-3>', self.onRightClick)

  def onClick(self, event):

    canvas = event.widget
    control = self.master.control
    acrossScale = control.acrossScale
    downScale = control.downScale

    acrossScale.configure(state = DISABLED)
    downScale.configure(state = DISABLED)

    # first unhighlight the current cell

    canvas.itemconfigure('highlight', fill=blackFill)
    canvas.dtag('highlight', 'highlight')

    obj = canvas.find_withtag('current')
    canvas.addtag_withtag('highlight', obj)
    canvas.addtag_withtag('black', obj)
    canvas.itemconfigure(obj, fill = currentFill)

    tags = canvas.gettags('current')
    rTag = [tag for tag in tags if tag.startswith('R')][0]
    cTag = [tag for tag in tags if tag.startswith('C')][0]
    clueTag = 'clue' + rTag + cTag

    aText = canvas.itemcget(clueTag+'A', 'text')
    aClue = int(aText) if aText else 0
    acrossScale.configure(state = NORMAL)
    acrossScale.set(aClue)
    if 'top' in tags or 'right' in tags:
      acrossScale.configure(state = DISABLED)

    dText = canvas.itemcget(clueTag+'D', 'text')
    dClue = int(dText) if dText else 0
    downScale.configure(state = NORMAL)
    downScale.set(dClue)
    if 'bottom' in tags or 'left' in tags:
      downScale.configure(state = DISABLED)

  def onRightClick(self, event):

    # Unselect a black square

    canvas = event.widget

    control = self.master.control
    acrossScale = control.acrossScale
    downScale = control.downScale

    # first unhighlight the highlighted cell

    canvas.itemconfigure('highlight', fill=blackFill)
    canvas.dtag('highlight', 'highlight')

    # Erase any clues
    tags = canvas.gettags('current')
    rTag = [tag for tag in tags if tag.startswith('R')][0]
    cTag = [tag for tag in tags if tag.startswith('C')][0]
    clueTag = 'clue' + rTag + cTag
    for scale in (acrossScale, downScale):
      scale.configure(state = NORMAL)
      scale.set(0)
      scale.configure(state = DISABLED)
    for d in ('A', 'D'):
      canvas.itemconfigure(clueTag+d, text = '')

    if 'top' not in tags and 'left' not in tags:
      canvas.dtag('current', 'black')
      canvas.itemconfigure('current', fill = defaultFill)

  def showSolution(self, idx):
    canvas = self.canvas
    master = self.master
    soln = master.solns[idx]
    variables = master.vars
    canvas.delete('solution')
    for v in variables:
      coords = '%s.%s' % v
      cell = canvas.find_withtag(coords)[0]
      left, top, right, bottom = canvas.bbox(cell)
      x = (left + right)//2
      y = (top+bottom)//2
      canvas.create_text(x, y, anchor=CENTER, fill='dark green',
                         text = str(soln[v]),
                         tag='solution', font = answerFont)
    master.menu.file.entryconfigure('Clear', state = NORMAL)

  def printBoard(self):
    fout = asksaveasfilename( filetypes=[('postscript files', '.ps')],
                            title='Print to File',
                            defaultextension='ps')
    #height = self.cellHeight * self.rows + 5
    #width  = self.cellWidth * self.cols + 5
    canvas = self.canvas
    left, top, right, bottom = canvas.bbox('all')

    if fout:
      canvas.postscript(colormode="gray", file=fout,
                        height = bottom-top, width = right-left,
                        x = 10, y = 10)

class Kakuro(Frame):

  def __init__(self, master, bg = 'white', cursor = 'crosshair'):
    Frame.__init__(self, master)
    self.pack(expand = YES, fill = BOTH)
    self.master = master
    self.board = Board(self, bg = bg, cursor=cursor)
    self.control = Control(self)
    self.setTitle()
    self.control.pack(side=BOTTOM, expand=YES, fill = X)
    self.board.pack(side=TOP, expand = YES, fill = BOTH)
    self.menu = self.makeMenu(master)
    self.fileSaveDir = '.'        # directory for saving puzzles
    self.fileOpenDir = '.'        # directory for saved puzzles

  def setTitle(self):
    b = self.board
    self.master.title('Kakuro Solver %d-by-%d' %(b.rows-1, b.cols-1))

  def makeMenu(self, win):
    def notdone():
      showerror('Not implemented', 'Not yet available')

    top = Menu(win)                                # win=top-level window
    win.config(menu=top)                           # set its menu option

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

  def clearSolution(self):
    canvas = self.board.canvas
    canvas.itemconfigure('solution', fill='white')
    self.menu.file.entryconfigure('Clear', state = DISABLED)

  def solve(self):
    canvas = self.board.canvas
    rows = self.board.rows
    cols = self.board.cols
    across = dict()
    down = dict()

    # unhighlight any highlighted cell
    canvas.itemconfigure('highlight', fill=blackFill)
    canvas.dtag('highlight', 'highlight')

    # add a sentinel black square to the end of each row and column
    for r in range(rows+1):
      across[r, cols] = 0
    for c in range(cols+1):
      down[rows, c] = 0

    for sq in canvas.find_withtag('black'):
      tags = canvas.gettags(sq)
      rTag = [t for t in tags if t.startswith('R')][0]
      cTag = [t for t in tags if t.startswith('C')][0]
      r = int(rTag[1:])
      c = int(cTag[1:])
      clueTag = 'clue'+rTag+cTag
      try:
        id = canvas.find_withtag(clueTag+'A')[0]
        across[r,c] = int(canvas.itemcget(id, 'text'))
      except (IndexError, ValueError):
        across[r, c] = 0
      try:
        id = canvas.find_withtag(clueTag+'D')[0]
        down[r, c] = int(canvas.itemcget(id, 'text'))
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

    left, top, right, bottom = canvas.bbox('all')
    canvas.create_text(left+20, top+20, anchor = NW, text = "Solving 00:00",
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
      canvas.itemconfigure('notice', text = timeText)
      canvas.update_idletasks()

    self.solns = kakuroCSP.solutions
    self.vars  = kakuroCSP.variables

    self.report()
    self.board.canvas.delete('notice')   # solution timer created this object

  def errorDialog(self, errs):
    win = Toplevel()
    win.withdraw()

    label = Label(win, text = errs)
    label.grid(row= 0, column = 0)
    button = Button(win, text = 'Okay', command = win.destroy)

    displayDialog(win, self.master, 'Invalid Clues')

  def report(self):
    solns = self.solns
    if not solns:
      showerror('Bad Problem', 'No Solution')
    elif len(solns) == 1:
      self.menu.file.entryconfigure('Save', state = NORMAL)
      if askyesno('One Solution', 'Display the solution?', default='no'):
        self.board.showSolution(0)
    else:
      for idx, soln in enumerate(solns):
        if askyesno('%d Solutions' % len(solns), 'Display solution number %d?'
                     %(idx+1)):
          self.board.showSolution(idx)
        else:
          break

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

    displayDialog(win, self.master, 'Dimension', True)

  def okayDim(self):
    self.winDim.destroy()
    rows = int(self.rowVar.get())
    cols = int(self.colVar.get())
    self.drawNew(rows, cols)

  def drawNew(self, rows, cols):
    root = self.master
    board = self.board
    self.menu.file.entryconfigure('Save', state = DISABLED)
    width = root.winfo_width() - 15
    board.canvas.delete('all')
    board.reset(width, rows, cols)
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
    for clue in clues:
      row, col, across, down = clue.split()
      aTag = 'clueR%sC%sA' % (row, col)
      dTag = 'clueR%sC%sD' % (row, col)
      coords = '%s.%s' % (row, col)
      cell = canvas.find_withtag(coords)
      canvas.addtag_withtag('black', coords)
      if across != '0':
        canvas.itemconfigure(aTag, text = across)
      if down != '0':
        canvas.itemconfigure(dTag, text = down)
    canvas.itemconfigure('black', fill = blackFill)

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

  def wrapup(self):
    if self.menu.file.entrycget('Save', 'state') == NORMAL:
      if askyesno('Puzzle Not Saved', "Save Current Puzzle?"):
        self.savePuzzle()
    self.master.destroy()

class Control(Frame):
  def __init__(self, master):
    Frame.__init__(self, master)
    self.board = master.board
    self.master = master

    helpButton = Button(self, text = 'Help', command = self.help)

    solveButton = Button(self, text = 'Solve',
                              command = master.solve)

    self.across = IntVar()
    self.down = IntVar()
    self.acrossScale = Scale(self, orient = HORIZONTAL, from_ = 0, to = 45,
                        label = 'Across', variable = self.across,
                        command = self.enterAcross, state = DISABLED)
    self.downScale = Scale(self, orient = HORIZONTAL, from_ = 0, to = 45,
                            label = 'Down', variable = self.down,
                            command = self.enterDown, state = DISABLED)

    helpButton.pack(side = LEFT, expand = YES)
    self.acrossScale.pack(side = LEFT, expand = YES)
    self.downScale.pack(side = LEFT, expand = YES)
    solveButton.pack(side = LEFT, expand = YES)

  def help(self):
    win = Toplevel()
    win.withdraw()
    helpText = "Click on a cell to make a black square.\n"
    helpText += "Select a black square to enter clues.\n"
    helpText += "To delete a black square, right-click it.\n"
    Label(win, text = helpText, font = clueFont, justify = LEFT).pack()
    Button(win, text = 'Okay', command = win.destroy).pack()
    displayDialog(win, self.master.master, "Kakuro Help")

  def enterAcross(self, value):
    self.enterValue(value, 'A')

  def enterDown(self, value):
    self.enterValue(value, 'D')

  def enterValue(self, value, direction):
    canvas = self.master.board.canvas
    tags = canvas.gettags('highlight')

    try:
      rTag = [t for t in tags if t.startswith('R')][0]
      cTag = [t for t in tags if t.startswith('C')][0]
      clueTag = 'clue' + rTag + cTag + direction
      text = ('%s' % value) if int(value) >= 3 else ''
      canvas.itemconfigure(clueTag, text = text)
    except IndexError:
      return

  def getReady(self):
      self.across.focus_set()

def main():
  root = Tk()
  root.wm_geometry('615x650')
  app = KakuroSolver(root)
  root.wm_protocol('WM_DELETE_WINDOW', app.wrapup)
  root.mainloop()

if __name__ == "__main__":
  main()