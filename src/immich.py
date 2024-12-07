import dbm
import hashlib
import json
import os.path
import shelve
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from time import sleep

import requests


class Immich:
    def __init__(self, immich_host, api_key, album_name=None, album_id=None, device_id=None, shelve_path=None):
        self.__immichHost = immich_host
        self.__apiKey = api_key

        if shelve_path is None:
            self.__shelve_path = str(Path.home()) + "/.Immich-desktop-client/shelve"
        else:
            self.__shelve_path = shelve_path

        if device_id is None:
            self.__uuid = self.__get_uuid()
        else:
            self.__uuid = device_id

        if album_name is None:
            self.album_name = socket.gethostname()
        else:
            self.album_name = album_name

        if album_id is None:
            self.__album_id = self.__get_album_id()
        else:
            self.__album_id = album_id

    def upload_all_images(self, directories, media_file_extensions):
        try:
            with shelve.open(self.__shelve_path, flag='r') as db:
                print("catch up with files already stored in shelve")
                # TODO fix uploading modified files
                data = db.keys()
                for key in data:
                    if os.path.isfile(key):
                        if self.__get_sha1(key) != db[key][1]:
                            self.created(str(key))
                    else:
                        self.delete(key)

                print("uploading new files")
                matching_files = []
                for directory in directories:
                    for filename in os.listdir(directory):
                        if filename.endswith(media_file_extensions):
                            matching_files.append(os.path.join(directory, filename))

                for file in matching_files:
                    if file not in db:
                        self.created(file)


        except dbm.error:
            print("cant open non-existing shelve")

    def created(self, file):
        try:
            stats = self.__get_file_stats(file)
        except FileNotFoundError:
            print("could not create file")
            return

        headers = {
            'Accept': 'application/json',
            'x-api-key': self.__apiKey,
            'x-Immich-checksum': self.__get_sha1(file)
        }

        data = {
            'deviceAssetId': f"{file}-{stats.st_mtime}",
            'deviceId': self.__uuid,
            'fileCreatedAt': datetime.fromtimestamp(stats.st_mtime),
            'fileModifiedAt': datetime.fromtimestamp(stats.st_mtime),
            'isFavorite': 'false',
        }

        files = {
            'assetData': open(file, 'rb')
        }
        try:
            response = requests.post(self.__immichHost + "/assets", headers=headers, data=data, files=files)
        except Exception as e:
            print(e)
        else:
            image_id = json.loads(response.text)
            print("satus: " + image_id['status'])
            self.__save_image_to_shelve(image_id['id'], file)
            self.__add_asset_to_album(image_id['id'])
            print("saved image successfully: " + str(response.text))

    #    def modify(self, file):
    #                try:
    #                    stats = self.__get_file_stats(file)
    #                except FileNotFoundError:
    #                    print("could not create file")
    #                    return
    #
    #        try:
    #            asset_id = self.__get_image_id(file)
    #        except KeyError:
    #            print("trying to modify non-uploaded file ... uploading file")
    #            self.created(file)
    #        else:
    #            print(file)
    #            data = {
    #                'deviceAssetId': f"{file}-{stats.st_mtime}",
    #                'deviceId': self.__uuid,
    #                'fileCreatedAt': datetime.fromtimestamp(stats.st_mtime),
    #                'fileModifiedAt': datetime.fromtimestamp(stats.st_mtime)
    #            }
    #            files=[
    #                ('assetData',('IMAGE',open(file,'rb'),'application/octet-stream'))
    #            ]
    #            headers = {
    #                'Accept': 'application/json',
    #                'x-api-key': self.__apiKey
    #            }
    #            try:
    #                print(f"{self.__immichHost}/assets/{asset_id}/original")
    #                response = requests.request(method="PUT", url=f"{self.__immichHost}/assets/{asset_id}/original", headers=headers,
    #                                            files=files, data=data)
    #            except Exception as e:
    #                print("error when replacing file" + e.__str__())
    #            else:
    #                if response.status_code == 200:
    #                    self.__save_image_to_shelve(asset_id, file)
    #                else:
    #                    print("error when replacing file")
    #                print(response.text)

    def delete(self, file):
        try:
            self.__delete_image_from_shelve(file)
        except KeyError:
            print("trying to delete non-uploaded file")

    # TODO create Option for deleting images on server too
    #    try:
    #        assetId = self.__getImageId(file)
    #    except KeyError:
    #        print("deleting non-uploaded file")
    #    else:
    #        payload = json.dumps({
    #            "force": True,
    #            "ids": [
    #                assetId
    #            ]
    #        })
    #        headers = {
    #            'Content-Type': 'application/json',
    #            'x-api-key': self.__apiKey
    #        }
    #        try:
    #            response = requests.request("DELETE", self.__immichHost + "/assets", headers=headers, data=payload)
    #        except Exception as e:
    #            print("error when deleting file: "+ e.__str__())
    #            return
    #        else:
    #            print(response.text)
    #            self.__delete_image_from_shelve(file)
    def move(self, source, destination):
        asset_id = self.__get_image_id(source)
        self.__delete_image_from_shelve(source)
        self.__save_image_to_shelve(asset_id, destination)

    def __create_album(self):
        payload = json.dumps({
            "albumName": self.album_name,
            "description": "The Immich Desktop Client puts all images from " + self.album_name + " in this folder",
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': self.__apiKey
        }
        response = requests.request("POST", self.__immichHost + "/albums", headers=headers, data=payload)
        print("Successfully created album " + str(response.json()))
        return json.loads(response.text)['asset_id']

    def __get_album_id(self):
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.__apiKey
        }

        response = requests.request("GET", self.__immichHost + "/albums", headers=headers)
        response = json.loads(response.text)

        album_id = None
        for album in response:
            if album['albumName'] == self.album_name:
                album_id = album['id']
        if album_id is None:
            print("no album found ... creating new one")
            album_id = self.__create_album()

        return album_id

    def __add_asset_to_album(self, asset_id):
        payload = json.dumps({
            "ids": [
                str(asset_id)
            ]
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': self.__apiKey
        }

        response = requests.request("PUT", self.__immichHost + "/albums/" + self.__album_id + "/assets",
                                    headers=headers, data=payload)
        print(response.json())
        print("successfully added asset to album")

    def __save_image_to_shelve(self, asset_id, file):
        with shelve.open(self.__shelve_path, flag='c', writeback=True) as images:
            images[file] = [asset_id, self.__get_sha1(file)]
            print("added to shelve: " + str(file) + str(images[file]))

    def __get_image_id(self, file):
        with shelve.open(self.__shelve_path, flag='r') as images:
            image_id = images[file][0]
            return image_id

    def __delete_image_from_shelve(self, file):
        with shelve.open(self.__shelve_path, flag='c', writeback=True) as images:
            del images[file]

    def export_shelve(self):
        try:
            with shelve.open(self.__shelve_path, flag='r') as db:
                data = db.keys()

                print("Start of stored data")
                for key in data:
                    print(key, db[key])
                print("End of stored data")
        except dbm.error:
            print("cant export non-existing shelve")

    @staticmethod
    def __get_sha1(file: str):
        for i in range(0, 3):
            try:
                with open(file, 'rb', buffering=0) as f:
                    # noinspection PyTypeChecker
                    return hashlib.file_digest(f, 'sha1').hexdigest()
            except Exception as e:
                print(e)
                sleep(0.5)

    @staticmethod
    def __get_file_stats(file: str):
        # when downloading images via the browser sometimes os.stat() fails therefore it retries for 3 times
        for i in range(0, 3):
            try:
                return os.stat(file)
            except FileNotFoundError:
                sleep(0.5)
        else:
            print("Error: could not get file stats since could not find file")
            raise FileNotFoundError

    @staticmethod
    def __get_uuid():
        return str(subprocess.check_output('wmic csproduct get uuid')).split('\\r\\n')[1].strip('\\r').strip()

    def test_connection(self):
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.__apiKey
        }

        try:
            response = requests.request("POST", self.__immichHost + "/auth/validateToken", headers=headers)
            print(response.json())
            return response.status_code
        except requests.exceptions.RequestException as e:
            print(e)
