import sys
import os
import logging
import argparse
import json
from brass_api.orientdb.orientdb_helper import BrassOrientDBHelper


def setup_logger():
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    log = logging.getLogger()

    fileHandler = logging.FileHandler('Update_Schedule.log')
    fileHandler.setFormatter(logFormatter)
    log.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    log.addHandler(consoleHandler)

    log.setLevel('INFO')
    return log

def setup_node(database, name, property, property_type='String'):
    database.create_node_class(name)
    database.create_node_property(name, property, property_type)


def main(constraints=None, config_file=None, data_input=None, bw_allocs=None):
    # Create Radio Queues Database
    queue_database = BrassOrientDBHelper(constraints, config_file)
    queue_database.open_database()

    radio_input_name = 'Radio_Input'
    radio_control_name = 'Radio_Control'
    radio_queues_name = 'Radio_Queues'

    radio_input_property = 'Input_Rate'
    radio_control_property = 'BW_Allocs'
    radio_queues_property = 'Radio_Queues'

    # Create Classes and Properties in Database
    setup_node(queue_database, radio_input_name, radio_input_property, 'EMBEDDEDLIST')
    setup_node(queue_database, radio_control_name, radio_control_property, 'EMBEDDEDLIST')
    setup_node(queue_database, radio_queues_name, radio_queues_property, 'EMBEDDEDLIST')

    data_input_properties = {}
    if data_input is not None:
        with open(data_input, 'r') as f:
            data_input_properties[radio_input_property] = json.load(f)

    bw_allocs_properties = {}
    if bw_allocs is not None:
        with open(bw_allocs, 'r') as f:
            bw_allocs_properties[radio_control_property] = json.load(f)

    radio_queues_properties = {radio_queues_property: {}}

    queue_database.create_node(radio_input_name, data_input_properties)
    queue_database.create_node(radio_control_name, bw_allocs_properties)
    queue_database.create_node(radio_queues_name, radio_queues_properties)
    return queue_database


if __name__ == "__main__":
    log = setup_logger()
    print = log.info
    log.info("START NEW RUN\n")
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('DATABASE', action='store', default=sys.stdin, help='Database to be accessed', type=str)
        parser.add_argument('CONFIG', action='store', default=sys.stdin, help='Config file to access database server', type=str)
        parser.add_argument('-i', action='store', dest='data_input', default='data_input_rates.json', help='data input rates to be stored', type=str)
        parser.add_argument('-b', action='store', dest='bw_allocs', default='bw_allocs.json', help='data input rates to be stored', type=str)
        cli_args = parser.parse_args()
        database = cli_args.DATABASE
        config_file = cli_args.CONFIG
        bw_allocs = cli_args.bw_allocs
        data_input = cli_args.data_input
        main(database, config_file, data_input, bw_allocs)
    except IndexError:
        log.exception('Not enough arguments. The script should be called as following: '
                      'python {0} <MDL OrientDbDatabase> <config file>'.format(os.path.basename(__file__)))
    finally:
        log.info("Ending Current Run\n\n")