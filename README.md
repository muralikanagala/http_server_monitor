# Server Status Reporter

Python3 script to collect JSON responses from HTTP endpoints and perform aggregations based on the configuration.
This script requires a configuration file(config.yml) and a text file with the list of servers (servers.txt) passed as command line parameters.

## Features
 - Can hit thousands of endpoints and collect the JSON responses.
 - Validate the JSON responses with the schema provided in the config file.
 - Extract specified JSON properties from the response.
 - Perform add/subtract/multiply/divide operations across the JSON properties.
 - Perform average/sum aggregations of a JSON property (withnumerical value) by other properties.
 - Write output to files in JSON, YAML formats. 
 - Write output to the console in a format (template) defined the in the configuration.


## Installation
Make sure your computer has Python3 installed and it is the default Python version.

Copy the directory server_status_reporter to your computer and switch to that directory.
 
Run pip install, make sure you are using the right pip (Python3)
```bash 
pip install -r requirements.txt
```

## Usage
Create a server.txt file with the list of endpoints. Do not prefix HTTP/HTTPS or suffix with the  request path.
If there is a port number it is needed to be there. 

For exmaple, 
```bash
server-1
server-2.example.com:9999
server-3:8080
```
Edit the config.yml as per your use case, the example file provided is a good starting point. 
```yaml
config:
  name: Server Status Test
  timeout: 5  # aiohttp request timeout

check:
  name: "server status"
  path: "/status" # HTTP request path

  validate_properties:  # list of properties you are expecting to see and their types in the JSON response from the endpoint.
    - name: Application
      type: str
    - name: Success_Count
      type: int
    - name: Request_Count
      type: int
    - name: Version
      type: str

  extractions:  # JSON properties to extract from the response from the endpoint.
      application: Application
      request_count: Request_Count
      success_count: Success_Count
      version: Version

  calculations:  # math operations to perform between the extracted values defined in the section above.
    - new_var: success_rate  # new variable name with the value calculated from the operation below.
      operation: division # val1/val2
      val1: success_count
      val2: request_count

  aggregations: # after collecting the data from all the endpoints below aggregations are performed, average_by and sum_by are supported.
    - type: average_by
      value_field: success_rate  # the filed (with numerical value) for which the average is calculated.
      fields:  # average by these two fields from the extracted values from the extraction section above.
        - application
        - version

  outputs:  # produce output from all the endpoint data, calculations and aggregations.
      - type: file # write to a file.
        name: output.json   # file name.
        format: json  # file format, JSON and yml are supported.
      - type: console  # print to the screen.
        template: Application $application with Version $version has average success rate of $average # console output template, variables (with $ symbol) should be from the fields and aggregation results.
      - type: file
        name: output.yml
        format: yml
```

To start the script run the below.
```bash
python server_status_reporter.py -c config.yml -s servers.txt
```

## support
Please send an email to muralikanagala@outlook.com

