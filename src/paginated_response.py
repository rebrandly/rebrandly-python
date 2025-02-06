import json
from requests.exceptions import HTTPError

class PaginatedResponse:
    def __init__(self, initial_response, session):
        self.session = session
        self.current_response = initial_response
        self.current_items = json.loads(initial_response.text)
        self.current_items_count = len(self.current_items)
        self.total_items_count = self.current_items_count
        self.iteration_count = 1
        if self.current_items_count > 0:
            self.last_item = self.current_items[-1]["id"]
        else:
            self.last_item = None
        self.request_url = initial_response.request.url
        self.request_method = initial_response.request.method.lower()
        self.request_path_url = initial_response.request.path_url.lower()

    def __iter__(self):
        return iter(self.current_items)

    def next(self):
        if self.request_method == 'get' and self.request_path_url[:9] == '/v1/links':
            if self.current_items_count == 0:
                return
            last_item = self.last_item
            endpoint = self.request_url + f"&last={last_item}"
            response = self.session.get(endpoint)
            response_json = json.loads(response.text)
            if response.status_code != 200:
                raise HTTPError("Next method failed due to error trying to get next page", response_json)
            response_has_new_items = (len(json.loads(response.text)) > 0)
            if response_has_new_items:
                self.current_items = response_json
                self.current_items_count = len(self.current_items)
                self.total_items_count += self.current_items_count
                self.last_item = self.current_items[-1]['id']
                self.iteration_count += 1
                self.current_response = response
            else:
                self.current_items_count = 0