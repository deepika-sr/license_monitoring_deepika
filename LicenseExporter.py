import time
import datetime
import concurrent.futures
import base64
import json
import copy
from prometheus_client import Gauge, start_http_server
from kafka import KafkaAdminClient, KafkaConsumer
from kafka.structs import TopicPartition
import config_reader as config
import logging
import argparse

logging.basicConfig(level=logging.ERROR)
# A status value used to indicate unable to read license
UNAVAILABLE = -255

LICENSE_INFO = Gauge('license_expiry_in_days',
                     'Confluent Kafka License validity for each cluster', ['envs', 'cluster', 'host', 'exp_date'])

# This takes individual license message from __confluent-command topic
# and parses the value part of the JWT and decode into a dict


def decode_license(message):
    '''
    Utility to decode the license information from the topic.
    essentially extrats the 'exp' data from the base64 encoded license JWT that 
    can be read from either '_confluent-command' or '_confluent-license' topic
    '''
    encoded_license = base64.b64decode(message.value)
    license_string = encoded_license.decode("utf-8")
    # get the second half of jwt after '.' TODO use jwt.decode instead
    value_begin_index = license_string.find('}')+1
    license_value = license_string[value_begin_index:]
    license_dict = json.loads(license_value)
    return license_dict

# Decorate function with metric


def export_license(client_config, security, cluster_name, envs, hosts):
    '''
    This function is called to read data from a cluster and decode the license info
    This function co-ordinate calling many utilities functions to get the work done
    '''

    topic = decide_license_topic(client_config, security, hosts)

    try:
        consumer = KafkaConsumer(auto_offset_reset='earliest',
                                 ** client_config, ** security, bootstrap_servers=hosts,
                                 consumer_timeout_ms=10000)

        lastOffset = get_lastOffset(topic, consumer)

        license_dict = {'exp': UNAVAILABLE}

        for message in consumer:
            if b'CONFLUENT_LICENSE' in message.key:
                license_dict = decode_license(message)
            if message.offset == lastOffset - 1:
                break

        host = hosts[0]
        # Check if a response was received
        if (license_dict['exp'] != UNAVAILABLE):
            exp_date, days_remaining = extract_expiry_time(license_dict)
            # add details to the Metics
            LICENSE_INFO.labels(envs, cluster_name,  host,
                                exp_date).set(days_remaining)  # in days
        else:
            # Declare that data was not received
            LICENSE_INFO.labels(envs, cluster_name, host,
                                'NA').set(UNAVAILABLE)
            logging.error('Unable to read license info from {0} in cluster {1}'.format(
                host, cluster_name))

    except Exception as e:
        print(e)
        logging.error('Could not connect to {0} in cluster {1}'.format(
            hosts[0], cluster_name))


def get_lastOffset(topic, consumer):
    '''
    Returns the last offset value for a given topic, partition=0. lastOffSet is needed to exit out when 
    messages are read upt to lastOffset
    '''
    tp = TopicPartition(topic, 0)
    # register to the topic
    consumer.assign([tp])

    # obtain the last offset value
    consumer.seek_to_end(tp)
    lastOffset = consumer.position(tp)

    consumer.seek_to_beginning(tp)
    return lastOffset


def decide_license_topic(client_config, security, hosts):
    '''
    License information can be in '_confluent-command' or '_confluent-license' topics,
     '_confluent-license' is used in pre 6.2.1 installations, in which case, '_confluent-command' doesnot exist
    '''
    adminclient = KafkaAdminClient(
        ** client_config, ** security, bootstrap_servers=hosts)

    topic = '_confluent-command'
    topic_desc = adminclient.describe_topics([topic])
    if not topic_desc[0]['error_code'] == 0:
        topic = '_confluent-license'

    adminclient.close()
    return topic


def extract_expiry_time(license_dict):
    '''
    Extracts the time remaining in a human readable form as expiry data and days remaining to expiry
    The original time of expiry as received from license is in Unix epoch time 
    '''
    expires_on = datetime.datetime.utcfromtimestamp(
        license_dict['exp'])
    exp_date = expires_on.strftime('%Y-%m-%d %H:%M:%S')
    time_remaining = (expires_on.date() -
                      datetime.date.today()).days
    return exp_date, time_remaining

##


def extract_props(security, cluster):
    '''
    An utility method that extracts cluster related properities and security 
    properties needed to connect and access data from the cluster
    '''
    bootstrap_servers = cluster['hosts']
    envs = cluster['envs']
    name = cluster['name']
    if 'cred' in cluster.keys():  # some clusters may have their own creds
        security['sasl_plain_username'] = cluster['cred']['sasl_plain_username']
        security['sasl_plain_password'] = cluster['cred']['sasl_plain_password']
    return bootstrap_servers, name, envs, security


def parseargs():
    '''
    Utility to neatly parse command line arguments
    '''
    cli = argparse.ArgumentParser(
        description="Component to monitor Confluent Kafka License Expiry dates")
    cli.add_argument('-p', '--port', metavar=' ', type=int,
                     default=8000, help='the port for prometheus endpoint: default=None', required=False)
    cli.add_argument('-c', '--config-path', metavar=' ', type=str,
                     help='file path to yml file containing target kafka clusters: default=None', required=True)
    cli.add_argument('-w', '--workers', metavar=' ', type=int, default=8,
                     help=' Number of workers to handle concurrent requests to kafka clusters:default=8', required=False)
    args = cli.parse_args()

    if not (0 < args.workers <= 16):
        logging.error(
            "Number of workers specified for arg -w/--workers too low or too high:min=1,max=16")
        exit(1)
    if not (0 < args.port):
        logging.error("Port number too low:try -p 8000")
        exit(1)

    return args.port, args.config_path, args.workers


if __name__ == '__main__':

    port, conf_file_path, num_workers = parseargs()

    start_http_server(port)
    logging.info('Starting server at port {0}'.format(port))

    while True:
        logging.info('started collecting license expiry details ..')
        # Obtain target cluster congifs from yml file
        client_config = config.get_client_config(conf_file_path)
        client = client_config['client']

        #  The following will exectue parallel reads to clusters
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:

            for cluster in client_config['clusters']:
                security = copy.deepcopy(client_config['security'])
                # extract props from congifs
                hosts, cluster_name, envs, sec = extract_props(
                    security, cluster)
                # each cluster in the config read by a worker from a pool of max_workers
                futuren_to_export_license = executor.submit(
                    export_license, client, sec, cluster_name, envs, hosts)

        # we may want to scrape once a day
        time.sleep(24*60*60)
        # time.sleep(180)
