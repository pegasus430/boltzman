import os
import uuid
import statistics
from time import time
from datetime import datetime
import numpy
from sklearn import preprocessing as p
from core.aibase import AIBase, AIAggregationType
from core.aidataport import AIDataport
from genes.aigene import AIGene
from exceptions.exceptions import *
import enum
from config import config
from core.aiprediction import AIPrediction
from utils.aiutils import make_sure
from utils.loggerfactory import logger
from utils.psqlutils import PsqlUtils
from tensorflow import keras
sql_utils = PsqlUtils()


class AINetworkTrainingStatus(int, enum.Enum):
    NewTraining: int = 0
    HalfTrained: int = 1
    InTraining: int = 2
    ShortTrainingRequired: int = 3
    TrainingUpToDate: int = 4
    TrainingError: int = 5


class AINetworkStatus(int, enum.Enum):
    Dead: int = 0  # marked to be removed
    Frozen: int = 1  # No training no trading
    Inactive: int = 2  # Being traded but no trade activity due to low score
    Active: int = 3  # Actively being trained and used for trade


class AINetwork (AIBase):
    def __init__(self, output_dataport=None, training_status=AINetworkTrainingStatus.NewTraining):
        AIBase.__init__(self, name="AINetwork", class_name="AINetwork",
                        record_id=-1, table_name="network")
        self.keras = keras

        self._input_layer_size = 0
        self.hidden_layers = []
        self.model: keras.Model = None
        self.model_file = ""
        self.last_trained_time = 0
        self.output_dataport: AIDataport = output_dataport
        self._training_status = training_status
        self.score = 75
        self._status = AINetworkStatus.Inactive
        self._running_score_average = 0
        self._total_scores = 0
        self._profit_weight_map = config.PROFIT_WEIGHT_MAP
        self._prediction = None
        self.prediction_queue: list = []
        # assign a uuid for model file name
        self.model_file = str(uuid.uuid4())
        self.processed_predictions = 0
        self._location = "IDLE"

    def __str__(self):
        last_trained_pretty = datetime.fromtimestamp(self.last_trained_time) \
            .strftime("%m/%d/%Y, %H:%M:%S")
        input_dp_details = ""
        for dp in self.children:
            if isinstance(dp, AIDataport):
                input_dp_details += dp.params["symbol"] + ":" + str(
                    dp.params["size"]) + ":" + str(dp.params["aggregation_type"]) + " "
        return (
            f'Network id    : {self.record_id}\n'
            f'Symbol        : {self.output_dataport.params["symbol"]}\n'
            f'Status        : {self.status}\n'
            f'Input details : [{input_dp_details}]\n'
            f'Input size    : {self._input_layer_size}\n'
            f'Hidden layers : {self.hidden_layers}\n'
            f'Output size   : {self.output_dataport.params["size"]}\n'
            f'Output agg.   : {self.output_dataport.params["aggregation_type"]}\n'
            f'Trained up to : {last_trained_pretty}\n'
            f'Next Training : {datetime.fromtimestamp(self.next_training_time())}\n'
            f'Predictions   : {len(self.prediction_queue)}\n'
            f'Score         : {self.score}\n')

    def get_details(self):
        print("IN GET DETAILSSSSSSSSSSSSSS")
        last_trained_pretty = datetime.fromtimestamp(self.last_trained_time) \
            .strftime("%m/%d/%Y, %H:%M:%S")
        input_dp_details = ""
        for dp in self.children:
            if isinstance(dp, AIDataport):
                input_dp_details += dp.params["symbol"] + ":" + str(
                    dp.params["size"]) + ":" + str(dp.params["aggregation_type"]) + " "
        return {
            'id': self.record_id,
            'symbol': self.output_dataport.params["symbol"],
            'status': self.status,
            'input_details': input_dp_details,
            'input_size': self._input_layer_size,
            'hidden_layers': self.hidden_layers,
            'output_size': self.output_dataport.params["size"],
            'output_aggragation': self.output_dataport.params["aggregation_type"],
            'trained_up_to': last_trained_pretty,
            'next_training': datetime.fromtimestamp(self.next_training_time()),
            'predictions': len(self.prediction_queue),
            'score': self.score
        }

    def _after_load(self):
        if self.model_file:
            self.model = self.keras.models.load_model(
                f"{self._get_model_path()}{self.model_file}")

    def _save_dataports(self):
        """utility function to save dataport key fields
        """
        # just going lazy and deleting and repopulating the records

        make_sure((self.record_id > 0),
                  "Network should saved before saving dataports")

        sql_utils.delete("dataport", {
            "network_id": self.record_id
        })
        for dp in self.children:
            if isinstance(dp, AIDataport):
                sql_utils.insert("dataport", {
                    "network_id": self.record_id,
                    "size": dp.params["size"],
                    "timeseries_id": -1,  # TODO : once time series reference implemented, change this
                    "aggregation_type": dp.params["aggregation_type"]
                })

    def _after_post(self):
        if self.model_file and self.model:
            self.model.save(f"{self._get_model_path()}{self.model_file}")

        self._save_dataports()

    def __eq__(self, other):
        if (super().__eq__(other) and
            self.hidden_layers == other.hidden_layers and
            self.last_trained_time == other.last_trained_time and
            self.output_dataport == other.output_dataport and
                self.training_status == other.training_status):
            return True
        return False

    def _get_model_path(self):
        if os.getenv("RUN_TIME_ENV") == 'docker':
            return config.MODEL_FILES_LOCATION_IN_DOCKER
        else:
            return config.MODEL_FILES_LOCATION



    def _get_record(self):
        """this method is called by base class right before posting the network to the database, anything needs to be done
        for persistentency purpose can be taken care here. for instance models are saved to files before ost and path is saved to the db
        second phase of this function is to return network table specific fields that we like to persist in db
        although network instance serialized in data field via pickle , we need these extra fields for quick data query purposes
        Returns:
            record_obect: record to be posted to the network table. make sure that all keys in the records exist in network table schema
            and data assigned to them are commpatable with schema data types
        """

        return {
            "classname": "AINetwork",
            "score": self.score,
            "lasttraineddate": self.last_trained_time,
            "modelfile": self.model_file,
            "location": self.location
        }

    def _set_output_dataport(self, dp, reconstruct):
        """Sets the output dataport. Eachnetwork has only one output dataport where having many input dataports

        Args:
            dp (AIDataport): dataport to set as output dataport
            reconstruct (Boolean): whetver model should be reconstructed, once this function is called resconstruct should be done at some point
            However durng batch modification to the network sometimes it would be disabled and done once after all changes are made , mostly genes use this argument

        Raises:
            DataportInputOutputTypeMismatch: DataportInputOutputTypeMismatch
        """        ''''''
        if (dp.is_input_port):
            raise DataportInputOutputTypeMismatch(
                "input dataport cannot be set as output dataport")
        self.output_dataport=dp
        if (reconstruct):
            self._reconstruct_model()

    def _reconstruct_model(self):
        self._update_input_layer_size()
        inputs=self.keras.Input(shape = (self._input_layer_size,))
        x=inputs

        # construct hidden layers
        for ls in self.hidden_layers:
            layer=self.keras.layers.Dense(ls, activation = "sigmoid")
            x=layer(x)

        output_layer=self.keras.layers.Dense(
            len(self.profit_weight_map) + 1, activation="sigmoid")
        x = output_layer(x)

        self.model = self.keras.Model(inputs=inputs, outputs=x, name="arif")
        self.model.compile(
            optimizer='sgd', loss='categorical_crossentropy', metrics=['accuracy'])

    def _update_input_layer_size(self):
        '''
            Calculates input layer neuron size from networks dataports.
        '''
        input_size = 0
        for dp in self.children:
            if isinstance(dp, AIDataport):
                input_size += dp.params["size"]
        self._input_layer_size = input_size

    def _pull_input_data(self, time_stamp):
        '''

        '''
        """generates input layer data from input daaports by iterating children and and type checking for AIDataport

        Raises:
            DataportInputOutputTypeMismatch: it is raised of any of the dataports are not set input dataport
                                                This indicates a bug that created this Network

        Yields:
            _type_: _description_
        """        ''''''

        for it in self.children:
            if isinstance(it, AIDataport):
                if not it.is_input_port:
                    raise DataportInputOutputTypeMismatch(
                        "output dataport is detected in input dataports")
                pulled_record_count = 0
                for each in it.pull_data(time_stamp):
                    pulled_record_count +=1
                    yield each

    def _pull_output_data(self, time_stamp):
        """Generates output layer data from output dataport

        Args:
            time_stamp (int): unix time stamp

        Yields:
            dict: Returns one record at a time
        """
        def normalizer_func (d1, d2):
            return d1

        for each in self.output_dataport.pull_data(time_stamp, normalizer_func):
            yield each

    def normalize_output_data(self, data, aggregation_type: AIAggregationType):
        """Cpnverts output dataport's data to tensorflow y training format, could be labels , could be anything that
        tensor flow suports. For the first iterattion of this project we will generate 5 binary values in following format:
        [1, 0, 0, 0, 0] : symbol significantly went up , sell opportunity
        [0, 1, 0, 0, 0] : symbol  went up , mild sell opportunity
        [0, 0, 1, 0, 0] : no meaningful price change, keeping the current position is recommended
        [0, 0, 0, 1, 0] : symbol  went down , mild buy opportunity
        [0, 0, 0, 0, 1] : symbol significantly went down , buy opportunity

        networks are trained not to make buy/sell decision but guess the future movements. trading requires another approach that
        evaluates the guessed future

        normalization algorithm (for now) (avg (data) - first value / first value) * 100 => this will give us a precentage for time frame
        using that percentage dailiy average perc is calculated and mapped against the success map defined in params



        Args:
            data (list): list of values , it is real currency values now but might required to be normalized
            aggregation_type (AIAggregationType): Aggregation type of the output dataport
        """

        avg = statistics.mean(data)
        # how long of a period does this time series cover i seconds
        period = aggregation_type.value * len(data)
        profit_percentage = (avg - data[0]) / data[0] * 100
        mapped_precentage = float(
            AIAggregationType.Daily.value) * float(profit_percentage) / float(period)
        rv = [0] * (len(self.profit_weight_map) + 1)
        in_list = False
        for i, v in enumerate(self.profit_weight_map):
            if mapped_precentage < v:
                in_list = True
                rv[i] = 1.0
                break
        if not in_list:
            rv[len(rv) - 1] = 1.0
            # rv[len(rv) - 1] = 1.0

        return rv

    def set_output_symbol(self, symbol, output_aggregation, output_size, reconstruct_required=True):
        """ Output dataport is used to construct networks output layer in terms of number of output neurons.
            Each network can have only one output dataport and each time it is set network should be reconstructed.
            However in some cases , e.g batch gene processing it would be expensive to reconstruct the network each time network is changed
            to avoid the overhead of reconstruction reconstruct_required might be set to False if only at the end it is called once

        Args:
            symbol (string): symbol e.g GOOGL
            output_aggregation (AIAggregationType): One of the aggregation types available such as daily or weekly
            output_size (int): number of forward records being pulled from timestamp provided, also it means the output layer neuron count
            reconstruct_required (bool, optional): force reconstruct, default is True
        """
        self._set_output_dataport(AIDataport(
            symbol, output_size, output_aggregation, is_input_port=False), reconstruct_required)

    def add_hidden_layer(self, layer_size):
        '''
        Adds hidden layer with layer_size neurons.
        '''
        self.hidden_layers.append(layer_size)

    def build_output_tensor(self, time_stamp, data_processor_fn=None):
        '''
            builds output data for the network from out dataports.
            In ML terms this data is the training data generated by output dataport
            each data point is sent through data_processer_fn if defined

            ****NON COMPLETED METHOD. TENSORFLOW DEPENDENCY
        '''
        print("Building output tensor for time stamp :{}".format(time_stamp))
        for rec in self._pull_output_data(time_stamp):
            if(data_processor_fn):
                rec = data_processor_fn(rec)

    def short_term_trainable(self, time_stamp):
        '''
            returns True if it is ok to train this network from a single process without threading
            also called real time training by tradetasks , when networks are trained right before predictions are
            created.if training seems taking more than a few hundred milliseconds networks should be sent to
            dedicated trainer process and leave the trade process

            ****NON COMPLETED METHOD. TENSORFLOW DEPENDENCY
        '''

        return True
    def _scale(self, x, out_range=(-1, 1)):
        domain = numpy.min(x), numpy.max(x)
        y = (x - (domain[1] + domain[0]) / 2) / (domain[1] - domain[0])
        return y * (out_range[1] - out_range[0]) + (out_range[1] + out_range[0]) / 2

    def train(self, time_stamp):
        '''
            Trains the network for given timestamp
        '''
        date_obj = datetime.fromtimestamp(time_stamp)
        print (date_obj)

        numpy.set_printoptions(suppress=True)
        input_data = []
        output_data = []
        for rec in self._pull_input_data(time_stamp):
            input_data.append(rec[0])
        
        if len(input_data) != self._input_layer_size:
            raise NetworkInputSizeDataMismatch(f'generated input data is not equal to required.Recevied:{len(input_data)} expected: {self._input_layer_size}')

        for rec in self._pull_output_data(time_stamp):
            output_data.append(rec[0])

        if len(output_data) != self.output_dataport.params["size"]:
            raise NetworkInputSizeDataMismatch(f'generated output data is not equal to required.Recevied:{len(output_data)} expected: {self.output_dataport.params["size"]}')


        i_numpy = numpy.array(input_data)
        temp = self.normalize_output_data(
            output_data, self.output_dataport.params["aggregation_type"])
        o_numpy = numpy.array(temp)
        i_numpy = i_numpy.reshape(1, len(input_data))
        o_numpy = o_numpy.reshape(1, len(temp))

        normalizedData = self._scale(i_numpy, (0, 1))

        self.model.fit(normalizedData, o_numpy,
                       batch_size=1, epochs=250, verbose=0)

        self.last_trained_time = time_stamp

    def batch_train (self, timestamp1, timestamp2):
        """Trains network from timestamp1 to timestamp2

        Args:
            timestamp1 (timestamp): from time stamp
            timestamp2 (timestamp): to time stamp (it is included)
        """
        step: int = self.minimum_aggregation_type().value
        for ts in range (int(timestamp1), int(timestamp2 + step), step):
            self.train(ts)   

    def build_from_genes(self):
        '''
            iterates genes and ask one by one to process the network.
            Should be apply to empty networks. after all genes are processed ML model is reconstructed
        '''
        for obj in self.children:
            if isinstance(obj, AIGene):
                obj.process_network(self)
        self._reconstruct_model()

    def minimum_aggregation_type(self):
        """returns the minimum aggregation type which also tells the smaller step to move in trainings.
        functions check all dtaports and spots the minimum aggregation of all

        Returns:
            _type_: AIAggregationType
        """
        min_agg = AIAggregationType.Monthly
        for it in self.children:
            if isinstance(it, AIDataport):
                if min_agg.value > int(it.params["aggregation_type"].value):
                    min_agg = it.params["aggregation_type"]
        return min_agg

    def timestamp_bucket(self, ts):
        """returns the timestamp bucket for given time stamp for the smallest aggregation. time stamp bucket is calculated by using minimum_aggregation_type
        and timestamps within that aggregation slot returns the beginning of that time window
        for instance:

        Args:
            ts (time stamp): time stamp that will be aligned to the smallest aggregation type in input dataports
        """
        rv = None
        for it in self.children:
            if isinstance(it, AIDataport):
                t = it.time_stamp_bucket(ts)
                if not rv:
                    rv = t
                else:
                    if t > rv:
                        rv = t
        return rv

    def next_training_time (self):
        """time in future where training doesnt repeat itself.
        """        
        process_step = self.minimum_aggregation_type().value
        time_cursor = self.last_trained_time + process_step \
                        if self.last_trained_time > 0 else self.earliest_time_stamp()
        return time_cursor


    def earliest_time_stamp(self):
        rv = None
        for it in self.children:
            if isinstance(it, AIDataport):
                t = it.earliest_time_stamp()
                if not rv:
                    rv = t
                else:
                    if t > rv:
                        rv = t
        if not rv:
            raise NetworkDataportError(
                "Network has no dataports with enough data for training")
        return max(self.last_trained_time, rv)

    def latest_time_stamp(self):
        return self.output_dataport.latest_time_stamp()

    def get_genes(self):
        """Returns networks gene

        Returns:
            []]: Array of gene objects
        """
        rv = []
        for obj in self.children:
            if isinstance(obj, AIGene):
                rv.append(obj)
        return rv

    def print_genes(self):
        """prints out the gene params, for debugging purposes
        """
        for obj in self.children:
            if isinstance(obj, AIGene):
                obj.print_params()

    def predict(self, time_stamp) -> list:
        """predicts future datapoints

        Args:
            time_stamp (int): prediction time

        returns:([{}]): returns an array of {time_stamp:<int>, predicted_value:<number>}
        TODO: implement rensor flow integration here
        """
        l = []
        for rec in self._pull_input_data(time_stamp):
            l.append(rec[0])
        return self.model.predict(numpy.array(l).reshape(1, len(l)))

    def add_new_score(self, score):
        old_score = self.score
        self.score += score
        for k in config.NETWORK_STATUS_THRESHOLDS.keys():
            if self.score in range(config.NETWORK_STATUS_THRESHOLDS[k][0],
                                   config.NETWORK_STATUS_THRESHOLDS[k][1]):
                self.status = AINetworkStatus[k]
                break

        self._running_score_average = (
            self._running_score_average * self._total_scores + score) + (self._total_scores + 1)
        self._total_scores += 1
        logger().info (f'Network {(self.record_id)} score changed. Old value: {old_score} new Value {self.score}')

    def clone(self):
        self.print_genes()
        new_network = AINetwork()
        for gene in self.get_genes():
            new_network.add_children(gene)
        new_network.build_from_genes()
        new_network.training_status = AINetworkTrainingStatus.NewTraining
        return new_network

    def clone_and_mutate(self, perc):
        self.print_genes()
        new_network = AINetwork()
        for gene in self.get_genes():
            gene.mutate(self.mutation_perc)
            new_network.add_children(gene)
        new_network.build_from_genes()
        new_network.training_status = AINetworkTrainingStatus.NewTraining
        return new_network

    def delete_from_db(self):
        if self.record_id < 0:
            raise (NetworkInvalidRecordToDelete(
                f'record is negactive, you are possibly trying to delete an object that never was posted'))
        sql_utils.begin()
        sql_utils.delete_record('network', self.record_id)
        self.record_id = -1
        sql_utils.commit()

    def set_training_status(self, new_status):
        self._training_status = new_status

    def get_training_status(self):
        return self._training_status

    training_status = property(get_training_status, set_training_status)

    def get_running_score_average(self):
        return self._running_score_average

    def set_status(self, new_status):
        self._status = new_status

    def get_status(self):
        return self._status

    def set_profit_weight_map(self, p_map):
        self._profit_weight_map = p_map
        self._reconstruct_model()

    def get_profit_weight_map(self):
        return self._profit_weight_map

    def set_location(self, new_location):
        self._location = new_location

    def get_location(self):
        return self._location

    location = property(get_location, set_location)
    profit_weight_map = property(get_profit_weight_map, set_profit_weight_map)
    status = property(get_status, set_status)
    running_score_average = property(get_running_score_average)

    def new_prediction_request(self, time_stamp):
        q_size = len(self.prediction_queue)
        if q_size != 0:
            last_prediction:AIPrediction = self.prediction_queue[q_size - 1]
            if self.timestamp_bucket (last_prediction.prediction_time) >= self.timestamp_bucket(time_stamp):
                raise PredictionAlreadyExists
        self.prediction_queue.append (AIPrediction (self, time_stamp, self.predict(time_stamp)))
        if (q_size > config.MAX_PREDICTION_SIZE):
            raise MaximumPredictionExceeded
        return self.prediction_queue[q_size]

    def process_predictions(self, process_time):
        '''
            - Check if prediction can be realized
            - If so, compare real data with prediction and add score to network
            - remove matured prediction from network's prediction queue
            - Return all processed predictions to the caller
        '''
        predictions_to_delete = []
        for p in self.prediction_queue:
            score = p.mature(process_time)
                # mature function returns a score if process time - prediction time gives
                # enough points otherwise it returns none
            if score:
                self.add_new_score(score)
                predictions_to_delete.append (p)
                self.processed_predictions = self.processed_predictions + 1

        prediction_list = []
        for tp in predictions_to_delete:
            prediction_list.append(tp)
            self.prediction_queue.remove(tp)
        
        return prediction_list



    def network_details (self):
        '''
            Returns serialized network details in dict
            This object is sent to update topics of kafka to inform state changes of the networks by
            worker processes. Add fields as you need.
        '''
        last_trained_pretty = datetime.fromtimestamp(self.last_trained_time) \
            .strftime("%m/%d/%Y, %H:%M:%S")
        input_dp_details = ""

        for dp in self.children:
            if isinstance(dp, AIDataport):
                input_dp_details += dp.params["symbol"] + ":" + str(dp.params["size"]) + ":"+ str(dp.params["aggregation_type"]) + " " 

        return {
            'network_id': self.record_id,
            'symbol' :self.output_dataport.params["symbol"],
            'status' : self.status.name,
            'input_details' : input_dp_details,
            'input_size'    : self._input_layer_size,
            'hidden_layers' : self.hidden_layers,
            'output_size'   : self.output_dataport.params["size"],
            'output_agg'   : self.output_dataport.params["aggregation_type"].name,
            'trained_up_to' : last_trained_pretty,
            'next_training' : str(datetime.fromtimestamp(self.next_training_time())),
            'pending_predictions' : len(self.prediction_queue),
            'processed_predictions' : self.processed_predictions,
            'score' : self.score
        }
            
if __name__ == "__main__":
    network = AINetwork("")
    network.load(1749)
    counter = 0
    process_step = network.minimum_aggregation_type().value
    latest_time_to_train = network.latest_time_stamp()
    network.training_status = AINetworkTrainingStatus.InTraining
    time_cursor = network.earliest_time_stamp()
    # while time_cursor <= latest_time_to_train:
    while counter <= 120:
        if counter > 150:
            output_data = []
            for rec in network._pull_output_data(time_cursor):
                output_data.append(rec[0])
            temp = network.normalize_output_data(
                output_data, network.output_dataport.params["aggregation_type"])

            predicted_values = network.predict(time_cursor)
            max_value = max(predicted_values[0])
            prediction_index = predicted_values[0].tolist().index(max_value)
            prediction_perc = prediction_index / len(predicted_values)
            verdict = "NO IDEA"
            if (prediction_perc < 0.20):
                verdict = " WILL GO DOWN"
            elif (prediction_perc < 0.30):
                verdict = " MAY GO DOWN"
            elif (prediction_perc < 0.60):
                verdict = " STAY"
            elif (prediction_perc < 0.70):
                verdict = " MAY GO UP"
            else:
                verdict = " WILL GO UP"

            dt_object = datetime.fromtimestamp(time_cursor)
            print('date: {}\nNetwork: {}\ntime stamp: {}\nprediction: {}\nreal values: {}\nvector: {}\n'
                  .format(dt_object, network.output_dataport.params["symbol"], time_cursor, verdict, output_data, temp))
        network.train(time_cursor)
        time_cursor += process_step
        counter += 1
    predicted_values_original = network.predict(time_cursor)
    print(predicted_values_original)
    rec_id = network.post()
    network2 = AINetwork("")
    network2.load(rec_id)
    print(network2.predict(time_cursor))
