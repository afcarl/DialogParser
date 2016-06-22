from DialogParser import DialogParser
from SessionReader import SessionReader
from AnnotationWriter import AnnotationWriter
import os
from Utils import Utils
from nltk import Tree


class LogEditor(object):
    line_len = 150
    session_reader = None
    parser = None
    log_files = None
    log_dir = 'data/'
    label_dir = log_dir + 'labels/'
    grammar_path = "/Users/Tony/Documents/intellIJWorkSpace/HRL-RavenClawJava/log/grammar.txt"

    pruned_subtree = '(MISUNDERSTAND_ROOT (MISUNDERSTAND_CHOICE-geography_city epsilon pop)' \
                     '(MISUNDERSTAND_CHOICE-datetime_date epsilon pop)' \
                     '(MISUNDERSTAND_CHOICE-yelp_food_detail epsilon pop)pop)pop)'

    def infer_decisions(self, tree, train_list, parse, prefix_terminals):
        cur_label = Utils.node_label(tree)
        if type(tree) is not Tree:
            if len(prefix_terminals) > 0:
                if cur_label == prefix_terminals[0]:
                    prefix_terminals.remove(cur_label)
                elif not self.parser.is_dummy(cur_label):
                    print "WHAT!!!"
            parse.append(cur_label)
            return
        parse.append('(')
        parse.append(cur_label)
        if len(prefix_terminals) == 0 and cur_label in self.parser.train_set.keys():
                children = [Utils.node_label(node) for node in tree]
                train_list.append({"lhs": cur_label, "rhs": children, 'parse': Utils.clean_parse(' '.join(parse))})
        for node in tree:
            self.infer_decisions(node, train_list, parse, prefix_terminals)
        parse.append(')')

    def __init__(self):
        super(LogEditor, self).__init__()
        self.session_reader = SessionReader()
        self.parser = DialogParser(parse_type="bottom")
        self.log_files = [f for f in os.listdir(self.log_dir) if f.endswith('.log')]
        self.parser.load_grammar_from_path(self.grammar_path)

    def filter_parses(self, prefix, parses):
        print str(len(parses)) + " tree(s) found"
        return [p for p in parses if Utils.clean_parse(p).startswith(prefix) and self.pruned_subtree not in p[len(prefix):]]

    def is_valid_action(self, decode):
        if len(decode) <= 0:
            return False
        needs_input = [self.parser.expect_input(d) for d in decode]
        correct_input = [False] * len(decode)
        correct_input[-1] = True
        return correct_input == needs_input

    def get_label(self, decode, parse, prefix_ts, usr_utt, belief):
        p = []
        train = []
        selected_tree = Tree.fromstring(parse)
        self.infer_decisions(tree=selected_tree, train_list=train, parse=p, prefix_terminals=list(prefix_ts))
        return {'actions': decode, 'train': train, 'usrUtt':usr_utt, 'belief': belief, 'new': True}

    def run(self):
        for file_name in self.log_files:
            file_name = '945887D2016-06-21T20-52-31.log'
            self.session_reader.parse_session_log(self.log_dir+file_name)
            self.session_reader.print_meta()
            turns = self.session_reader.cur_log.get(self.session_reader.TURNS)
            ann_writer = AnnotationWriter(self.session_reader.cur_log['id'], len(turns))
            self.session_reader.print_turns()

            for turn in turns[1:]:
                idx = turn.get("idx")
                print "="*self.line_len
                self.session_reader.print_turns(up_to=idx)
                print "-"*self.line_len
                self.session_reader.print_sys_utt(turn, self.parser)
                print "-"*self.line_len
                self.parser.print_terminal_set()
                print "="*self.line_len

                done = False
                while done is not True:
                    response = raw_input("Choose correct actions for turn " + str(idx) + ", 'ok' if already good: \n")
                    if response == 'exit':
                        exit(1)

                    # parse the decoded and find all possible trees
                    (prefix_parse, prefix_ts) = self.session_reader.get_partial_parse(up_to=idx)
                    select_parse = None
                    error = False
                    usr_utt = turn.get(self.session_reader.USR_UTT)
                    belief = turn.get(self.session_reader.BELIEF)

                    if response.lower() == "ok":
                        # get the original parse tree for training
                        (ok_parse, ok_ts) = self.session_reader.get_partial_parse(up_to=idx+1)
                        correct_actions = ok_ts[len(prefix_ts):]
                        select_parse = Utils.resolve_unbalanced_parse(ok_parse)
                    else:
                        # parse the annotation
                        tokens = response.split(",")
                        correct_actions = []
                        for t in tokens:
                            temp = self.parser.decode_terminal(t.strip())
                            if temp is not None:
                                correct_actions.append(temp)

                        # check if the decode message is valid
                        if self.is_valid_action(correct_actions):
                            parser_results = self.parser.inc_parse(prefix_ts + correct_actions)
                            valid_results = self.filter_parses(prefix=prefix_parse, parses=parser_results)
                            result_size = len(valid_results)
                            # if more than 1 tree, choose one
                            if len(valid_results) > 0:
                                selected_idx = 0
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

                                select_parse = valid_results[selected_idx]
                            else:
                                print "No parse tree found. Try debug."
                                error = True
                        else:
                            print "Invalid actions. Try again:"
                            error = True

                    # confirm with annotator
                    if not error:
                        confirm = None
                        while confirm not in ['y', 'n']:
                            confirm = raw_input("Are you sure? [y/n] \n")
                            if confirm == "y":
                                label = self.get_label(decode=correct_actions, parse=select_parse,
                                                       prefix_ts=prefix_ts, usr_utt=usr_utt, belief=belief)
                                ann_writer.set_annotation(turn_id=idx, labels=label)
                                done = True

            print "finish labelling for " + file_name
            ann_writer.dump(self.label_dir + file_name)
        print "Done!"

editor = LogEditor()
editor.parser.print_terminal_set()
editor.run()
