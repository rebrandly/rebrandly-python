from src.paginated_response import PaginatedResponse
import json
from requests.exceptions import HTTPError

class Links:
    def __init__(self, session):
        self.session = session
        self.base_uri = 'https://api.rebrandly.com/v1'
        self.base_links_uri = 'https://api.rebrandly.com/v1/links'
        self.base_enterprise_links_uri = 'https://enterprise-api.rebrandly.com/v1/links'

    def evaluate_response_status_code_return_object(self, response, request_type, object_type, object_id):
        response_json = json.loads(response.text)
        if response.status_code == 200:
            if response_json:
                return response_json
            elif response.request.method == "GET":
                return response_json
            else:
                return object_id
        elif response.status_code == 403:
            if "code" in response_json and response_json["code"] == 'OwnerFeatureNotIncluded':
                permission_missing = response_json["source"]
                raise HTTPError(f"{request_type} request failed for {object_type} with id {object_id} due to missing permission: {permission_missing}.")
            if response_json["errors"]:
                error = response_json["errors"][0]
                if error["property"] == 'destination' and error["code"] == "InvalidFormat":
                    raise ValueError(f"{request_type} request failed for {object_type} with id {object_id} due to invalid destination URL.")
        # When specifying a workspace without a domain, response will be a 404 for create link endpoint
        elif response.status_code == 404:
            if response_json["code"] == 'NotFound' and response_json["source"] == 'domain':
                raise ValueError(f"{request_type} request failed for {object_type} with id {object_id}. Please ensure appropriate domain is specified.")
        else:
            raise HTTPError(f"{request_type} request failed for {object_type} with id {object_id}", response_json)
        raise HTTPError(f"{request_type} request failed for {object_type} with id {object_id}", response_json)

    def evaluate_response_status_code_return_count(self, response, request_type, object_type, object_id):
        if response.status_code == 200:
            response_json = json.loads(response.text)
            return response_json['count']
        elif response.status_code == 401:
            raise HTTPError(f"{request_type} request failed for {object_type} with id {object_id}. Please ensure a valid api key is set.")
        else:
            raise HTTPError(f"{request_type} request failed for {object_type} with id {object_id}", response)

    def get(self, link_id, workspace_id=None):
        url = self.base_links_uri + '/' + link_id
        params = {
            'workspace':workspace_id
        }
        response = self.session.get(url, params=params)
        return self.evaluate_response_status_code_return_object(response, 'Get', 'link', link_id)

    def update(self, link_id, destination, title, favourite='', description='', workspace_id=''):
        if favourite is not None:
            self.favourite(link_id, favourite, workspace_id=workspace_id)
        url = self.base_links_uri + '/' + link_id
        body = {
            'destination':destination,
            'title':title
        }
        if description:
            body["description"] = description
        data = json.dumps(body)
        response = self.session.post(url, params={"workspace":workspace_id}, data=data)
        return self.evaluate_response_status_code_return_object(response, 'Update', 'link', link_id)

    def favourite(self, link_id, favourite, workspace_id=''):
        url = self.base_links_uri + '/' + link_id + '/favourite'
        body = {
            'favourite':favourite
        }
        data = json.dumps(body)
        response = self.session.post(url, params={"workspace":workspace_id}, data=data)
        return self.evaluate_response_status_code_return_object(response, 'Favourite', 'link', link_id)

    def list(self, workspace_id='',order_by='', order_dir='', limit='',favourite='',domain_id='',domain_name='',creator_id='',slashtag='',date_from='',date_to=''):
        url = self.base_links_uri
        params = {
            'workspace':workspace_id,
            'orderBy':order_by,
            'orderDir':order_dir,
            'limit':limit,
            'favourite':favourite,
            'domain.id':domain_id,
            'domain.fullName':domain_name,
            'creator.id':creator_id,
            'slashtag':slashtag,
            'dateFrom':date_from,
            'dateTo':date_to
        }
        response = self.session.get(url, params=params)
        if type(self.evaluate_response_status_code_return_object(response, 'List', 'links', 'all_links')) == list:
            return PaginatedResponse(response, self.session)

    def create(self, destination, slashtag='', title='', domain_id='', domain_name='', description='', workspace_id=''):
        url = self.base_links_uri
        params = {
            'workspace':workspace_id
        }
        body = {
            "destination": destination,
            "slashtag":slashtag,
            "title":title,
            "domain":{
                "id": domain_id,
                "fullName": domain_name
            }
        }
        if description:
            body["description"] = description
        data = json.dumps(body)
        response = self.session.post(url, params=params, data=data)
        return self.evaluate_response_status_code_return_object(response, 'Create', 'link', '')

    def bulk_create(self, workspace_id, links):
        url = self.base_enterprise_links_uri
        # do we even want to check link validity?
        for link in links:
            self.check_link_validity(link)
        data = json.dumps(links)
        response = self.session.put(url, params={"workspace":workspace_id}, data=data)
        return self.evaluate_response_status_code_return_object(response, 'Bulk create', 'links', '')

    def check_link_validity(self, link):
        if (not "destination" in link) or (not link["destination"]):
            raise KeyError('Destination must be specified for every link.')

        if "domain" in link and "domainId" in link:
            raise KeyError('Specify the domain only once per link.')

        if "domainId" in link:
            if link["domainId"]:
                return
            else:
                raise ValueError('domainId key must have a valid value specified.')
        elif "domain" in link:
            if "id" in link["domain"] and link["domain"]["id"]:
                return
            elif "id" in link["domain"]:
                raise ValueError('Domain object must have a valid value for id key.')
            else:
                raise KeyError('Domain object must have id key specified.')
        else:
            raise KeyError('A key specifying the domain or domainId must exist for every link.')

    def count(self, favourite=None, domain_id='', domain_name='',workspace_id=''):
        url = self.base_links_uri + '/count'
        favourite_str = str(favourite).lower()
        params = {
            'favourite':favourite_str,
            'domain.id':domain_id,
            'domain.fullName':domain_name,
            'workspace':workspace_id
        }
        response = self.session.get(url, params=params)
        return self.evaluate_response_status_code_return_count(response, 'Count', 'links', '')

    def delete(self, link_id, workspace_id=''):
        url = self.base_links_uri + '/' + link_id
        response = self.session.delete(url, params={"workspace":workspace_id})
        return self.evaluate_response_status_code_return_object(response, 'Delete', 'link', link_id)

    # Links param expects an array of strings
    def bulk_delete(self, links, workspace_id=''):
        url = self.base_links_uri
        data = json.dumps({"links": links})
        response = self.session.delete(url, params={"workspace":workspace_id}, data=data)
        return self.evaluate_response_status_code_return_count(response, 'Bulk delete', 'workspace', workspace_id)

    # Route should specify the destination and conditions to be met for routing to that destination
    def create_route(self, link_id, route: dict, workspace_id=''):
        url = self.base_links_uri + '/' + link_id + '/rules'
        data = json.dumps(route)
        response = self.session.post(url, params={"workspace":workspace_id}, data=data)
        return self.evaluate_response_status_code_return_object(response, 'Create route', 'link', link_id)

    def update_route(self, link_id, route_id, routes, workspace_id=''):
        url = self.base_links_uri + '/' + link_id + '/rules/' + route_id
        data = json.dumps(routes)
        response = self.session.post(url, params={"workspace":workspace_id}, data=data)
        return self.evaluate_response_status_code_return_object(response, 'Update route', 'link', link_id)

    def list_routes(self, link_id, workspace_id=''):
        url = self.base_links_uri + '/' + link_id + '/rules'
        response = self.session.get(url, params={"workspace":workspace_id})
        return self.evaluate_response_status_code_return_object(response, 'Get routes', 'link', link_id)

    def delete_route(self, link_id, route_id, workspace_id=''):
        url = self.base_links_uri + '/' + link_id + '/rules/' + route_id
        response = self.session.delete(url, params={"workspace":workspace_id})
        return self.evaluate_response_status_code_return_object(response, 'Delete route', 'link', link_id)

    # Essential for configuring deep links
    def get_apps(self, workspace_id=''):
        url = 'https://api.rebrandly.com/v1/apps'
        response = self.session.get(url, params={"workspace":workspace_id})
        return self.evaluate_response_status_code_return_object(response, 'get', 'apps', 'any')

    # Deep links are also referred to as native routes in developer documentation for API
    def list_deep_links(self, link_id, workspace_id=''):
        url = self.base_links_uri + '/' + link_id + '/apps'
        response = self.session.get(url, params={"workspace":workspace_id})
        return self.evaluate_response_status_code_return_object(response, 'List deep links', 'link', link_id)

    # App must already be created within Rebrandly
    # Deep Links can only be created, read, and deleted. Deep Links can not be updated.
    def create_deep_link(self, link_id, app_id, path, workspace_id=''):
        url = self.base_links_uri + '/' + link_id + '/apps/' + app_id
        data = json.dumps(path)
        response = self.session.post(url, params={"workspace":workspace_id}, data=data)
        return self.evaluate_response_status_code_return_object(response, 'Update deep link', 'link', link_id)

    def delete_deep_link(self, link_id, app_id, workspace_id=''):
        url = self.base_links_uri + '/' + link_id + '/apps/' + app_id
        response = self.session.delete(url, params={"workspace":workspace_id})
        return self.evaluate_response_status_code_return_object(response, 'Delete deep link', 'link', link_id)

    def delete_deep_links(self, link_id, workspace_id=''):
        apps = self.list_deep_links(link_id, workspace_id=workspace_id)
        if len(apps) == 0:
            return 0
        for app in apps:
            app_id = app['id']
            self.delete_deep_link(link_id, app_id, workspace_id=workspace_id)
        return len(apps)

    def get_opengraph(self, link_id, workspace_id=''):
        url = self.base_links_uri + '/' + link_id +'/opengraph'
        response = self.session.get(url, params={"workspace":workspace_id})
        return self.evaluate_response_status_code_return_object(response, 'Get opengraph', 'link', link_id)

    def delete_opengraph(self, link_id, workspace_id=''):
        url = self.base_links_uri + '/' + link_id +'/opengraph'
        response = self.session.delete(url, params={"workspace":workspace_id})
        return self.evaluate_response_status_code_return_object(response, 'Delete opengraph', 'link', link_id)

    def set_opengraph(self, link_id, title, description='', image_url='', object_type='', locale='', workspace_id=''):
        url = self.base_links_uri + '/' + link_id +'/opengraph'
        opengraph_config = {
                "title": title,
                "description": description,
                "image": image_url,
                "type": object_type,
                "locale": locale
                }
        data = json.dumps(opengraph_config)
        response = self.session.post(url, params={"workspace":workspace_id}, data=data)
        return self.evaluate_response_status_code_return_object(response, 'Update opengraph', 'link', link_id)