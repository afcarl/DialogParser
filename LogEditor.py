from DialogParser import DialogParser
from SessionReader import SessionReader
import os
import pprint
from Utils import Utils


class LogEditor(object):
    session_reader = None
    parser = None
    log_files = None
    log_dir = '/Users/Tony/Documents/intelliJWorkSpace/DialogParser/data/'
    grammar_path = "/Users/Tony/Documents/intellIJWorkSpace/HRL-RavenClawJava/log/grammar.txt"

    pruned_subtree = '(MISUNDERSTAND_ROOT (MISUNDERSTAND_CHOICE-geography_city epsilon pop)' \
                     '(MISUNDERSTAND_CHOICE-datetime_date epsilon pop)' \
                     '(MISUNDERSTAND_CHOICE-yelp_food_detail epsilon pop)pop)pop)'

    def __init__(self):
        super(LogEditor, self).__init__()
        self.session_reader = SessionReader()
        self.parser = DialogParser(parse_type="bottom")
        self.log_files = os.listdir(self.log_dir)
        self.parser.load_grammar_from_path(self.grammar_path)

    def filter_parses(self, prefix, parses):
        print str(len(parses)) + " tree(s) found"
        return [p for p in parses if Utils.clean_parse(p).startswith(prefix) and self.pruned_subtree not in p]

    def run(self):
        for file_name in self.log_files:
            self.session_reader.parse_session_log(self.log_dir+file_name)
            self.session_reader.print_meta()
            turns = self.session_reader.cur_log.get("turns")
            for t in turns[1:]:
                idx = t.get("idx")
                print "========================="
                self.session_reader.print_turns(up_to=idx)
                print "-------------------------"
                self.session_reader.print_sys_utt(t, self.parser)
                print "-------------------------"
                self.parser.print_terminal_set()
                print "========================="
                while True:
                    response = raw_input("Choose correct actions for turn "  + str(idx) + ", 'ok' if already good: \n")
                    if response == 'exit':
                        exit(1)
                    if response == "ok":
                        break
                    # parse the annotation
                    tokens = response.split(",")
                    decode = []
                    for t in tokens:
                        temp = self.parser.decode_terminal(t.strip())
                        if temp is not None:
                            decode.append(temp)

                    # check if the decode message is valid
                    if len(decode) > 0 and self.parser.expect_input(decode[-1]):
                        # parse the decoded and find all possible trees
                        (prefix_parse, prefix_ts) = self.session_reader.get_partial_parse(up_to=idx)
                        parser_results = self.parser.inc_parse(prefix_ts + decode)
                        valid_results = self.filter_parses(prefix=prefix_parse, parses=parser_results)
                        result_size = len(valid_results)
                        # if more than 1 tree, choose one
                        if len(valid_results) > 0:
                            for i, tree in enumerate(valid_results):
                                pretty_tree = tree.replace(prefix_parse, "$", 1).replace('pop', '').replace('epsilon', '')
                                print "(" + str(i) + "): " + Utils.clean_parse(pretty_tree)
                        if len(valid_results) > 1:
                            selected_idx = -1
                            while selected_idx not in range(result_size):
                                selected_str = raw_input("Select a tree in range [0-" + str(len(valid_results)-1) + "]\n")
                                if selected_str.isdigit() and int(selected_str) in range(result_size):
                                    selected_idx = int(selected_str)
                                    print "Select tree " + selected_str
                                else:
                                    print "Invalid input"

                        # confirm with annotator
                        confirm = None
                        while confirm not in ['y', 'n']:
                            confirm = raw_input("Are you sure? [y/n] \n")
                        if confirm == "y":
                            # save new train example
                            break
                    else:
                        print "Invalid actions. Try again:"
        print "Done!"

editor = LogEditor()
editor.run()