import yaml


def create_config_from_file(file_path: str):
    with open(file_path, 'r') as config_file:
        config_dict = yaml.full_load(config_file)

    return config_dict
