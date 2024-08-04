from flask import request, abort, jsonify
from flask_restx import Resource, Namespace, fields
from src.model.entity.Content import Content
from src.manager.FolderManager import FolderManager
from src.model.enum.ContentType import ContentType
from src.model.enum.FolderEntity import FolderEntity, FOLDER_ROOT_PATH
from src.interface.ObController import ObController
from src.util.utils import str_to_enum
from plugins.system.CoreApi.exception.ContentPathMissingException import ContentPathMissingException
from plugins.system.CoreApi.exception.ContentNotFoundException import ContentNotFoundException
from plugins.system.CoreApi.exception.FolderNotFoundException import FolderNotFoundException
from plugins.system.CoreApi.exception.FolderNotEmptyException import FolderNotEmptyException


# Namespace for content operations
content_ns = Namespace('content', description='Operations related to content management')

# Input model for adding/updating content
content_model = content_ns.model('Content', {
    'name': fields.String(required=True, description='Name of the content'),
    'type': fields.String(required=True, description='Type of the content'),
    'location': fields.String(description='Location of the content (optional)'),
    'path': fields.String(description='Path of the folder')
})

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
    'path': fields.String(description='Path of the folder')
})

# Model for bulk operations
bulk_move_model = content_ns.model('BulkMove', {
    'entity_ids': fields.List(fields.Integer, required=True, description='List of content IDs to move'),
    'path': fields.String(description='Path of the folder')
})


class ContentApiController(ObController):

    def register(self):
# -        self._app.add_url_rule('/api/content', 'api_content_list', self.list_content, methods=['GET'])
# -        self._app.add_url_rule('/api/content', 'api_content_add', self.add_content, methods=['POST'])
# -        self._app.add_url_rule('/api/content/<int:content_id>', 'api_content_get', self.get_content, methods=['GET'])
# -        self._app.add_url_rule('/api/content/<int:content_id>', 'api_content_update', self.update_content, methods=['PUT'])
# -        self._app.add_url_rule('/api/content/<int:content_id>', 'api_content_delete', self.delete_content, methods=['DELETE'])
# -        self._app.add_url_rule('/api/content/location/<int:content_id>', 'api_content_location', self.location_content, methods=['GET'])
# -        self._app.add_url_rule('/api/content/upload-bulk', 'api_content_upload_bulk', self.upload_bulk_content, methods=['POST'])
# -        self._app.add_url_rule('/api/content/folder/move-bulk', 'api_folder_content_bulk_move', self.move_bulk_content_folder, methods=['POST'])
# -        self._app.add_url_rule('/api/content/folder', 'api_folder_add', self.add_folder, methods=['POST'])
# -        self._app.add_url_rule('/api/content/folder', 'api_folder_delete', self.delete_folder, methods=['DELETE'])
# -        self._app.add_url_rule('/api/content/folder', 'api_folder_update', self.update_folder, methods=['PUT'])
        self.api().add_namespace(content_ns, path='/api/content')
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
            '_controller': self
        })

    def get_request_data(self):
        data = {}

        try:
            if 'multipart/form-data' in request.headers.get('Content-Type'):
                data = request.form
            else:
                data = request.get_json()
        except:
            pass

        return data

    def get_folder_context(self):
        data = self.get_request_data()
        path = data.get('path')
        path = "{}/{}".format(FOLDER_ROOT_PATH, path.strip('/')) if path and not path.startswith(FOLDER_ROOT_PATH) else path

        if 'folder_id' in data:
            folder = self._model_store.folder().get(id=data.get('folder_id'))
            return path, folder

        if 'path' not in data:
            raise ContentPathMissingException()

        folder = self._model_store.folder().get_one_by_path(path=path, entity=FolderEntity.CONTENT)
        is_root_drive = FolderManager.is_root_drive(path)

        if not folder and not is_root_drive:
            raise FolderNotFoundException()

        return FOLDER_ROOT_PATH if is_root_drive else path, folder


class ContentListResource(Resource):

    @content_ns.marshal_list_with(content_output_model)
    def get(self):
        """List all contents"""
        data = self._controller.get_request_data()
        working_folder_path = None
        working_folder = None
        folder_id = None

        try:
            working_folder_path, working_folder = self._controller.get_folder_context()
            folder_id = data.get('folder_id', 0 if not working_folder else working_folder.id)
        except ContentPathMissingException:
            pass

        contents = self._model_store.content().get_contents(
            folder_id=folder_id,
            slide_id=data.get('slide_id', None),
        )
        result = [content.to_dict() for content in contents]

        return {
            'contents': result,
            'working_folder_path': working_folder_path,
            'working_folder': working_folder.to_dict() if working_folder else None
        }

    @content_ns.expect(content_model)
    @content_ns.marshal_with(content_output_model, code=201)
    def post(self):
        """Add new content"""
        data = self._controller.get_request_data()
        working_folder_path, working_folder = self._controller.get_folder_context()

        if 'name' not in data:
            abort(400, description="Name is required")

        if 'type' not in data:
            abort(400, description="Type is required")

        if data.get('type') not in {type.value for type in ContentType}:
            abort(400, description="Invalid type")

        content_type = str_to_enum(data.get('type'), ContentType)
        location = data.get('location', None)

        content = self._model_store.content().add_form_raw(
            name=data.get('name'),
            type=content_type,
            request_files=request.files,
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
        content = self._model_store.content().get(content_id)
        if not content:
            raise ContentNotFoundException()

        return content.to_dict()

    @content_ns.expect(content_model)
    @content_ns.marshal_with(content_output_model)
    def put(self, content_id: int):
        """Update existing content"""
        data = self._controller.get_request_data()
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
        content = self._model_store.content().get(content_id)

        if not content:
            raise ContentNotFoundException()

        content_location = self._model_store.content().resolve_content_location(content)

        return {'location': content_location}


class ContentBulkUploadResource(Resource):

    def post(self):
        """Upload multiple content files"""
        working_folder_path, working_folder = self._controller.get_folder_context()

        for key in request.files:
            files = request.files.getlist(key)
            for file in files:
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

    @content_ns.expect(bulk_move_model)
    def post(self):
        """Move multiple content to another folder"""
        data = self._controller.get_request_data()
        working_folder_path, working_folder = self._controller.get_folder_context()

        if 'entity_ids' not in data:
            abort(400, description="Content IDs are required under 'entity_ids' field")

        entity_ids = data.get('entity_ids')

        for entity_id in entity_ids:
            self._model_store.folder().move_to_folder(
                entity_id=entity_id,
                folder_id=working_folder if working_folder else None,
                entity_is_folder=False,
                entity=FolderEntity.CONTENT
            )

        return {'status': 'ok'}


class FolderResource(Resource):

    @content_ns.expect(folder_model)
    @content_ns.marshal_with(folder_model, code=201)
    def post(self):
        """Add a new folder"""
        data = self._controller.get_request_data()
        working_folder_path, working_folder = self._controller.get_folder_context()

        if 'name' not in data:
            abort(400, description="Name is required")

        folder = self._model_store.folder().add_folder(
            entity=FolderEntity.CONTENT,
            name=data.get('name'),
            working_folder_path=working_folder_path
        )

        return folder.to_dict(), 201

    def delete(self):
        """Delete a folder"""
        working_folder_path, working_folder = self._controller.get_folder_context()

        if not working_folder:
            abort(400, description="You can't delete this folder")

        content_counter = self._model_store.content().count_contents_for_folder(working_folder.id)
        folder_counter = self._model_store.folder().count_subfolders_for_folder(working_folder.id)

        if content_counter > 0 or folder_counter:
            raise FolderNotEmptyException()

        self._model_store.folder().delete(id=working_folder.id)
        self._controller._post_update()

        return {'status': 'ok'}, 204

    @content_ns.expect(folder_model)
    def put(self):
        """Update a folder"""
        data = self._controller.get_request_data()
        working_folder_path, working_folder = self._controller.get_folder_context()

        if 'name' not in data:
            abort(400, description="Name is required")

        if not working_folder:
            abort(400, description="You can't update this folder")

        self._model_store.folder().rename_folder(
            folder_id=working_folder.id,
            name=data.get('name')
        )

        return {'status': 'ok'}

