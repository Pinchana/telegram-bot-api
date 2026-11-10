"""Select verified release binaries or trusted successful master build artifacts."""

import base64
import json
import os
import re
import subprocess

VERSION_TAG = re.compile(r"v\d+\.\d+(?:\.\d+)?(?:-[A-Za-z0-9.-]+)?\Z")


def api(path, *, paginate=False):
    args = ["gh", "api", path]
    if paginate:
        args += ["--paginate", "--slurp"]
    return json.loads(subprocess.check_output(args, text=True))


def cmake_version(repo, sha):
    data = api(f"repos/{repo}/contents/CMakeLists.txt?ref={sha}")
    text = base64.b64decode(data["content"]).decode()
    match = re.search(r"project\(TelegramBotApi VERSION ([0-9.]+)", text)
    if not match:
        raise ValueError("Cannot determine Bot API version from the binary source commit")
    return match.group(1)


def release(repo, tag):
    if not VERSION_TAG.fullmatch(tag):
        raise ValueError("Invalid Bot API version tag")
    data = api(f"repos/{repo}/releases/tags/{tag}")
    asset = next((item for item in data["assets"] if item["name"] == "telegram-bot-api"), None)
    if not asset or not re.fullmatch(r"sha256:[0-9a-f]{64}", asset.get("digest") or ""):
        raise ValueError(f"{tag} needs a release binary with a GitHub SHA-256 digest")
    sha = api(f"repos/{repo}/commits/{tag}")["sha"]
    version = cmake_version(repo, sha)
    if version != tag[1:].split("-", 1)[0]:
        raise ValueError("Release tag does not match the Bot API source version")
    return {"kind": "release", "ref": tag, "version": tag[1:], "sha": sha,
            "digest": asset["digest"], "run_id": "",
            "tags": f"ghcr.io/{repo.lower()}:{tag},ghcr.io/{repo.lower()}:{tag[1:]}"}


def master(repo, run_id=None):
    if run_id:
        if not str(run_id).isdecimal():
            raise ValueError("Invalid build run ID")
        run = api(f"repos/{repo}/actions/runs/{run_id}")
    else:
        runs = api(f"repos/{repo}/actions/workflows/build.yml/runs?branch=master&status=success&per_page=50")["workflow_runs"]
        run = next((item for item in runs if item["event"] in {"push", "workflow_dispatch"}), None)
    if not run or (run["status"], run["conclusion"], run["head_branch"], run["path"]) != (
        "completed", "success", "master", ".github/workflows/build.yml"
    ) or run["event"] not in {"push", "workflow_dispatch"} or run["head_repository"]["full_name"].lower() != repo.lower():
        raise ValueError("Refusing to publish binaries from an untrusted or unsuccessful build")
    sha = run["head_sha"]
    artifact = next((item for item in api(f"repos/{repo}/actions/runs/{run['id']}/artifacts")["artifacts"]
                     if item["name"] == "telegram-bot-api-linux-x86_64" and not item["expired"]), None)
    if not artifact:
        raise ValueError("Successful master build artifact has expired; run build.yml again")
    return {"kind": "artifact", "ref": "master", "version": cmake_version(repo, sha), "sha": sha,
            "digest": "", "run_id": str(run["id"]),
            "tags": f"ghcr.io/{repo.lower()}:latest,ghcr.io/{repo.lower()}:master,ghcr.io/{repo.lower()}:sha-{sha[:12]}"}


def select(repo, event, version):
    if "workflow_run" in event:
        run = event["workflow_run"]
        if run["event"] not in {"push", "workflow_dispatch"} or run["head_repository"]["full_name"].lower() != repo.lower():
            raise ValueError("Pull request/fork builds cannot publish images")
        if run["head_branch"] == "master":
            return [master(repo, run["id"])]
        if run["status"] != "completed" or run["conclusion"] != "success" or run["path"] != ".github/workflows/build.yml":
            raise ValueError("Only successful build.yml runs can publish images")
        return [release(repo, run["head_branch"])]
    if "release" in event:
        return [release(repo, event["release"]["tag_name"])]
    if version == "all":
        tags = [tag["name"] for page in api(f"repos/{repo}/tags?per_page=100", paginate=True)
                for tag in page if VERSION_TAG.fullmatch(tag["name"])]
        return [release(repo, tag) for tag in tags] + [master(repo)]
    return [master(repo)] if version == "master" else [release(repo, version)]


if __name__ == "__main__":
    with open(os.environ["GITHUB_EVENT_PATH"]) as source:
        event = json.load(source)
    matrix = {"include": select(os.environ["GITHUB_REPOSITORY"], event, os.environ.get("VERSION", "all"))}
    print(json.dumps(matrix, indent=2))
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write("matrix=" + json.dumps(matrix, separators=(",", ":")) + "\n")
