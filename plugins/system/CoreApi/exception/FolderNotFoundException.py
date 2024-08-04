from src.exceptions.HttpClientException import HttpClientException


class FolderNotFoundException(HttpClientException):
    code = 404
    description = "Folder not found"
