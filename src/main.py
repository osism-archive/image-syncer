import logging
import socket

import docker
from tabulate import tabulate
import yaml

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

client = docker.APIClient(base_url='unix:///var/run/docker.sock')

with open("etc/images.yml", "rb") as fp:
    images = yaml.load(fp, Loader=yaml.SafeLoader)

result = []

for image in images:
    logging.info("processing image %s" % image)

    source = images[image]['source']
    target = images[image]['target']

    for tag in images[image]['tags']:
        logging.info("processing tag %s" % tag)

        try:
            logging.info("pulling - %s:%s" % (source, tag))
            client.pull(source, tag)

            docker_image = client.inspect_image("%s:%s" % (source, tag))
            result.append([source, tag, docker_image["Id"],
                           docker_image["Created"]])

            logging.info("tagging - %s:%s" % (target, tag))
            client.tag("%s:%s" % (source, tag), target, tag)

            logging.info("pushing - %s:%s" % (target, tag))
            client.push(target, tag)
        except docker.errors.APIError:
            pass
        except socket.timeout:
            pass

for image in images:

    source = images[image]['source']
    target = images[image]['target']

    for tag in images[image]['tags']:

        try:
            logging.info("removing - %s:%s" % (source, tag))
            client.remove_image("%s:%s" % (source, tag))

            logging.info("removing - %s:%s" % (target, tag))
            client.remove_image("%s:%s" % (target, tag))
        except docker.errors.APIError:
            pass
        except socket.timeout:
            pass

print(tabulate(result, headers=["Image", "Tag", "Hash", "Created"]))
