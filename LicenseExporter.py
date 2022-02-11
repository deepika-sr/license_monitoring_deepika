import time
import datetime
import concurrent.futures
import base64
import json
import copy
from prometheus_client import Gauge, start_http_server, Summary, Info
from kafka import KafkaConsumer
import config_reader as config
import logging

logging.basicConfig(level=logging.ERROR)
# A status value used to indicate unable to read license
UNAVAILABLE = -255

LICENSE_INFO = Gauge('license_expiry_in_days',
                     'License expirty of each cluster', ['cluster', 'host', 'exp_date'])

# This takes individual license message from __confluent-command topic
# and parses the value part of the JWT and decode into a dict


def decode_license(message):
    encoded_license = base64.b64decode(message.value)
    license_string = encoded_license.decode("utf-8")
    # get the second half of jwt after '.' TODO use jwt.decode instead
    value_begin_index = license_string.find('}')+1
    license_value = license_string[value_begin_index:]
    license_dict = json.loads(license_value)
    return license_dict

# Decorate function with metric
def export_license(client_config, security, cluster_name, bootstrap_servers):
    try:
        consumer = KafkaConsumer('_confluent-command', auto_offset_reset='earliest',
                                 ** client_config, ** security, bootstrap_servers=bootstrap_servers,
                                 consumer_timeout_ms=10000)
        # set default expiry to UNAVAILABLE, A received response will overwrite it.
        license_dict = {'exp': UNAVAILABLE}
        for message in consumer:
            if b'CONFLUENT_LICENSE' in message.key:
                license_dict = decode_license(message)
                # Other messages in this topic are not important, hence break
                break

        host = bootstrap_servers[0]
        # Check if a response was received
        if (license_dict['exp'] != UNAVAILABLE):
            exp_date, days_remaining = extract_expiry_time(license_dict)
            # add details to the Metics
            LICENSE_INFO.labels(cluster_name, host, exp_date).set(days_remaining)
        else:
            # Declare that data was not received
            LICENSE_INFO.labels(cluster_name, host, 'NA').set(UNAVAILABLE)
            logging.error('Unable to read license info from {0}'.format(host))

    except Exception as e:
        logging.error(e)
        logging.error(bootstrap_servers[0])


def extract_expiry_time(license_dict):
    expires_on = datetime.datetime.utcfromtimestamp(
        license_dict['exp'])
    exp_date = expires_on.strftime('%Y-%m-%d %H:%M:%S')
    days_remaining = (expires_on.date() - datetime.date.today()).days
    return exp_date, days_remaining


def extract_props(security, cluster):
    bootstrap_servers = cluster['hosts']
    name = cluster['name']
    if 'cred' in cluster.keys():  # some clusters may have their own creds
        security['sasl_plain_username'] = cluster['cred']['sasl_plain_username']
        security['sasl_plain_password'] = cluster['cred']['sasl_plain_password']
    return bootstrap_servers, name, security


if __name__ == '__main__':

    # Start up the server to expose the metrics.
    port = 8000
    start_http_server(port)
    logging.info('Starting server at port {0}'.format(port))
    # Generate some requests.
    while True:
        logging.info('started collecting license expiry details ..')

        client_config = config.get_client_config()
        client = client_config['client']

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for cluster in client_config['clusters']:
                security = copy.deepcopy(client_config['security'])
                hosts, cluster_name, sec = extract_props(security, cluster)
                futuren_to_export_license = executor.submit(
                    export_license, client, sec, cluster_name, hosts)

            # we may want to scrape once a day
        time.sleep(24*60*60)
        # time.sleep(180)
