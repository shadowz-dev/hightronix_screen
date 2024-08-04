from src.exceptions.HttpClientException import HttpClientException


class ContentNotFoundException(HttpClientException):
    code = 404
    description = "Content not found"
