from src.paginated_response import PaginatedResponse
import json
from requests.exceptions import HTTPError

class Domains:
    def __init__(self, session):
        self.session = session
        self.base_domains_uri = 'https://api.rebrandly.com/v1/domains'

    def evaluate_response_status_code_return_object(self, response, request_type, object_id):
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            raise HTTPError(f"{request_type} request failed for domain with id {object_id}", response)

    def list(self):
        response = self.session.get(self.base_domains_uri)
        if type(self.evaluate_response_status_code_return_object(response, 'List', 'all')) == list:
            return PaginatedResponse(response, self.session)