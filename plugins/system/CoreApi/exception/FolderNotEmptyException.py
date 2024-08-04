from src.exceptions.HttpClientException import HttpClientException


class FolderNotEmptyException(HttpClientException):
    code = 400
    description = "Folder is not empty"
