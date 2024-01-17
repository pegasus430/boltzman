from core.ainetwork import AINetwork
from core.aibase import AIAggregationType
from genes.aigeneinputlayer import AIGeneInputLayer
from genes.aigenelayers import AIGeneLayers
from genes.aigeneoutput import AIGeneOutput
from datetime import datetime


def generate_test_network () -> AINetwork:
    n = AINetwork("")
    input_gene = AIGeneInputLayer([{
                "symbol": "TSLA",
                "aggregation": AIAggregationType.Daily,
                "size" : 30
            },
            {
                "symbol": "GOOGL",
                "aggregation": AIAggregationType.ThirtySeconds,
                "size" : 30
            },
            {
                "symbol": "FB",
                "aggregation": AIAggregationType.FifteenMinutes,
                "size" : 30
            }])

    layer_gene = AIGeneLayers([32, 32, 16])
    output_gene = AIGeneOutput(2, "TSLA")

    n.add_children(input_gene, layer_gene, output_gene)
    n.build_from_genes()
    return n




def test_save_load():
    n = generate_test_network()
    recid = n.post()
    print ("first rec id ", recid, n.record_id)
    n2=AINetwork("")
    n2.load(recid) 
    print (n2.post(),n2.record_id)
    print (n2.post(), n2.record_id)
    assert (n == n2)
    print (n2.__dict__)

def test_set_output_dataport():
    n = AINetwork("")
    n.set_output_symbol("TSLA", AIAggregationType.OneHour , 10)
    assert(n.output_dataport.params["symbol"] == "TSLA")
    assert(n.output_dataport.params["size"] == 10)
    assert(n.output_dataport.params["aggregation_type"] == AIAggregationType.OneHour)    
    assert(n.output_dataport.is_input_port == False)

def test_add_hidden_layer():
    n = AINetwork("")
    n.add_hidden_layer(4)
    n.add_hidden_layer(3)
    assert(n.hidden_layers[0] == 4)
    assert(len(n.hidden_layers) == 2)
    assert(n.hidden_layers[1] == 3)

def test_timestamp_bucket():
    n = generate_test_network()
    for ts in range (1650504480 , 1650504480 + 100):
        b_ts = n.timestamp_bucket(ts)
        b_dt_object = datetime.fromtimestamp(b_ts)
        dt_object = datetime.fromtimestamp(ts)
        assert (b_ts % 30 == 0)


def test_profit_weight_map():
    n = generate_test_network()
    n._profit_weight_map = [-10, -5, -0, 5, 10]
    test_data = [
        {
            "output" : [5, 6, 2, 20],
            "weight_map" : [-10, -5, -0, 5, 10],
            "aggregation" : AIAggregationType.Daily,
            "expected_label" : [0, 0, 0, 0, 0, 1.0]
        },
        {
            "output" : [5, 1, 2, 1],
            "weight_map" : [-10, -5, -0, 5, 10],
            "aggregation" : AIAggregationType.Daily,
            "expected_label" : [1.0, 0, 0, 0, 0, 0]
        },
        {
            "output" : [5, 4.9, 4.7, 5.0],
            "weight_map" : [-10, -5, -1, 1, 5, 10],
            "aggregation" : AIAggregationType.Daily,
            "expected_label" : [0, 0, 0, 1.0, 0, 0, 0]
        }

    ]
    for test in test_data:      
        n.profit_weight_map = test["weight_map"]  
        assert ( n.normalize_output_data (test ["output"], test["aggregation"]) == test["expected_label"])

#test_profit_weight_map()
for i in range (0, 10):
    test_save_load()