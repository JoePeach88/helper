import requests
import os
import tempfile
import tarfile
import shutil
from helpers import print_message, print_choice, WARNING, ERROR, install_requirements
from pathlib import Path
from tqdm import tqdm
from env import GITHUB_TOKEN


headers = {
    'authorization': 'Bearer {token}'.format(token=GITHUB_TOKEN)
}

if GITHUB_TOKEN in ['', ' '] or not GITHUB_TOKEN:
    print_message('GitHub token not set, update, install and check functions of modules and core modules will work incorrect, set token via `helper core config set core:remote gh_api_token <your token here>`.', WARNING, force=True)


def github_repo_to_ssh(repo_url: str):
    if not repo_url:
        return
    repo_url = repo_url.rstrip('/')

    if not repo_url.startswith('https://github.com/'):
        print_message(f"Not a valid GitHub URL: {repo_url}", WARNING)
        return

    path = repo_url.replace('https://github.com/', '')
    parts = path.split('/')

    if len(parts) < 2:
        print_message(f"Invalid GitHub repository URL: {repo_url}", WARNING)
        return

    owner = parts[0]
    repo = parts[1]

    ssh_repo_url = f"git@github.com:{owner}/{repo}.git"
    
    return ssh_repo_url


def github_url_to_releases_api(github_url: str):
    if not github_url:
        return
    github_url = github_url.rstrip('/')

    if not github_url.startswith('https://github.com/'):
        print_message(f"Not a valid GitHub URL: {github_url}", WARNING)
        return

    path = github_url.replace('https://github.com/', '')
    parts = path.split('/')

    if len(parts) < 2:
        print_message(f"Invalid GitHub repository URL: {github_url}", WARNING)
        return

    owner = parts[0]
    repo = parts[1]

    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    
    return api_url


def retrieve_json(url: str):
    return requests.get(url, headers=headers).json()


def download_file(url: str, dest: str):
    def _get_response_with_cookies(session: requests.Session, url: str, headers: dict):
        response = session.get(url, headers=headers, allow_redirects=True, stream=True)
        if response.status_code != 200:
            print_message('Something went wrong when trying to download file.', ERROR)
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            response = session.get(url, headers=headers, allow_redirects=True, cookies=response.cookies, stream=True)
        return response

    with requests.Session() as session:
        response = _get_response_with_cookies(session, url, headers)

        total_size = int(response.headers.get('Content-Length', 0))

        with open(dest, 'wb') as f, tqdm(desc=os.path.basename(dest), total=total_size, unit='iB', unit_scale=True, unit_divisor=1024) as bar:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    size = f.write(chunk)
                    bar.update(size)


def detect_builtin():
    from helpers import list_helpers
    helpers = list_helpers()
    builtin_helpers = []
    for helper in helpers:
        if helper['builtin']:
            builtin_helpers.append(Path(helper['file']).parent.relative_to(Path("./").resolve()))

    # Extends with core helper module and documentation
    builtin_helpers.extend([Path('helpers/__init__.py'), Path('helpers/README.md')])
    return builtin_helpers


def detect_core():
    core_files = ['libs', 'cli.py', 'env.py', 'helper', 'helper.bat', 'README.md', 'requirements.txt']
    core_files_paths = []
    for core_file in core_files:
        core_file_path = Path(core_file)
        if core_file_path.is_dir():
            if core_file_path not in core_files_paths:
                core_files_paths.append(core_file_path)
            core_files_paths.extend(core_file_path.glob('*'))
        else:
            core_files_paths.append(core_file_path)
    return core_files_paths


def collect_requirements(structure: list):
    requirements = []
    def recurse_collect(item: Path):
        if item.is_dir():
            for child in sorted(item.iterdir()):
                recurse_collect(child)
        else:
            if item.name == 'requirements.txt':
                requirements.append(item)

    for file in structure: 
        recurse_collect(file)
    return requirements


def install_update(version: str, update_link: str):
    install_dest = Path(__file__).resolve().parent.parent.parent.absolute()
    with tempfile.TemporaryDirectory() as tmp_dir:
        archive_path = Path(tmp_dir) / f'core-update-{version}.tar.gz'
        print_message(f"Downloading core update version '{version}' to '{archive_path}'.")
        download_file(update_link, archive_path)

        print_message(f"Unpacking and installing core update '{version}' to '{install_dest}'.")
        with tarfile.open(archive_path, "r:gz") as tar:
            root_folder = tar.getmembers()[0].name
            matching = [m for m in tar.getmembers()]
            tar.extractall(tmp_dir, members=matching)

        shutil.copytree(Path(tmp_dir) / root_folder, install_dest, dirs_exist_ok=True)

    core_files = detect_core()
    print_message('Listing builtin modules files...')
    builtin_helpers = detect_builtin()
    final_structure_files = core_files + builtin_helpers
    print_message('Listing requirements.txt files...')
    requirements  = collect_requirements(final_structure_files)
    print_message(f'Installing requirements...')
    for req in requirements:
        install_requirements(f'core update {version}', Path(f'./{req}').as_posix())
    return f'Core update version {version} successfully installed.'
