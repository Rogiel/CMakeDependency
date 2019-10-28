import json, os, sys
from urllib.parse import urlparse

tab = " "*4
nl_indent = "\n"+tab*2


def escape(s, n):
    return ' ' * n + s


def generate_dependency_decl(name, keys):
    max_key_length = 0
    for (key, value) in keys.items():
        max_key_length = max(max_key_length, len(key))

    s = "import_dependency(" + name + nl_indent + (nl_indent).join(
        map(lambda k: k[0] + " " + escape(k[1], max_key_length - len(k[0]) + 3), keys.items())) + ")"
    return s


j = json.load(sys.stdin)

for (name, dep_info) in j.items():
    sys.stderr.write('Updating dependency definitions for ' + name + '\n')
    target_info = dep_info["target"]

    target_type = target_info["type"]
    src_dir = "${" + name + "_SOURCE_DIR}/"

    dep_args = {}
    if "git" in dep_info:
        git_info = dep_info["git"]
        git_repo = git_info["repository"]
        git_tag = git_info["tag"]

        git_url_parsed = urlparse(git_repo)
        if git_url_parsed.hostname == 'github.com':
            parts = git_url_parsed.path.split("/")
            user = parts[1]
            repo = parts[2]
            repo = repo[:-4] if repo.endswith('.git') else repo
            dep_args["URL"] = "https://github.com/" + user + "/" + repo + "/archive/" + git_tag + ".zip"
            dep_args["DOWNLOAD_NAME"] = repo + "-" + git_tag + ".zip"
        else:
            print('git is only supported for github repositories at the moment.', file=sys.stderr)
            exit(-1)
    elif "url" in dep_info:
        dep_args["URL"] = " ".join(dep_info["url"])

    if 'download_name' in dep_info:
        dep_args["DOWNLOAD_NAME"] = dep_info['download_name']

    print("# -- Dependency: " + name)
    print(generate_dependency_decl(name, dep_args))

    public_decl_type = "PUBLIC"
    if target_type == "static":
        if isinstance(target_info["srcs"], list):
            srcs = (nl_indent).join(map(lambda x: src_dir + x,target_info["srcs"]))
        else:
            print("file(GLOB " + name + "_SRCS " + src_dir + target_info["srcs"] + ")")
            srcs = "${" + name + "_SRCS}"
        print("add_library("+name+" STATIC "+nl_indent+srcs+")")

    if target_type == "interface":
        print("add_library("+name+" INTERFACE)")
        public_decl_type = "INTERFACE"

    if target_type == "subdirectory":
        if "cache" in target_info:
            for (var_name, value) in target_info["cache"].items():
                if isinstance(value, bool):
                    print("set("+var_name+" "+("ON" if value else "OFF")+" CACHE INTERNAL \"\" FORCE)")

        print("add_subdirectory(${" + name + "_SOURCE_DIR} ${" + name + "_BINARY_DIR})")

    if target_type == "cmake":
        print("include(${PROJECT_SOURCE_DIR}/" + target_info["file"]+")\n")
        continue

    includes = []
    if "public_includes" in target_info:
        includes += list(map(lambda x: public_decl_type + " " + src_dir + x, target_info["public_includes"]))
    if "private_includes" in target_info:
        includes += list(map(lambda x: "PRIVATE " + src_dir + x, target_info["private_includes"]))
    if len(includes) != 0:
        print("target_include_directories("+name+" "+nl_indent+
              nl_indent.join(includes)
              +")")

    defines = []
    if "public_defines" in target_info:
        defines += list(map(lambda x: public_decl_type + " " + x, target_info["public_defines"]))
    if "private_defines" in target_info:
        defines += list(map(lambda x: "PRIVATE " + x, target_info["private_defines"]))
    if len(defines) != 0:
        print("target_compile_definitions("+name+" "+nl_indent+
              nl_indent.join(defines)
              +")")

    if "links" in target_info:
        print("target_link_libraries("+name+" "+nl_indent+
              nl_indent.join(map(lambda x: public_decl_type + ' ' + x, target_info["links"]))
              +")")

    if "aliases" in target_info:
        for (tgt, src) in target_info["aliases"].items():
            print("add_library("+tgt+" ALIAS "+src+")")

    if "extra_cmake" in target_info:
        print()
        print("include(${PROJECT_SOURCE_DIR}/" + target_info["extra_cmake"]+")")
    print()

