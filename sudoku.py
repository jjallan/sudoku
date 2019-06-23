import dlx
from itertools import permutations, takewhile
from random import choice, shuffle

'''
A 9 by 9 sudoku solver.
'''
_N = 3
_NSQ = _N**2
_NQU = _N**4
_VALID_VALUE_INTS = list(range(1, _NSQ + 1))
_VALID_VALUE_STRS = [str(v) for v in _VALID_VALUE_INTS]
_EMPTY_CELL_CHAR = '·'

# The following are mutually related by their ordering, and define ordering throughout the rest of the code. Here be dragons.
#
_CANDIDATES = [(r, c, v) for r in range(_NSQ) for c in range(_NSQ) for v in range(1, _NSQ + 1)]
_CONSTRAINT_INDEXES_FROM_CANDIDATE = lambda r, c, v: [ _NSQ * r + c, _NQU + _NSQ * r + v - 1, _NQU * 2 + _NSQ * c + v - 1, _NQU * 3 + _NSQ * (_N * (r // _N) + c // _N) + v - 1]
_CONSTRAINT_FORMATTERS =                             [ "R{0}C{1}"  , "R{0}#{1}"                , "C{0}#{1}"                   , "B{0}#{1}"]
_CONSTRAINT_NAMES = [(s.format(a, b + (e and 1)), dlx.DLX.PRIMARY) for e, s in enumerate(_CONSTRAINT_FORMATTERS) for a in range(_NSQ) for b in range(_NSQ)]
_EMPTY_GRID_CONSTRAINT_INDEXES = [_CONSTRAINT_INDEXES_FROM_CANDIDATE(r, c, v) for (r, c, v) in _CANDIDATES]
#
# The above are mutually related by their ordering, and define ordering throughout the rest of the code. Here be dragons.


class Solver:
    def __init__(self, representation=''):
        if not representation or len(representation) != _NQU:
            self._complete = False
            self._NClues = 0
            self._repr = [None]*_NQU # blank grid, no clues - maybe to extend to a generator by overriding the DLX column selection to be stochastic.
        else:
            nClues = 0
            repr = []
            for value in representation:
                if not value:
                    repr.append(None)
                elif isinstance(value, int) and 1 <= value <= _NSQ:
                    nClues += 1
                    repr.append(value)
                elif value in _VALID_VALUE_STRS:
                    nClues += 1
                    repr.append(int(value))
                else:
                    repr.append(None)
            self._complete = nClues == _NQU
            self._NClues = nClues
            self._repr = repr

    def genSolutions(self, genSudoku=True, genNone=False, dlxColumnSelctor=None):
        '''
        if genSudoku=False, generates each solution as a list of cell values (left-right, top-bottom)
        '''
        if self._complete:
            yield self
        else:
            self._initDlx()
            dlxColumnSelctor = dlxColumnSelctor or dlx.DLX.smallestColumnSelector
            if genSudoku:
                for solution in self._dlx.solve(dlxColumnSelctor):
                    yield Solver([v for (r, c, v) in sorted([self._dlx.N[i] for i in solution])])
            elif genNone:
                for solution in self._dlx.solve(dlxColumnSelctor):
                    yield
            else:
                for solution in self._dlx.solve(dlxColumnSelctor):
                    yield [v for (r, c, v) in sorted([self._dlx.N[i] for i in solution])]

    def uniqueness(self, returnSolutionIfProper=False):
        '''
        Returns: 0 if unsolvable;
                 1 (or the unique solution if returnSolutionIfProper=True) if uniquely solvable; or
                 2 if multiple possible solutions exist
        - a 'proper' sudoku is uniquely solvable.
        '''
        slns = list(takewhile(lambda t: t[0] < 2, ((i, sln) for i, sln in enumerate(self.genSolutions(genSudoku=returnSolutionIfProper, genNone=not returnSolutionIfProper)))))
        uniqueness = len(slns)
        if returnSolutionIfProper and uniqueness == 1:
            return slns[0][1]
        else:
            return uniqueness

    def representation(self, asString=True, noneCharacter='.'):
        if asString:
            return ''.join([v and str(_VALID_VALUE_STRS[v - 1]) or noneCharacter for v in self._repr])
        return self._repr[:]

    def __repr__(self):
        return display(self._repr)
    
    def _initDlx(self):
        self._dlx = dlx.DLX(_CONSTRAINT_NAMES)
        rowIndexes = self._dlx.appendRows(_EMPTY_GRID_CONSTRAINT_INDEXES, _CANDIDATES)
        for r in range(_NSQ):
            for c in range(_NSQ):
                v = self._repr[_NSQ * r + c]
                if v is not None:
                    self._dlx.useRow(rowIndexes[_NQU * r + _NSQ * c + v - 1])


_ROW_SEPARATOR_COMPACT = '+'.join(['-' * (2 * _N + 1) for b in range(_N)])[1:-1] + '\n'
_ROW_SEPARATOR = ' ·-' + _ROW_SEPARATOR_COMPACT[:-1] + '-·\n'
_TOP_AND_BOTTOM = _ROW_SEPARATOR.replace('+', '·')

_ROW_LABELS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J']
_COL_LABELS = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
_COLS_LABEL = ' ' + ' '.join([i % _N == 0 and '  ' + l or l for i, l in enumerate(_COL_LABELS)]) + '\n'


def display(representation, conversion=None, labelled=True):
    result = ''
    raw = [conversion[n or 0] for n in representation] if conversion else representation
    if labelled:
        result += _COLS_LABEL + _TOP_AND_BOTTOM
        rSep = _ROW_SEPARATOR
    else:
        rSep = _ROW_SEPARATOR_COMPACT
    for r in range(_NSQ):
        if r > 0 and r % _N == 0:
            result += rSep
        for c in range(_NSQ):
            if c % _N == 0:
                if c == 0:
                    if labelled:
                        result += _ROW_LABELS[r] + '| '
                else:
                    result += '| '
            result += str(raw[_NSQ * r + c] or _EMPTY_CELL_CHAR) + ' '
        if labelled:
            result += '|'
        result += '\n'
    if labelled:
        result += _TOP_AND_BOTTOM
    else:
        result = result[:-1]
    return result

def permute(representation):
    '''
    returns a random representation from the given representation's equivalence class
    '''
    rows = [list(representation[i:i+_NSQ]) for i in range(0, _NQU, _NSQ)]
    rows = permuteRowsAndBands(rows)
    rows = [[r[i] for r in rows] for i in range(_NSQ)]
    rows = permuteRowsAndBands(rows)
    pNumbers = [str(i) for i in range(1, _NSQ + 1)]
    shuffle(pNumbers)
    return ''.join(''.join([pNumbers[int(v) - 1] if v.isdigit() and v != '0' else v for v in r]) for r in rows)

def permuteRowsAndBands(rows):
    bandP = choice([x for x in permutations(range(_N))])
    rows = [rows[_N * b + r] for b in bandP for r in range(_N)]
    for band in range(0, _NSQ, _N):
        rowP = choice([x for x in permutations([band + i for i in range(_N)])])
        rows = [rows[rowP[i % _N]] if i // _N == band else rows[i] for i in range(_NSQ)]
    return rows


def getRandomSolvedStateRepresentation():
    return permute('126459783453786129789123456897231564231564897564897231312645978645978312978312645')


def getRandomSudoku():
    r = getRandomSolvedStateRepresentation()
    s = Solver(r)
    indices = list(range(len(r)))
    shuffle(indices)
    for i in indices:
        ns = Solver(s._repr[:i] + [None] + s._repr[i+1:])
        if ns.uniqueness() == 1:
            s = ns
    return s


if __name__ == '__main__':
    print('Some example useage:')
    inputRepresentation = '..3......4......2..8.12...6.........2...6...7...8.7.31.1.64.9..6.5..8...9.83...4.'
    print('>>> s = Solver({})'.format(inputRepresentation))
    s = Solver(inputRepresentation)
    print('>>> s')
    print(s)
    print('>>> print(s.representation())')
    print(s.representation())
    print('>>> print(display(s.representation(), labelled=False))')
    print(display(s.representation(), labelled=False))
    print('>>> for solution in s.genSolutions(): solution')
    for solution in s.genSolutions(): print(solution)
    inputRepresentation2 = inputRepresentation[:2] + '.' + inputRepresentation[3:]
    print('>>> s.uniqueness()')
    print(s.uniqueness())
    print('>>> s2 = Solver({})  # removed a clue; this has six solutions rather than one'.format(inputRepresentation2))
    s2 = Solver(inputRepresentation2)
    print('>>> s2.uniqueness()')
    print(s2.uniqueness())
    print('>>> for solution in s2.genSolutions(): solution')
    for solution in s2.genSolutions(): print(solution)
    print('>>> s3 = getRandomSudoku()')
    s3 = getRandomSudoku()
    print('>>> s3')
    print(s3)
    print('>>> for solution in s3.genSolutions(): solution')
    for solution in s3.genSolutions(): print(solution)
