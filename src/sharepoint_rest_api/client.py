import logging
import os

from office365.runtime.auth.userCredential import UserCredential
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
from office365.sharepoint.files.file_creation_information import FileCreationInformation
from office365.sharepoint.search.searchRequest import SearchRequest
from office365.sharepoint.search.searchService import SearchService

from sharepoint_rest_api import config
from sharepoint_rest_api.builders.camlquery_builder import CamlQueryBuilder
from sharepoint_rest_api.builders.querystring_builder import QueryStringBuilder
from sharepoint_rest_api.builders.search_request_builder import SearchRequestBuilder

logger = logging.getLogger(__name__)


default_select = ['*', 'FileLeafRef']


class SharePointClientException(BaseException):
    """SharePoint Exception when initializing the client"""


class SharePointClient:
    """Client to access SharePoint Document Library"""

    def __init__(self, *args, **kwargs) -> None:
        self.relative_url = kwargs.get('relative_url', None)
        self.site_path = kwargs.get('url', config.SHAREPOINT_TENANT)
        username = kwargs.get('username', config.SHAREPOINT_USERNAME)
        password = kwargs.get('password', config.SHAREPOINT_PASSWORD)
        self.folder = kwargs.get('folder', 'Documents')
        self.context = ClientContext.connect_with_credentials(self.site_path, UserCredential(username, password))

    def get_folder(self, list_title):
        list_obj = self.context.web.lists.get_by_title(list_title)
        folder = list_obj.rootFolder
        self.context.load(folder)
        self.context.execute_query()
        logger.info(f'List url: {folder.properties["ServerRelativeUrl"]}')
        return folder

    def read_folders(self, list_title):
        self.get_folder(list_title)
        folders = self.context.web.folders
        self.context.load(folders)
        self.context.execute_query()
        for folder in folders:
            logger.info(f'Folder name: {folder.properties["Name"]}')

        return folders

    def read_files(self, filters=None):
        filters = filters or dict()
        querystring = QueryStringBuilder(filters).get_querystring()
        folder = self.get_folder(self.folder)
        files = folder.files.filter(querystring)
        self.context.load(files)
        self.context.execute_query()
        for cur_file in files:
            logger.info(f'File name: {cur_file.properties["Name"]}')

        return files

    def read_items(self, filters=None, select=None):
        filters = filters or dict()
        querystring = QueryStringBuilder(filters).get_querystring()
        list_object = self.context.web.lists.get_by_title(self.folder)
        select_string = select or default_select
        items = list_object.get_items().filter(querystring).select(select_string)
        self.context.load(items)
        self.context.execute_query()
        return items

    def read_file(self, filename):
        folder = self.get_folder(self.folder)
        cur_file = folder.files.get_by_url(f'/{self.relative_url}/{self.folder}/{filename}')
        self.context.load(cur_file)
        self.context.execute_query()
        logger.info(f'File name: {cur_file.properties["Name"]}')
        return cur_file

    def read_caml_items(self, filters=None, scope=None):
        filters = filters or dict()
        list_obj = self.context.web.lists.get_by_title(self.folder)
        qry = CamlQueryBuilder(filters, scope).get_query()
        items = list_obj.get_items(qry)
        self.context.execute_query()
        return items

    def search(self, filters=None):
        filters = filters or dict()
        qry = SearchRequestBuilder(filters).get_query()
        search = SearchService(self.context)
        request = SearchRequest(qry)
        result = search.post_query(request)
        self.context.execute_query()
        relevant_results = result.PrimaryQueryResult.RelevantResults
        results = relevant_results['Table']['Rows'].values()
        return [list(item['Cells'].values()) for item in results]

    def upload_file_alt(self, target_folder, name, content):
        context = target_folder.context
        info = FileCreationInformation()
        info.content = content
        info.url = name
        info.overwrite = True
        target_file = target_folder.files.add(info)
        context.execute_query()
        return target_file

    def upload_file(self, path, list_title='Documents', upload_into_library=True):
        with open(path, 'rb') as content_file:
            file_content = content_file.read()

        if upload_into_library:
            target_folder = self.context.web.lists.get_by_title(list_title).rootFolder
            file = self.upload_file_alt(target_folder, os.path.basename(path), file_content)
            logger.info('File url: {}'.format(file.properties['ServerRelativeUrl']))
        else:
            target_url = f'/{self.folder}/{os.path.basename(path)}'
            File.save_binary(self.context, target_url, str(file_content))

    def download_file(self, filename):
        response = File.open_binary(self.context, f'/{self.folder}/{filename}')
        with open(f'./data/{filename}', 'wb') as local_file:
            local_file.write(response.content)
