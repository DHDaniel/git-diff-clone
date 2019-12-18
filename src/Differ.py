
##############
# Implements the Differ class, which provides the implementation
# of the Myers difference algorithm to compare two files.
###############

from collections import deque

from .utilities import Line, Edit, Document

def myers_diff(a, b):
    # get length of respective elements
    m, n = len(a), len(b)

    # the maximum possible D-path is the one where we delete
    # all elements from string A and insert all elements
    # from string B.
    MAX = m + n

    # initialize our V array, which contains the row indeces of the
    # endpoints of the furthest-reaching D-paths in V[-D], V[-D+2], ...
    # V[D-2], V[D]. Since the sets of furthest-reaching D-paths of even
    # and odd diagonals are disjoint, we can use the same array to
    # store odd endpoints whilst we use them to compute the even ones.
    v = [-1 for i in range(2 * MAX + 1)]

    # we set V[1] = 0 so that the algorithm behaves as if it starts from
    # an imaginary move downwards from (x,y) = (0, -1)
    v[1] = 0

    trace = []

    # for each possible -D to D-path, starting at 0
    for d in range(MAX+1):
        for k in range(-d, d+1, 2):
            # we take a single step downwards (keeping x the same)
            # if these conditions hold, or we go rightwards if not
            if k == -d or (k != d and v[k - 1] < v[k + 1]):
                x = v[k + 1]
            else:
                x = v[k - 1] + 1
            # y is calculated from x and k
            y = x - k
            # compute the "snake" at the end of the d-path
            # as far as we can go.
            while x < m and y < n and a[x] == b[y]:
                x, y = x + 1, y + 1
            # add our endpoint to v
            v[k] = x
            # if we've reached the end of the graph, return the current trace
            if x >= n and y >= m:
                return trace
        trace.append(v[:])
    raise Exception("SES is longer than max length")

def myers_backtrack(trace, a, b):
    # endpoint of our SES
    x, y = len(a), len(b)

    # enumerate each v[] that we obtained from myers_diff
    # and reverse it to get our last trace appended as the first element
    trace_enum = list(enumerate(trace))
    trace_enum.reverse()

    # the trace number is our d-path
    for d, v in trace_enum:
        k = x - y
        # if we moved horizontally, then our previous
        # diagonal is k+1. If not, it is k-1
        if k == -d or (k != d and v[k - 1] < v[k + 1]):
            prev_k = k + 1
        else:
            prev_k = k - 1

        # calculate our previous x and previous y
        # based on our v array
        prev_x = v[prev_k]
        prev_y = prev_x - prev_k

        # backtrack up the "snake", yielding
        # the values of our previous x and previous y and
        # updating
        while x > prev_x and y > prev_y:
            yield (x - 1, y - 1, x, y)
            x, y = x - 1, y - 1

        # if we are not yet at the start, yield where we left off.
        if d > 0:
            yield (prev_x, prev_y, x, y)

        x, y = prev_x, prev_y

    # this yields the final snake that connects us to the beginning
    # of our graph if our first edit was not at (0,0)
    while x > 0 and y > 0:
        yield (x - 1, y - 1, x, y)
        x, y = x - 1, y - 1


class Differ:
    """
    Class that uses the myers difference algorithm to compute and display
    the difference between two files.
    """

    # amount of context to show around edits
    BUFFER = 6

    @staticmethod
    def myers_git_diff(a, b):
        """
        Uses the myers difference algorithm to compute the difference between
        two files, and then backtracks to reconstruct the shortest edit script.
        """
        diff = deque()
        m, n = len(a), len(b)
        # get the generator that returns the x and y coords of the
        # reconstructed solution
        trace = myers_diff(a, b)
        backtrack = myers_backtrack(trace, a, b)
        # for each prev_x, prev_y, x, y determine what kind of move
        # we made (insert, delete or equal) and make an appropriate
        # Edit that can be printed later.
        for prev_x, prev_y, x, y in backtrack:
            a_line = a[prev_x] if prev_x < m else None
            b_line = b[prev_y] if prev_y < n else None

            if a_line is not None and b_line is not None:
                if x == prev_x:
                    diff.appendleft(Edit("insert", a_line, b_line))
                elif y == prev_y:
                    diff.appendleft(Edit("delete", a_line, b_line))
                else:
                    diff.appendleft(Edit("equal", a_line, b_line))

        return list(diff)

    @staticmethod
    def diff(doc1, doc2):
        """
        Finds the difference between file doc1 and file doc2.
        """
        print("Difference between:")
        print("a/", doc1.filepath)
        print("b/", doc2.filepath)
        # find the edits made between both files
        diff = Differ.myers_git_diff(doc1.lines(), doc2.lines())
        diff_locs = []
        # store the locations of each edit.
        # this preliminary step is done to be able to display
        # the buffer around the edits.
        for num, edit in enumerate(diff):
            if edit.edit_type != "equal":
                diff_locs.append(num)

        chunk_locs = []
        prev_loc = None
        chunk_start = None

        # get chunks of edits to print with context around them.
        # this piece of code constructs chunks of edits with an appropriate
        # buffer around them, and handles edge cases such as the start or
        # end of the file, and edits that are closer together than the
        # required buffer
        if len(diff_locs) > 1:
            for num, diff_loc in enumerate(diff_locs):
                if prev_loc is None:
                    chunk_start, prev_loc = diff_loc, diff_loc
                    continue
                if diff_loc - prev_loc <= Differ.BUFFER and num != len(diff_locs) - 1:
                    prev_loc = diff_loc
                elif num != len(diff_locs) - 1:
                    chunk_locs.append((chunk_start, prev_loc))
                    chunk_start, prev_loc = diff_loc, diff_loc
                else:
                    chunk_locs.append((chunk_start, diff_loc))
        elif len(diff_locs) == 1:
            chunk_locs.append((0, 0))

        # print each chunk
        for start, end in chunk_locs:
            to_print = diff[max(0, start - Differ.BUFFER):min(len(diff), end + 1 + Differ.BUFFER)]
            insertions = 0
            deletions = 0
            for edit in to_print:
                if edit.edit_type == "insert":
                    insertions += 1
                elif edit.edit_type == "delete":
                    deletions += 1
            # display a git-style header, containing the old line number where the
            # chunk starts and the length of the chunk in the old file, along with
            # the new start line number and the length of the chunk in the new file.
            header = "@@   -{old_start},{old_length} +{new_start},{new_length}   @@".format(
                old_start=to_print[0].old.num,
                old_length=len(to_print) - insertions,
                new_start=to_print[0].new.num,
                new_length=len(to_print) - deletions
            )
            # print everything
            print(header)
            for edit in to_print:
                print(edit)
            print()
