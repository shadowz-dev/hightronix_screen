from typing import Optional
from flask import Flask, send_file, render_template_string, jsonify, request

from src.interface.ObController import ObController
from src.util.UtilChromecast import fetch_friendly_names, cast_url


class CoreController(ObController):

    def register(self):
        self._app.add_url_rule('/manifest.json', 'manifest', self.manifest, methods=['GET'])
        self._app.add_url_rule('/favicon.ico', 'favicon', self.favicon, methods=['GET'])
        self._app.add_url_rule('/cast-scan', 'cast_scan', self.cast_scan, methods=['GET'])
        self._app.add_url_rule('/cast-url', 'cast_url', self.cast_url, methods=['POST'])

    def manifest(self):
        with open("{}/manifest.jinja.json".format(self.get_template_dir()), 'r') as file:
            template_content = file.read()

        rendered_content = render_template_string(template_content)

        return self._app.response_class(rendered_content, mimetype='application/json')

    def favicon(self):
        return send_file("{}/favicon.ico".format(self.get_web_dir()), mimetype='image/x-icon')

    def cast_scan(self):
        return jsonify({
            'devices': fetch_friendly_names(discovery_timeout=5)
        })

    def cast_url(self):
        data = request.get_json()
        success = cast_url(friendly_name=data.get('device'), url=data.get('url'), discovery_timeout=5)

        return jsonify({
            'success': success
        })
