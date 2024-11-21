from immich import immich
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import yaml
from pathlib import Path
import mimetypes
from pystray import Icon as icon, Menu as menu, MenuItem as item
from PIL import Image


def get_extensions_for_type(general_type):
    mimetypes.init()
    for ext in mimetypes.types_map:
        if mimetypes.types_map[ext].split('/')[0] == general_type:
            yield ext

class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if (not event.is_directory and event.src_path.endswith(tuple(get_extensions_for_type("video")))
                or event.src_path.endswith(tuple(get_extensions_for_type("image"))) or event.src_path.endswith(".webp")):
            print(f"File {event.src_path} has been created!")
            api.created(event.src_path)
    def on_deleted(self, event):
        if (not event.is_directory and event.src_path.endswith(tuple(get_extensions_for_type("video")))
                or event.src_path.endswith(tuple(get_extensions_for_type("image"))) or event.src_path.endswith(".webp")):
            print(f"File {event.src_path} has been deleted!")
            api.delete(event.src_path)
    #   def on_moved(self, event):
    #       if not event.is_directory and event.src_path.endswith(".png") or event.src_path.endswith(".jpg") or event.src_path.endswith(".jpeg"):
    #           print(f"File {event.src_path} has been moved!")
    #           api.move(event.src_path,event.dest_path)
    #  def on_modified(self, event):
    #      if not event.is_directory and event.src_path.endswith(".png") or event.src_path.endswith(".jpg") or event.src_path.endswith(".jpeg"):
    #          print(f"File {event.src_path} has been modified!")
    #          api.modify(event.src_path)

#def on_clicked(icon, item):
#    global sync_toggle_state
#    print("cahnging state")
#    sync_toggle_state = not item.checked
#def startSystemTrayIcon():
#    icon('test', Image.open("C:\\Users\\maxid\\Documents\\GitHub\\Immich Desktop Client\\resources\\icon.ico"), menu=menu(
#        item('Checkable',on_clicked,checked=lambda item: sync_toggle))).run()

# Load Config
config = open(str(Path.home())+'/.immich-desktop-client/config.yaml', 'r')
config = yaml.safe_load(config)

immichHost = config["api"]["url"]
apiKey = config["api"]["key"]
directories_to_watch = config["watchdog"]["directories"]

api = immich(immichHost, apiKey)
api.testConnection()
api.exportShelve()
#sync_toggle = False
#icon('test', Image.open("C:\\Users\\maxid\\Documents\\GitHub\\Immich Desktop Client\\resources\\icon.ico"), menu=menu(
#    item('Checkable',on_clicked,checked=lambda item: sync_toggle))).run()

# Create observer and event handler
observer = Observer()
event_handler = MyHandler()
for directory in directories_to_watch:
    observer.schedule(event_handler, directory, recursive=True)
    print("watching directory: " + directory)
observer.start()

# Keep the script running
state = False

def on_clicked(icon, item):
    global state

    state = not item.checked
    print("change state to: ", state)
# Update the state in `on_clicked` and return the new state in
# a `checked` callable
icon('test',Image.open("C:\\Users\\maxid\\Documents\\GitHub\\Immich Desktop Client\\resources\\icon.ico") , menu=menu(
    item(
        'Sync directories to Immich',
        on_clicked,
        checked=lambda item: state))).run()

observer.join()
