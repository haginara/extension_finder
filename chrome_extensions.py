"""
chrome_extensions.py
@brad_anton
@jonghak Choi

Constant variables.

Path names are prefexed by HOMEDIR unless starting 
with a slash

"""

import os
import platform
import json

from tabulate import tabulate


class MacBrowsers(object):
    SLASH = '/'
    CHROME = '/Applications/Google Chrome.app'
    CHROME_NAME = 'Chrome - MacOSX'
    CHROME_EXTENSIONS = 'Library/Application Support/Google/Chrome/Default/Extensions'
    CHROME_EXTENSIONS_PREFS = 'Library/Application Support/Google/Chrome/Default/Preferences'

    SAFARI = '/Applications/Safari.app'
    IE = None

class WinBrowsers(object):
    SLASH = '\\'
    CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    CHROME_NAME = 'Chrome - Windows'
    CHROME_EXTENSIONS = r'AppData\Local\Google\Chrome\User Data\Default\Extensions'
    CHROME_EXTENSIONS_PREFS = r'AppData\Local\Google\Chrome\User Data\Default\Preferences'
    

operating_system = platform.system()
Browser = None
if operating_system == 'Darwin':
    Browser = MacBrowsers
elif operating_system == 'Windows':
    Browser = WinBrowsers
else:
    raise Exception("[!] Unsupported Operating System!!")


def _check_preferences_json():
    preferences = os.path.join(os.path.expanduser('~'), Browser.CHROME_EXTENSIONS_PREFS)
    if not os.path.exists(preferences):
        raise Exception("No Chrome preference found")
    extensions = []
    with open(preferences, 'rb') as f:
        prefs_json = json.load(f)

        extensions_json = prefs_json.get('extensions', {'settings': []}).get('settings')
        for extension in extensions_json.iterkeys():
            extensions.append(extension)

    return extensions

def _process_manifest_json(manifest_path):
    extension_id = manifest_path.split(os.sep)[-3]
    with open(manifest_path, 'rb') as f:
        manifest = json.load(f)
    
    name = manifest.get('name')
    version = manifest.get('version')
    return name, version, extension_id


def _check_app_directory():
    app_directory = os.path.join(os.path.expanduser('~'), Browser.CHROME_EXTENSIONS)
    if not os.path.exists(app_directory):
        raise Exception("No Chrome app directory found")

    extensions = []
    for root, dirs, files in os.walk(app_directory):
        for f in files:
            if f == 'manifest.json':
                manifest = os.path.join(root, f)
                try:
                    name, version, extension_id = _process_manifest_json(manifest)
                except Exception as e:
                    print(e)
                    raise e
                if name[0] == '_':
                    locale_paths = [
                        os.path.join('_locales', 'en_US', 'messages.json'),
                        os.path.join('_locales', 'en', 'messages.json')
                    ]
                    for locale_path in locale_paths:
                        locale_json = os.path.join(root, locale_path)
                        if os.path.isfile(locale_json):
                            with open(locale_json, 'rb') as f:
                                locale_manifest = json.load(f)
                                name = locale_manifest.get('appName', {'message': None}).get('message')
                                if name is None:
                                    name = locale_manifest.get('extName', {'message': None}).get('message')
                                if name is None:
                                    name = locale_manifest.get('app_name', {'message': None}).get('message')
                extensions.append({
                    'name': name,
                    'version': version,
                    'path': None,
                    'id': extension_id,
                })
    return extensions
                                

def find_extensions():
    print("[+] Find Chrome extensions")
    if not os.path.exists(Browser.CHROME):
        raise Exception("Could not find chrome extensions")

    try:
        print("[+] Check Chrome preferences")
        result = _check_preferences_json()
    except Exception:
        print('[-] Could not parse the Chrome preferences JSON')
        result = _check_app_directory()
    
    print(tabulate(result, headers='keys'))

if __name__ == '__main__':
    try:
        find_extensions()
    except Exception as e:
        raise SystemExit(e)