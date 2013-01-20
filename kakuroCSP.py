# kakuroCSP.py
# Solve a kakuro puzzle as a constraint satisfaction problem
# Constraint API documentation is available at
# http://labix.org/doc/constraint/
# Documentation isn't very good.  There are examples at
# http://www.csee.umbc.edu/courses/graduate/CMSC671/fall12/code/python/python-constraint-1.1/examples/

from constraint import Problem, ExactSumConstraint, AllDifferentConstraint
from collections import namedtuple

Equation = namedtuple('Equations', 'variables clue')

def kakuroCSP():
  # Pre: variables and equations have been computed by sanityCheck
  # Return (solutions, variables)

  problem = Problem()

  # one variable for each white square, with values in range 1-9

  problem.addVariables(variables, (1,2,3,4,5,6,7,8,9))

  for eq in equations:
    # All the numbers in a single sum are distinct

    problem.addConstraint(AllDifferentConstraint(), eq.variables)

    # The numbers must sum to the clue

    problem.addConstraint(ExactSumConstraint(eq.clue), eq.variables)

  solutions = problem.getSolutions()
  return (solutions, variables)


def sanityCheck(rows, cols, across, down):
  # Returns a list of impossible clues, if any
  # As a SIDE EFFECT, initializes the global equations object, and the
  # the global varaibles object which are used later by kakuroCSP

  # across and down are dicts whose keys are the coords of the black squares,
  # and whose values are the clues.  Besides the blacks square in row and
  # column 0, there are a row and column of sentinel black squares, with
  # inidices row and column.  A clue value of zero means there is no clue.

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

  return (n*(n+1)//2, n*(19-n)//2)







