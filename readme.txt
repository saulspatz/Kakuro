This project is concerned with kakuro. or cross sums puzzles.  A kakuro puzzle
is like a crossword puzzle, but instead of letters you fill in
numbers.  The clues are the totals that the numbers in a particular sum have to
come to.  Each number is a single difit from 1 to 9, and the numbers in each
sum must all be different.

There is a great source of free kakuro puzzles at
http://www.atksolutions.com/games/kakuro.html

These puzzles are rated easy, medium and hard, but I am challenged by the medium
ones.  While I like the puzzles very much, there are some things about the user
interface that I dislike; hence this project.  As a first step, I am writing a
solver program, that allows one to enter a puzzle.  This will also verify that
the puzzle has a unique solution, and display the solution, if desired.  It will
save the puzzle in a format that can then be used by the client program to
interactively solve the puzzle.  The program is modified from a program I wrote
do the same sort or thing for kenken puzzles, and some of the functions don't
make sense yet.

I am writing this not only to enhance my enjoyment in doing the puzzles, but to
advance my ability.  One of the things I don't like about the ATK Solutions site
is that once you solve a puzzle, you can't replay it in any way.  This means
that you can't go back over it to recall any difficult inferences you made, and
to learn from them.  A related problem is that the ATK GUI only allows five
levels of undo.  I understand that this is to discourage solution by trial and
error, but it also means that you pretty well have to start all over if you
make a mistake.  I plan on unlimited undo.

Eventually, I may add hints to the client program, to make it more useful as a
learning tool.

The programs are written in python 2.7, and require the third-party constraint
module from http://labix.org/python-constraint.

