import sys
import logging
import signal
import threading

from src.service.ModelStore import ModelStore
from src.service.PluginStore import PluginStore
from src.service.TemplateRenderer import TemplateRenderer
from src.service.WebServer import WebServer
from src.model.enum.HookType import HookType


class Application:

    def __init__(self, application_dir: str):
        self._application_dir = application_dir
        self._stop_event = threading.Event()
        self._model_store = ModelStore(self, self.get_plugins)
        self._template_renderer = TemplateRenderer(kernel=self, model_store=self._model_store, render_hook=self.render_hook)
        self._web_server = WebServer(kernel=self, model_store=self._model_store, template_renderer=self._template_renderer)

        logging.info("[{}] Starting application v{}...".format(self.get_name(), self.get_version()))
        self._plugin_store = PluginStore(kernel=self, model_store=self._model_store, template_renderer=self._template_renderer, web_server=self._web_server)
        signal.signal(signal.SIGINT, self.signal_handler)

    def start(self) -> None:
        variable = self._model_store.variable().get_one_by_name('start_counter')

        if variable:
            self._model_store.variable().update_by_name(variable.name, variable.as_int() + 1)

        self._web_server.run()

    def signal_handler(self, signal, frame) -> None:
        logging.info("[{}] Shutting down...".format(self.get_name()))
        self._model_store.database().close()
        self._stop_event.set()
        sys.exit(0)

    def get_application_dir(self) -> str:
        return self._application_dir

    def render_hook(self, hook: HookType) -> str:
        return self._template_renderer.render_hooks(self._plugin_store.map_hooks()[hook])

    def get_plugins(self):
        return self._plugin_store.map_plugins()

    @staticmethod
    def get_name() -> str:
        return 'Hightronix Screen-studio'

    @staticmethod
    def get_version() -> str:
        with open("version.txt", 'r') as file:
            return file.read().strip()

    def reload_lang(self, lang: str) -> None:
        self._model_store.lang().set_lang(lang)
        self._model_store.variable().reload()
        self._plugin_store.reload_lang()
