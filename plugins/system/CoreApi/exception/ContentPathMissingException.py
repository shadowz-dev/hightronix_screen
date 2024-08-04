from src.exceptions.HttpClientException import HttpClientException


class ContentPathMissingException(HttpClientException):
    code = 400
    description = "Path is required"
