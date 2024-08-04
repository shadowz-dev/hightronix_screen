from flask import request, abort, jsonify
from flask_restx import Resource, Namespace, fields
from src.model.entity.Playlist import Playlist
from src.interface.ObController import ObController

# Namespace pour les opérations sur les playlists
playlist_ns = Namespace('playlists', description='Operations on playlist')

# Modèle d'entrée pour la playlist
playlist_model = playlist_ns.model('Playlist', {
    'name': fields.String(required=True, description='The playlist name'),
    'enabled': fields.Boolean(default=True, description='Is the playlist enabled?'),
    'time_sync': fields.Boolean(default=False, description='Is time synchronization enabled?')
})

# Modèle de sortie pour la playlist
playlist_output_model = playlist_ns.model('PlaylistOutput', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a playlist'),
    'name': fields.String(required=True, description='The playlist name'),
    'enabled': fields.Boolean(description='Is the playlist enabled?'),
    'time_sync': fields.Boolean(description='Is time synchronization enabled?')
})


class PlaylistApiController(ObController):

    def register(self):
        self.api().add_namespace(playlist_ns, path='/api/playlists')
        playlist_ns.add_resource(self.create_resource(PlaylistResource), '/<int:playlist_id>')
        playlist_ns.add_resource(self.create_resource(PlaylistListResource), '/')
        playlist_ns.add_resource(self.create_resource(PlaylistSlidesResource), '/<int:playlist_id>/slides')
        playlist_ns.add_resource(self.create_resource(PlaylistNotificationsResource), '/<int:playlist_id>/notifications')

    def create_resource(self, resource_class):
        # Function to inject dependencies into resources
        return type(f'{resource_class.__name__}WithDependencies', (resource_class,), {
            '_model_store': self._model_store
        })


class PlaylistListResource(Resource):
    @playlist_ns.marshal_list_with(playlist_output_model)
    def get(self):
        """List all playlists"""
        playlists = self._model_store.playlist().get_all(sort="created_at", ascending=True)
        result = [playlist.to_dict() for playlist in playlists]
        return result

    @playlist_ns.expect(playlist_model)
    @playlist_ns.marshal_with(playlist_output_model, code=201)
    def post(self):
        """Create a new playlist"""
        data = request.get_json()
        if not data or 'name' not in data:
            abort(400, description="Invalid input")

        playlist = Playlist(
            name=data.get('name'),
            enabled=data.get('enabled', True),
            time_sync=data.get('time_sync', False)
        )

        try:
            playlist = self._model_store.playlist().add_form(playlist)
        except Exception as e:
            abort(409, description=str(e))

        return playlist.to_dict(), 201


class PlaylistResource(Resource):

    @playlist_ns.marshal_with(playlist_output_model)
    def get(self, playlist_id):
        """Get a playlist by its ID"""
        playlist = self._model_store.playlist().get(playlist_id)
        if not playlist:
            abort(404, description="Playlist not found")
        return playlist.to_dict()

    @playlist_ns.expect(playlist_model)
    @playlist_ns.marshal_with(playlist_output_model)
    def put(self, playlist_id):
        """Update an existing playlist"""
        data = request.get_json()

        playlist = self._model_store.playlist().get(playlist_id)
        if not playlist:
            abort(404, description="Playlist not found")

        self._model_store.playlist().update_form(
            id=playlist_id,
            name=data.get('name', playlist.name),
            time_sync=data.get('time_sync', playlist.time_sync),
            enabled=data.get('enabled', playlist.enabled)
        )
        updated_playlist = self._model_store.playlist().get(playlist_id)
        return updated_playlist.to_dict()

    def delete(self, playlist_id):
        """Delete a playlist"""
        playlist = self._model_store.playlist().get(playlist_id)
        if not playlist:
            abort(404, description="Playlist not found")

        if self._model_store.slide().count_slides_for_playlist(playlist_id) > 0:
            abort(400, description="Playlist cannot be deleted because it has slides")

        if self._model_store.node_player_group().count_node_player_groups_for_playlist(playlist_id) > 0:
            abort(400, description="Playlist cannot be deleted because it is associated with node player groups")

        self._model_store.playlist().delete(playlist_id)
        return '', 204


class PlaylistSlidesResource(Resource):

    def get(self, playlist_id):
        """Get slides associated with a playlist"""
        playlist = self._model_store.playlist().get(playlist_id)

        if not playlist:
            abort(404, description="Playlist not found")

        slides = self._model_store.slide().get_slides(is_notification=False, playlist_id=playlist_id)

        result = [slide.to_dict() for slide in slides]
        return jsonify(result)


class PlaylistNotificationsResource(Resource):

    def get(self, playlist_id):
        """Get notifications associated with a playlist"""
        playlist = self._model_store.playlist().get(playlist_id)

        if not playlist:
            abort(404, description="Playlist not found")

        slides = self._model_store.slide().get_slides(is_notification=True, playlist_id=playlist_id)

        result = [slide.to_dict() for slide in slides]
        return jsonify(result)
