from core.aibase import AIBase
from exceptions.exceptions import *
from config import config
import datetime
from statistics import mean
from utils.loggerfactory import logger

import json


class AIPrediction (AIBase):
    def __init__(self, network, prediction_time, prediction_points):
        AIBase.__init__(self, name="AIPrediction",
                        class_name="AIPrediction", record_id=-1)
        self.network = network
        self.prediction_time = prediction_time
        network.prediction = self
        self.prediction_points = prediction_points
        self.real_values = None
        self.matured_time = network.output_dataport.predicton_matured_time(prediction_time) + config.PREDICTION_MATURATION_BUFFER_TIME

    def __str__(self):
        n = self.network
        return (
            f'Prediction Details\n'
            f'Network id      : {n.record_id}\n'
            f'Symbol          : {n.output_dataport.params["symbol"]}\n'
            f'Input size      : {n._input_layer_size}\n'
            f'Output size     : {n.output_dataport.params["size"]}\n'
            f'Prediction time : {datetime.datetime.fromtimestamp(self.prediction_time)}\n'
            f'Next P. time    : {datetime.datetime.fromtimestamp(self.prediction_time)}\n'
            f'Matured_time    : {datetime.datetime.fromtimestamp(self.matured_time)}\n'
            f'Prediction      : {self.prediction_points}\n'
            f'Real Values     : {self.real_values}\n'
            f'Network score   : {n.score}\n')

    def get_details (self):
        n = self.network
        return {
            'network_id' : n.record_id,
            'symbol' : n.output_dataport.params["symbol"],
            'input_size' : n._input_layer_size,
            'output_size' : n.output_dataport.params["size"],
            'prediction_time' : self.prediction_time,
            'next_prediction_time' : self.prediction_time,
            'matured_time' : self.matured_time,
            'prediction' : str(self.prediction_points),
            'real_values' : str(self.real_values),
            'network_score' : n.score
        }        

    def calculate_score(self, predicted_data, real_data):
        if not len(real_data) == len(predicted_data):
            logger().error(
                f'prediction data size is not same with real data.\n expected: {len(real_data)} retrieved: {len(predicted_data)}')
            logger().info(str(self))
            raise PredictionDataMismatch (f'prediction data size is not same with real data.\n expected: {len(real_data)} retrieved: {len(predicted_data)}')

        diff_list = [(abs(predicted_data[i] - real_data[i]))
                     for i in range(0, len(predicted_data))]
        score = 1.0 - sum(diff_list) / mean(real_data)
        return score

    def mature(self, time_stamp):
        """matches prediction data to real data and returns a score
           if time_stamp is not late enough to gather real time data returns None

        Args:
            time_stamp (time_Stamp): process time

        Returns:
            None, Float: either returns a score or None if score cannot be calculated due to limited data
        """
        score = 0
        maturization_time = self.matured_time
        if time_stamp < maturization_time:
            logger().info (f'Network {self.network.record_id} is not mature. Maturization Time: {datetime.datetime.fromtimestamp(maturization_time)} process time: {datetime.datetime.fromtimestamp(time_stamp)}')
#            print (f'prediction is not mature yet! p. time: {datetime.datetime.fromtimestamp(self.prediction_time)}  maturizitation time: {datetime.datetime.fromtimestamp(maturization_time)}')
            return None
        output_data = []
        for rec in self.network._pull_output_data(time_stamp):
            output_data.append(rec[0])

        normalized_values = self.network.normalize_output_data(output_data,
                                                               self.network.output_dataport.params["aggregation_type"])
        self.real_values = [x for x in normalized_values]
        try:
            score = self.calculate_score(self.prediction_points[0], self.real_values)
        except PredictionDataMismatch as e:
            print (f'error (PredictionDataMismatch): {e}')
        return score
