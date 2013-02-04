# utilities.py

from Tkinter import *
import time

class ScrolledCanvas(Frame):
  def __init__(self, master, width, height, bg, cursor, scrolls = BOTH):
    Frame.__init__(self, master)
    canv = self.canvas = Canvas(self, bg=bg, relief=SUNKEN)
    canv.config(width=width, height=height)           # display area size
    canv.config(scrollregion=(0, 0, width, height))   # canvas size corners
    canv.config(highlightthickness=0)                 # no pixels to border
    canv.grid(row = 0, column = 0, sticky = 'news')

    if scrolls in (BOTH, VERTICAL):
      ybar = Scrollbar(self, orient = VERTICAL)
      ybar.config(command=canv.yview)                   # xlink sbar and canv
      canv.config(yscrollcommand=ybar.set)              # move one moves other
      ybar.grid(row = 0, column = 1, sticky = 'ns')


    if scrolls in (BOTH, HORIZONTAL):
      xbar = Scrollbar(self, orient = HORIZONTAL)
      xbar.config(command=canv.xview)                   # xlink sbar and canv
      canv.config(xscrollcommand=xbar.set)              # move one moves other
      xbar.grid(row = 1, column = 0, sticky = 'ew')

    self.columnconfigure(0, weight = 1)
    self.rowconfigure(0, weight = 1)

  def __getattr__(self, name):
    return getattr(self.canvas, name)

  def __nonzero__(self):
    return True

def displayDialog(win, master, title, modal = False):
  # Win is the toplevel for the dialog
  # master is typically the app main window

  relx= .5
  rely = .3
  win.transient(master)

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
  win.title(title)

  win.deiconify()          # Become visible at the desired location
  if modal:
    win.wait_visibility()
    win.grab_set()           # make modal

class StopWatch(Frame):
  def __init__(self, win):
    Frame.__init__(self, win)
    self.label = Label(self)
    timeFont = ('helevetica', 12, 'bold')
    self.label.config(bd=4, relief=SUNKEN, bg='black',
                      fg = 'yellow', text='00:00', font = timeFont)
    self.state = 'waiting'
    self.afterID = 0
    self.label.pack()

  def start(self):
    self.startTime = time.time()
    self.state = 'running'
    self.label.config(fg = 'green')
    self.onTimer()

  def stop(self):
    if self.state == 'running':
      self.after_cancel(self.afterID)
    self.label.configure(fg = 'red')
    self.state = 'stopped'

  def onTimer(self):
    elapsed = int(time.time() - self.startTime)
    if elapsed >= 3600:
      hours = elapsed // 3600
      elapsed -= 3600*hours
      minutes = elapsed // 60
      seconds = elapsed % 60
      timeText = '%d:%02d:%02d' % (hours, minutes, seconds)
    else:
      minutes = elapsed // 60
      seconds = elapsed % 60
      timeText = '%02d:%02d' % (minutes, seconds)
    self.label.config(text = timeText)
    if self.state == 'running':
      self.afterID = self.after(100, self.onTimer)

  def pause(self):
    self.after_cancel(self.afterID)
    self.label.configure(fg = 'yellow')
    self.elapsedTime = time.time() - self.startTime
    self.state = 'paused'

  def resume(self):
    self.startTime = time.time() - self.elapsedTime
    self.label.config(fg = 'green')
    self.state = 'running'
    self.onTimer()

  def time(self):
    return time.time() - self.startTime

  def setTime(self, seconds):
    self.elapsedTime = seconds