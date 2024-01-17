import time
from core.aibase import AIAggregationType
from workers.aiservice import AITask, AITaskStatus
from core.ainetwork import AINetwork , AINetworkTrainingStatus
from exceptions.exceptions import TrainerBeginTimeError, TrainerDispatcherError
import config.config as config
import uuid
import random
from mutators.aimutator import AIMutator
from utils.psqlutils import PsqlUtils 
sql_utils = PsqlUtils()


class AIMutatorTask(AITask):
    def __init__(self, mutation_percentage = config.DEFAULT_MUTATION_PERC, networks = [],capacity = config.DEFAULT_MUTATOR_CAPACITY):
        AITask.__init__(self, networks,[], [config.KAFKA_TOPICS["TOPIC_MODEL_NEEDS_TRAINING"]], capacity )
        self.mutation_perc = mutation_percentage

    def pull_source_networks(self):
        limit = self.capacity - len(self.networks)
        if limit <=0:
            return
        query ="SELECT * FROM network ORDER BY SCORE DESC LIMIT {}".format(limit)
        for rec in sql_utils.run_select_query(query):
            n = AINetwork("FB")
            n.load(rec[0])
            self.networks.append(n)

    def service_main(self):
        self.pull_source_networks()
        for n in self.networks:
            new_network = AINetwork()
            for gene in n.get_genes():
                gene.mutate(self.mutation_perc)
                new_network.add_children(gene)

            new_network.build_from_genes()
            new_network.post()
            new_network.training_status = AINetworkTrainingStatus.NewTraining
            new_network.post()
            new_network.print_genes()
            self.distribute_network (n)

        time.sleep(2)
