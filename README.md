# Immich Desktop Client

![The Immich Logo behind a monitor](resources%2Ficon.png "Icon of the Immich Desktop Client Application")

The **Immich Desktop Client** is an open-source application designed to integrate seamlessly with the Immich self-hosted media management platform. This client simplifies the process of uploading and managing media files directly from your desktop to your Immich server.

## Features

- **Automated Media Upload**: Scans specified directories for media files and uploads new or modified files to your Immich server
- **Uploads to Album**: Automatically creates an album and puts all the images in it
- **Local Shelve Storage**: Tracks uploaded files using local shelve storage to avoid duplicate uploads and facilitate file management
- **Checksum Validation**: Ensures data integrity with SHA-1 checksum verification during uploads.
- **Cross-Platform**: _should_ be compatible with Windows, macOS, and Linux (only tested on Windows 11)

## Prerequisites

- Immich server instance
- API key for your Immich server (accessible from the Immich web interface)

## Installation

### Windows
        
1. Install with the Installer executable
2. modify the config file in the .immich-desktop-client folder in your home directory
3. enjoy

### Other Platforms
    
theoretically the python script is cross platform, therefore it should be executable on macOS and Linux

## Roadmap

- Add support for replacing assets instead of duplicating versions.
- Enable file deletion from the Immich server through the client.
- Put files from different folders in different albums
