import json
from Utils import Utils


class SessionReader(object):
    # dictionary KEY
    PARSE = 'parseTree'
    TURNS = 'turns'
    SYS_UTT = 'sysUtt'
    TAG = 'tag'

    # the log that is currently red
    cur_log = None
    cur_path = None

    def parse_session_log(self, path):
        # open file
        f = open(path, 'rb')
        log = json.load(f)
        f.close()
        self.cur_log = log
        self.cur_path = path
        # convert system utt also into dict
        turns = self.cur_log.get(self.TURNS)
        norm_turns = list(turns)
        for idx, t in enumerate(turns):
            sys_utt = t.get(self.SYS_UTT).split("\n")
            norm_sys_utt = []
            for utt in sys_utt:
                norm_sys_utt.append(json.loads(utt))
            norm_turns[idx][self.SYS_UTT] = norm_sys_utt
        self.cur_log[self.TURNS] = norm_turns
        # remove white space in parse tree
        self.cur_log[self.PARSE] = Utils.clean_parse(self.cur_log.get(self.PARSE))

    def get_partial_parse(self, up_to=None):
        turns = self.cur_log.get(self.TURNS)
        parse = self.cur_log.get(self.PARSE)
        end_turn = len(turns)
        if up_to is not None:
            end_turn = up_to
        terminals = []
        for t in turns[0:end_turn]:
            sys_utt = t.get(self.SYS_UTT)
            for utt in sys_utt:
                tags = utt.get(self.TAG).split(" ")
                terminals.extend(tags)
        # find partial partial parsee (prefix not complete tree)
        last_count = terminals.count(terminals[-1])
        end_idx = Utils.find_nth(parse, terminals[-1], last_count) + len(terminals[-1])
        prefix = parse[0:end_idx]

        return prefix, terminals

    def get_sys_utt(self, turn):
        sys_utt = turn.get(self.SYS_UTT)
        result = []
        for utt in sys_utt:
            tags = utt.get(self.TAG).split(" ")
            result += tags
        return result

    """
    printers
    """

    def print_meta(self):
        print "User ID: " + self.cur_log.get("id")
        print "Number of turns: " + str(len(self.cur_log.get(self.TURNS)))

    def print_turns(self, up_to=None):
        turns = self.cur_log.get(self.TURNS)
        end_turn = len(turns)
        if up_to is not None:
            end_turn = up_to

        for t in turns[0:end_turn]:
            sys_utt = t.get(self.SYS_UTT)
            print "sys:",
            for utt in sys_utt:
                print utt.get('utterance'),
            print
            usr_utt = t.get('usrUtt')
            if usr_utt is None:
                usr_utt = ""
            print "usr: " + usr_utt

    def print_sys_utt(self, turn, parser):
        sys_utt = turn.get(self.SYS_UTT)
        print "policy:",
        for utt in sys_utt:
            tags = utt.get(self.TAG).split(" ")
            encode_tag = ""
            for t in tags:
                encode_tag += parser.encode_terminal(t) + ' '
            encode_tag = encode_tag.strip()
            print utt.get('utterance') + "(" + utt.get(self.TAG) + " " + encode_tag + ")",
        print
