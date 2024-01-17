
from genes.aigeneinputlayer import AIGeneInputLayer
from genes.aigenelayers import AIGeneLayers
from genes.aigeneoutput import AIGeneOutput
from mutators.aimutator import AIMutator
from core.ainetwork import AINetwork
mutator = AIMutator()
import atexit
network_list = []

def dec(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        network_list.append(result)
        return result
    return wrapper



@dec
def generate_dummy_network(symbols = [{
                        "symbol":mutator.random_symbol(),
                        "aggregation": mutator.random_aggregation(),
                        "size" : mutator.random_number(2, 32)}], output_size = None):
    
    n = AINetwork("")
    input_gene = AIGeneInputLayer([]);
    for symbol in symbols:
        input_gene.add_symbol(symbol)

    layer_gene = AIGeneLayers([32, 32, 16])
    output_gene = AIGeneOutput(output_size if output_size else mutator.random_number(2, 6), "TSLA")

    n.add_children(input_gene, layer_gene, output_gene)
    n.build_from_genes()
    n.post()
    return n    

@atexit.register
def clean_up():
    for n in network_list:
        n.delete_from_db()
