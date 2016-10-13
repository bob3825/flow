import json
from vizone.client import HTTPServerError, HTTPClientError


class Store(object):
    """
    A Store is a centralized store based on the Client Config API. Note that:

    - The Client Config API operates per user.
    - The Client Config API operates per application.
    - Data can be any JSON serializable object, for instance nested python
      dicts, lists, strings, ints, floats and booleans.

    Usage example:

    .. code-block:: python

        from flow import Flow
        from flow.needs import NeedsStore, NeedsClient
        from flow.source import UnmanagedFilesListener

        class MyFlow(Flow, NeedsStore):
            \"""
            MyFlow uses a Store.
            \"""
            source = UnmanagedFilesListener

            def start(self, f, info=None, log_id=-1):

                # If your Flow class inherits NeedsStore, it will be equipped with
                # an ``self.store`` attribute which can be used to get, update and
                # delete stored data on the server.
                stored_info = self.store.get('key')
                if stored_info is None:
                    # there was nothing there
                
                self.store.put('key', {
                    'any': 'json',
                    'serializable': ['structure', 'goes', 'here']
                })

                # You can also delete
                self.store.delete('key')
    """
    def __init__(self, appname, client):
        """
        Store contructor is not lightweight, so you might want to reuse the instance.
        It only works with dicts for values and they are stored as JSON strings on
        the server side.

        Args:
            appname (unicode): Name of the application, used in the API calls
            client (vizone.client.Instance): Viz One client to use for calls
        """
        self._appname = appname or ''  # application is optional
        self._client = client

        collection = client.servicedoc.get_collection_by_keyword('client-config')
        self._resolve = collection.get_resolve_by_id('client-config')
        self._asset_resolve = collection.get_resolve_by_id('client-asset-config')
    
    def get(self, key, atomid=None):
        """
        Get the value of a certain key for the object's application.

        Args:
            key (unicode): The key used for storage

        Returns:
            dict: The stored value or ``None``
        """
        resolve, subs = self._get_resolve_and_subs(atomid)

        response = self._client.GET(resolve.make_url(key, subs), check_status=False)
        if response.status_code == 404:
            return None
        elif response.status_code >= 500:
            logging.log("HTTP Server Error %i" % response.status_code, response.content, 'xml', debug=False)
            raise HTTPServerError(response)
        elif response.status_code >= 400:
            logging.log("HTTP Client Error %i" % response.status_code, response.content, 'xml', debug=False)
            raise HTTPClientError(response)

        if response.content != '':
            return json.loads(response.content)
        else:
            return None

    def put(self, key, value, atomid=None):
        """
        Put a ``value`` under a ``key`` for the object's application.

        Args:
            key (unicode): The key used for storage
            value (dict): The data to store, as a dict

        Returns:
            dict: The stored value is returned
        """
        value = json.dumps(value)
        resolve, subs = self._get_resolve_and_subs(atomid)

        self._client.PUT(resolve.make_url(key, subs), value, {'Content-Type': 'application/octet-stream'})
        return value

    def delete(self, key, atomid=None):
        """
        Delete the stored ``value`` under a ``key`` for the object's application.

        Args:
            key (unicode): The key to delete
        """
        resolve, subs = self._get_resolve_and_subs(atomid)

        self._client.DELETE(resolve.make_url(key, subs))

    def _get_resolve_and_subs(self, atomid):

        if atomid:
            subs = {'vizid:application': self._appname, 'vizid:atom-id': atomid}
            resolve = self._asset_resolve
        else:
            subs = {'vizid:application': self._appname}
            resolve = self._resolve

        return resolve, subs
