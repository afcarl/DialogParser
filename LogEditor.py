from DialogParser import DialogParser
from SessionReader import SessionReader
from AnnotationWriter import AnnotationWriter
import os
from Utils import Utils
from nltk import Tree


class ConceptReader(object):
    # a dictionary of concept name -> a list of monitoring entities
    concepts = None

    def __init__(self, path):
        f = open(path, 'rb')
        lines = f.readlines()
        f.close()
        self.concepts = {}
        for l in lines:
            tokens = l.split("->")
            lhs = tokens[0]
            rhs = tokens[1].split(",")
            self.concepts[lhs] = rhs


class LogEditor(object):
    line_len = 150
    session_reader = None
    parser = None
    log_files = None
    lbl_files = None
    log_dir = 'data/'
    label_dir = log_dir + 'labels/'
    grammar_path = "/Users/Tony/Documents/intellIJWorkSpace/HRL-RavenClawJava/log/grammar.txt"
    concept_path = "/Users/Tony/Documents/intellIJWorkSpace/HRL-RavenClawJava/log/concepts.txt"
    concept_reader = ConceptReader(concept_path)

    pruned_subtree = '(MISUNDERSTAND_ROOT (MISUNDERSTAND_CHOICE-geography_city epsilon pop)' \
                     '(MISUNDERSTAND_CHOICE-datetime_date epsilon pop)' \
                     '(MISUNDERSTAND_CHOICE-yelp_food_detail epsilon pop)pop)pop)'
    PASS = 0
    FAIL = 1
    PREV = 2

    def __init__(self):
        super(LogEditor, self).__init__()
        self.session_reader = SessionReader()
        self.parser = DialogParser(parse_type="bottom")
        self.log_files = [f for f in os.listdir(self.log_dir) if f.endswith('.log')]
        self.lbl_files = [f.replace(".label", "") for f in os.listdir(self.label_dir) if f.endswith('.label')]
        self.parser.load_grammar_from_path(self.grammar_path)

    @staticmethod
    def get_mentions_up_to(turns, up_to):
        mentions = []
        for turn in turns[0:up_to]:
            mentions.extend(turn.get(SessionReader.ENTITIES))
        return mentions

    @staticmethod
    def _print_mentions(c, options):
        print c + ": "
        for idx, o in enumerate(options):
            print str(idx) + " " + o

    def infer_decisions(self, tree, train_list, parse, prefix_terminals):
        """
        create training data given the label data
        :param tree: the
        :param train_list: the list of training examples
        :param parse: a parse string
        :param prefix_terminals: the t-1 turn terminal action sequences
        :return:
        """
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

    def filter_parses(self, prefix, parses):
        """
        Prune away parse thee that is bad
        :param prefix: the prefix parse at t-1 turns
        :param parses: a list of proposed parse tree for t turns
        :return: the filtered list of parse tree for t turns
        """
        print str(len(parses)) + " tree(s) found"
        return [p for p in parses if Utils.clean_parse(p).startswith(prefix) and self.pruned_subtree not in p[len(prefix):]]

    def is_valid_action(self, decode):
        """
        :param decode: the list of actions from annotator
        :return: true if the action sequence is valid
        """
        if len(decode) <= 0:
            return False
        needs_input = [self.parser.expect_input(d) for d in decode]
        correct_input = [False] * len(decode)
        correct_input[-1] = True
        return correct_input == needs_input

    def get_label(self, turn_actions, parse, prefix_ts, usr_utt, belief):
        """

        :param turn_actions: the actions for this turn
        :param parse: the parse that is selected by annotator
        :param prefix_ts: the prefix sequecne of termianl actions
        :param usr_utt: the user utterance at this turn
        :param belief: the belief state at turn t
        :return:
        """
        p = []
        train = []
        selected_tree = Tree.fromstring(parse)
        self.infer_decisions(tree=selected_tree, train_list=train, parse=p, prefix_terminals=list(prefix_ts))
        return {'actions': turn_actions, 'train': train, 'usrUtt':usr_utt, 'belief': belief, 'new': True}

    def print_at_turn(self, turn, idx):
        print "="*self.line_len
        print "Turn-" + str(idx)
        self.session_reader.print_turns(up_to=idx)
        print "-"*self.line_len
        self.session_reader.print_sys_utt(turn, self.parser)
        print "-"*self.line_len
        self.parser.print_terminal_set()
        print "="*self.line_len

    def label_belief(self, all_mentions):
        # reorganize all the mentions
        type_to_entity = {}
        for mention in all_mentions:
            temp = type_to_entity.get(mention.get("type"), [])
            temp.append(mention.get("entity"))
            type_to_entity[mention.get("type")] = temp

        # label all concepts
        belief = {}
        for c, watches in self.concept_reader.concepts.iteritems():
            # check if we have any candidates
            options = []
            for w in watches:
                options.extend(type_to_entity.get(w.strip(), []))
            options = list(set(options))
            options.append("none")
            if len(options) > 1:
                corr_idx = -1
                while corr_idx < 0 or corr_idx >= len(options):
                    LogEditor._print_mentions(c, options)
                    selected_str = raw_input("Choose the correct value for " + c + "\n")
                    if selected_str.isdigit():
                        corr_idx = int(selected_str)
                    else:
                        corr_idx = -1
                belief[c] = options[corr_idx]
            else:
                belief[c] = "none"

        return belief

    def label_actions(self, turn, idx, belief, ann_writer):
        """
        :param turn: turn dict
        :param idx: the index of turn
        :param belief: the belief state
        :param ann_writer: the writer holds training data
        :return: new done
        """
        status = self.FAIL
        response = raw_input("Choose correct actions for turn " + str(idx)
                             + ", 'ok' if already good, 'prev' to go back: \n")
        # parse the decoded and find all possible trees
        (prefix_parse, prefix_ts) = self.session_reader.get_partial_parse(up_to=idx)
        select_parse = None
        error = False
        usr_utt = turn.get(self.session_reader.USR_UTT)

        if response.lower() == "prev":
            return self.PREV

        # not previous
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
            label = self.get_label(turn_actions=correct_actions, parse=select_parse,
                                   prefix_ts=prefix_ts, usr_utt=usr_utt, belief=belief)
            ann_writer.set_annotation(turn_id=idx, labels=label)
            status = self.PASS

        return status

    def run(self):
        """
        At turn t-1, we print t-1 turns and the annotator needs :
        1. give a sequence of correct actions
        2. give a binary label for all the mentioned entities so far
        3. new training examples are created for training
        4. the resulting data is saved to disk
        """
        for file_name in self.log_files:
            if file_name in self.lbl_files:
                print "skip file " + file_name
                continue
            # read the log file from disk
            print "*" * self.line_len
            print "Labelling " + file_name
            self.session_reader.parse_session_log(self.log_dir+file_name)
            self.session_reader.print_meta()
            turns = self.session_reader.cur_log.get(self.session_reader.TURNS)
            ann_writer = AnnotationWriter(self.session_reader.cur_log['id'], len(turns))
            # print turns
            # self.session_reader.print_turns()
            idx = 1
            while idx < len(turns):
                turn = turns[idx]
                self.print_at_turn(turn=turn, idx=idx)
                # begin annotation for the belief state
                mentions = LogEditor.get_mentions_up_to(turns, idx)
                belief = self.label_belief(mentions)
                # begin annotation loop for this turn
                status = self.FAIL
                while status == self.FAIL:
                    status = self.label_actions(turn, idx, belief, ann_writer)
                if status == self.PREV and idx > 1:
                    idx -= 2
                idx += 1

            print "finish labelling for " + file_name
            ann_writer.dump(self.label_dir + file_name)
        print "Done!"

if __name__ == "__main__":
    editor = LogEditor()
    editor.parser.print_terminal_set()
    editor.run()
