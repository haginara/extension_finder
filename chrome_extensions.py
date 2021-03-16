# -*- coding: utf-8 -*-
"""
chrome_extensions.py
@brad_anton
@jonghak Choi

Constant variables.

Path names are prefexed by HOMEDIR unless starting 
with a slash

"""

import logging
import sys
import io
import os
import argparse
import platform
import csv
import json

logging.basicConfig(level=logging.WARNING, format="%(asctime)-15s | %(levelname)s | %(message)s")

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


def get_users():
    users = []
    if operating_system == 'Darwin':
        for user in os.listdir('/Users'):
            if user.startswith('.') or user == 'Shared':
                continue
            users.append(os.path.join('/Users', user))
    
    return users


def _check_preferences_json(user_path):
    preferences = os.path.join(user_path, Browser.CHROME_EXTENSIONS_PREFS)
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


def _check_app_directory(user_path):
    app_directory = os.path.join(user_path, Browser.CHROME_EXTENSIONS)
    if not os.path.exists(app_directory):
        logging.error("[-] No Chrome app directory found")
        return

    extensions = []
    for root, dirs, files in os.walk(app_directory):
        for f in files:
            if f == 'manifest.json':
                manifest_path = os.path.join(root, f)
                try:
                    name, version, extension_id = _process_manifest_json(manifest_path)
                except Exception as e:
                    logging.error(e)
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
                    'name': "N/A" if name is None else unicode(name).encode("utf-8"),
                    'version': version,
                    'id': extension_id,
                    'manifest_path': "N/A" if manifest_path is None else unicode(manifest_path).encode("utf-8"),
                })
    return extensions


def find_extensions(options):
    logging.info("[+] Find Chrome extensions")
    if not os.path.exists(Browser.CHROME):
        raise Exception("Could not find chrome extensions")
    
    results = []
    users = get_users()
    for user in users:
        try:
            logging.info("[+] Check Chrome preferences")
            result = _check_preferences_json(user)
        except Exception:
            logging.error('[-] Could not parse the Chrome preferences JSON')
            result = _check_app_directory(user)
        if result is None:
            result = []
        results.extend(result)
    with open(options.out, mode='w') as f:
        if options.format == 'json':
            result_raw = json.dumps(results, sort_keys=True, indent=2)
            f.write(result_raw)
        else:
            writer = csv.DictWriter(f, delimiter='|', fieldnames=['name', 'id', 'version', 'manifest_path'])
            writer.writeheader()
            for row in results:
                writer.writerow(row)
    with open(options.out, 'r') as f:
        print(f.read())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f' ,'--format', default='csv')
    parser.add_argument('-o', '--out', default='chrome_extensions.out')

    options = parser.parse_args()
    try:
        find_extensions(options)
    except Exception as e:
        raise SystemExit(e)
