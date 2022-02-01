import time
import datetime
import base64
import json
from prometheus_client import Gauge, start_http_server, Summary, Info
from kafka import KafkaConsumer
import config_reader as config

# Create a metric to track time spent and requests made.
# REQUEST_TIME = Summary('request_processing_seconds',
#                        'Time spent processing request', ['method','host'])
#LICENSE_INFO = Info('license_expiry_information', 'License expirty of each cluster',['host'])
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


def export_license(client, security, name, bootstrap_servers):
    # REQUEST_TIME.labels('export_license',bootstrap_servers[0]).time()
    try:
        consumer = KafkaConsumer('_confluent-command', auto_offset_reset='earliest',
                                 ** client, ** security, bootstrap_servers=bootstrap_servers,
                                 consumer_timeout_ms=10000)
        # set default expiry to -1, A received response will overwrite it.
        license_dict = {'exp': -1}
        for message in consumer:
            if b'CONFLUENT_LICENSE' in message.key:
                license_dict = decode_license(message)
                # Other messages in this topic are not important, hence break
                break

        host = bootstrap_servers[0]
        # Check if a response was received 
        if (license_dict['exp'] != -1):
            expires_on = datetime.datetime.utcfromtimestamp(
                license_dict['exp'])
            exp_date = expires_on.strftime('%Y-%m-%d %H:%M:%S')
            days_remaining = (expires_on.date() - datetime.date.today()).days
            # add details to the Metics
            LICENSE_INFO.labels(name, host, exp_date).set(days_remaining)
        else:
            # Declare that data was not received
            LICENSE_INFO.labels(name, host, 'NA').set(-1)

    except Exception as e:
        print(e)


if __name__ == '__main__':

    # Start up the server to expose the metrics.
    start_http_server(8000)
    # Generate some requests.
    while True:
        print('started collecting license expiry details ..')
        client = config.client_conf['client']
        security = config.client_conf['security']
        for cluster in config.client_conf['clusters']:
            bootstrap_servers = cluster['hosts']
            name = cluster['name']
            export_license(client, security, name, bootstrap_servers)

        # TODO in real life, we may want to scrape 1 a day
        time.sleep(24*60*60)
        #time.sleep(60)
