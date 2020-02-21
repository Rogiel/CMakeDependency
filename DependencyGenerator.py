import json, sys
from urllib.parse import urlparse

tab = " " * 4
nl_indent = "\n" + tab * 2


def target_relative_path(path, name=None, src_dir=None, bin_dir=None):
    if src_dir is None:
        src_dir = "${" + name + "_SOURCE_DIR}"
    if bin_dir is None:
        bin_dir = "${CMAKE_CURRENT_BINARY_DIR}/" + name

    if path.startswith('/'):
        return '${PROJECT_SOURCE_DIR}' + path
    elif path.startswith(':'):
        return bin_dir + '/' + path[1:]
    elif path.startswith('${'):
        return path
    else:
        if path == '.' or path == '':
            return src_dir
        else:
            return src_dir + '/' + path


def generate_dependency_decl(name, keys):
    max_key_length = 0
    for (key, value) in keys.items():
        max_key_length = max(max_key_length, len(key))

    def align(s, n):
        return ' ' * n + s

    s = "import_dependency(" + name + nl_indent + (nl_indent).join(
        map(lambda k: k[0] + " " + align(k[1], max_key_length - len(k[0]) + 3), keys.items())) + ")"
    return s


def to_cmake_datatype(value):
    def escape_str(s):
        if ' ' in s:
            return '"' + s.replace('"', '\\"') + '"'
        return s

    if isinstance(value, str):
        return escape_str(value)
    elif isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    else:
        return escape_str(str(value))


def generate_target_definition(name, target_name, public_decl_type, src_dir, target_info):
    def gen_entry(decl, values, normalizer=None):
        if values is None or len(values) == 0:
            return []
        if normalizer is None:
            normalizer = lambda x: x

        if isinstance(values, str):
            values = [values]
        if isinstance(values, dict):
            values = values.items()

        return list(map(lambda x: decl + " " + normalizer(x), values))

    def gen_cmake_call(call, entries, glue=None):
        if glue is None:
            glue = ''
        if len(entries) != 0:
            print(call + "(" + target_name + (glue + " " if glue is not None else "") + nl_indent +
                  nl_indent.join(entries)
                  + ")")

    def gen_cmake_target_attrs(call, attr_name, default_scope=public_decl_type, normalizer=None, as_system=False):
        values = []

        values += gen_entry(default_scope, target_info.get(attr_name), normalizer=normalizer)
        values += gen_entry(public_decl_type, target_info.get("public_" + attr_name), normalizer=normalizer)
        values += gen_entry('PRIVATE', target_info.get("private_" + attr_name), normalizer=normalizer)
        values += gen_entry('INTERFACE', target_info.get("interface_" + attr_name), normalizer=normalizer)
        gen_cmake_call(call, values, glue=' SYSTEM' if as_system else '')

    def gen_cmake_target_props(call, attr_name, glue=None):
        if not attr_name in target_info:
            return

        values = list(map(lambda x: x[0] + ' ' + to_cmake_datatype(x[1]), target_info[attr_name].items()))
        gen_cmake_call(call, values, glue=glue)

    def cmake_define_kv(item):
        if isinstance(item, str):
            return item
        if item[1] is None:
            return item[0]
        return item[0] + '=' + to_cmake_datatype(item[1])

    # gen_cmake_target_attrs('target_sources', 'srcs', suffix=src_dir, default_scope='PRIVATE')
    gen_cmake_target_attrs('target_include_directories', 'includes',
                           normalizer=lambda x: target_relative_path(x, name),
                           as_system=True)
    gen_cmake_target_attrs('target_compile_definitions', 'defines', normalizer=cmake_define_kv)
    gen_cmake_target_attrs('target_compile_options', 'options')
    gen_cmake_target_attrs('target_compile_features', 'features')
    gen_cmake_target_attrs('target_link_libraries', 'links')
    gen_cmake_target_attrs('target_link_directories', 'link_directories')
    gen_cmake_target_attrs('target_link_options', 'link_options')
    gen_cmake_target_attrs('target_precompile_headers', 'precompile_headers')
    gen_cmake_target_props('set_target_properties', 'properties', ' PROPERTIES')


def enumerate_srcs(name, target_name, srcs):
    if isinstance(srcs, str):
        srcs = [srcs]
    target_name = target_name.replace('.', '_')

    globs = list(filter(lambda x: '*' in x, srcs))
    paths = list(filter(lambda x: not '*' in x, srcs))

    paths = list(map(lambda x: target_relative_path(x, name), paths))
    if len(globs) != 0:
        print("file(GLOB_RECURSE " + target_name + "_SRCS CONFIGURE_DEPENDS " + (nl_indent).join(
            map(lambda x: target_relative_path(x, name), globs)) + ")")
        paths = ["${" + target_name + "_SRCS}"] + paths

    return (nl_indent).join(paths)


j = json.load(sys.stdin)

for (name, dep_info) in j.items():
    sys.stderr.write('Updating dependency definitions for ' + name + '\n')
    src_dir = "${" + name + "_SOURCE_DIR}"

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

    if 'configure' in dep_info:
        configures = dep_info['configure']
        for (conf_name, configure) in configures.items():
            configure_type = 'configure_file'
            if 'type' in configure:
                configure_type = configure['type']

            if configure_type == 'configure':
                print('configure_file('
                      + nl_indent + to_cmake_datatype(target_relative_path(configure['input'], name)) + ' '
                      + nl_indent + to_cmake_datatype(target_relative_path(conf_name, name)) + ')')
            elif configure_type == 'generate':
                print('file(GENERATE'
                      + (nl_indent + 'OUTPUT ' + to_cmake_datatype(target_relative_path(conf_name, name)))
                      + (nl_indent + 'CONTENT ' + to_cmake_datatype(configure['content']) if 'content' in configure else '')
                      + (nl_indent + 'INPUT ' + to_cmake_datatype((target_relative_path(configure['input'], name))) if 'input' in configure else '')
                      + (nl_indent + 'CONDITION  ' + configure['condition'] if 'condition' in configure else '')
                      + ')')
            else:
                raise RuntimeError("Unsupported configure type!")

        if len(configures) != 0:
            print()

    target_infos = dep_info["target"]
    if isinstance(target_infos, dict):
        target_infos = [target_infos]

    for target_n, target_info in enumerate(target_infos):
        public_decl_type = "PUBLIC"

        target_name = name
        if 'name' in target_info:
            target_name = name + '.' + target_info['name']
        target_type = target_info["type"]

        if target_type == "static":
            srcs = enumerate_srcs(name, target_name, srcs=target_info["srcs"])
            print("add_library(" + target_name + " STATIC EXCLUDE_FROM_ALL" + nl_indent + srcs + ")")
        if target_type == "shared":
            srcs = enumerate_srcs(name, target_name, srcs=target_info["srcs"])
            print("add_library(" + target_name + " SHARED EXCLUDE_FROM_ALL" + nl_indent + srcs + ")")
        if target_type == "object":
            srcs = enumerate_srcs(name, target_name, srcs=target_info["srcs"])
            print("add_library(" + target_name + " OBJECT" + nl_indent + srcs + ")")
        elif target_type == "interface":
            print("add_library(" + target_name + " INTERFACE)")
            public_decl_type = "INTERFACE"
        elif target_type == "imported":
            print("add_library(" + target_name + " UNKNOWN IMPORTED)")
            public_decl_type = "INTERFACE"
        elif target_type == "subdirectory":
            if "cache" in target_info:
                for (var_name, value) in target_info["cache"].items():
                    if isinstance(value, bool):
                        print("set(" + var_name + " " + ("ON" if value else "OFF") + " CACHE INTERNAL \"\" FORCE)")
            print("add_subdirectory(${" + target_name + "_SOURCE_DIR} ${" + target_name + "_BINARY_DIR})")
        elif target_type == "cmake":
            print("include(${PROJECT_SOURCE_DIR}/" + target_info["file"] + ")")

        if target_type in ["static", "interface", "object"]:
            generate_target_definition(
                name, target_name,
                public_decl_type=public_decl_type,
                target_info=target_info,
                src_dir=src_dir)

        if target_n != len(target_infos) - 1:
            print()

    done_nl = False
    def do_nl():
        global done_nl
        if not done_nl:
            print()
            done_nl = True

    if "aliases" in dep_info:
        do_nl()
        for (tgt, src) in dep_info["aliases"].items():
            print("add_library(" + tgt + " ALIAS " + src + ")")

    if "extra_cmake" in dep_info:
        do_nl()
        extra_cmakes = dep_info["extra_cmake"]
        if isinstance(extra_cmakes, str):
            extra_cmakes = [extra_cmakes]
        for extra_cmake in extra_cmakes:
            extra_cmake = target_relative_path(extra_cmake, name)
            print("include(" + extra_cmake + ")")

    print()
