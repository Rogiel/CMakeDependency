# CMakeDependency

A little and lightweight CMake helper tool that automatically downloads, extracts and configures dependencies based on a declaration on a .json file.

## Getting started

First you need to declare a dependency in your `dependencies.json` file:

```json
{
  "JSON": {
    "url": [
      "https://github.com/nlohmann/json/releases/download/v3.7.0/include.zip"
    ],
    "download_name": "json-3.7.0.zip",
    "target": {
      "type": "interface",
      "includes": "."
    }
  }
}
```

In your CMakeLists.txt all you need is to include the module and import all dependencies from your JSON file:

```cmake
# Include the CMakeDependency module
include(CMakeDependency/CMakeDependency.cmake)

# Import dependencies from JSON
import_dependencies_from_json(${PROJECT_SOURCE_DIR}/dependencies.json)
```

You are done! `JSON` is now available as a target in CMake!

```cmake
target_link_libraries(MyTarget PUBLIC JSON)
```

Note that CMakeDependency will create a file called `CMakeLists.deps.txt` in `CMAKE_CURRENT_SOURCE_DIR`. This file contains the preprocessed JSON file that is included by CMake. You can commit this file into your repository if you don't want to depend on Python 3 when compiling.

## Dependencies

This CMake module requires **CMake 3.15** and up. **Python3** is required if you want to automatically generate the CMake dependencies from the JSON file.

## Declaring dependencies manually in CMake

You don't have to use the JSON file if you don't want to. You can import dependencies directly in CMake by calling `import_dependency`:

```cmake
import_dependency(JSON
        URL              https://github.com/nlohmann/json/releases/download/v3.7.0/include.zip
        DOWNLOAD_NAME    json-3.7.0.zip)
```

Note that `DOWNLOAD_NAME` is optional. If not given, CMakeDependency will resolve a name based on the given `URL`.

In this mode, no target is created but the ZIP file is downloaded and extracted. The extracted contents are in `JSON_SOURCE_DIR`. If this library is a CMake library, you can simply call `add_subdirectory` and be done with it.

```cmake
add_subdirectory(${JSON_SOURCE_DIR} ${JSON_BINARY_DIR})
```

or if the dependency is **NOT** a CMake project, you can manually create a target:

```cmake
add_library(JSON INTERFACE)
target_include_directories(JSON INTERFACE ${JSON_SOURCE_DIR})
```

## Overriding a dependency

If you don't want to duplicate your dependencies across multiple projects you can override the dependency source dir by setting `JSON_DIR` cache variable. You can do so when invoking CMake:

```shell script
cmake -DJSON_DIR="/my/json/lib" [...]
```

or from within CMake itself, before calling `import_dependency` or `import_dependencies_from_json`:

```cmake
set(JSON_DIR "/my/json/lib" CACHE PATH "" FORCE)
```

Node that when setting `JSON_DIR`, if the dependency is not downloaded it will be downloaded and imported to the given directory. If this is not something you want, for example, you want to use a system provided dependency, you can override the directory by setting `JSON_SOURCE_DIR`.

Additionally, you can override just the zip file by setting `JSON_ZIP`.

## `dependencies.json` by example

### [Boost](https://www.boost.org/)

This example downloads the Boost source zip and configures it by building the `system` library.

```json
{
  "Boost": {
    "url": [
      "https://dl.bintray.com/boostorg/release/1.71.0/source/boost_1_71_0.zip"
    ],
    "target": {
      "type": "static",
      "srcs": [
        "libs/system/src/error_code.cpp"
      ],
      "includes": ".",
      "defines": [
        "BOOST_ALL_NO_LIB",
        "BOOST_ASIO_NO_TYPEID"
      ],
      "links": [
        "$<$<PLATFORM_ID:Windows>:bcrypt.dll>"
      ]
    }
  }
}
```

### [Catch2](https://github.com/catchorg/Catch2)

This example will download and configure the Catch testing framework for compilation. Note that the `configure` directive is used to create a `.cpp` file for the runner and also note that the path is prefixed with `:`, this means that the generation will take place into a subdirectory in `${CMAKE_CURRENT_BINARY_DIR}`.

Additionally, two `extra_cmake` paths are given to be included by CMake after the target is configured.

```json
{
  "Catch2": {
    "git": {
      "repository": "https://github.com/catchorg/Catch2.git",
      "tag": "c8db4e77c4c9aa20776db162e982f1af693ab8fe"
    },
    "configure": {
      ":catch2.cpp": {
        "type": "generate",
        "content": "#include \"catch.hpp\""
      }
    },
    "target": [
      {
        "type": "interface",
        "includes": "single_include/catch2",
        "defines": [
          "CATCH_CONFIG_NO_CPP17_UNCAUGHT_EXCEPTIONS",
          "CATCH_CONFIG_ENABLE_BENCHMARKING"
        ],
        "public_defines": {
          "CATCH_CONFIG_CONSOLE_WIDTH": 300
        }
      },
      {
        "type": "object",
        "name": "Runner",
        "srcs": ":catch2.cpp",
        "private_defines": [
          "CATCH_CONFIG_MAIN"
        ],
        "links": "Catch2"
      }
    ],
    "extra_cmake": [
      "contrib/Catch.cmake",
      "contrib/ParseAndAddCatchTests.cmake"
    ]
  }
}
```

### [Naios/continuable](https://github.com/Naios/continuable)

This will [Naios/continuable](https://github.com/Naios/continuable) and it's dependency [Naios/function2](https://github.com/Naios/function2) create both targets as a CMake interface library and link `Function2` into `Continuable`. As a consumer, you can simply link against `Continuabe` and CMake will add `Function2` transitively fot you.

```json
{
  "Continuable": {
    "git": {
      "repository": "https://github.com/Naios/continuable.git",
      "tag": "cacb84371a5e486567b4aed244ce742ea6509d7d"
    },
    "target": {
      "type": "interface",
      "includes": "include",
      "links": "Function2"
    }
  },
  "Function2": {
    "git": {
      "repository": "https://github.com/Naios/function2.git",
      "tag": "7cd95374b0f1c941892bfc40f0ebb6564d33fdb9"
    },
    "target": {
      "type": "interface",
      "includes": "include"
    }
  }
}
```

### [Rogiel/PacketBuffer](https://github.com/Rogiel/PacketBuffer)

This will download [Rogiel/PacketBuffer](https://github.com/Rogiel/PacketBuffer) and import it by using CMake's `add_subdirectory` command.

```json
{
  "PacketBuffer": {
    "git": {
      "repository": "https://github.com/Rogiel/PacketBuffer.git",
      "tag": "37e76659eaf4ed7d4407d1ccc5e31dee5454ef2c"
    },
    "target": {
      "type": "subdirectory"
    }
  }
}
```

### [Poco](https://pocoproject.org/)

This example will download the Poco library and include `/Poco.cmake` for further configuration. You can use `Poco_SOURCE_DIR` and `Poco_BINARY_DIR` if needed to configure your target. Note that the file is an absolute paht (starting with `/`). This means that CMakeDependency will include this dependency from `${PROJECT_SOURCE_DIR}`.

This allows very flexible build configuration for dependencies.

```json
{
  "Poco": {
    "url": [
      "https://pocoproject.org/releases/poco-1.9.4/poco-1.9.4.zip"
    ],
    "target": {
      "type": "cmake",
      "file": "/Poco.cmake"
    }
  }
}
```

### [STB Image](https://github.com/nothings/stb)

This example will download and configure STB Image for compilation. Note that the `configure` directive is used to create a `.c` file for compilation. Also note that the path is prefixed with `:`, this means that the generation will take place into a subdirectory in `${CMAKE_CURRENT_BINARY_DIR}`.

```json
{
  "STB": {
    "git": {
      "repository": "https://github.com/nothings/stb.git",
      "tag": "052dce117ed989848a950308bd99eef55525dfb1"
    },
    "configure": {
      ":stb_image.c": {
        "type": "generate",
        "content": "#include <stb_image.h>"
      }
    },
    "target": [
      {
        "type": "static",
        "name": "Image",
        "srcs": ":stb_image.c",
        "private_defines": [
          "STB_IMAGE_IMPLEMENTATION"
        ],
        "includes": "."
      }
    ]
  }
}
```

## Advanced features

### Global cache variables
 - **`CMDEP_ROOT_DIR`**: A path that points to the location in which CMake dependency files should be downloaded and extracted to. Defaults to `${CMAKE_CURRENT_SOURCE_DIR}`.
 - **`CMDEP_ZIP_DIR`**: A path that points to the location in which ZIP files should be downloaded to. Defaults to `${CMDEP_ROOT_DIR}/zips`.
 
### Dependency cache variables
 - **`<name>_URL`**: A path that points to a URL to be downloaded. CMake will use this URL to download the file if needed. Defaults to the value given in `import_dependency`.
 - **`<name>_DIR`**: A path that points to a directory containing the dependency sources. Defaults to `${CMDEP_ROOT_DIR}/<name>`.
 - **`<name>_SOURCE_DIR`**: A path that points to a source directory. If manually set, no downloading or extraction will take place and this will be used instead. Defaults to `${<name>_DIR}`.
 - **`<name>_ZIP`**: A path that points to a zip file. If this file does not exists, it will be downloaded. You can use this to override the download and point to an already existing ZIP file. Defaults to `${CMDEP_ZIP_DIR}/<file name>.zip`.
 
## Concurrency with CMake

Some IDEs, such as CLion, use multiple CMake invocations for each configuration. This could cause problems when downloading dependencies to a common location. To avoid such problems, `CMakeDependency` uses CMake's advisory locking mechanism to prevent multiple CMake instances from downloading the same file.

This lock is acquired in the `CMDEP_ROOT_DIR` directory. Beware that CMake will create a `cmake.lock` file in this directory and you should exclude it from your source control if needed.

## TODO

 - Improve documentation on `dependencies.json` syntax.
