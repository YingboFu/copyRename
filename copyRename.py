import sys
import getopt
import os
import git
import subprocess
import json


def setup_dirs(repo_slug):
    repo_dir = os.path.join(".", "repositories", repo_slug)
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)
    return repo_dir


def clone_repository(repo_slug, repo_dir):
    github_url = 'https://github.com/{0}'.format(repo_slug)
    repo = git.Repo.clone_from(github_url, repo_dir)
    return repo


def process_project_list(project_list):
    res = {}
    totalCommitCounter = 0
    totalRenameCounter = 0
    totalCopyCounter = 0
    for project in project_list:
        commitCounter = 0
        renameCounter = 0
        copyCounter = 0
        repo_dir = setup_dirs(project)
        repo_owner = project.split('/')[0]
        repo_name = project.split("/")[1]
        repo = clone_repository(project, repo_dir)
        with open(f"./Commit Pair Hash/{repo_owner}---{repo_name}.csv", "r") as f:
            for line in f.readlines():
                commitCounter += 1
                before = line.strip().split(",")[0]
                after = line.strip().split(",")[1]
                result = subprocess.run(["git", "diff", "--name-status", "-C", before, after],
                                        cwd=f"repositories/{repo_owner}/{repo_name}/",
                                        capture_output=True, text=True)
                for line in result.stdout.split("\n"):
                    if line.startswith("R"):
                        idx = line.rfind("\t")
                        if (project, after, "rename") not in res:
                            res[(project, after, "rename")] = []
                        res[(project, after, "rename")].append(line[idx + 1:])
                        renameCounter += 1
                    elif line.startswith("C"):
                        idx = line.rfind("\t")
                        if (project, after, "copy") not in res:
                            res[(project, after, "copy")] = []
                        res[(project, after, "copy")].append(line[idx + 1:])
                        copyCounter += 1
        print(f"There are {renameCounter} times renaming and {copyCounter} times copying "
              f"in {commitCounter} commits in {project}")
        totalRenameCounter += renameCounter
        totalCopyCounter += copyCounter
        totalCommitCounter += commitCounter
        subprocess.run(["rm", "-rf", f"./repositories/{repo_owner}/"])
    print(f"There are {totalRenameCounter} times renaming and {totalCopyCounter} times copying "
              f"in {totalCommitCounter} commits in total")
    return res

def parse_project_list():
    project_list = []
    for root, dirs, files in os.walk("./Commit Pair Hash/"):
        for f in files:
            fname = f.split("---")[0] + "/" + f.split("---")[1][:-4]
            project_list.append(fname)
    return project_list

def remap_keys(mapping):
    return [{'key': k, 'value': v} for k, v in mapping.items()]

def main(args=sys.argv[1:]) -> None:
    project = ''
    fileName = ''
    res = {}
    try:
        opts, args = getopt.getopt(args, "hp:f:", ["project=", "file="])
    except getopt.GetoptError:
        'copyRename.py -p <project> -f <fileName>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('copyRename.py -p <project> -f <fileName>')
            sys.exit()
        elif opt in ("-p", "--project"):
            project = arg
        elif opt in ("-f", "--file"):
            fileName = arg

    if os.path.exists("result.json"):
        with open('result.json') as json_file:
            _res = json.load(json_file)
            for item in _res:
                res[tuple(item['key'])] = item['value']
    else:
        project_list = parse_project_list()
        res = process_project_list(project_list)
        with open('result.json', 'w') as fp:
            json.dump(remap_keys(res), fp)

    if project != '' and fileName != '':
        for p, c, o in res.keys():
            if p == project and o == 'rename' and fileName in res[(p, c, o)]:
                print(c)


if __name__ == "__main__":
    main()
