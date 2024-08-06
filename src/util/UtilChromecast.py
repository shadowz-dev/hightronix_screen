# import time
# import pychromecast
# import zeroconf
# import logging
#
# from pychromecast.discovery import stop_discovery
# from pychromecast import CastBrowser, SimpleCastListener, get_chromecast_from_host, Chromecast
# from pychromecast.controllers import BaseController
# from typing import Optional
#
#
# APPLICATION_ID = '81585E3E'
#
#
# class CastController(BaseController):
#     def __init__(self):
#         super(CastController, self).__init__("urn:x-cast:com.jrk.obscreen")
#
#     def load_url(self, url: str):
#         self.send_message({
#             'url': url,
#             'type': 'load'
#         })
#
#
# def _discover(discovery_timeout: int = 5):
#     zconf = zeroconf.Zeroconf()
#     browser = pychromecast.CastBrowser(pychromecast.SimpleCastListener(), zconf)
#     browser.start_discovery()
#     time.sleep(discovery_timeout)
#     stop_discovery(browser)
#
#     return browser
#
#
# def fetch_friendly_names(discovery_timeout: int = 5):
#     return [{"friendly_name": cast_info.friendly_name} for device, cast_info in _discover(discovery_timeout).devices.items()]
#
#
# def fetch_chromecast(friendly_name: str, discovery_timeout: int = 5) -> Optional[Chromecast]:
#     for uuid, cast_info in _discover(discovery_timeout).devices.items():
#         if cast_info.friendly_name == friendly_name:
#             try:
#                 return get_chromecast_from_host((cast_info.host, cast_info.port, uuid, cast_info.model_name, cast_info.friendly_name))
#             except:
#                 pass
#
#     logging.info("No chromecast found for friendly_name {}".format(friendly_name))
#     return None
#
#
# def cast_url(friendly_name: str, url: str, discovery_timeout: int = 5) -> bool:
#     chromecast = fetch_chromecast(friendly_name, discovery_timeout)
#
#     if not chromecast:
#         logging.info("Can't instantiate Chromecast {}".format(friendly_name))
#         return False
#
#     chromecast.wait()
#     chromecast.quit_app()
#     time.sleep(2)
#
#     cast_controller = CastController()
#     chromecast.register_handler(cast_controller)
#     chromecast.start_app(APPLICATION_ID)
#     time.sleep(2)
#     cast_controller.load_url(url)
#
#     return True
