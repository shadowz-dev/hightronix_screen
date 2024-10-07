import json

from flask import Flask, render_template, redirect, request, url_for, jsonify, abort
from src.service.ModelStore import ModelStore
from src.model.entity.NodePlayer import NodePlayer
from src.interface.ObController import ObController
from src.model.enum.OperatingSystem import OperatingSystem
from src.model.enum.FolderEntity import FolderEntity, FOLDER_ROOT_PATH
from src.util.utils import str_to_enum


class FleetNodePlayerController(ObController):

    def guard_fleet(self, f):
        def decorated_function(*args, **kwargs):
            if not self._model_store.variable().map().get('fleet_player_enabled').as_bool():
                return redirect(url_for('manage'))
            return f(*args, **kwargs)

        return decorated_function

    def register(self):
        self._app.add_url_rule('/fleet/node-player', 'fleet_node_player_list', self.guard_fleet(self._auth(self.fleet_node_player_list)), methods=['GET'])
        self._app.add_url_rule('/fleet/node-player/add', 'fleet_node_player_add', self.guard_fleet(self._auth(self.fleet_node_player_add)), methods=['GET', 'POST'])
        self._app.add_url_rule('/fleet/node-player/edit/<node_player_id>', 'fleet_node_player_edit', self._auth(self.fleet_node_player_edit), methods=['GET'])
        self._app.add_url_rule('/fleet/node-player/save/<node_player_id>', 'fleet_node_player_save', self._auth(self.fleet_node_player_save), methods=['POST'])
        self._app.add_url_rule('/fleet/node-player/delete', 'fleet_node_player_delete', self.guard_fleet(self._auth(self.fleet_node_player_delete)), methods=['GET'])
        self._app.add_url_rule('/fleet/node-player/rename', 'fleet_node_player_rename', self.guard_fleet(self._auth(self.fleet_node_player_rename)), methods=['POST'])
        self._app.add_url_rule('/fleet/node-player/cd', 'fleet_node_player_cd', self._auth(self.fleet_node_player_cd), methods=['GET'])
        self._app.add_url_rule('/fleet/node-player/add-folder', 'fleet_node_player_folder_add', self._auth(self.fleet_node_player_folder_add), methods=['POST'])
        self._app.add_url_rule('/fleet/node-player/move-folder', 'fleet_node_player_folder_move', self._auth(self.fleet_node_player_folder_move), methods=['POST'])
        self._app.add_url_rule('/fleet/node-player/rename-folder', 'fleet_node_player_folder_rename', self._auth(self.fleet_node_player_folder_rename), methods=['POST'])
        self._app.add_url_rule('/fleet/node-player/delete-folder', 'fleet_node_player_folder_delete', self._auth(self.fleet_node_player_folder_delete), methods=['GET'])
        self._app.add_url_rule('/fleet/node-player/delete-bulk-explr', 'fleet_node_player_delete_bulk_explr', self._auth(self.fleet_node_player_delete_bulk_explr), methods=['GET'])

    def get_working_folder(self):
        working_folder_path = request.args.get('path', None)
        working_folder = None

        if working_folder_path:
            working_folder = self._model_store.folder().get_one_by_path(path=working_folder_path, entity=FolderEntity.NODE_PLAYER)

        if not working_folder:
            working_folder_path = self._model_store.variable().get_one_by_name('last_folder_node_player').as_string()
            working_folder = self._model_store.folder().get_one_by_path(path=working_folder_path, entity=FolderEntity.NODE_PLAYER)

        return working_folder_path, working_folder

    def fleet_node_player_list(self):
        self._model_store.variable().update_by_name('last_pillmenu_fleet', 'fleet_node_player_list')
        working_folder_path, working_folder = self.get_working_folder()

        return render_template(
            'fleet/node-players/list.jinja.html',
            foldered_node_players=self._model_store.node_player().get_all_indexed('folder_id', multiple=True),
            groups=self._model_store.node_player_group().get_all_labels_indexed(),
            folders_tree=self._model_store.folder().get_folder_tree(FolderEntity.NODE_PLAYER),
            working_folder_path=working_folder_path,
            working_folder=working_folder,
            working_folder_children=self._model_store.folder().get_children(folder=working_folder, entity=FolderEntity.NODE_PLAYER, sort='created_at', ascending=False),
            enum_operating_system=OperatingSystem,
            enum_folder_entity=FolderEntity,
        )

    def fleet_node_player_add(self):
        working_folder_path, working_folder = self.get_working_folder()

        self._model_store.node_player().add_form(
            NodePlayer(
                name=request.form['name'],
                host=request.form['host'],
                operating_system=str_to_enum(request.form['operating_system'], OperatingSystem),
                folder_id=working_folder.id if working_folder else None,
            )
        )

        return redirect(url_for('fleet_node_player_list', path=working_folder_path))

    def fleet_node_player_edit(self, node_player_id: int = 0):
        node_player = self._model_store.node_player().get(node_player_id)

        if not node_player:
            return abort(404)

        working_folder_path, working_folder = self.get_working_folder()

        return render_template(
            'fleet/node-players/edit.jinja.html',
            node_player=node_player,
            working_folder_path=working_folder_path,
            working_folder=working_folder,
            enum_operating_system=OperatingSystem,
        )

    def fleet_node_player_save(self, node_player_id: int = 0):
        node_player_id = request.form['id'] if 'id' in request.form else node_player_id
        node_player = self._model_store.node_player().get(node_player_id)
        working_folder_path, working_folder = self.get_working_folder()

        if not node_player:
            return redirect(url_for('fleet_node_player_list', path=working_folder_path))

        self._model_store.node_player().update_form(
            id=node_player.id,
            name=request.form['name'],
            operating_system=str_to_enum(request.form['operating_system'], OperatingSystem),
            host=request.form['host'],
        )
        self._post_update()

        # return redirect(url_for('fleet_node_player_edit', node_player_id=node_player_id, saved=1))
        return redirect(url_for('fleet_node_player_list', path=working_folder_path))

    def fleet_node_player_delete(self):
        working_folder_path, working_folder = self.get_working_folder()
        error_tuple = self.delete_node_player_by_id(request.args.get('id'))
        route_args = {
            "path": working_folder_path,
        }

        if error_tuple:
            route_args[error_tuple[0]] = error_tuple[1]

        return redirect(url_for('fleet_node_player_list', **route_args))

    def fleet_node_player_rename(self):
        working_folder_path, working_folder = self.get_working_folder()
        self._model_store.node_player().update_form(
            id=request.form['id'],
            name=request.form['name'],
        )

        return redirect(url_for('fleet_node_player_list', path=working_folder_path))

    def fleet_node_player_cd(self):
        path = request.args.get('path')

        if path == FOLDER_ROOT_PATH:
            self._model_store.variable().update_by_name("last_folder_node_player", FOLDER_ROOT_PATH)
            return redirect(url_for('fleet_node_player_list', path=FOLDER_ROOT_PATH))

        if not path:
            return abort(404)

        cd_folder = self._model_store.folder().get_one_by_path(
            path=path,
            entity=FolderEntity.NODE_PLAYER
        )

        if not cd_folder:
            return abort(404)

        self._model_store.variable().update_by_name("last_folder_node_player", path)

        return redirect(url_for('fleet_node_player_list', path=path))

    def fleet_node_player_folder_add(self):
        working_folder_path, working_folder = self.get_working_folder()

        self._model_store.folder().add_folder(
            entity=FolderEntity.NODE_PLAYER,
            name=request.form['name'],
            working_folder_path=working_folder_path
        )

        return redirect(url_for('fleet_node_player_list', path=working_folder_path))

    def fleet_node_player_folder_rename(self):
        working_folder_path, working_folder = self.get_working_folder()

        self._model_store.folder().rename_folder(
            folder_id=request.form['id'],
            name=request.form['name'],
        )

        return redirect(url_for('fleet_node_player_list', path=working_folder_path))

    def fleet_node_player_folder_move(self):
        working_folder_path, working_folder = self.get_working_folder()
        entity_ids = request.form['entity_ids'].split(',')
        folder_ids = request.form['folder_ids'].split(',')

        for id in entity_ids:
            self._model_store.folder().move_to_folder(
                entity_id=id,
                folder_id=request.form['new_folder_id'],
                entity_is_folder=False,
                entity=FolderEntity.NODE_PLAYER
            )

        for id in folder_ids:
            self._model_store.folder().move_to_folder(
                entity_id=id,
                folder_id=request.form['new_folder_id'],
                entity_is_folder=True,
                entity=FolderEntity.NODE_PLAYER
            )

        return redirect(url_for('fleet_node_player_list', path=working_folder_path))

    def fleet_node_player_folder_delete(self):
        working_folder_path, working_folder = self.get_working_folder()
        error_tuple = self.delete_folder_by_id(request.args.get('id'))
        route_args = {
            "path": working_folder_path,
        }

        if error_tuple:
            route_args[error_tuple[0]] = error_tuple[1]

        return redirect(url_for('fleet_node_player_list', **route_args))

    def fleet_node_player_delete_bulk_explr(self):
        working_folder_path, working_folder = self.get_working_folder()
        entity_ids = request.args.get('entity_ids', '').split(',')
        folder_ids = request.args.get('folder_ids', '').split(',')
        route_args_dict = {"path": working_folder_path}

        for id in entity_ids:
            if id:
                error_tuple = self.delete_node_player_by_id(id)

                if error_tuple:
                    route_args_dict[error_tuple[0]] = error_tuple[1]

        for id in folder_ids:
            if id:
                error_tuple = self.delete_folder_by_id(id)

                if error_tuple:
                    route_args_dict[error_tuple[0]] = error_tuple[1]

        return redirect(url_for('fleet_node_player_list', **route_args_dict))

    def delete_node_player_by_id(self, id):
        node_player = self._model_store.node_player().get(id)

        if not node_player:
            return None

        self._model_store.node_player().delete(node_player.id)
        self._post_update()
        return None

    def delete_folder_by_id(self, id):
        folder = self._model_store.folder().get(id)

        if not folder:
            return None

        node_player_counter = self._model_store.node_player().count_node_players_for_folder(folder.id)
        folder_counter = self._model_store.folder().count_subfolders_for_folder(folder.id)

        if node_player_counter > 0 or folder_counter:
            return 'folder_not_empty_error', folder.name

        self._model_store.folder().delete(id=folder.id)

        return None

    def _post_update(self):
        pass
