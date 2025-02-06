import json
from requests.exceptions import HTTPError
from src.paginated_response import PaginatedResponse

class Workspaces:
    WORKSPACE_TYPES = {'classic','extended'}

    def __init__(self, session):
        self.session = session
        self.base_workspaces_uri = 'https://api.rebrandly.com/v1/workspaces'

    def evaluate_response_status_code_return_object(self, response, request_type, object_id):
        if response.status_code == 200:
            response_json = json.loads(response.text)
            if response_json:
                return response_json
            else:
                return object_id
        elif response.status_code == 401:
            raise HTTPError(f"{request_type} request failed for workspace with id {object_id} as the request was unauthorized. Please ensure a valid api key is specified.")
        elif response.status_code == 403:
            response_json = json.loads(response.text)
            code = response_json["code"]
            if response.request.method == "DELETE":
                if code == 'CouldNotDeleteExtendedWorkspace':
                    raise ValueError(f"{request_type} request failed for workspace with id {object_id} because extended workspaces cannot be deleted.")
            else:
                if code and "errors" in response_json:
                    raise ValueError(f"{request_type} request failed for workspace with id {object_id} with error code: {code}.", response_json["errors"])
                if code:
                    raise HTTPError(f"{request_type} request failed for workspace with id {object_id} with error code: {code}.", response_json)
        elif response.status_code == 404:
            raise ValueError(f"{request_type} request failed for workspace with id {object_id} as the resource was not found. Please ensure all ids specified are correct.")
        else:
            raise HTTPError(f"{request_type} request failed for workspace with id {object_id}", json.loads(response.text))
        raise HTTPError(f"{request_type} request failed for workspace with id {object_id}", json.loads(response.text))

    def create(self, name, type, domain_ids=[]):
        workspace_type = type.lower()
        if workspace_type not in self.WORKSPACE_TYPES:
            workspace_types_str = ", ".join(self.WORKSPACE_TYPES)
            raise ValueError(f'Workspace type must be one of the following: {workspace_types_str}')
        workspace_config = {"name":name, "type":type}
        data = json.dumps(workspace_config)
        response = self.session.post(self.base_workspaces_uri, data=data)
        workspace = self.evaluate_response_status_code_return_object(response, 'Create', '')
        for domain_id in domain_ids:
                add_domain_to_workspace_url = self.base_workspaces_uri + '/' + workspace["id"] + '/domains/' + domain_id
                add_domain_response = self.session.post(add_domain_to_workspace_url)
                self.evaluate_response_status_code_return_object(add_domain_response, 'Associate domains', workspace["id"])
        return workspace

    def get(self, workspace_id):
        url = self.base_workspaces_uri + '/' + workspace_id
        response = self.session.get(url)
        return self.evaluate_response_status_code_return_object(response, 'Get', '')

    def list(self):
        response = self.session.get(self.base_workspaces_uri)
        if type(self.evaluate_response_status_code_return_object(response, 'List', 'all')) == list:
            return PaginatedResponse(response, self.session)

    def update(self, workspace_id, name=''):
        url = self.base_workspaces_uri + '/' + workspace_id
        data = json.dumps({"name":name})
        response = self.session.post(url, data=data)
        return self.evaluate_response_status_code_return_object(response, 'Update', workspace_id)

    def delete(self, workspace_id):
        url = self.base_workspaces_uri + '/' + workspace_id
        response = self.session.delete(url)
        return self.evaluate_response_status_code_return_object(response, 'Delete', workspace_id)

    def get_domains(self, workspace_id):
        url = self.base_workspaces_uri + '/' + workspace_id + '/domains'
        response = self.session.get(url)
        return self.evaluate_response_status_code_return_object(response, 'Get domains', workspace_id)