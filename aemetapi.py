import requests
import json
import pytz
from tzlocal import get_localzone
from datetime import datetime, timedelta

# how to use
# initialize AEMTApi object with apikey and timezone (optional)
class AEMETApi:
    def __init__(self, apikey, timezone=None):
        # basic api and url parameters
        self.api_key = apikey
        self.params = {"api_key": self.api_key}
        self.base_url = "https://opendata.aemet.es/opendata"

        # supported options for station id and time aggregation
        self.stations = {
            "89064": "Juan Carlos I Meteorological Station",
            "89070": "Gabriel de Castilla Meteorological Station}"
        }
        self.time_aggregation_options = [None, "Hourly", "Daily", "Monthly"]

        # used to save dataset in local timezone if not provided it will try to use local timezone
        self.local_timezone = pytz.timezone(timezone) if timezone else get_localzone()

    def __get_data(self, endpoint):
        response = requests.get(self.base_url + endpoint, params=self.params)
        return response.json()

    # datetime format YYYY-MM-DDTHH:MM:SSUTC
    def get_antarctica_data(self, start_date, end_date, station_id, time_aggregation=None):
        if time_aggregation not in self.time_aggregation_options:
            time_aggregation_valid_options = (", ").join(
                ["None" if item is None else item for item in self.time_aggregation_options])
            return {
                "status":
                "400",
                "description":
                "Validation failure. Time aggregation not valid must be one of: %s" %
                time_aggregation_valid_options,
                "data": []
            }

        if station_id not in self.stations:
            return {
                "status":
                "400",
                "description":
                "Validation failure. Station id must be one of: %s" % self.stations,
                "dataset": []
            }

        endpoint = f"/api/antartida/datos/fechaini/{start_date}/fechafin/{end_date}/estacion/{station_id}"
        response = self.__get_data(endpoint)

        # if response contains data
        if response["estado"] == 200 and "datos" in response:
            return {
                "status": 200,
                "description": "OK",
                "dataset": self.aggregate_data(response["datos"], time_aggregation)
            }

        return {
            "status": response["estado"],
            "description": response["descripcion"],
            "dataset": []
        }
    
    # sorts data by time either on the raw data or on a processed/aggregated data
    def sort_data(self, data):
        return sorted(data, key=lambda x: x['fhora'] if 'fhora' in x else x['utc_datetime'])

    # assumes data is ordered by time
    # the algorithm is quite simple and not very efficient mainly useful for smaller sets of data
    # a better implementation would be done using pandas for very large datasets
    def aggregate_data(self, data_url, time_aggregation):
        # used to test the aggregated data from a file
        # data = json.load(open("test_data.json", "r"))
        data = json.loads(requests.get(data_url).text)

        aggregated_data = []
        if len(data) == 0:
            return aggregated_data

        # sort data by time
        data = self.sort_data(data)

        aggregated_item = {}
        for item in data:
            time = datetime.strptime(item["fhora"], "%Y-%m-%dT%H:%M:%S")

            if len(aggregated_data) > 0 and time_aggregation:
                last_time = aggregated_data[-1]["utc_datetime"]
                aggregate = time_aggregation == "Hourly" and last_time.hour == time.hour or time_aggregation == "Daily" and last_time.day == time.day or time_aggregation == "Monthly" and last_time.month == time.month
                if aggregate:
                    aggregated_item["temperature"] = (aggregated_item["temperature"] + item["temp"]) / 2
                    aggregated_item["pressure"] = (aggregated_item["pressure"] + item["pres"]) / 2
                    aggregated_item["speed"] = (aggregated_item["speed"] + item["vel"]) / 2
                    continue

            aggregated_item = {
                "station": item["nombre"],
                "utc_datetime": time,
                "datetime": time.replace(tzinfo=pytz.utc).astimezone(self.local_timezone),
                "temperature": item["temp"],
                "pressure": item["pres"],
                "speed": item["vel"]
            }
            aggregated_data.append(aggregated_item)

        return aggregated_data

    def print_aggregated_data(self, aggregated_data):
        if len(aggregated_data) > 0:
            for data in aggregated_data:
                print("Station: {0}\nDatetime: {1}\nTemperature (C): {2}\nPressure (hpa): {3}\nVelocity (m/s): {4}\n".format(
                    data['station'],
                    data['datetime'],
                    data['temperature'],
                    data['pressure'],
                    data['speed'])
                )


# used for testing the module directly
if __name__ == "__main__":
    apikey = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJjb250aW51YWxseWZvcmV2ZXJAZ21haWwuY29tIiwianRpIjoiM2QzZTY5YWUtN2RiZi00OTEwLTljMGQtNTM5MjQ1NDZjYjc4IiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE3MTA1OTE0MzIsInVzZXJJZCI6IjNkM2U2OWFlLTdkYmYtNDkxMC05YzBkLTUzOTI0NTQ2Y2I3OCIsInJvbGUiOiIifQ.I1RrlBauAYUHvCFn_tV8Fa_NZigNLIBX0fJe9xO1OfI"
    api = AEMETApi(apikey, "Europe/Madrid")

    aggregated_obj = api.get_antarctica_data(
        "2022-07-01T00:00:00UTC", "2022-08-04T00:00:00UTC", "89064", "Monthly")

    if aggregated_obj["status"] == 200:
        api.print_aggregated_data(aggregated_obj["dataset"])
