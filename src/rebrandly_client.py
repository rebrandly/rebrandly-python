import requests
from src.links import Links
from src.workspaces import Workspaces
from src.domains import Domains

class RebrandlyClient:
    def __init__(self, api_key: str):
        self.session = requests.Session()
        headers = {"accept": "application/json", 'apikey': api_key, 'Content-type': 'application/json', 'User-Agent': 'rebrandly-python-sdk'}
        self.session.headers.update(headers)
        self.links = Links(self.session)
        self.workspaces = Workspaces(self.session)
        self.domains = Domains(self.session)

    def update_api_key(self, api_key):
        self.session.headers.update({"apikey":api_key})

    def update_workspace(self, workspace_id):
        self.session.headers.update({"workspace":workspace_id})