# Overwritten installation script, which copies/remove files of the tmp directory of the container to the mounted host path.
# Additionally is runs a installation and uninstallation workflow for this extension.

import os
import glob
import shutil
import re
import requests
import warnings
import time

tmp_prefix = "/kaapana/tmp/"
target_prefix = os.getenv("TARGET_PREFIX", "/kaapana/mounted/workflows/")
archive_prefix = ".old_files"
action = os.getenv("ACTION", "copy")

if not target_prefix.startswith(f"/kaapana/mounted/"):
    print(f"Unknown prefix {target_prefix=} -> issue")
    exit(1)


def gen_archive_dir(path):
    dir_name = os.path.dirname(path)
    file_name = os.path.basename(path)

    archive_path = os.path.join(dir_name, archive_prefix, file_name)
    if not os.path.isdir(os.path.dirname(archive_path)):
        os.makedirs(os.path.dirname(archive_path))

    return archive_path


def listdir_nohidden(path):
    if target_prefix.startswith(f"/kaapana/mounted/workflows"):
        for f in os.listdir(path):
            if (
                not f.endswith(".pyc")
                and not f.startswith(".")
                and not (f.startswith("__") and f.endswith("__"))
            ):
                yield f
    else:
        for f in os.listdir(path):
            if f.endswith(".tgz"):
                yield f


def get_images(target_dir):
    print("Searching for images...")
    default_registry_identifier = "{DEFAULT_REGISTRY}"
    default_version_identifier = "{KAAPANA_BUILD_VERSION}"
    image_dict = {}
    file_paths = glob.glob(f"{target_dir}/**/*.py", recursive=True)
    print("Found %i files..." % len(file_paths))
    for file_path in file_paths:
        if os.path.isfile(file_path):
            print(f"Checking file: {file_path}")
            content = open(file_path).read()
            matches = re.findall(REGEX, content)
            if matches:
                for match in matches:
                    # Backward compatibility default_registry vs DEFAULT_REGISTRY
                    match = list(match)
                    match[1] = match[1].replace(
                        "{default_registry}", default_registry_identifier
                    )
                    docker_registry_url = (
                        match[1]
                        if default_registry_identifier not in match[1]
                        else match[1].replace(
                            default_registry_identifier, KAAPANA_DEFAULT_REGISTRY
                        )
                    )
                    docker_image = match[3]
                    # Backward compatibility default_registry vs DEFAULT_REGISTRY
                    match[4] = match[4].replace(
                        "{default_version_identifier}", default_version_identifier
                    )
                    docker_version = (
                        match[4]
                        if default_version_identifier not in match[4]
                        else match[4].replace(
                            default_version_identifier, KAAPANA_BUILD_VERSION
                        )
                    )
                    print(f"{docker_registry_url=}")
                    print(f"{docker_image=}")
                    print(f"{docker_version=}")

                    image_dict.update(
                        {
                            f"{docker_registry_url}/{docker_image}:{docker_version}": {
                                "docker_registry_url": docker_registry_url,
                                "docker_image": docker_image,
                                "docker_version": docker_version,
                            }
                        }
                    )
        else:
            print(f"Skipping directory: {file_path}")
    print("Found %i images to download..." % len(image_dict))
    return image_dict


def setup_files():
    global action, tmp_prefix, archive_prefix, target_prefix
    files_to_copy = glob.glob(f"{tmp_prefix}**", recursive=True)
    print(
        "################################################################################"
    )
    print(f"Starting to apply overwritten action {action} to all the files")
    print(
        "################################################################################"
    )
    if action == "remove":
        files_to_copy = reversed(files_to_copy)

    for file_path in files_to_copy:
        rel_dest_path = os.path.relpath(file_path, tmp_prefix)

        if rel_dest_path == "" or rel_dest_path == ".":
            print(f"Skipping root {rel_dest_path=}")
            continue

        if (
            not rel_dest_path.startswith(f"plugins")
            and not rel_dest_path.startswith("dags")
            and not rel_dest_path.startswith("mounted_scripts")
            and not rel_dest_path.startswith("extensions")
            and not rel_dest_path.startswith("data")
        ):
            print(f"Unknown relative directory {rel_dest_path=} -> issue")
            exit(1)

        dest_path = os.path.join(target_prefix, rel_dest_path)

        print(f"Copy file: {file_path=} to {dest_path=}")

        print(file_path, dest_path)
        # TODO should old folder also be saved?
        if os.path.isdir(file_path):
            if not os.path.isdir(dest_path) and action == "copy":
                os.makedirs(dest_path)
            if action == "remove":
                if os.path.isdir(dest_path) and not list(listdir_nohidden(dest_path)):
                    shutil.rmtree(dest_path, ignore_errors=True)
        else:
            if action == "copy":
                if os.path.isfile(dest_path) and action == "copy":
                    warnings.warn(
                        f"Attention! You are overwriting the file {dest_path}!"
                    )
                    old_file = gen_archive_dir(dest_path)
                    # copy of overwrite files
                    print(f"Archive old file to {old_file}")
                    shutil.copyfile(dest_path, old_file)
                shutil.copyfile(file_path, dest_path)
            elif action == "remove":
                if os.path.isfile(dest_path):
                    os.remove(dest_path)
                    old_file = gen_archive_dir(dest_path)
                    if os.path.isfile(old_file):
                        # TODO delete .old_files directory in the end
                        shutil.copyfile(old_file, dest_path)
            else:
                pass

    print(
        "################################################################################"
    )
    print(f"✓ Successfully applied action {action} to all the files")
    print(
        "################################################################################\n"
    )


def trigger_airflow_dags(api: str,tries:int=1):
    for _ in range(tries):
        print(
            "################################################################################"
        )
        print(f"Run {api.split('/')[-1]} workflow!")
        print(
            "################################################################################"
        )
        r = requests.post(api, json={})
        print(r.status_code)
        print(r.text)

        if r.status_code == 200:
            return
        time.sleep(10)

ADMIN_NAMESPACE = os.getenv("ADMIN_NAMESPACE", None)
print(f"{ADMIN_NAMESPACE=}")
assert ADMIN_NAMESPACE
SERVICES_NAMESPACE = os.getenv("SERVICES_NAMESPACE", None)
print(f"{SERVICES_NAMESPACE=}")
assert SERVICES_NAMESPACE
KAAPANA_BUILD_VERSION = os.getenv("KAAPANA_BUILD_VERSION", None)
print(f"{KAAPANA_BUILD_VERSION=}")
assert KAAPANA_BUILD_VERSION
KAAPANA_DEFAULT_REGISTRY = os.getenv("KAAPANA_DEFAULT_REGISTRY", None)
print(f"{KAAPANA_DEFAULT_REGISTRY=}")
assert KAAPANA_DEFAULT_REGISTRY

REGEX = r"image=(\"|\'|f\"|f\')([\w\-\\{\}.]+)(\/[\w\-\.]+|)\/([\w\-\.]+):([\w\-\\{\}\.]+)(\"|\'|f\"|f\')"
HELM_API = f"http://kube-helm-service.{ADMIN_NAMESPACE}.svc:5000"
AIRFLOW_UPDATE_API = f"http://airflow-webserver-service.{SERVICES_NAMESPACE}.svc:8080/flow/kaapana/api/trigger/service-daily-cleanup-jobs"

# uninstall plugin from os
if action == "remove":
    AIRFLOW_UNINSTALL_API = f"http://airflow-webserver-service.{SERVICES_NAMESPACE}.svc:8080/flow/kaapana/api/trigger/uninstall-annotation-collect-meta"
    trigger_airflow_dags(AIRFLOW_UNINSTALL_API,tries=3)
    time.sleep(20)

# copy/remove dags and operator to mounted directory
setup_files()

# install plugin from os
if action == "copy":
    AIRFLOW_INSTALL_API = f"http://airflow-webserver-service.{SERVICES_NAMESPACE}.svc:8080/flow/kaapana/api/trigger/install-annotation-collect-meta"
    # wait to trigger
    trigger_airflow_dags(AIRFLOW_UPDATE_API)
    time.sleep(10)
    trigger_airflow_dags(AIRFLOW_INSTALL_API,tries=5)

if not target_prefix.startswith(f"/kaapana/mounted/workflows"):
    print(f"Calling it a day since I am not any workflow-related file")
    exit()

if action == "copy" or action == "prefetch":
    url = f"{HELM_API}/pull-docker-image"
    for name, payload in get_images(tmp_prefix).items():
        print(payload)
        r = requests.post(url, json=payload)
        print(r.status_code)
        print(r.text)

if action == "remove":
    trigger_airflow_dags(AIRFLOW_UPDATE_API)
    time.sleep(30)
    AIRFLOW_REINDEX_API = f"http://airflow-webserver-service.{SERVICES_NAMESPACE}.svc:8080/flow/kaapana/api/trigger/service-re-index-dicom-data"
    trigger_airflow_dags(AIRFLOW_REINDEX_API,tries=3)

if action == "prefetch":
    print("Running forever :)")
    while True:
        pass
