import json

from flask import Flask, render_template, redirect, request, url_for, jsonify
from flask_login import login_user, logout_user, current_user
from src.service.ModelStore import ModelStore
from src.model.entity.User import User
from src.interface.ObController import ObController
from typing import Optional
import logging 
from datetime import datetime

logging.basicConfig(filename='user_activity.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
class AuthController(ObController):

    def guard_auth(self, f):
        def decorated_function(*args, **kwargs):
            if not self._model_store.variable().map().get('auth_enabled').as_bool():
                return redirect(url_for('manage'))
            return f(*args, **kwargs)

        return decorated_function

    def register(self):
        self._app.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        self._app.add_url_rule('/logout', 'logout', self.logout, methods=['GET'])
        self._app.add_url_rule('/auth/user/list', 'auth_user_list', self.guard_auth(self._auth(self.auth_user_list)), methods=['GET'])
        self._app.add_url_rule('/auth/user/add', 'auth_user_add', self.guard_auth(self._auth(self.auth_user_add)), methods=['POST'])
        self._app.add_url_rule('/auth/user/edit', 'auth_user_edit', self.guard_auth(self._auth(self.auth_user_edit)), methods=['POST'])
        self._app.add_url_rule('/auth/user/delete/<user_id>', 'auth_user_delete', self.guard_auth(self._auth(self.auth_user_delete)), methods=['GET'])

    def login(self):
        login_error = None

        if current_user.is_authenticated:
            return redirect(url_for('playlist'))

        if not self._model_store.variable().map().get('auth_enabled').as_bool():
            return redirect(url_for('playlist'))

        if len(request.form):
            user = self._model_store.user().get_one_by_username(request.form['username'], enabled=True)
            if user:
                if user.password == self._model_store.user().encode_password(request.form['password']):
                    login_user(user)
                    logging.info(f"User {user.username} logged in successfully.")
                    return redirect(url_for('playlist'))
                else:
                    login_error = 'bad_credentials'
                    logging.warning(f"Failed login attempt for user {request.form['username']} - Incorrect password.")
            else:
                login_error = 'not_found'
                logging.warning(f"Failed login attempt - User {request.form['username']} not found.")

        return render_template(
            'auth/login.jinja.html',
            login_error=login_error,
            last_username=request.form['username'] if 'username' in request.form else None
        )

    def logout(self):
        logout_user()

        if request.args.get('restart'):
            return redirect(url_for(
                'sysinfo_restart',
                secret_key=self._model_store.config().map().get('secret_key')
            ))

        return redirect(url_for('login'))

    def auth_user_list(self):
        demo = self._model_store.config().map().get('demo')

        return render_template(
            'auth/list.jinja.html',
            error=request.args.get('error', None),
            users=self._model_store.user().get_users(exclude=User.DEFAULT_USER if demo else None),
            plugin_core_api_enabled=self._model_store.variable().map().get('plugin_core_api_enabled').as_bool()
        )

    def auth_user_add(self):
        user = User(
            username=request.form['username'],
            password=request.form['password'],
            enabled=True if 'enabled' in request.form and request.form['enabled'] == '1' else False,
        )
        self._model_store.user().add_form(user)
        logging.info(f"User {user.username} added.")
        return redirect(url_for('auth_user_list'))

    def auth_user_edit(self):
        user_id = request.form['id']
        username = request.form['username']
        enabled = True if 'enabled' in request.form and request.form['enabled'] == '1' else False
        password = request.form['password'] if 'password' in request.form and request.form['password'] else None
        
        self._model_store.user().update_form(id=user_id, enabled=enabled, username=username, password=password)
        logging.info(f"User {username} (ID: {user_id}) updated.")
        return redirect(url_for('auth_user_list'))

    def auth_user_delete(self, user_id: Optional[int] = 0):
        user = self._model_store.user().get(user_id)

        if not user:
            logging.warning(f"Attempt to delete non-existent user with ID: {user_id}.")
            return redirect(url_for('auth_user_list'))

        if user.id == str(current_user.id):
            logging.warning(f"User {user.username} (ID: {user_id}) attempted to delete themselves.")
            return redirect(url_for('auth_user_list', error='auth_user_delete_cant_delete_yourself'))

        if self._model_store.user().count_all_enabled() == 1:
            logging.warning(f"Attempt to delete the last enabled user: {user.username} (ID: {user_id}).")
            return redirect(url_for('auth_user_list', error='auth_user_delete_at_least_one_account'))

        self._model_store.user().delete(user_id)
        logging.info(f"User {user.username} (ID: {user_id}) deleted.")
        return redirect(url_for('auth_user_list'))
