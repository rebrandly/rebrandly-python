import os
from dotenv import load_dotenv
from src.rebrandly_client import RebrandlyClient
import pytest


load_dotenv()
client = RebrandlyClient(os.getenv('API_KEY'))
workspaces = client.workspaces

name = 'your rb workspace'

def test_workspace_crud():
    with pytest.raises(ValueError):
        workspaces.create(name, 'invalidtype')

    workspace_id = workspaces.create(name, 'classic')["id"]
    assert workspace_id is not None

    workspace = workspaces.get(workspace_id)
    assert workspace['id'] == workspace_id
    assert workspace['name'] == name

    updated_name = 'updated rb workspace'
    updated_workspace = workspaces.update(workspace_id, updated_name)
    assert updated_workspace['name'] == updated_name

    assert workspaces.delete(workspace_id)

def test_workspace_create_with_domains():
    domains = client.domains.list()
    domain_id = [domains.last_item]
    workspace_id = workspaces.create(name, 'classic', domain_ids=domain_id)["id"]
    assert workspace_id is not None

    associated_domains = workspaces.get_domains(workspace_id)
    assert len(associated_domains) == 1

    assert workspaces.delete(workspace_id)

def test_workspace_list():
    page_of_workspaces = workspaces.list()
    assert  page_of_workspaces.current_items_count >= 1