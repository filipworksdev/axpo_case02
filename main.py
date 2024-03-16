from aemetapi import AEMETApi

apikey = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJjb250aW51YWxseWZvcmV2ZXJAZ21haWwuY29tIiwianRpIjoiM2QzZTY5YWUtN2RiZi00OTEwLTljMGQtNTM5MjQ1NDZjYjc4IiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE3MTA1OTE0MzIsInVzZXJJZCI6IjNkM2U2OWFlLTdkYmYtNDkxMC05YzBkLTUzOTI0NTQ2Y2I3OCIsInJvbGUiOiIifQ.I1RrlBauAYUHvCFn_tV8Fa_NZigNLIBX0fJe9xO1OfI"
api = AEMETApi(apikey, "Europe/Madrid")

aggregated_obj = api.get_antarctica_data(
    "2022-08-01T00:00:00UTC", "2022-08-04T00:00:00UTC", "89064", "Daily")

if aggregated_obj["status"] == 200:
    api.print_aggregated_data(aggregated_obj["dataset"])
