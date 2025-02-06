import json
import requests
import pytest
import unittest
import time
import os
from dotenv import load_dotenv
from src.rebrandly_client import RebrandlyClient

env = os.getenv("ENVIRONMENT", "development")

if env == "production":
    load_dotenv(".env.production")
elif env == "test":
    load_dotenv(".env.test")
else:
    load_dotenv(".env.development")

client = RebrandlyClient(os.getenv('API_KEY'))
links = client.links

extended_workspace_id = os.getenv('EXTENDED_WORKSPACE_ID')
extended_workspace_domain_id = os.getenv('EXTENDED_WORKSPACE_DOMAIN_ID')
existing_ios_app_id = os.getenv('IOS_APP_ID')
existing_android_app_id = os.getenv('ANDROID_APP_ID')
destination_url_rbgy = 'https://rb.gy'
destination_url_rebrandly = 'https://rebrandly.com'
destination_url_invalid = 'ribrandly.com'
link_title = 'Your Rebrandly link title'

class LinksTest(unittest.TestCase):

    def tearDown(self):
        time.sleep(1)

    def test_update_client_api_key(self):
        assert isinstance(links.count(), int)

        client.update_api_key('012345678901234567890123456789ab')
        with pytest.raises(requests.exceptions.HTTPError):
            links.count()

    def test_link_single_create_with_domain_name(self):
        active_domains = links.session.get('https://api.rebrandly.com/v1/domains?active=true')
        response_json = json.loads(active_domains.text)
        domain_name = response_json[0]['fullName']
        link = links.create(destination_url_rbgy, title=link_title, domain_name=domain_name)
        link_id = link['id']
        assert link_id is not None
        assert link['destination'] == destination_url_rbgy
        assert link['title'] == link_title
        assert link['domainName'] == domain_name

        assert links.delete(link_id)

    def test_link_single_crud(self):
        link = links.create(destination_url_rbgy, title=link_title)
        link_id = link['id']
        assert link_id is not None
        assert link['destination'] == destination_url_rbgy
        assert link['title'] == link_title

        response = links.get(link_id)
        assert response['id'] == link_id

        updated_destination = destination_url_rebrandly
        updated_title = 'rebrandly home'
        updated_link = links.update(link_id, updated_destination, updated_title, True)
        assert updated_link['destination'] == updated_destination
        assert updated_link['title'] == updated_title
        assert updated_link['favourite'] == True
        assert link['slashtag'] == updated_link['slashtag']

        favourite_removed_link = links.update(link_id, updated_destination, updated_title, False)
        assert favourite_removed_link['favourite'] == False

        with pytest.raises(ValueError):
            links.update(link_id, destination_url_invalid, updated_title, False)

        assert links.delete(link_id)
        with pytest.raises(requests.exceptions.HTTPError):
            links.delete(link_id)

    def test_link_single_crud_with_workspace_session_header(self):
        workspace_id, domain_id = self._create_workspace_and_associate_domain()
        client.update_workspace(workspace_id)
        with pytest.raises(ValueError):
            links.create(destination_url_rbgy, title=link_title)

        link = links.create(destination_url_rbgy, title=link_title, domain_id=domain_id)
        link_id = link['id']
        assert link_id is not None
        assert link['destination'] == destination_url_rbgy
        assert link['title'] == link_title

        response = links.get(link_id)
        assert response['id'] == link_id

        updated_destination = destination_url_rebrandly
        updated_title = 'rebrandly home'
        updated_link = links.update(link_id, updated_destination, updated_title, True)
        assert updated_link['destination'] == updated_destination
        assert updated_link['title'] == updated_title
        assert updated_link['favourite'] == True
        assert link['slashtag'] == updated_link['slashtag']

        with pytest.raises(ValueError):
            links.update(link_id, destination_url_invalid, updated_title, False)

        assert links.delete(link_id)
        with pytest.raises(requests.exceptions.HTTPError):
            links.delete(link_id)

        self._cleanup_links_and_workspace([link_id], workspace_id)
        client.update_workspace('')

    def test_link_single_crud_with_workspace_oneoff_header(self):
        workspace_id, domain_id = self._create_workspace_and_associate_domain()
        with pytest.raises(ValueError):
            links.create(destination_url_rbgy, title=link_title, workspace_id=workspace_id)

        link = links.create(destination_url_rbgy, title=link_title, domain_id=domain_id,  workspace_id=workspace_id)
        link_id = link['id']
        assert link_id is not None
        assert link['destination'] == destination_url_rbgy
        assert link['title'] == link_title

        response = links.get(link_id, workspace_id=workspace_id)
        assert response['id'] == link_id

        updated_destination = destination_url_rebrandly
        updated_title = 'rebrandly home'
        updated_link = links.update(link_id, updated_destination, updated_title, True,  workspace_id=workspace_id)
        assert updated_link['destination'] == updated_destination
        assert updated_link['title'] == updated_title
        assert updated_link['favourite'] == True
        assert link['slashtag'] == updated_link['slashtag']

        with pytest.raises(ValueError):
            links.update(link_id, destination_url_invalid, updated_title, False,  workspace_id=workspace_id)

        assert links.delete(link_id, workspace_id=workspace_id)
        with pytest.raises(requests.exceptions.HTTPError):
            links.delete(link_id, workspace_id=workspace_id)

        self._cleanup_links_and_workspace([link_id], workspace_id)


    def _create_workspace_and_associate_domain(self):
        url = 'https://api.rebrandly.com/v1/workspaces'
        workspace_config = {"name":"new-workspace-test", "type":"classic"}
        data = json.dumps(workspace_config)
        create_workspace_response = links.session.post(url, data=data)
        response_json = json.loads(create_workspace_response.text)
        workspace_id = response_json['id']

        active_domains = links.session.get('https://api.rebrandly.com/v1/domains?active=true')
        response_json = json.loads(active_domains.text)
        domain_id = response_json[0]['id']
        url = 'https://api.rebrandly.com/v1/workspaces/' + workspace_id + '/domains/' + domain_id
        links.session.post(url)
        return workspace_id, domain_id

    def test_link_list(self):
        workspace_id, domain_id = self._create_workspace_and_associate_domain()

        no_links_response = links.list(workspace_id=workspace_id)
        assert no_links_response.current_items_count == 0

        link_array = []
        for i in range(5):
            link_id = links.create(destination_url_rbgy, workspace_id=workspace_id, domain_id=domain_id)['id']
            link_array.append(link_id)

        page_of_links = links.list(workspace_id=workspace_id,limit=2)
        assert page_of_links.current_items_count == 2
        assert page_of_links.total_items_count == 2
        assert page_of_links.iteration_count == 1

        page_of_links.next()
        assert page_of_links.current_items_count == 2
        assert page_of_links.total_items_count == 4
        assert page_of_links.iteration_count == 2

        page_of_links.next()
        assert page_of_links.current_items_count == 1
        assert page_of_links.total_items_count == 5
        assert page_of_links.iteration_count == 3

        page_of_links.next()
        assert page_of_links.current_items_count == 0
        assert page_of_links.total_items_count == 5
        assert page_of_links.iteration_count == 3

        page_of_links.next()
        assert page_of_links.current_items_count == 0
        assert page_of_links.total_items_count == 5
        assert page_of_links.iteration_count == 3

        self._cleanup_links_and_workspace(link_array, workspace_id)

    def test_link_list_iter(self):
        workspace_id, domain_id = self._create_workspace_and_associate_domain()
        link_array = []
        for i in range(3):
            link_id = links.create(destination_url_rbgy, workspace_id=workspace_id, domain_id=domain_id)['id']
            link_array.append(link_id)

        page_of_links = links.list(workspace_id=workspace_id,limit=2)
        links_listed = []
        while page_of_links.current_items_count > 0:
            for link in page_of_links:
                links_listed.append(link)
            page_of_links.next()

        assert len(links_listed) == len(link_array)
        self._cleanup_links_and_workspace(link_array, workspace_id)


    def test_link_bulk_create_failures(self):
        link_array = [{
            "destination": destination_url_rbgy,
            "title": link_title,
            "ttl": 3600
            }
        ]
        with pytest.raises(KeyError):
            links.bulk_create(extended_workspace_id, link_array)

        link_array = [{
            "destination": destination_url_rbgy,
            "title": link_title,
            "ttl": 3600,
            "domainId": ''
            }
        ]
        with pytest.raises(ValueError):
            links.bulk_create(extended_workspace_id, link_array)

        link_array = [{
                "destination": destination_url_rbgy,
                "title": link_title,
                "ttl": 3600,
                "domain": ''
            }
        ]
        with pytest.raises(KeyError):
            links.bulk_create(extended_workspace_id, link_array)

        link_array = [{
                "destination": destination_url_rbgy,
                "title": link_title,
                "ttl": 3600,
                "domain": {"id": ''}
            }
        ]
        with pytest.raises(ValueError):
            links.bulk_create(extended_workspace_id, link_array)

    def test_link_bulk_create_http_errors(self):
        invalid_domain_id = 'd2eb9a9cb86e3830a821392d147f9a0a'
        link_array = [{
            "destination": destination_url_rbgy,
            "title": link_title,
            "ttl": 3600,
            "domain": {"id": 'invalid-id-value'}
            }
        ]
        with pytest.raises(requests.exceptions.HTTPError):
            links.bulk_create(extended_workspace_id, link_array)
        time.sleep(1)
        link_array[0]["domain"]["id"] = invalid_domain_id
        with pytest.raises(ValueError):
            links.bulk_create(extended_workspace_id, link_array)


        time.sleep(1)
        link_array = [{
            "destination": destination_url_rbgy,
            "title": link_title,
            "ttl": 3600,
            "domainId": "invalid-id-value"
        }
        ]
        with pytest.raises(requests.exceptions.HTTPError):
            links.bulk_create(extended_workspace_id, link_array)
        time.sleep(1)
        link_array[0]["domainId"] = invalid_domain_id
        with pytest.raises(ValueError):
            links.bulk_create(extended_workspace_id, link_array)


    def test_link_bulk_create(self):
        link_array = []
        link_one = {
            "destination": destination_url_rbgy,
            "slashtag": 'the-rb-gy-homepage',
            "tags": [],
            "scripts": [],
            "title": link_title,
            "ttl": 3600,
            "domainId": extended_workspace_domain_id
        }
        link_two = {
            "destination": destination_url_rebrandly,
            "ttl": 3600,
            "domain": {"id":extended_workspace_domain_id}
        }
        link_array.append(link_one)
        link_array.append(link_two)

        bulk_create_response = links.bulk_create(extended_workspace_id, link_array)
        assert len(bulk_create_response) == 2
        assert bulk_create_response[0]["destination"] == destination_url_rbgy
        assert bulk_create_response[1]["destination"] == destination_url_rebrandly

        link_ids = []
        for link in bulk_create_response:
            link_ids.append(link["id"])

        links.bulk_delete(link_ids, workspace_id=extended_workspace_id)

    def test_link_count(self):
        workspace_id, domain_id = self._create_workspace_and_associate_domain()

        link_array = []
        for i in range(5):
            link_id = links.create(destination_url_rbgy, workspace_id=workspace_id, domain_id=domain_id)['id']
            link_array.append(link_id)

        count_all = links.count(domain_id=domain_id, workspace_id=workspace_id)
        assert count_all == 5

        links.update(link_array[-1], destination_url_rbgy, link_title, favourite=True, workspace_id=workspace_id)

        count_favourites = links.count(domain_id=domain_id, favourite=True, workspace_id=workspace_id)
        assert count_favourites == 1
        count_nonfavourites = links.count(domain_id=domain_id, favourite=False, workspace_id=workspace_id)
        assert count_nonfavourites == 4
        assert count_favourites + count_nonfavourites == count_all

        self._cleanup_links_and_workspace(link_array, workspace_id)

    def _cleanup_links_and_workspace(self, link_array, workspace_id):
        links.bulk_delete(link_array, workspace_id=workspace_id)
        delete_workspace_url = 'https://api.rebrandly.com/v1/workspaces/'+workspace_id
        links.session.delete(delete_workspace_url)

    def test_link_bulk_delete(self):
        link_array = []
        for i in range(3):
            link_id = links.create(destination_url_rbgy)['id']
            link_array.append(link_id)
        number_links_deleted = links.bulk_delete(link_array)
        assert number_links_deleted == 3

    def test_route_crud(self):
        link_id = links.create(destination_url_rbgy)['id']
        assert len(links.list_routes(link_id)) == 0

        route = {
            "destination":destination_url_rebrandly,
            "condition":
                {"and":[{"property":"req.country","operator":"in","values":["ie"]}]}
        }
        route_details = links.create_route(link_id, route)
        route_id = route_details['id']
        assert route_details["destination"] == destination_url_rebrandly
        assert len(links.list_routes(link_id)) == 1

        route["destination"] = destination_url_rbgy
        updated_route_details = links.update_route(link_id, route_id, route)
        assert updated_route_details["destination"] == destination_url_rbgy
        assert len(links.list_routes(link_id)) == 1

        assert links.delete_route(link_id, route_id)
        assert len(links.list_routes(link_id)) == 0

        links.delete(link_id)

    def test_opengraph_crud(self):
        link_id = links.create(destination_url_rbgy)['id']
        assert links.get_opengraph(link_id) == {}

        assert links.set_opengraph(link_id, 'What is Rebrandly', image_url='https://rebrandly.com/example.jpg', object_type='website')

        opengraph_config = links.get_opengraph(link_id)
        assert opengraph_config == {
                'description': '',
                'image': 'https://rebrandly.com/example.jpg',
                'locale': '',
                'title': 'What is Rebrandly',
                'type': 'website'
            }

        link_opengraph = links.set_opengraph(link_id, 'URL Shortener', image_url='https://rebrandly.com/example.jpg', object_type='website')
        assert link_opengraph["title"] == 'URL Shortener'

        assert links.delete_opengraph(link_id) == link_id
        assert links.get_opengraph(link_id) == {}

        links.delete(link_id)

    def test_deep_links_crd(self):
        link_id = (links.create(destination_url_rbgy))['id']
        path_string = "/watch?apex=&ios_scheme=&v=3VmtibKpmXI"
        path_dict = {"path":path_string}
        assert links.create_deep_link(link_id, existing_ios_app_id, path_dict)

        first_deep_link = links.list_deep_links(link_id)[0]
        assert first_deep_link['active']
        assert first_deep_link['path'] == path_string

        assert links.delete_deep_link(link_id, existing_ios_app_id)
        assert len(links.list_deep_links(link_id)) == 0

        links.delete(link_id)

    def test_delete_deep_links(self):
        link_id = (links.create(destination_url_rbgy))['id']
        ios_path = {"path":"/watch?apex=&ios_scheme=&v=3VmtibKpmXI"}
        android_path = {"path":"/home?append=&prepend="}
        assert links.create_deep_link(link_id, existing_ios_app_id, ios_path)
        assert links.create_deep_link(link_id, existing_android_app_id, android_path)
        assert links.delete_deep_links(link_id) == 2
        links.delete(link_id)

if __name__ == '__main__':
    unittest.main()