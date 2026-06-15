import os
import tarfile
import re
import shutil
import tempfile
import hashlib
import math
import yaml
import glob
import subprocess
import sys
from urllib.parse import urlparse
from pathlib import Path
from env import UNPACK_FILE_FILTER
from helpers import print_message, print_choice, WARNING, ERROR, HELPERS_DIR, install_requirements, get_system_based_value
from helpers.core.utils import download_file, retrieve_json, github_url_to_releases_api


def _run_commands(commands, phase, command_kind, scenario_type):
    for raw_command in commands:
        resolved_command = get_system_based_value(raw_command, return_default=True)
        if not resolved_command:
            continue

        try:
            command = (
                resolved_command.split(resolved_command)
                if command_kind == "inline" and isinstance(resolved_command, str)
                else resolved_command
            )
            subprocess.check_call(command, stdout=sys.stdout, stderr=sys.stderr)
        except Exception as exc:
            print_message(
                f"Error during package {scenario_type}ation while executing "
                f"{phase}-{scenario_type}ation {command_kind} '{resolved_command}': {exc}",
                ERROR,
            )
            return False
    return True


def _run_scenario(phase, scenario, module_name, scenario_type):
    if not scenario:
        return True

    print_message(f"Executing {phase}-{scenario_type}ation scenarios for module '{module_name}'...")

    if not _run_commands(scenario.get("scripts", []), phase, "script", scenario_type):
        return False
    if not _run_commands(scenario.get("inline", []), phase, "inline", scenario_type):
        return False

    return True


def format_bytes(size_bytes):
    if size_bytes == 0:
        return "0B"
    units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {units[i]}"

def get_dir_size(path='.'):
    root_directory = Path(path)
    return sum(f.stat().st_size for f in root_directory.rglob('*') if f.is_file())


def get_file_sha256(file: str):
    sha256_hash = hashlib.sha256()
    with open(file, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def install_module(module_name: str, module_link: str, module_version: str = None, link_type: str = 'url', skip_check: bool = False, force: bool = False):
    valid_link_types = {'url', 'file'}
    helper_changelog = ""
    if link_type not in valid_link_types:
        print_message(f"Unrecognized link type '{link_type}'.", ERROR)
        return
    install_dest = Path(f'{HELPERS_DIR}/{module_name}').absolute()
    changelog_path = install_dest / 'CHANGELOG.md'
    if install_dest.exists() and not force:
        print_message(f"Module '{module_name}' already installed.", WARNING, force=True)
        return

    print_message(f"Working with link type '{link_type}'.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        archive_path = Path(tmp_dir) / f'{module_name}.tar.gz'

        if link_type == 'url':
            print_message(f"Downloading module '{module_name}' to '{archive_path}'.")
            github_module_link = github_url_to_releases_api(module_link)
            if github_module_link:
                helper_releases_data = retrieve_json(github_module_link)
                if not isinstance(helper_releases_data, list):
                    print_message(f"Failed to retrieve updates of module '{module_name}'.", WARNING)
                    return
                if not module_version:
                    helper_last_release = helper_releases_data[0]
                else:
                    for release in helper_releases_data:
                        if module_version == release['tag_name']:
                            helper_last_release = release
                            break
                if helper_last_release:
                    helper_remote_download_link = helper_last_release.get('tarball_url')
                    helper_changelog = helper_last_release.get('body')
                    helper_changelog = re.sub('\r\n', '\n', helper_changelog) + '\n'
                    module_link = helper_remote_download_link
                else:
                    print_message('Source not found, aborting.', ERROR)
                    return f"Source for module {module_name} not found."
            else:
                print_message("Link already converted to GitHub API or link not GitHub API (maybe straight link to source), trying to download source.", WARNING)
            download_file(module_link, archive_path)
        else:
            archive_path = module_link

        print_message(f"Unpacking and installing module '{module_name}' to '{install_dest}'.")
        with tarfile.open(archive_path, "r:gz") as tar:
            root_folder = tar.getmembers()[0].name
            matching = [m for m in tar.getmembers() if re.match(UNPACK_FILE_FILTER, m.name)]
            tar.extractall(tmp_dir, members=matching)

        shutil.copytree(Path(tmp_dir) / root_folder, install_dest, dirs_exist_ok=True)
        if not skip_check:
            print_message(f"Checking module`s '{module_name}' SHA256 sum.")
            sha256_file = Path(f"{install_dest}/SHA256").absolute()
            sha256_incorrect = False
            sha256_sums = None
            if sha256_file.exists():
                with open(sha256_file, 'r', encoding='utf-8') as f:
                    sha256_sums = yaml.safe_load(f.read())
                correct_file_list = []
                correct_file_list = [list(sha256_sum.keys())[0] for sha256_sum in sha256_sums]
                current_files = glob.glob(str(install_dest / "*"), recursive=True)
                files_list_prepared = []
                for file in current_files:
                    file_obj= Path(file)
                    file_parent = file_obj.parent.name
                    if file_parent == module_name:
                        file_parent = '.'
                    else:
                        file_parent = f"./{file_parent}"
                    file_name = file_obj.name
                    if file_name in ['SHA256', 'CHANGELOG.md', 'README.md'] or file_obj.is_dir():
                        continue
                    files_list_prepared.append(f"{file_parent}/{file_name}")
                for current_file in files_list_prepared:
                    if current_file not in correct_file_list:
                        sha256_incorrect = True
                for sha256_sum in sha256_sums:
                    sha256_correct_file = list(sha256_sum.keys())[0]
                    sha256_correct_file = install_dest / sha256_correct_file
                    sha256_correct_sum = list(sha256_sum.values())[0]
                    correct_file_list.append(sha256_correct_file)
                    sha256_current_sum = get_file_sha256(sha256_correct_file)
                    print_message(f"Current file '{sha256_correct_file}' SHA256 sum: {sha256_current_sum}\nCorrect file '{sha256_correct_file}' SHA256 sum: {sha256_correct_sum}")
                    if sha256_correct_sum != sha256_current_sum:
                        print_message(f"File '{sha256_correct_file}' has incorrect sha256 sum.\nCorrect: {sha256_correct_sum}\nCurrent: {sha256_current_sum}")
                        sha256_incorrect = True
            if sha256_incorrect or not sha256_file.exists():
                print_message(f"File 'SHA256' not found or some file has incorrect sha256 sum, it means module can be infected, removing it...", WARNING, force=True)
                uninstall_module(module_name, force=True)
                print_message(f"If you want to install module without checking sha256 sum, you need to install module with --skip-check flag.", WARNING, force=True)
                return
        if helper_changelog:
            with open(changelog_path, 'w' if changelog_path.exists() else 'x', encoding='utf-8') as changelog_file:
                changelog_file.write(helper_changelog)
        req_file = Path(f"{install_dest}/requirements.txt").absolute()
        install_sc = Path(f"{install_dest}/INSTALL.sc")
        scenario_pre = None
        scenario_post = None
        if install_sc.exists():
            print_message(f"Reading installation scenarios for module '{module_name}'...")
            with open(install_sc, 'r', encoding='utf-8') as install_sc_file:
                scenario_content = yaml.safe_load(install_sc_file.read())
                scenario_pre = scenario_content.get('pre', None)
                scenario_post = scenario_content.get('post', None)
        if scenario_pre:
            _run_scenario('pre', scenario_pre, module_name, 'install')
        if req_file.exists():
            print_message(f"Installing module '{module_name}' packages.")
            install_requirements(module_name, req_file)
        if scenario_post:
            _run_scenario('post', scenario_post, module_name, 'install')
    return f"Module '{module_name}' installed successfully."


def uninstall_module(module_name: str, force: bool = False):
    module_path = Path(HELPERS_DIR, module_name).absolute()
    uninstall_scenario = Path(f'{HELPERS_DIR}/{module_name}/UNINSTALL.sc')
    scenario_pre = None
    scenario_post = None
    if not module_path.exists():
        return f"Module '{module_name}' not found."

    if not force:
        if not print_choice(f"Do you really want to remove module '{module_name}'?"):
            return f"Module '{module_name}' uninstall cancelled."

    if uninstall_scenario.exists():
        print_message(f"Reading uninstallation scenarios for module '{module_name}'...")
        with open(uninstall_scenario, 'r', encoding='utf-8') as uninstall_scenario_file:
            scenario_content = yaml.safe_load(uninstall_scenario_file.read())
            scenario_pre = scenario_content.get('pre', None)
            scenario_post = scenario_content.get('post', None)

    if scenario_pre:
        _run_scenario('pre', scenario_pre, module_name, 'uninstall')
    shutil.rmtree(module_path)
    if scenario_post:
        _run_scenario('post', scenario_post, module_name, 'uninstall')
    return f"Module '{module_name}' uninstalled."


def pack_module(module_name: str, module_version: str, location: str):
    module_path = Path(HELPERS_DIR, module_name).absolute()

    if not module_path.exists():
        return f"Module '{module_name}' not found."

    if location:
        location = Path(location).absolute()
        if not location.exists():
            os.makedirs(location, mode=0o755, exist_ok=True)
        archive = location / f"{module_name}-{module_version}.tar.gz"
    else:
        archive = HELPERS_DIR / f"{module_name}-{module_version}.tar.gz"

    with tarfile.open(archive, mode="w:gz") as tar:
        tar.add(module_path, arcname=f'{module_name}-{module_version}')
    return f"Module packed to '{archive}'."

def determine_type(input_string):
    parsed = urlparse(input_string)
    if parsed.scheme in ('http', 'https'):
        return 'url'
    else:
        return 'file'
