# Python SDK

For our official developer documentation, visit [our developer site](https://developers.rebrandly.com/docs/get-started)

## Description

This repository is a Python SDK that wraps the [Rebrandly API](https://developers.rebrandly.com/docs/get-started).

## Installation

```pip install rebrandly-sdk```

## Local Development and Testing

Create a .env.development or .env.test file with the below code and populate the values:

```bash
API_KEY='YOUR_API_KEY'
EXTENDED_WORKSPACE_ID='YOUR_EXTENDED_WORKSPACE_ID'
EXTENDED_WORKSPACE_DOMAIN_ID='YOUR_EXTENDED_WORKSPACE_DOMAIN_ID'
IOS_APP_ID='YOUR_IOS_APP_ID'
ANDROID_APP_ID='YOUR_ANDROID_APP_ID'
```

Export your ```ENVIRONMENT``` variable before running tests so test files know which .env file to load. If the ```ENVIRONMENT``` variable is not specified, the default file to be loaded is ```.env.development```.

## Authentication

This SDK supports authentication via API key. You can create an API key in your [Rebrandly dashboard](https://app.rebrandly.com/account/api).
The API key should be specified when creating a RebrandlyClient instance.

```python
from src.rebrandly_client import RebrandlyClient

client = RebrandlyClient('YOUR_API_KEY')
```

## Usage

### Create a link:

```python
client = RebrandlyClient('YOUR_API_KEY')
new_link = client.links.create('https://destination_url_...')
```

### Create conditional traffic routing rule:

```python
link_id = client.links.create('https://www.rebrandly.com')['id']
route = {
    "destination":'https://www.rebrandly.com/enterprise-security',
    "condition":
        {"and":[{"property":"req.country","operator":"in","values":["ie"]}]}
    }
client.links.create_route(link_id, route)
```

### Create link OpenGraph:

```python
link_id = client.links.create(destination_url_google)['id']
client.links.set_opengraph(link_id, 'What is Rebrandly', image_url='https://rebrandly.com/example.jpg', object_type='website')
```

### Create deep link:

```python
link_id = client.links.create('https://wwww.rebrandly.com')['id']
path = {"path":"/watch?apex=&ios_scheme=&v=3VmtibKpmXI"}
client.links.create_deep_link(link_id, 'YOUR-APP-ID-HERE', path)
```

## Pagination

This SDK supports pagination for requests that return many results. When a method that supports pagination is called, a PaginatedResponse instance will be returned. A PaginatedResponse is an iterable object that supports a next() function to retrieve the next batch of results.
Here is a code snippet for how to work with a method that supports pagination. In the example below, it will list all links and aggregate those links into an array called `all_links`.

```python
    page_of_links = client.links.list()
    all_links = []
    while page_of_links.current_links_count > 0:
        for link in page_of_links:
            all_links.append(link)
        page_of_links.next()
```

## Design Patterns

### Create and Update vs Set

Create methods will create a new resource. Update methods will update an existing resource. Set methods will create a resource or overwrite the existing resource if one already exists.

## License

Rebrandly Python SDK is released under the [MIT License](./LICENSE).
