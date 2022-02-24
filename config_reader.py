from yaml import safe_load


# TODO handle DB  to read from inventory DB

# Every Time read from file.s
def get_client_config(conf_file_path):
    with open(conf_file_path, 'r') as conf:
        client_conf = safe_load(conf.read())
        return client_conf
