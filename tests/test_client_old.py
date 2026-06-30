from unittest import mock

import pytest

from sharepoint_rest_api.client import SharePointClient, SharePointClientException


@mock.patch("sharepoint_rest_api.client.ClientContext")
@mock.patch("sharepoint_rest_api.client.ClientCredential")
@mock.patch("sharepoint_rest_api.client.config.SHAREPOINT_CONNECTION", "app")
def test_init_app(mock_credential, mock_context):
    mock_context_instance = mock.MagicMock()
    mock_context.return_value = mock_context_instance
    mock_context_instance.with_credentials.return_value = mock_context_instance

    client = SharePointClient(
        url="https://test.sharepoint.com/",
        relative_url="sites/test",
        folder="Docs",
        client_id="test_id",
        client_secret="test_secret",
    )

    mock_credential.assert_called_once_with("test_id", "test_secret")
    mock_context.assert_called_once_with("https://test.sharepoint.com/")
    mock_context_instance.with_credentials.assert_called_once_with(mock_credential.return_value)
    assert client.folder == "Docs"


@mock.patch("sharepoint_rest_api.client.config.SHAREPOINT_CONNECTION", "invalid")
def test_init_invalid():
    with pytest.raises(SharePointClientException, match="Invalid connection type"):
        SharePointClient(url="https://test.sharepoint.com/", relative_url="sites/test")


@mock.patch("sharepoint_rest_api.client.ClientContext")
@mock.patch("sharepoint_rest_api.client.ClientCredential")
@mock.patch("sharepoint_rest_api.client.config.SHAREPOINT_CONNECTION", "app")
def test_reduce(mock_credential, mock_context):
    mock_context_instance = mock.MagicMock()
    mock_context.return_value = mock_context_instance
    mock_context_instance.with_credentials.return_value = mock_context_instance

    client = SharePointClient(
        url="https://test.sharepoint.com/",
        relative_url="sites/test",
        folder="Docs",
    )

    result = client.__reduce__()
    assert result == (SharePointClient, ("sites/test", "https://test.sharepoint.com/", "Docs"))


@mock.patch("sharepoint_rest_api.client.ClientContext")
@mock.patch("sharepoint_rest_api.client.ClientCredential")
@mock.patch("sharepoint_rest_api.client.config.SHAREPOINT_CONNECTION", "app")
def test_read_file(mock_credential, mock_context):
    mock_context_instance = mock.MagicMock()
    mock_context.return_value = mock_context_instance
    mock_context_instance.with_credentials.return_value = mock_context_instance

    client = SharePointClient(
        url="https://test.sharepoint.com/",
        relative_url="sites/test",
        folder="Docs",
    )

    mock_folder = mock.MagicMock()
    mock_file = mock.MagicMock()
    mock_file.properties = {"Name": "test.txt"}
    mock_folder.files.get_by_url.return_value = mock_file
    client.get_folder = mock.MagicMock(return_value=mock_folder)

    result = client.read_file("test.txt")

    client.get_folder.assert_called_once_with("Docs")
    mock_folder.files.get_by_url.assert_called_once_with("/sites/test/Docs/test.txt")
    mock_context_instance.load.assert_called_once_with(mock_file)
    mock_context_instance.execute_query.assert_called_once()
    assert result == mock_file


@mock.patch("sharepoint_rest_api.client.SearchRequestBuilder")
@mock.patch("sharepoint_rest_api.client.SearchService")
@mock.patch("sharepoint_rest_api.client.ClientContext")
@mock.patch("sharepoint_rest_api.client.ClientCredential")
@mock.patch("sharepoint_rest_api.client.config.SHAREPOINT_CONNECTION", "app")
def test_search(mock_credential, mock_context, mock_search_service, mock_builder):
    mock_context_instance = mock.MagicMock()
    mock_context.return_value = mock_context_instance
    mock_context_instance.with_credentials.return_value = mock_context_instance

    client = SharePointClient(
        url="https://test.sharepoint.com/",
        relative_url="sites/test",
        folder="Docs",
    )

    mock_search_instance = mock.MagicMock()
    mock_search_service.return_value = mock_search_instance

    mock_builder_instance = mock.MagicMock()
    mock_builder.return_value = mock_builder_instance
    mock_builder_instance.build.return_value = {"query": "test"}

    mock_result = mock.MagicMock()
    mock_search_instance.post_query.return_value = mock_result
    mock_result.value.PrimaryQueryResult.RelevantResults.Table.Rows = [mock.MagicMock()]
    mock_result.value.PrimaryQueryResult.RelevantResults.TotalRows = 5
    mock_result.value.PrimaryQueryResult.RelevantResults.Table.Rows[0].Cells = ["cell1"]

    result_items, total = client.search(search="test", page=1)

    mock_search_service.assert_called_once_with(mock_context_instance)
    mock_builder.assert_called_once_with("test", {}, None, None, None, 0)
    mock_builder_instance.build.assert_called_once()
    mock_search_instance.post_query.assert_called_once_with(query="test")
    mock_context_instance.execute_query.assert_called_once()
    assert result_items == [["cell1"]]
    assert total == 5


@mock.patch("sharepoint_rest_api.client.FileCreationInformation")
@mock.patch("sharepoint_rest_api.client.ClientContext")
@mock.patch("sharepoint_rest_api.client.ClientCredential")
@mock.patch("sharepoint_rest_api.client.config.SHAREPOINT_CONNECTION", "app")
def test_upload_file_alt(mock_credential, mock_context, mock_creation_info):
    mock_context_instance = mock.MagicMock()
    mock_context.return_value = mock_context_instance
    mock_context_instance.with_credentials.return_value = mock_context_instance

    client = SharePointClient(
        url="https://test.sharepoint.com/",
        relative_url="sites/test",
        folder="Docs",
    )

    mock_folder = mock.MagicMock()
    mock_folder.context = mock_context_instance
    mock_file = mock.MagicMock()
    mock_folder.files.add.return_value = mock_file

    mock_info = mock.MagicMock()
    mock_creation_info.return_value = mock_info

    result = client.upload_file_alt(mock_folder, "test.txt", b"content")

    mock_creation_info.assert_called_once()
    assert mock_info.content == b"content"
    assert mock_info.url == "test.txt"
    assert mock_info.overwrite is True
    mock_folder.files.add.assert_called_once_with(mock_info)
    mock_context_instance.execute_query.assert_called_once()
    assert result == mock_file


@mock.patch("sharepoint_rest_api.client.ClientContext")
@mock.patch("sharepoint_rest_api.client.ClientCredential")
@mock.patch("sharepoint_rest_api.client.config.SHAREPOINT_CONNECTION", "app")
def test_upload_file(mock_credential, mock_context):
    mock_context_instance = mock.MagicMock()
    mock_context.return_value = mock_context_instance
    mock_context_instance.with_credentials.return_value = mock_context_instance

    client = SharePointClient(
        url="https://test.sharepoint.com/",
        relative_url="sites/test",
        folder="Docs",
    )

    mock_file = mock.MagicMock()
    mock_file.read.return_value = b"content"
    mock_file.name = "test.txt"

    mock_root_folder = mock.MagicMock()
    mock_root_folder.context = mock_context_instance
    mock_list = mock.MagicMock()
    mock_list.root_folder = mock_root_folder
    mock_context_instance.web.lists.get_by_title.return_value = mock_list

    mock_target_file = mock.MagicMock()
    mock_root_folder.upload_file.return_value = mock_target_file
    mock_target_file.execute_query.return_value = mock_target_file

    mock_item = mock.MagicMock()
    mock_target_file.listItemAllFields = mock_item

    client.upload_file(mock_file, folder_name="MyDocs", metadata={"Title": "My Doc"})

    mock_file.read.assert_called_once()
    mock_context_instance.web.lists.get_by_title.assert_called_once_with("MyDocs")
    mock_root_folder.upload_file.assert_called_once_with("test.txt", b"content")
    mock_target_file.execute_query.assert_called_once()
    mock_item.set_property.assert_called_once_with(name="Title", value="My Doc")
    mock_item.update.assert_called_once()
    mock_context_instance.execute_query.assert_called_once()


@mock.patch("builtins.open", new_callable=mock.mock_open)
@mock.patch("sharepoint_rest_api.client.File")
@mock.patch("sharepoint_rest_api.client.ClientContext")
@mock.patch("sharepoint_rest_api.client.ClientCredential")
@mock.patch("sharepoint_rest_api.client.config.SHAREPOINT_CONNECTION", "app")
def test_download_file(mock_credential, mock_context, mock_file, mock_open):
    mock_context_instance = mock.MagicMock()
    mock_context.return_value = mock_context_instance
    mock_context_instance.with_credentials.return_value = mock_context_instance

    client = SharePointClient(
        url="https://test.sharepoint.com/",
        relative_url="sites/test",
        folder="Docs",
    )

    mock_response = mock.MagicMock()
    mock_response.content = b"file content"
    mock_file.open_binary.return_value = mock_response

    client.download_file("test.txt")

    mock_file.open_binary.assert_called_once_with(mock_context_instance, "/Docs/test.txt")
    mock_open.assert_called_once_with("./data/test.txt", "wb")
    mock_open.return_value.__enter__.return_value.write.assert_called_once_with(b"file content")
