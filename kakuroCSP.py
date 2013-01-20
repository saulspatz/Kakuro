# kakuroCSP.py
# Solve a kakuro puzzle as a constraint satisfaction problem
# Constraint API documentation is available at
# http://labix.org/doc/constraint/

from constraint import Problem
from collections import namedtuple

Equation = namedtuple('Equations', variables, clue)

def kakuroCSP():
  # across and down are dicts whose keys are the coords of the black squares,
  # and whose values are the clues.  Besides the blacks squares in row and
  # column 0, there are a row and column of sentinel black squares, with
  # inidices row and column.  A clue value of zero means there is no clue.

  pass

def sanityCheck(rows, cols, across, down):
  # Returns a list of impossible clues, if any
  # As a SIDE EFFECT, initializes the global equations object, and the
  # the global varaibles object which are used later by kakuroCSP

  global equations, variables
  equations = []
  contradictions = []

  # One variable for each white square

  variables = [(r, c) for r in range(rows) for c in range(cols) if
                (r, c) not in across]
  for (r, c) in across:
    clue = across[r, c]
    if clue == 0: continue
    # find the next black square in the row
    nextBlack = min([a[1] for a in across if a[0] == r and a[1] > c])
    vs = [(r, col) for col in range(c+1, nextBlack)]
    equations.append(Equation(vs, clue))
    minSum, maxSum = limits(len(vs))
    if not minSum <= clue <= maxSum:
      contradictions.append((r, c, clue, len(vs)))

  for (r, c) in down:
    clue = down[r, c]
    if clue == 0: continue
    # find the next black square in the column
    nextBlack = min([d[0] for d in down if d[1] == c and d[0] > r])
    vs = [(row, c) for row in range(r+1, nextBlack)]
    equations.append(Equation(vs, clue))
    minSum, maxSum = limits(len(vs))
    if not minSum <= clue <= maxSum:
      contradictions.append((r, c, clue, len(vs)))

  return contradictions

def limits(n):
  # maximim and minimum sums in n numbers

  return (n*(n+1)//2, (10-n)*(n+9)//2)







