import json
import pickle as pkl

class AnnotationWriter(object):
    id = None
    annotation = None

    def __init__(self, session_id, num_turns):
        super(AnnotationWriter, self).__init__()
        self.id = session_id
        self.annotation = {'id': self.id, 'annotations':[None]*num_turns}

    def set_annotation(self, turn_id, labels):
        self.annotation.get('annotations')[turn_id] = labels

    def dump(self, path):
        path += '.label'
        data = json.dumps(self.annotation)
        f = open(path, 'wb')
        f.write(data)
        f.close()

    def dump_pkl(self, path):
        path += '.p'
        f = open(path, 'wb')
        pkl.dump(self.annotation, f)
        f.close()


