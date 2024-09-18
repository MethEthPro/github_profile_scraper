import requests
import math
from bs4 import BeautifulSoup as soup
import os
import re
import ast
import time
from functools import lru_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import datetime


# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# service = Service(executable_path="chromedriver.exe")
# driver = webdriver.Chrome(service=service)
#

CODE_FILE_EXTENSIONS = ['.py', '.js', '.java', '.cpp', '.html', '.css', '.rb', '.go', '.rs']
EXCLUDE_EXTENSIONS = ['.json', '.ipynb', '.csv', '.md', '.txt']
MAX_FILE_SIZE = 1024 * 1024 * 3   # 3 MB

def requests_retry_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504)):
    session = requests.Session()
    retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor, status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def condition_rate(token):
    rate_limit_status = check_rate_limit(token)
    remaining = rate_limit_status['resources']['core']['remaining']
    limit = rate_limit_status['resources']['core']['limit']

    if limit > 1000:
        print(f"REMAINING LIMIT {remaining}")
        repos = get_user_repos(username, github_token)
        if repos:
            i = 0
            for repo in repos:
                i += 1
                repo_name = repo['name']
                metadata = get_repo_metadata(username, repo_name, github_token)
                language = get_language_percentages(username, repo_name, github_token)
                print(f"Repository Number: {i}")
                print(f"Repository: {repo['name']}")
                print(f"Description: {repo['description']}")
                print(f"Stars: {repo['stargazers_count']}")
                print(f"Watchers: {repo['watchers']}")

                if metadata:
                    print(f"Primary Language: {metadata['language']}")
                    print(f"Forks count: {metadata['forks']}")
                    print(f"Size: {convert_size(metadata['size'])}")

                if language:
                    for key, value in language.items():
                        print(f"Language: {key} --- Percentage: {value}%")
                print(f"Commit count: {commit_contributors_Count(username, repo_name)[0]}")
                print(f"Contributors count: {commit_contributors_Count(username, repo_name)[1]}")
                repo_url = "https://github.com/" + username + "/" + repo_name

                analysis_results = analyze_repository(username, repo_name)
                final_score = calculate_final_score(analysis_results)
                print(f"Final score for repository: {final_score}")
                print("---")
    else:
        reset_timestamp = rate_limit_status['resources']['core']['reset']
        reset_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(reset_timestamp))
        print(f"Rate limit will reset at: {reset_time}")
        utc_time = datetime.datetime.utcfromtimestamp(reset_timestamp)
        ist_time = utc_time + datetime.timedelta(hours=5, minutes=30)
        ist_time_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"Rate limit will reset at (IST): {ist_time_str}")


def check_rate_limit(token):
    url = "https://api.github.com/rate_limit"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    session = requests_retry_session()
    response = session.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error checking rate limit: {response.status_code}")
        return None


# ////////////////////////////             DATA     EXTRACTION      /////////////////////////////////////


def get_page(url):
    session = requests_retry_session()
    page = session.get(url, headers={
        "User-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"})
    doc = soup(page.content, "html.parser")
    return doc

@lru_cache(maxsize=128)
def get_user_repos(username, token):
    all_repos = []
    page = 1
    per_page = 100  # Adjust as needed (max is 100)

    while True:
        url = f"https://api.github.com/users/{username}/repos?per_page={per_page}&page={page}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        session = requests_retry_session()
        response = session.get(url, headers=headers)

        if response.status_code == 200:
            repos = response.json()
            if not repos:
                break  # No more repositories to fetch

            all_repos.extend(repos)
            page += 1  # Move to the next page
        else:
            print(f"Error fetching repositories: {response.status_code}")
            return None

    return all_repos

def get_repo_metadata(username, repo_name, token):
    url = f"https://api.github.com/repos/{username}/{repo_name}"
    headers = {'Authorization': f'token {token}'}
    session = requests_retry_session()
    response = session.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return {
            'name': data['name'],
            'stars': data['stargazers_count'],
            'forks': data['forks_count'],
            'language': data['language'],
            'size': data['size'],
            'watchers': data['subscribers_count']
        }
    else:
        print(f"Error: {response.status_code}")
        return None


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def get_language_percentages(username, repo_name, token):
    url = f"https://api.github.com/repos/{username}/{repo_name}/languages"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    session = requests_retry_session()
    response = session.get(url, headers=headers)
    if response.status_code == 200:
        lang = response.json()
        lang_keys = list(lang.keys())
        lang_values = list(lang.values())
        total = sum(lang_values)
        final_dic = {key: (value / total) * 100 for key, value in zip(lang_keys, lang_values)}
        return final_dic
    else:
        print(f"Error: {response.status_code}")
        return None


def commit_contributors_Count(username, repo_name):

    url = "https://github.com/"+username+"/"+repo_name
    doc = get_page(url)
    span1 = doc.find("span",attrs={"class":"fgColor-default"})
    span2 = doc.find("span", attrs={"class" : "Counter ml-1"})
    try :
        return [span1.get_text(), span2.get_text()]
    except AttributeError:
        return [1, 1]


#  /////////////////////////////////////                        FILE     HANDLING     //////////////////////////////


def get_repo_contents(username,repo_name,token, path=''):


    api_url =  "https://api.github.com/repos/"+username+"/"+repo_name+"/contents/"+path
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(api_url,headers=headers)
    return response.json()


def count_lines_of_code(content):
    lines = content.split('\n')
    code_line_count = 0
    comment_line_count = 0
    blank_line_count = 0
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            blank_line_count += 1
        elif stripped_line.startswith("#") or stripped_line.startswith("//"):
            comment_line_count += 1
        else:
            code_line_count += 1
    line_dic = {
        'total_lines': len(lines),
        'code_lines': code_line_count,
        'comment_lines': comment_line_count,
        'blank_lines': blank_line_count
    }
    return code_line_count


def should_process_file(file_name, file_size):
    _, extension = os.path.splitext(file_name.lower())
    return (
        extension in CODE_FILE_EXTENSIONS
        and extension not in EXCLUDE_EXTENSIONS
        and file_size <= MAX_FILE_SIZE
    )


def analyze_code_structure(content, file_extension):
    extension = file_extension.lower()
    if extension == '.py':
        return analyze_python_structure(content)
    elif extension in ['.js', '.jsx']:
        return analyze_javascript_structure(content)
    elif extension in ['.java']:
        return analyze_java_structure(content)
    elif extension in ['.cpp', '.c', '.h', '.hpp']:
        return analyze_cpp_structure(content)
    elif extension in ['.html', '.htm']:
        return analyze_html_structure(content)
    elif extension == '.css':
        return analyze_css_structure(content)
    elif extension == '.rb':
        return analyze_ruby_structure(content)
    elif extension == '.go':
        return analyze_go_structure(content)
    elif extension == '.rs':
        return analyze_rust_structure(content)
    else:
        return {'error': f'Unsupported file type: {extension}'}


def analyze_python_structure(content):
    try:
        tree = ast.parse(content)
        classes = sum(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
        functions = sum(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
        imports = sum(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(tree))
        return {'classes': classes, 'functions': functions, 'imports': imports}
    except SyntaxError as e:
        print(f"SyntaxError encountered: {e}")
        return {'classes': 0, 'functions': 0, 'imports': 0}


def analyze_javascript_structure(content):
    try :
        class_pattern = r'\bclass\s+\w+'
        function_pattern = r'\bfunction\s+\w+|\bconst\s+\w+\s*=\s*(\(.*\)\s*=>|\function\b)'
        import_pattern = r'\b(import|require)\b'
        classes = len(re.findall(class_pattern, content))
        functions = len(re.findall(function_pattern, content))
        imports = len(re.findall(import_pattern, content))
        return {'classes': classes, 'functions': functions, 'imports': imports}
    except SyntaxError as e:
        print(f"SyntaxError encountered: {e}")
        return {'classes': 0, 'functions': 0, 'imports': 0}


def analyze_java_structure(content):
    try :
        class_pattern = r'\bclass\s+\w+'
        method_pattern = r'\b(public|private|protected)?\s+\w+\s+\w+\s*\([^)]*\)\s*\{'
        import_pattern = r'\bimport\s+[\w.]+;'
        classes = len(re.findall(class_pattern, content))
        methods = len(re.findall(method_pattern, content))
        imports = len(re.findall(import_pattern, content))
        return {'classes': classes, 'methods': methods, 'imports': imports}
    except SyntaxError as e:
        print(f"SyntaxError encountered: {e}")
        return {'classes': 0, 'functions': 0, 'imports': 0}


def analyze_cpp_structure(content):
    try:
        class_pattern = r'\bclass\s+\w+'
        function_pattern = r'\b\w+\s+\w+\s*\([^)]*\)\s*{'
        include_pattern = r'#include\s+[<"][\w.]+[>"]'
        classes = len(re.findall(class_pattern, content))
        functions = len(re.findall(function_pattern, content))
        includes = len(re.findall(include_pattern, content))
        return {'classes': classes, 'functions': functions, 'includes': includes}
    except SyntaxError as e:
        print(f"SyntaxError encountered: {e}")
        return {'classes': 0, 'functions': 0, 'imports': 0}


def analyze_html_structure(content):
    try :
        tag_pattern = r'<(\w+)[^>]*>'
        script_pattern = r'<script[^>]*>.*?</script>'
        style_pattern = r'<style[^>]*>.*?</style>'
        tags = re.findall(tag_pattern, content)
        scripts = len(re.findall(script_pattern, content, re.DOTALL))
        styles = len(re.findall(style_pattern, content, re.DOTALL))
        return {'total_tags': len(tags), 'unique_tags': len(set(tags)), 'scripts': scripts, 'styles': styles}
    except SyntaxError as e:
        print(f"SyntaxError encountered: {e}")
        return {'total_tags': 0, 'unique_tags': 0, 'scripts': 0, 'styles': 0}

def analyze_css_structure(content):
    try:
        selector_pattern = r'([^{]+)\s*{'
        property_pattern = r'(\w+[-\w]*)\s*:'
        media_query_pattern = r'@media\b'
        selectors = len(re.findall(selector_pattern, content))
        properties = len(re.findall(property_pattern, content))
        media_queries = len(re.findall(media_query_pattern, content))
        return {'selectors': selectors, 'properties': properties, 'media_queries': media_queries}
    except SyntaxError as e:
        print(f"SyntaxError encountered: {e}")
        return {'selectors': 0, 'properties': 0, 'media_queries': 0}


def analyze_ruby_structure(content):
    try :
        class_pattern = r'\bclass\s+\w+'
        method_pattern = r'\bdef\s+\w+'
        module_pattern = r'\bmodule\s+\w+'
        require_pattern = r'\brequire\s+["\'][\w./]+["\']'
        classes = len(re.findall(class_pattern, content))
        methods = len(re.findall(method_pattern, content))
        modules = len(re.findall(module_pattern, content))
        requires = len(re.findall(require_pattern, content))
        return {'classes': classes, 'methods': methods, 'modules': modules, 'requires': requires}
    except SyntaxError as e:
        print(f"SyntaxError encountered: {e}")
        return {'classes': 0, 'methods': 0, 'modules': 0, 'requires': 0}


def analyze_go_structure(content):
    try :
        func_pattern = r'\bfunc\s+\w+'
        struct_pattern = r'\btype\s+\w+\s+struct\b'
        interface_pattern = r'\btype\s+\w+\s+interface\b'
        import_pattern = r'\bimport\s+(\([\s\S]*?\)|\S+)'
        funcs = len(re.findall(func_pattern, content))
        structs = len(re.findall(struct_pattern, content))
        interfaces = len(re.findall(interface_pattern, content))
        imports = len(re.findall(import_pattern, content))
        return {'functions': funcs, 'structs': structs, 'interfaces': interfaces, 'imports': imports}
    except SyntaxError as e:
        print(f"SyntaxError encountered: {e}")
        return {'functions': 0, 'structs': 0, 'interfaces': 0, 'imports': 0}


def analyze_rust_structure(content):
    try:
        fn_pattern = r'\bfn\s+\w+'
        struct_pattern = r'\bstruct\s+\w+'
        enum_pattern = r'\benum\s+\w+'
        trait_pattern = r'\btrait\s+\w+'
        mod_pattern = r'\bmod\s+\w+'
        use_pattern = r'\buse\s+[\w:]+;'
        fns = len(re.findall(fn_pattern, content))
        structs = len(re.findall(struct_pattern, content))
        enums = len(re.findall(enum_pattern, content))
        traits = len(re.findall(trait_pattern, content))
        mods = len(re.findall(mod_pattern, content))
        uses = len(re.findall(use_pattern, content))
        return {'functions': fns, 'structs': structs, 'enums': enums, 'traits': traits, 'modules': mods, 'uses': uses}
    except SyntaxError as e:
        print(f"SyntaxError encountered: {e}")
        return {'functions': 0, 'structs': 0, 'enums': 0, 'traits': 0, 'modules': 0, 'uses': 0}


def detect_python_complex_algorithms(content):
    complex_patterns = [
        r'for.*for',
        r'while.*while',
        r'recursion',
        r'[^\w]map\(',
        r'[^\w]reduce\(',
        r'[^\w]filter\('
    ]
    return sum(1 for pattern in complex_patterns if re.search(pattern, content, re.IGNORECASE))


def process_file_content(content, file_name):
    _, extension = os.path.splitext(file_name.lower())
    loc = count_lines_of_code(content)
    structure = analyze_code_structure(content, extension)
    complex_algos = detect_python_complex_algorithms(content) if extension == ".py" else 0
    return {
        'line_count': loc,
        'structure': structure,
        'complex_algorithms': complex_algos
    }


def calculate_final_score(analysis_results):
    total_loc = sum(result['analysis']['line_count'] for result in analysis_results)
    total_files = len(analysis_results)
    max_depth = max(result['folder_depth'] for result in analysis_results) if analysis_results else 0
    avg_complex_algos = (sum(result['analysis']['complex_algorithms'] for result in analysis_results) / total_files) if total_files > 0 else 0
    complexity_score = (
        0.3 * total_loc +
        0.3 * total_files +
        0.2 * max_depth +
        0.2 * avg_complex_algos
    )
    return complexity_score


def analyze_repository(username, repo_name, path=''):
    results = []
    contents = get_repo_contents(username, repo_name, github_token, path)
    folder_depth = len(path.split('/')) if path else 0
    if isinstance(contents, dict) and 'message' in contents:
        print(f"Error: {contents['message']}")
        return results

    for item in contents:
        full_path = path + "/" + item['name']
        if should_process_file(item['name'], item['size']) and item['type'] == 'file' and item['name'] != '.gitignore':
            session = requests_retry_session()
            file_content = session.get(item['download_url']).text
            analysis = process_file_content(file_content, item['name'])
            results.append({
                'name': full_path,
                'analysis': analysis,
                'folder_depth': folder_depth
            })
        elif item['type'] == 'dir' and item['name'] != '.gitignore':
            sub_results = analyze_repository(username, repo_name, path=full_path)
            results.extend(sub_results)

    return results


# link = "https://github.com/JaideepGuntupalli"

link = input("Enter the profile link\n")
github_token = "YOUR_GITHUB_TOKEN"
username = link.split('/')[-1]

condition_rate(github_token)
