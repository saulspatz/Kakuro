from Tkinter import *
from tkFileDialog import *
import time
from puzzle import Update
from utilities import ScrolledCanvas

clueFont = ('helevetica', 12, 'normal')
answerFont = ('helvetica', 24, 'bold')
blackFill = 'dark gray'
defaultFill = 'white'
currentFill = 'light blue'

class Board(ScrolledCanvas):
  # View

  def __init__(self, master, width = 600, height = 800, bg = 'white',
               cols = 12, rows = 21, cursor = 'crosshair', scrolls = BOTH):

    ScrolledCanvas.__init__(self, master, width = width, height = height,
                            bg=bg, cursor=cursor, scrolls = scrolls)
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
    self.enableSolver()

  def enableSolver(self):
    self.tag_bind('cell', '<ButtonPress-1>', self.solverLeftClick)
    self.tag_bind('cell', '<ButtonPress-3>', self.solverRightClick)
    try:
      self.master.control.enable()
    except AttributeError:          # occurs at app startup
      pass

  def disableSolver(self):
    self.tag_bind('cell', '<ButtonPress-1>', lambda event:None)
    self.tag_bind('cell', '<ButtonPress-3>', lambda event:None)
    self.master.control.disable()

  def solverLeftClick(self, event):

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

  def solverRightClick(self, event):

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
    canvas = self.canvas
    left, top, right, bottom = canvas.bbox('all')

    if fout:
      canvas.postscript(colormode="gray", file=fout,
                        height = bottom-top, width = right-left,
                        x = 10, y = 10)

  def clearSolution(self):
    self.itemconfigure('solution', fill= defaultFill)

  def drawNew(self, rows, cols):
    root = self.winfo_toplevel()
    width = root.winfo_width() - 15
    self.delete('all')
    self.reset(width, rows, cols)

  def displaySolverClues(self, clues):
    canvas = self.canvas
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

  def displayPlayerClues(self, clues):
    canvas = self.canvas
    for clue in clues:
      row, col, across, down = clue.split()
      coords = '%s.%s' % (row, col)
      cell = canvas.find_withtag(coords)
      canvas.addtag_withtag('black', coords)
      if across != '0':
        left, top, right, bottom = canvas.bbox(cell)
        p = canvas.create_polygon(left, top, right, top, right, bottom,
                fill = '', activefill = currentFill, tag = coords)

        canvas.create_text(right-2, top+2, anchor = NE, text = across,
                           fill = 'black', font = clueFont)
      if down != '0':
        left, top, right, bottom = canvas.bbox(cell)
        p = canvas.create_polygon(left, top, left, bottom, right, bottom,
                fill = '', activefill = currentFill, tag = coords)
        canvas.create_text(left+2, bottom-2, anchor = SW, text = down,
                           fill = 'black', font = clueFont)
      if across != '0' or down != '0':
        canvas.create_line(left, top, right, bottom)
    canvas.itemconfigure('black', fill = blackFill)

  def unhighlight(self):
    self.itemconfigure('highlight', fill=blackFill)
    self.dtag('highlight', 'highlight')

  def getClues(self):
    clues = dict()
    for sq in self.find_withtag('black'):
      tags = self.gettags(sq)
      rTag = [t for t in tags if t.startswith('R')][0]
      cTag = [t for t in tags if t.startswith('C')][0]
      r = int(rTag[1:])
      c = int(cTag[1:])
      clueTag = 'clue'+rTag+cTag
      try:
        id = self.find_withtag(clueTag+'A')[0]
        a = int(self.itemcget(id, 'text'))
      except (IndexError, ValueError):
        a = 0
      try:
        id = self.find_withtag(clueTag+'D')[0]
        d = int(self.itemcget(id, 'text'))
      except (IndexError, ValueError):
        d = 0
      clues[r, c] = (a, d)

    return clues

#class Board(Canvas):
    ## View

    #def draw(self, rows, cols):
        #self.bind('<Configure>', self.redraw)
        #width = self.winfo_width()
        #height= self.winfo_height()
        #self.rows = rows
        #self.cols = cols
        #self.createCells(height, width)

        #control = self.parent.control
        #for cage in control.getCages():
            #self.drawCage(cage)
        #updates = control.getEntries()
        #self.postUpdates(updates)

        #self.focusFill = None
        #self.enterCell((0,0))         # initial focus in upper lefthand corner
        #self.focus_set()              # make canvas respond to keystrokes

        #self.activate()               # activate event bindings

    #def redraw(self, event):
        #self.clearAll()
        #self.createCells(event.height, event.width)
        #control = self.parent.control
        #updates = control.getEntries()
        #self.postUpdates(updates)
        #try:
            #self.enterCell(self.focus)
        #except (AttributeError, TypeError):
            #pass

    #def clearAll(self):
        #objects = self.find_all()
        #for object in objects:
            #self.delete(object)

    #def drawNew(self, dim):
        ## Draw a new board

        #self.parent.setTitle()
        #self.clearAll()
        #self.createCells(self.winfo_height(), self.winfo_width(), dim)

    #def highlight(self, cells, color='white', num = 2):
        ## Flash given cells in the given highlight color, num times
        ## It is assumed that the highlight color will never be the
        ## background color of a cell, except perhaps for the cell that
        ## has the focus.

        #rects = []
        #for cell in cells:
            #tag = 'rect%d%d' %cell
            #bg  = self.itemcget(tag, 'fill')
            #if bg != color:
                #rects.append((tag, bg, color))
            #else:
                #rects.append((tag, color, self.focusFill))
        #for k in range(num):
            #for tag, bg, col in rects:
                #self.itemconfigure(tag, fill = col)
            #self.update_idletasks()
            #time.sleep(.1)
            #for tag, bg, col in rects:
                #self.itemconfigure(tag, fill = bg)
            #self.update_idletasks()
            #time.sleep(.1)

    #def candidateString(self, cands):
        ## String representation of a list of candidates

        #if not cands:
            #return ''
        #string = ''.join([str(x) if x in cands else ' ' for x in range(1,1+self.dim)])
        #return string[:3] + '\n' + string[3:6] + '\n' + string[6:]

    #def enterCell(self, cell):
        ## Cell is (col, row) pair
        ## Give focus to cell
        ## Sets self.focus and self.focusFill

        #try:                                # release old focus, if any
            #tag = 'rect%d%d' % self.focus
            #self.itemconfigure(tag, fill = self.focusFill)
        #except TypeError:
            #pass
        #tag = 'rect%d%d' % cell
        #self.focus = cell
        #self.focusFill = self.itemcget(tag, 'fill')
        #self.itemconfigure(tag, fill = 'white')

    #def postUpdates(self, updates):
        ## Each update is an object of class Update

        #for update in updates:
            #coords = update.coords
            #cands  = update.candidates
            #answer = update.answer
            #atag = 'a%d%d' % coords
            #ctag = 'c%d%d' % coords

            #if answer:
                #self.itemconfigure(ctag, text = '' )
                #self.itemconfigure(atag, text = str(answer))
            #else:
                #self.itemconfigure(ctag, text = self.candidateString(cands))
                #self.itemconfigure(atag, text = '' )

    #def shiftFocus(self, x, y):
        ## User clicked the point (x, y)

        #j = (x - self.x0) // self.cellWidth
        #if not 0 <= j < self.dim:
            #return
        #k = (y - self.y0) // self.cellHeight
        #if not 0 <= k < self.dim:
            #return
        #self.enterCell( (j, k) )

    #def celebrate(self):
        ## Indicate a win by flashing board green
        ## Drop the focus
        ## Deactivate the board

        #all = [(x,y) for x in range(self.dim) for y in range(self.dim)]
        #self.highlight(all, 'green', 4)
        #tag = 'rect%d%d' % self.focus
        #self.itemconfigure(tag, fill = self.focusFill)
        #self.deactivate()
        #del(self.focus)
        #del(self.focusFill)

    #def restart(self, updates):
        ## Clear all solution data from the board, and then post the updates
        ## User wants to start current puzzle over

        #self.itemconfigure('atext', text = '')
        #cstr = self.candidateString([])
        #self.itemconfigure('ctext', text = cstr)
        #self.postUpdates(updates)
        #self.enterCell((0,0))
        #self.activate()

    #def deactivate(self):
        ## Replace the 'Board' bindtag by 'Canvas'.
        ## See defininition of Control in control.py
        ## Board will no longer respond to keypresses and mouseclicks

        #tags = self.bindtags()
        #tags = (tags[0], 'Canvas') + tags[2:]
        #self.bindtags(tags)

    #def activate(self):
        ## Activate event bindings
        ## Reverse of deactivate, above

        #tags = self.bindtags()
        #tags = (tags[0], 'Board') + tags[2:]
        #self.bindtags(tags)

