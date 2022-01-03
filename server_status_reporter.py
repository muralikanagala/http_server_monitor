#!/usr/bin/env python

__author__ = "Murali Kanagala"
__credits__ = ["Murali Kanagala"]
__version__ = "1.0.1"
__maintainer__ = "Murali Kanagala"
__status__ = "Production"

# http_server_monitor.py
# Python3 script to collect json responses from http end points and perform aggregations based on the configuration.
# Requires the configuration file passed as an argument
# Requires the list of http endpoints to collect data from.


import asyncio
import json
import time
import aiohttp
import argparse
import yaml
from itertools import groupby
from operator import itemgetter
from string import Template


class ServerStatus:
    def __init__(self, config_file, server_list):
        self.config_file = config_file
        self.server_list = server_list
        self.config_data = None

    # async function for speed up the network activity.
    async def get(self, url, session):
        try:
            async with session.get(url=url, timeout=self.config_data['config']['timeout']) as response:
                return await response.json()
        except Exception as e:
            print("Unable to get url {} due to {}.".format(url, e.__class__))
            return False

    # reads the config file passed as an parameter.
    def read_config(self):
        with open(self.config_file) as cfile:
            self.config_data = yaml.load(cfile, Loader=yaml.FullLoader)

    # main
    async def main(self):
        self.read_config()

        with open(self.server_list) as infile:
            check_result = []
            data_list = []
            check = self.config_data['check']

            for line in infile:
                url = "http://" + line.strip() + check['path']
                async with aiohttp.ClientSession() as session:
                    response = await asyncio.gather(self.get(url, session))
                    response = response[0]  # response object is a list with one response element

                    if response:
                        json_match = True  # boolean variable to skip the response if it is not valid as per config.

                        for prop in check['validate_properties']:

                            if not response.get(prop['name']):
                                print("Property {} is not available in the response {} from {}".format(prop['name'], response, url_with_path))
                                json_match = False

                            elif not isinstance(response[prop['name']], eval(prop['type'])):
                                print("Property {} type is not {} in {} from {}".format(prop['name'], prop['type'], response, url_with_path))
                                json_match = False

                        if not json_match:
                            continue  # this gets executed when the reponse is not meeting the config requirements (similar to schema)

                        temp_data_dict = {}  # this is a temporaty dictionary with json response items and also the calculated values

                        for k, v in check['extractions'].items():
                            temp_data_dict[k] = response[v]

                        # perform math operations as per config
                        # please make sure to define the response json properties to avoid errors here.
                        for calc in check['calculations']:

                            if calc['operation'] == "division":
                                result = temp_data_dict[calc['val1']] / temp_data_dict[calc['val2']]

                            elif calc['operation'] == "multiplication":
                                result = temp_data_dict[calc['val1']] * temp_data_dict[calc['val2']]

                            elif calc['operation'] == "addition":
                                result = temp_data_dict[calc['val1']] + temp_data_dict[calc['val2']]

                            elif calc['operation'] == "subtraction":
                                result = temp_data_dict[calc['val1']] - temp_data_dict[calc['val2']]

                            else:
                                result = None
                            temp_data_dict[calc['new_var']] = result
                            data_list.append(temp_data_dict)

        # below code block aggregates the values from the extraction and calculations from above.
        # average_by and sum_by are supported for now.
        for agg in check['aggregations']:

            grouper = itemgetter(*agg['fields'])
            agg_key = agg['type'].split('_')[0]
            value_field = agg['value_field']
            agg_type = agg['type']

            if agg_type == "average_by":

                for key, grp in groupby(sorted(data_list, key=grouper), grouper):
                    temp_dict = dict(zip(agg['fields'], key))
                    temp_list = [item[value_field] for item in grp]
                    temp_dict[agg_key] = round(sum(temp_list) / len(temp_list), 3)
                    temp_dict['metric'] = value_field
                    check_result.append(temp_dict)

            if agg_type == "sum_by":

                for key, grp in groupby(sorted(data_list, key=grouper), grouper):
                    temp_dict = dict(zip(agg['fields'], key))
                    temp_dict[agg_key] = round(sum(item[value_field] for item in grp), 3)
                    temp_dict['metric'] = value_field
                    check_result.append(temp_dict)

        # outputs to files and console
        # supports json and yaml file formats
        # console output uses a template from config
        # TODO: console output template needs some work to make it more flexible with different aggregation types.
        #  It works with average_by at the moment.
        for output in check['outputs']:

            if output['type'] == "console":
                t = Template(output['template'])

                for res in check_result:
                    print(t.substitute(res))

            elif output['type'] == "file":
                print("Writing output to the file {}".format(output['name']))

                if output['format'] == "json":
                    with open(output['name'], 'w') as outfile:
                        json.dump(check_result, outfile)

                elif output['format'] == "yml":
                    with open(output['name'], 'w') as outfile:
                        yaml.dump(check_result, outfile)


# MAIN
if __name__ == '__main__':
    # argument parser
    parser = argparse.ArgumentParser(description='Http server monitor')
    parser.add_argument('-c', action="store", dest="config_file", help='configuration yml file', required=True)
    parser.add_argument('-s', action="store", dest="server_list", help='file with list of servers', required=True)
    args = parser.parse_args()

    # starting the clock and creating an instance of the ServerStatus class.
    start = time.time()
    mon = ServerStatus(args.config_file, args.server_list)
    asyncio.run(mon.main())
    end = time.time()
    print("Duration: {} seconds".format(round(end - start), 3))
