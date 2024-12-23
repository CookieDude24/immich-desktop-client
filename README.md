# Immich Desktop Client

<p align="center">
  <img src="resources/icon.png" title="Icon of the Immich Desktop Client Application" alt="The Immich Logo behind a monitor">
</p>

The **Immich Desktop Client** is an open-source application designed to integrate seamlessly with the Immich self-hosted
media management platform. This client simplifies the process of uploading and managing media files directly from your
desktop to your Immich server.

## Features

- **Automated Media Upload**: Scans specified directories for media files and uploads new or modified files to your
  Immich server
- **Uploads to Album**: Automatically creates an album and puts all the images in it
- **Local Shelve Storage**: Tracks uploaded files using local shelve storage and SHA-1 hashes to avoid duplicate uploads
- **Checksum Validation**: Ensures data integrity with SHA-1 checksum verification during uploads
- **Cross-Platform**: _should_ be compatible with Windows, macOS, and Linux (only tested on Windows 11)

## Demo

<a href="resources/Demo-Video.mp4">Here is a short video demonstrating the use of Immich-Desktop-Client!</a>

## Prerequisites

- Immich server instance
- API key for your Immich server (accessible from the Immich web interface)

## Usage

### Installation

#### Windows

1. Install with the Installer executable
2. modify the config file in the .immich-desktop-client folder in your home directory
3. enjoy

#### Other Platforms

theoretically the python script is cross platform, therefore it should be executable on macOS and Linux

## Configuration

> [!NOTE]
> The config file __MUST__ be in the `.immich-desktop-client` folder in your home directory!

### Configuration Fields

#### `api`

- **`key`**: Your Immich API key. This is required to authenticate with the Immich server.
- **`url`**: The base URL of your Immich server API endpoint. _Ensure the URL ends with `/api` and does not have a
  trailing slash._
- **`album`**: (Optional) The name of the album where media files will be uploaded.

#### `watchdog`

- **`directories`**: A list of directories the client will monitor for media files. Files in these directories will be
  automatically uploaded to the Immich server.

### Example Configuration

Below is an example `config.yaml` file:

````yaml
api:
  key: apikey12345
  url: https://immich.domain.test/api
  album: Oida
watchdog:
  directories:
    - C:\Users\test\Images and Videos\
    - C:\Users\test\Screenshots\

````

## Build it yourself

1. run ``pyinstaller -n immich-dsektop-client -F src/main.py``
2. run ``resources\installer-script.iss`` with Inno Setup

## Roadmap

- Add support for replacing assets instead of duplicating versions.
- Enable file deletion from the Immich server through the client.
- Put files from different folders in different albums
