import json


class SessionReader(object):

    # the log that is currently red
    cur_log = None
    cur_path = None

    def parse_session_log(self, path):
        # open file
        f = open(path, 'rb')
        log = json.load(f)
        f.close()
        # return the log file
        self.cur_log = log
        self.cur_path = path

    def print_turns(self):
        print "User ID: " + self.cur_log.get("id")
        turns = self.cur_log.get('turns')
        print "Number of turns: " + str(len(turns))
        print "########"
        for t in turns:
            sys_utt = t.get('sysUtt').split("\n")
            print "sys: ",
            for utt in sys_utt:
                temp = json.loads(utt)
                print temp.get('utterance'),
            print
            usr_utt = t.get('usrUtt')
            if usr_utt is None:
                usr_utt = ""
            print "usr: " + usr_utt
        print "########"