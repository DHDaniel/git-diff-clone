
class Document:
    """
    Represents a document.
    """

    def __init__(self, filepath):
        self.filepath = filepath


    def lines(self):
        """
        Reads a document line-by-line and creates the corresponding Line objects.
        Returns an array of lines.
        """
        lines = []
        with open(self.filepath, "r") as file:
            for num, line in enumerate(file):
                lines.append(Line(num, line.rstrip("\n")))
        return lines


class Line:
    """
    Implements the Line class, which represents a line in a file.
    """

    def __init__(self, num, text):
        """
        Accepts the number of the line and the content of the line.
        """
        self.text = text
        self.num = num

    def __eq__(self, other_line):
        return self.text == other_line.text

    def __ne__(self, other_line):
        return self.text != other_line.text

    def __str__(self):
        return self.text

# symbols that will be displayed as a prefix when printing
# out the difference between two files
SYMBOLS = {
    "insert": "+",
    "delete": "-",
    "equal": " "
}

# to colour lines when printing. Will only work on
# UNIX systems.
TERM_COLORS = {
    "insert": '\033[92m',
    "equal": '',
    "delete": '\033[91m',
    "end": '\033[0m'
}

class Edit:
    """
    Represents an Edit from one file to another.
    """

    def __init__(self, edit_type, old, new):
        """
        Stores the edit type, where it can be one of insert, delete, or equal,
        along with the old and new line.
        """
        self.edit_type = edit_type
        self.old = old
        self.new = new
        self.prefix = SYMBOLS[edit_type]

    def __str__(self):
        if self.edit_type == "delete":
            line = self.old
        else:
            line = self.new
        return "{color}{symb}    {text}    {endsymb}".format(
            color=TERM_COLORS[self.edit_type],
            symb=self.prefix,
            text=line.text,
            endsymb=TERM_COLORS["end"]
        )
