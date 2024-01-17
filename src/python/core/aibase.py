import cloudpickle
from config import config
import pickle
import enum
from functools import wraps
from exceptions.exceptions import *
from utils.psqlutils import PsqlUtils

sql_utils = PsqlUtils()

 



def pickle_trick(obj, max_depth=10):
    output = {}
    print ("----------")
    print (obj)
    print (type(obj))
    print ("----------")

    if max_depth <= 0:
        return output

    try:
        pickle.dumps(obj)
    except (pickle.PicklingError, TypeError) as e:
        failing_children = []

        if hasattr(obj, "__dict__"):
            for k, v in obj.__dict__.items():
                result = pickle_trick(v, max_depth=max_depth - 1)
                if result:
                    failing_children.append(result)

        output = {
            "fail": obj, 
            "err": e, 
            "depth": max_depth, 
            "failing_children": failing_children
        }

    return output


def print_recursively(method):
    @wraps(method)
    def _impl(self, intend=0):
        method(self, intend)
        for child in self.children:
            child.print_object(intend + 4)
    return _impl


class AIAggregationType(int, enum.Enum):
    OneSecond:int = 1
    FiveSeconds:int = 5
    FifteenSeconds:int = 15
    ThirtySeconds:int = 30
    OneMinute:int = 60
    FifteenMinutes:int = 60 *15
    OneHour:int = 60 * 60
    Daily:int = 60 * 60 * 24
    Weekly:int = 60 * 60 * 24 * 7
    Monthly:int = 60 * 60 * 24 * 7 * 30


class AIBase(object):
    def __init__(self, name="", class_name="", record_id=-1, parent_id=-1, table_name="object"):
        self.name = name
        self.class_name = class_name
        self.record_id = record_id
        self.parent_id = parent_id
        self.children = []
        self.params = {}
        self.table_name = table_name
        self.symbols =  []
        self.symbols_map = {}
        for rec in sql_utils.run_select_query("SELECT * FROM option"):
            self.symbols.append(rec)
            self.symbols_map[rec[2]] = rec        

    def __eq__(self, other):
        if (self.name == other.name and
            self.class_name == other.class_name and
            self.children == other.children and
            self.params == other.params and
            self.table_name == other.table_name):
            return True
        return False

    def add_child(self, child):
        self.children.append(child)

    def add_children(self, *objs):
        for o in objs:
            self.add_child(o)

    def ID(self):
        return self.record_id

    def post(self):
        # we dont want to serialize model, but rather save it to a file
        temp_ref = self.model
        self.model = None
        sql_utils.begin()
        #pickle_trick(self)
        if self.record_id == -1:
            obj_without_model = cloudpickle.dumps(self)
            self.model = temp_ref
            record = self._get_record()
            record["data"] = obj_without_model
            self.record_id = sql_utils.insert(self.table_name, record)
        else:
            obj_without_model = cloudpickle.dumps(self)
            self.model = temp_ref
            record = self._get_record()
            record["data"] = obj_without_model
            sql_utils.update(self.table_name, record, {
                                    "id": self.record_id})

        after_post = getattr(self, "_after_post", None)
        if after_post and callable(after_post):
            after_post()

        sql_utils.commit()
        return self.record_id

    def load(self, rec_id, shallow_load = False):
        object_record = list(sql_utils.run_select_query(
            "SELECT data, id, modelfile from {} WHERE id = {}".format(self.table_name, rec_id)))
        obj_dict = pickle.loads(object_record[0][0])
        self.__dict__.update(obj_dict.__dict__)
        self.record_id = object_record [0][1]
        if shallow_load:
            after_load = getattr(self, "_after_load", None)
            if after_load and callable(after_load):
                after_load()
        return self

    @print_recursively
    def print_object(self, intend=0):
        print(" " * intend, "class :{}  name :{}  id:{}".format(type(self),
              self.name, self.record_id))
