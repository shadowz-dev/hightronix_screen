import os
import psutil
import platform
import logging
import os

from typing import Dict, Optional, List, Tuple, Union

from src.model.entity.ExternalStorage import ExternalStorage


def list_usb_storage_devices() -> List[ExternalStorage]:
    os_type = platform.system()
    partitions = psutil.disk_partitions()
    removable_devices = []
    for partition in partitions:
        if 'dontbrowse' in partition.opts:
            continue

        if os_type == "Windows":
            if 'removable' in partition.opts:
                removable_devices.append(partition)
        else:
            if '/media' in partition.mountpoint or '/run/media' in partition.mountpoint or '/mnt' in partition.mountpoint or '/Volumes' in partition.mountpoint:
                removable_devices.append(partition)

    if not removable_devices:
        return {}

    storages = []

    for device in removable_devices:
        try:
            usage = psutil.disk_usage(device.mountpoint)
            # total_size = usage.total / (1024 ** 3)
            external_storage = ExternalStorage(
                logical_name=device.device,
                mount_point=device.mountpoint,
                content_id=None,
                total_size=usage.total,
            )
            storages.append(external_storage)
        except Exception as e:
            logging.error(f"Could not retrieve size for device {device.device}: {e}")

    return storages


def get_external_storage_devices():
    return {storage.mount_point: "{} ({} - {}GB)".format(
        storage.mount_point,
        storage.logical_name,
        storage.total_size_in_gigabytes()
    ) for storage in ExternalStorageServer.list_usb_storage_devices()}
