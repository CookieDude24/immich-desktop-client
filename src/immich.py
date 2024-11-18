import hashlib
import json
import os.path
import shelve
import socket
import subprocess
from datetime import datetime
from pathlib import Path
import requests


class immich:
    def __init__(self, immichHost, apiKey, album_name=None, album_id=None, device_id=None, shelve_path=None):
        self.__immichHost = immichHost
        self.__apiKey = apiKey

        if shelve_path is None:
            self.__shelve_path = str(Path.home()) + "/.immich-desktop-client/shelve"
        else:
            self.__shelve_path = shelve_path

        if device_id is None:
            self.__uuid = self.getUuid()
        else:
            self.__uuid = device_id

        if album_name is None:
            self.album_name = socket.gethostname()
        else:
            self.album_name = album_name

        if album_id is None:
            self.__album_id = self.__getAlbumId()
        else:
            self.__album_id = album_id

    def getUuid(self):
        return str(subprocess.check_output('wmic csproduct get uuid')).split('\\r\\n')[1].strip('\\r').strip()

    def testConnection(self):
        global response

        headers = {
            'Accept': 'application/json',
            'x-api-key': self.__apiKey
        }

        try:
            response = requests.request("POST", self.__immichHost + "/auth/validateToken", headers=headers)
            print(response.json())
        except requests.exceptions.RequestException as e:
            print(e)

        return response.status_code

    def created(self, file):
        stats = os.stat(file)

        headers = {
            'Accept': 'application/json',
            'x-api-key': self.__apiKey,
            'x-immich-checksum': self.__get_sha1(file)
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
            self.__saveImageToShelve(image_id['id'], file)
            self.__add_asset_to_album(image_id['id'])
            print("saved image successfully: " + str(response.text))

    def modify(self, file):
        try:
            assetId = self.__getImageId(file)
        except KeyError:
            print("trying to modify non-uploaded file ... uploading file")
            self.created(file)
        else:
            files = [
                ('assetData', ('file', open(file, 'rb'), 'application/octet-stream'))
            ]
            headers = {
                'Content-Type': 'multipart/form-data',
                'Accept': 'application/json',
                'x-api-key': self.__apiKey
            }
            try:
                response = requests.request("PUT", self.__immichHost + f"/assets/{assetId}/original", headers=headers,
                                            files=files)
            except Exception as e:
                print("error when replacing file" + e.__str__())
            else:
                print(response.text)

    def delete(self, file):
        try:
            self.__deleteImageFromShelve(file)
        except KeyError:
            print("trying to delete non-uploaded file")

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
    #            self.__deleteImageFromShelve(file)
    def move(self, source, destination):
        assetId = self.__getImageId(source)
        self.__deleteImageFromShelve(source)
        self.__saveImageToShelve(assetId, destination)

    def __createAlbum(self):
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
        return json.loads(response.text)['id']

    def __getAlbumId(self):
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.__apiKey
        }

        response = requests.request("GET", self.__immichHost + "/albums", headers=headers)
        response = json.loads(response.text)

        id = None
        for album in response:
            if album['albumName'] == self.album_name:
                id = album['id']
        if id is None:
            print("no album found ... creating new one")
            id = self.__createAlbum()

        return id

    def __add_asset_to_album(self, id):
        payload = json.dumps({
            "ids": [
                str(id)
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

    def __saveImageToShelve(self, id, file):
        images = shelve.open(self.__shelve_path, flag='c', writeback=True)
        images[file] = id

        print("added to shelve: " + str(images[file]))

        images.close()

    def __getImageId(self, file):
        images = shelve.open(self.__shelve_path, flag='r')
        imageId = images[file]

        images.close()

        return imageId

    def __deleteImageFromShelve(self, file):
        images = shelve.open(self.__shelve_path, flag='c', writeback=True)
        del images[file]

        images.close()

    def exportShelve(self):
        db = shelve.open(self.__shelve_path, flag='r')
        data = db.keys()

        print("Start of stored data")
        for key in data:
            print(key, db[key])
        print("End of stored data")

    def __get_sha1(self, file: str):
        with open(file, 'rb', buffering=0) as f:
            return hashlib.file_digest(f, 'sha1').hexdigest()
