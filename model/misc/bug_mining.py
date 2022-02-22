from pydriller import Repository, Git
import requests
import json
import re
import os
from io import BytesIO
from typing import Union, Tuple, Any, IO, Type, List

def getBugCommitsDataDir(owner: str, name: str) -> str:
  """ Returns a path to the bugcommits's data of a specific repository.
  
  :param owner: The owner of the repository.
  :type  owner: str
  :param name: The name of the repository.
  :type name: str
  :returns: A path to the bugcommits's data.
  :rtype: str.
  """
  file_name = f"{owner}_{name}.json"
  folder_dir = os.path.join(os.getcwd(), "BugCommitsData")
  if not os.path.exists(folder_dir):
    os.makedirs(folder_dir)
  file_path = os.path.join(folder_dir, file_name)
  return file_path

def getRepoDir(owner: str, name: str) -> str:
  """ Returns a repository directory given the owner and name.
  
  :param owner: The owner of the repository.
  :type  owner: str
  :param name: The name of the repository.
  :type name: str
  :returns: A path to the repository.
  :rtype: str.
  """
  folder_dir = os.path.join(os.getcwd(), "topRepositories")
  repo_name = f"{owner}/{name}"
  repo_dir = os.path.join(folder_dir, repo_name)
  if os.path.exists(repo_dir):
    return repo_dir
  repo_name = f"{owner}"
  repo_dir = os.path.join(folder_dir, repo_name)
  return repo_dir

def writeJSONFile(data: dict, file_path: str) -> bool:
  """ This function dumps JSON data into a file.

  :param data: JSON data that will be dumped.
  :type  data: dict
  :param file_path: The path to the file where the data will be stored.
  :type  file_path: str
  """
  try:
    with open(file_path, 'w', encoding = 'utf-8') as out_file:
      json.dump(data, out_file, separators=(',', ':'), indent=4, sort_keys=True)
  except Exception as e:
      print(f"Could not write file path {file_path}")
      print(f"Exception: {e}")
      return 0
  else:
    return 1

def json_serialize_sets(obj: Any) -> Any:
  if isinstance(obj, set):
    return list(obj)
  return obj


def saveBugfix(bugfix_metadata: dict, file_path: str = r"/content/bugfixes.json", pretty: bool = 0) -> bool:
  """ This function dumps JSON data into a file.

  :param bugfix_metadata: JSON data that will be dumped.
  :type  bugfix_metadata: dict
  :param file_path: The path to the file where the data will be stored.
  :type  file_path: str
  """
  if not bugfix_metadata: return 0
  #print(bugfix_metadata)
  try:
    with open(file_path, 'w', encoding = 'utf-8') as out_file:
      if pretty:
        json.dump(bugfix_metadata, out_file, default=json_serialize_sets, separators=(',', ':'), indent=4, sort_keys=True)
      else:
        json.dump(bugfix_metadata, out_file, default=json_serialize_sets, sort_keys=True)
  except Exception as e:
      print(f"Could not write file path {file_path}")
      print(f"Exception: {e}")
      return 0
  else:
    return 1

def getRepo(owner: str, name: str) -> Any:
  """ This function create an instance of PyDriller.Repository.

  :param owner: The owner of the repository.
  :type  owner: str
  :param name: The name of the repository.
  :type name: str
  :returns: An instance of main class of PyDriller.Repository that
      represents the repository object.
  :rtype: PyDriller.Repository.
  """
  print(f"Initializing {owner}/{name}...")
  folder_dir = os.path.join(os.getcwd(), "topRepositories")
  repo_name = f"{owner}/{name}"
  repo_dir = os.path.join(folder_dir, repo_name)
  #repo_dir = getRepoDir(owner, name)
  if os.path.exists(repo_dir):
    repo = Repository(repo_dir)
  else:
    repo_name = f"{owner}"
    repo_dir = os.path.join(folder_dir, repo_name)
    if not os.path.exists(repo_dir):
      os.makedirs(repo_dir)
    clone_url = f"https://github.com/{owner}/{name}.git"
    print(f"Cloning {owner}/{name} from {clone_url} ...")
    repo = Repository(clone_url, clone_repo_to=repo_dir)
  return repo

def commitFilesInspect(commits_files: list) -> Tuple[list, dict]:
  """ This functions inspects a list of files and extract a bugfix.
  
  :param commits_files: a list containing the names of the files
      that will be inspected.
  :type commits_files: list
  :returns: A list of bugfixes associated to a file.
  :rtype: list
  """
  if len(commits_files) != 1:
      return ([], {})
  bugfix_files = []
  bugfix_metadata = {}
  for f in commits_files:
    filename = f.filename
    """if filename == "lemmatizer.py":
      continue"""
    if f.added_lines == 1 and f.deleted_lines == 1 and filename.endswith('.py'):
      patch = f.diff_parsed
      bugged_line_no = patch['deleted'][0][0]
      bugged_source = f.source_code_before

      fixed_line_no = patch['added'][0][0]
      fixed_source = f.source_code

      bugfix = Bugfix(bugged_line_no, bugged_source, fixed_line_no, fixed_source)
      bugfix_metadata = bugfix.bugfix_data
      
      bugfix_files.append({
          'filename': filename,
          'patch': patch,
      })
      print(f"filename: {filename}")
      #print(f"filename: {filename}.\npatch: {patch}.")
  return (bugfix_files, bugfix_metadata)

def mineBugCommitsFromRepo(owner: str, name: str, process_meta_data: str = "") -> Tuple[dict, List]:
  """ This function.

  :param owner: The owner of the repository.
  :type  owner: str
  :param name: The name of the repository.
  :type name: str
  :returns: A JSON String that represents the repository data
      along with the bugfixing commits.
  :rtype: dict
  """
  repo = getRepo(owner, name)
  no_commits = len(list(repo.traverse_commits()))
  repo = getRepo(owner, name)
  commits = repo.traverse_commits()

  no_bug_commits = 0
  no_mined_bugfixes = 0

  keywords = '(fix|bug|error|issue|problem|defect|fault|flaw|mistake|incorrect)'
  bad_keywords = '(typo|comment)'
  
  repo_data = {
      "owner": owner,
      "repo": name,
      "no_commits": no_commits,
      "bugfixing_commits": []
  }
  bugfixes_data = []

  count_commits = 0
  for commit in commits:
    count_commits += 1
    commit_sha = commit.hash
    message = commit.msg
    if count_commits%500 == 0:
        clear_output()
        curr_process_data = f"{process_meta_data} Mining commit {count_commits} of {no_commits}."
        print(curr_process_data)
    if re.search(keywords, message, re.IGNORECASE):
      if not re.search(bad_keywords, message, re.IGNORECASE):
        no_bug_commits += 1
        if len(commit.parents) != 1:
          # check that the commit only has one parent.
          continue
        curr_process_data = f"{process_meta_data} Mining commit {count_commits} of {no_commits}."
        print(curr_process_data)
        print(f"commit sha: {commit_sha}")
        bugfix_metadata = {}
        bugfix_metadata.clear()
        commits_files = commit.modified_files
        (bugfix_files, bugfix_metadata) = commitFilesInspect(commits_files)
        if not bugfix_metadata:
          continue
        bugfix_metadata.update({
            "commit_sha": commit_sha
        })

        """json_serialize_sets = lambda obj: list(obj) if isinstance(obj, set) else obj
        bugfixes_data.append(
            json.dumps(bugfix_metadata, 
                       default=json_serialize_sets, 
                       sort_keys=True)
        )"""
        bugfixes_data.append(bugfix_metadata)
        #saveBugfix(bugfix_metadata.copy(), pretty=1)

        """curr_process_data = f"{process_meta_data} Mining commit {count_commits} of {no_commits}."
        print(curr_process_data)
        print(f"commit sha: {commit_sha}")"""
        no_mined_bugfixes += len(bugfix_files)
        repo_data['bugfixing_commits'].append({
            "sha": commit_sha,
            "message": message,
            "files": bugfix_files
        })
  repo_data['no_bug_commits'] = no_bug_commits
  repo_data['no_mined_bugfixes'] = no_mined_bugfixes
  return (repo_data, bugfixes_data)

def getTopRepositories(token: str = "", query: str = "", page: int = 1, max_per_page : int = 25) -> list:
  """ This function queries to the Github API to obtain the top repositores.

  :param token: The user access token to Github.
  :type  str
  :param query: The query that will be processed by the Github API.
  :type  str
  :param page: The page from which the query's data will be extracted.
  :type  str
  :param max_per_page: The Maximun number of registers that will be obtained from the query. 
  :type  str
  :returns: A list of strings containing the top repositories' data.
  :rtype: list.
  """
  headers = {'Authorization': 'token %s' % token}
  api_url = f"https://api.github.com/search/repositories?q={query}&page={page}&per_page={max_per_page}"
  #api_url = f"https://api.github.com/search/repositories?q={query}"
  api_response = requests.get(api_url, headers=headers)
  request_success_code = 200
  if api_response.status_code != request_success_code:
    return None
  api_response_json = api_response.json()
  repos_json = api_response_json['items']
  top_repositories = []
  for i in range(len(repos_json)):
    name = repos_json[i]['name']
    owner = repos_json[i]['owner']['login']
    top_repositories.append({
        "name": name,
        "owner": owner,
        "clone_url": f"https://github.com/{owner}/{name}.git"
    })
  return top_repositories

def getTopRepos(file_path: str = "top100PythonRepos.json") -> IO[str]:
  """ T.

  :returns: A JSON String that represents the abstracted ast graph.
  :rtype: String.
  """
  query = 'language:python&sort=stars'
  page = 5
  max_per_page = 100
  api_token = "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"
  repositories = getTopRepositories(api_token, query, page, max_per_page)
  writeJSONFile(repositories, file_path)
  
def removeMinedRepo(file_path):
  """ This property is a hexdigest of the abstracted ast graph of ´node_to_abstract´.

  :returns hexdigest: A JSON String that represents the abstracted ast graph.
  :rtype   hexdigest: String.
  """
  try:
    with open(file_path, 'r') as f:
      top_repositories = json.load(f)
    top_repositories = top_repositories[1:]
    with open(file_path, 'w') as f:
      json.dump(top_repositories, f, separators=(',', ':'), indent=4)
  except Exception as e:
        print(f"Could not write file path {file_path}")
        print(f"Exception: {e}")