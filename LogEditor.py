from DialogParser import DialogParser
from SessionReader import SessionReader
import os
from nltk.draw.tree import TreeView


class LogEditor(object):
    session_reader = None
    parser = None
    log_files = None
    log_dir = '/Users/Tony/Documents/intelliJWorkSpace/DialogParser/data/'
    grammar_path = "/Users/Tony/Documents/intellIJWorkSpace/HRL-RavenClawJava/log/grammar.txt"

    def __init__(self):
        super(LogEditor, self).__init__()
        self.session_reader = SessionReader()
        self.parser = DialogParser(parse_type="bottom")
        self.log_files = os.listdir(self.log_dir)
        self.parser.load_grammar_from_path(self.grammar_path)

    def run(self):
        for file_name in self.log_files:
            self.session_reader.parse_session_log(self.log_dir+file_name)
            self.session_reader.print_meta()
            response = None
            while response != "pass":
                response = raw_input("Please enter your name: \n")

editor = LogEditor()
editor.run()