import logging
import os

from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
from office365.sharepoint.files.file_creation_information import FileCreationInformation
from office365.sharepoint.search.searchService import SearchService

from sharepoint_rest_api import config
from sharepoint_rest_api.builders.camlquery_builder import CamlQueryBuilder
from sharepoint_rest_api.builders.querystring_builder import QueryStringBuilder
from sharepoint_rest_api.builders.search_request_builder import SearchRequestBuilder
from sharepoint_rest_api.config import SHAREPOINT_PAGE_SIZE

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
        self.context = ClientContext(self.site_path).with_user_credentials(username, password)

    def __reduce__(self):
        return SharePointClient, (self.relative_url, self.site_path, self.folder, )

    def get_folder(self, folder_name):
        """
        :param folder_name: name of the folder
        :return: folder object

        Return folder object
        """
        list_obj = self.context.web.lists.get_by_title(folder_name)
        folder = list_obj.root_folder
        self.context.load(folder)
        self.context.execute_query()
        logger.info(f'List url: {folder.properties["ServerRelativeUrl"]}')
        return folder

    def read_folders(self, folder_name):
        """
        :param folder_name:
        :return: folders

        Return folders metadata for subfolder of current folder
        """
        self.get_folder(folder_name)
        folders = self.context.web.folders
        self.context.load(folders)
        self.context.execute_query()
        for folder in folders:
            logger.info(f'Folder name: {folder.properties["Name"]}')
        return folders

    def read_files(self, filters=None):
        """
        :param filters:
        :return: files

        Returns files metadata for files in current folder
        """
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
        """
        :param filters: filter dictionary
        :param scope: SharePoint scope
        :return: items

        Retrieves (filtered) items on current folder using querystring
        """
        filters = filters or dict()
        querystring = QueryStringBuilder(filters).get_querystring()
        list_object = self.context.web.lists.get_by_title(self.folder)
        select_string = select or default_select
        items = list_object.get_items().filter(querystring).select(select_string)
        self.context.load(items)
        self.context.execute_query()
        return items

    def read_file(self, filename):
        """
        :param filename: filename
        :return:

        Retrieve file in current folder
        """
        folder = self.get_folder(self.folder)
        cur_file = folder.files.get_by_url(f'/{self.relative_url}/{self.folder}/{filename}')
        self.context.load(cur_file)
        self.context.execute_query()
        logger.info(f'File name: {cur_file.properties["Name"]}')
        return cur_file

    def read_caml_items(self, filters=None, scope=None):
        """
        :param filters: filter dictionary
        :param scope: SharePoint scope
        :return: items

        Retrieves (filtered) items on current folder using CamlQueries
        """
        filters = filters or dict()
        list_obj = self.context.web.lists.get_by_title(self.folder)
        qry = CamlQueryBuilder(filters, scope).get_query()
        items = list_obj.get_items(qry)
        self.context.execute_query()
        return items

    def search(self, filters=None, select=None, source_id=None, page=1):
        """
        :param filter: filter dictionary
        :param select: select string
        :param source_id: SharePoint SourceId
        :return: items and total row number

        search file in the SharePoint site
        """
        filters = filters or dict()
        search = SearchService(self.context)
        request = SearchRequestBuilder(filters, select, source_id, (page - 1) * SHAREPOINT_PAGE_SIZE).build()
        result = search.post_query(request)
        self.context.execute_query()
        relevant_results = result.PrimaryQueryResult.RelevantResults
        results = relevant_results['Table']['Rows'].values()
        logger.info(f'Retrieved: {relevant_results["TotalRows"]} results')
        items = [list(item['Cells'].values()) for item in results]
        return items, relevant_results["TotalRows"]

    def upload_file_alt(self, target_folder, name, content):
        context = target_folder.context
        info = FileCreationInformation()
        info.content = content
        info.url = name
        info.overwrite = True
        target_file = target_folder.files.add(info)
        context.execute_query()
        return target_file

    def upload_file(self, path, folder_name='Documents', upload_into_library=True):
        """
        :param path: location of the file
        :param folder_name:
        :param upload_into_library: boolean
        :return:
        """
        with open(path, 'rb') as content_file:
            file_content = content_file.read()

        if upload_into_library:
            target_folder = self.context.web.lists.get_by_title(folder_name).rootFolder
            file = self.upload_file_alt(target_folder, os.path.basename(path), file_content)
            logger.info('File url: {}'.format(file.properties['ServerRelativeUrl']))
        else:
            target_url = f'/{self.folder}/{os.path.basename(path)}'
            File.save_binary(self.context, target_url, str(file_content))

    def download_file(self, filename):
        """
        :param filename: name of the file to download
        :return:

        download file in current folder
        """
        response = File.open_binary(self.context, f'/{self.folder}/{filename}')
        with open(f'./data/{filename}', 'wb') as local_file:
            local_file.write(response.content)
