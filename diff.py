#!/usr/bin/env python

from src.Differ import Differ
from src.utilities import Document
import sys

if __name__ == '__main__':
    doc1 = Document(sys.argv[1])
    doc2 = Document(sys.argv[2])

    Differ.diff(doc1, doc2)
