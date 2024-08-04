import os
import time
import logging

from flask import request, abort, jsonify
from flask_restx import Resource, Namespace, fields, reqparse
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from src.model.entity.Content import Content
from src.manager.FolderManager import FolderManager
from src.model.enum.ContentType import ContentType, ContentInputType
from src.model.enum.FolderEntity import FolderEntity, FOLDER_ROOT_PATH
from src.interface.ObController import ObController
from src.util.utils import str_to_enum
from plugins.system.CoreApi.exception.ContentPathMissingException import ContentPathMissingException
from plugins.system.CoreApi.exception.ContentNotFoundException import ContentNotFoundException
from plugins.system.CoreApi.exception.FolderNotFoundException import FolderNotFoundException
from plugins.system.CoreApi.exception.FolderNotEmptyException import FolderNotEmptyException
from src.service.WebServer import create_require_api_key_decorator


# Namespace for content operations
content_ns = Namespace('contents', description='Operations on contents')

# Output model for content
content_output_model = content_ns.model('ContentOutput', {
    'id': fields.Integer(readOnly=True, description='Unique identifier of the content'),
    'name': fields.String(description='Name of the content'),
    'type': fields.String(description='Type of the content'),
    'location': fields.String(description='Location of the content'),
    'folder_id': fields.Integer(description='Folder ID where the content is stored')
})

# Model for folder operations
folder_model = content_ns.model('Folder', {
    'name': fields.String(required=True, description='Name of the folder'),
    'path': fields.String(required=False, description='Path context (with path starting with /)'),
    'folder_id': fields.Integer(required=False, description='Path context (with folder id)')
})

# Parser for bulk move operations
bulk_move_parser = content_ns.parser()
bulk_move_parser.add_argument('entity_ids', type=int, action='append', required=True, help='List of content IDs to move')
bulk_move_parser.add_argument('path', type=str, required=False, help='Path context (with path starting with /)')
bulk_move_parser.add_argument('folder_id', type=int, required=False, help='Path context (with folder id)')

# Parser for content add/upload (single file)
content_upload_parser = content_ns.parser()
content_upload_parser.add_argument('name', type=str, required=True, help='Name of the content')
content_upload_parser.add_argument('type', type=str, required=True, help='Type of the content')
content_upload_parser.add_argument('path', type=str, required=False, help='Path context (with path starting with /)')
content_upload_parser.add_argument('folder_id', type=str, required=False, help='Path context (with folder id)')
content_upload_parser.add_argument('location', type=str, required=False, help="Content location (valid for types: {}, {} and {})".format(
    ContentType.URL.value,
    ContentType.YOUTUBE.value,
    ContentType.EXTERNAL_STORAGE.value
))
content_upload_parser.add_argument('object', type=FileStorage, location='files', required=False, help="Content location (valid for types: {} and {})".format(
    ContentType.PICTURE.value,
    ContentType.VIDEO.value
))

# Parser for content add/bulk uploads (multiple files)
bulk_upload_parser = content_ns.parser()
bulk_upload_parser.add_argument('path', type=str, required=False, help='Path context (with path starting with /)')
bulk_upload_parser.add_argument('folder_id', type=str, required=False, help='Path context (with folder id)')
bulk_upload_parser.add_argument('object', type=FileStorage, location='files', action='append', required=True, help='Files to be uploaded')

# Parser for content edit
content_edit_parser = content_ns.parser()
content_edit_parser.add_argument('name', type=str, required=True, help='Name of the content')

# Parser for content path context actions
path_parser = content_ns.parser()
path_parser.add_argument('path', type=str, required=False, help='Path context (with path starting with /)')
path_parser.add_argument('folder_id', type=str, required=False, help='Path context (with folder id)')

# Parser for folder add/edit
folder_parser = content_ns.parser()
folder_parser.add_argument('name', type=str, required=True, help='Name of the folder')
folder_parser.add_argument('path', type=str, required=False, help='Path context (with path starting with /)')
folder_parser.add_argument('folder_id', type=str, required=False, help='Path context (with folder id)')

class ContentApiController(ObController):

    def register(self):
        self.api().add_namespace(content_ns, path='/api/contents')
        content_ns.add_resource(self.create_resource(ContentListResource), '/')
        content_ns.add_resource(self.create_resource(ContentResource), '/<int:content_id>')
        content_ns.add_resource(self.create_resource(ContentLocationResource), '/location/<int:content_id>')
        content_ns.add_resource(self.create_resource(ContentBulkUploadResource), '/upload-bulk')
        content_ns.add_resource(self.create_resource(FolderBulkMoveResource), '/folder/move-bulk')
        content_ns.add_resource(self.create_resource(FolderResource), '/folder')

    def create_resource(self, resource_class):
        # Function to inject dependencies into resources
        return type(f'{resource_class.__name__}WithDependencies', (resource_class,), {
            '_model_store': self._model_store,
            '_controller': self,
            'require_api_key': create_require_api_key_decorator(self._web_server)
        })

    def _get_folder_context(self, data):
        path = data.get('path', None)
        folder_id = data.get('folder_id', None)

        if folder_id:
            folder = self._model_store.folder().get(id=folder_id)

            if not folder:
                raise FolderNotFoundException()
            return path, folder

        if not path:
            raise ContentPathMissingException()

        path = "{}/{}".format(FOLDER_ROOT_PATH, path.strip('/')) if not path.startswith(FOLDER_ROOT_PATH) else path

        folder = self._model_store.folder().get_one_by_path(path=path, entity=FolderEntity.CONTENT)
        is_root_drive = FolderManager.is_root_drive(path)

        if not folder and not is_root_drive:
            raise FolderNotFoundException()

        return FOLDER_ROOT_PATH if is_root_drive else path, folder

    def _post_update(self):
        self._model_store.variable().update_by_name("last_content_update", time.time())


class ContentListResource(Resource):

    @content_ns.expect(path_parser)
    @content_ns.marshal_list_with(content_output_model)
    def get(self):
        """List all contents"""
        self.require_api_key()
        data = path_parser.parse_args()
        working_folder_path = None
        working_folder = None
        folder_id = None

        try:
            working_folder_path, working_folder = self._controller._get_folder_context(data)
            folder_id = data.get('folder_id', 0 if not working_folder else working_folder.id)
        except FolderNotFoundException:
            pass
        except ContentPathMissingException:
            pass

        contents = self._model_store.content().get_contents(
            folder_id=folder_id,
            slide_id=data.get('slide_id', None),
        )
        result = [content.to_dict() for content in contents]

        return result

    @content_ns.expect(content_upload_parser)
    @content_ns.marshal_with(content_output_model, code=201)
    def post(self):
        """Add new content"""
        self.require_api_key()
        data = content_upload_parser.parse_args()
        working_folder_path, working_folder = self._controller._get_folder_context(data)
        location = data.get('location', None)
        content_type = None

        # Handle content type conversion
        try:
            content_type = str_to_enum(data.get('type'), ContentType)
        except ValueError as e:
            abort(400, description=str(e))

        # Handle file upload
        file = data.get('object', None)

        if ContentType.get_input(content_type) == ContentInputType.UPLOAD:
            if not file:
                abort(400, description="File is required")

        content = self._model_store.content().add_form_raw(
            name=data.get('name'),
            type=content_type,
            request_files=file,
            upload_dir=self._controller._app.config['UPLOAD_FOLDER'],
            location=location,
            folder_id=working_folder.id if working_folder else None
        )

        if not content:
            abort(400, description="Failed to add content")

        return content.to_dict(), 201


class ContentResource(Resource):

    @content_ns.marshal_with(content_output_model)
    def get(self, content_id: int):
        """Get content by ID"""
        self.require_api_key()
        content = self._model_store.content().get(content_id)
        if not content:
            raise ContentNotFoundException()

        return content.to_dict()

    @content_ns.expect(content_edit_parser)
    @content_ns.marshal_with(content_output_model)
    def put(self, content_id: int):
        """Update existing content"""
        self.require_api_key()
        data = content_edit_parser.parse_args()
        content = self._model_store.content().get(content_id)

        if not content:
            raise ContentNotFoundException()

        if 'name' not in data:
            abort(400, description="Name is required")

        content = self._model_store.content().update_form(
            id=content.id,
            name=data.get('name'),
        )

        self._controller._post_update()

        return content.to_dict()

    def delete(self, content_id: int):
        """Delete content"""
        self.require_api_key()
        content = self._model_store.content().get(content_id)

        if not content:
            raise ContentNotFoundException()

        if self._model_store.slide().count_slides_for_content(content.id) > 0:
            abort(400, description="Content is referenced in slides")

        self._model_store.content().delete(content.id)
        self._controller._post_update()

        return {'status': 'ok'}, 204


class ContentLocationResource(Resource):

    def get(self, content_id: int):
        """Get content location by ID"""
        self.require_api_key()
        content = self._model_store.content().get(content_id)

        if not content:
            raise ContentNotFoundException()

        content_location = self._model_store.content().resolve_content_location(content)

        return {'location': content_location}


class ContentBulkUploadResource(Resource):

    @content_ns.expect(bulk_upload_parser)
    def post(self):
        """Upload multiple content files"""
        self.require_api_key()
        data = bulk_upload_parser.parse_args()
        working_folder_path, working_folder = self._controller._get_folder_context(data)

        for file in data.get('object'):
            content_type = ContentType.guess_content_type_file(file.filename)
            name = file.filename.rsplit('.', 1)[0]

            if content_type:
                self._model_store.content().add_form_raw(
                    name=name,
                    type=content_type,
                    request_files=file,
                    upload_dir=self._controller._app.config['UPLOAD_FOLDER'],
                    folder_id=working_folder.id if working_folder else None
                )

        return {'status': 'ok'}, 201


class FolderBulkMoveResource(Resource):

    @content_ns.expect(bulk_move_parser)
    def post(self):
        """Move multiple content to another folder"""
        self.require_api_key()
        data = bulk_move_parser.parse_args()

        working_folder_path, working_folder = self._controller._get_folder_context(data)

        if 'entity_ids' not in data:
            abort(400, description="Content IDs are required under 'entity_ids' field")

        entity_ids = data.get('entity_ids')

        for entity_id in entity_ids:
            self._model_store.folder().move_to_folder(
                entity_id=entity_id,
                folder_id=working_folder.id if working_folder else None,
                entity_is_folder=False,
                entity=FolderEntity.CONTENT
            )

        return {'status': 'ok'}


class FolderResource(Resource):

    @content_ns.expect(folder_parser)
    @content_ns.marshal_with(folder_model, code=201)
    def post(self):
        """Add a new folder"""
        self.require_api_key()
        data = folder_parser.parse_args()
        working_folder_path, working_folder = self._controller._get_folder_context(data)

        if 'name' not in data:
            abort(400, description="Name is required")

        folder = self._model_store.folder().add_folder(
            entity=FolderEntity.CONTENT,
            name=data.get('name'),
            working_folder_path=working_folder_path
        )

        return folder.to_dict(), 201

    @content_ns.expect(path_parser)
    def delete(self):
        """Delete a folder"""
        self.require_api_key()
        data = path_parser.parse_args()
        working_folder_path, working_folder = self._controller._get_folder_context(data)

        if not working_folder:
            abort(400, description="You can't delete this folder")

        content_counter = self._model_store.content().count_contents_for_folder(working_folder.id)
        folder_counter = self._model_store.folder().count_subfolders_for_folder(working_folder.id)

        if content_counter > 0 or folder_counter:
            raise FolderNotEmptyException()

        self._model_store.folder().delete(id=working_folder.id)
        self._controller._post_update()

        return {'status': 'ok'}, 204

    @content_ns.expect(folder_parser)
    def put(self):
        """Update a folder"""
        self.require_api_key()
        data = folder_parser.parse_args()
        working_folder_path, working_folder = self._controller._get_folder_context(data)

        if 'name' not in data:
            abort(400, description="Name is required")

        if not working_folder:
            abort(400, description="You can't update this folder")

        self._model_store.folder().rename_folder(
            folder_id=working_folder.id,
            name=data.get('name')
        )

        return {'status': 'ok'}
