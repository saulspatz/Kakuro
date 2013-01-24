# utilities.py

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