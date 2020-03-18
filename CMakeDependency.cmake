# CMake dependency: this is a little and lightweight helper tool that
# automatically downloads, extracts and configures dependencies based on a
# declaration on a .json file.
#
# To manually add a dependency, call `import_dependency(<name> URL <url>). After
# this call, CMake will have downloaded and extracted the dependency source. The
# extracted files are located at `${<name>_SOURCE_DIR}`.
#
# Also, it is possible to import a dependency JSON file by calling
# `import_dependencies_from_json(<json file>)`. All dependencies are
# automatically configured as declared in the JSON file. CMake will also
# regenerate any configuration needed if the JSON is ever changed.

set(CMDEP_GENERATOR_SCRIPT        ${CMAKE_CURRENT_LIST_DIR}/DependencyGenerator.py)
set(CMDEP_DEPENDENCY_DECL_TMPL    ${CMAKE_CURRENT_LIST_DIR}/DependencyDeclaration.cmake.in)

set(CMDEP_ROOT_DIR
        ${CMAKE_CURRENT_SOURCE_DIR}
        CACHE PATH "A path that points to the location in which CMake dependency files should be downloaded and extracted to.")
set(CMDEP_ZIP_DIR
        ${CMDEP_ROOT_DIR}/zips
        CACHE PATH "A path that points to the location in which ZIP files should be downloaded to.")

function(import_dependency name)
    set(options)
    set(oneValueArgs URL DOWNLOAD_NAME)
    set(multiValueArgs)
    cmake_parse_arguments(DEPENDENCY "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN} )
    cmake_parse_arguments(${name} "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN} )
    
    set(DEPENDENCY_NAME ${name})
    
    configure_file(${CMDEP_DEPENDENCY_DECL_TMPL} ${CMAKE_CURRENT_BINARY_DIR}/${name}.dep.cmake @ONLY)
    
    include(${CMAKE_CURRENT_BINARY_DIR}/${name}.dep.cmake)
endfunction()

function(import_dependencies_from_json json)
    set(json_dep_file   ${json})
    set(cmake_dep_file  ${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.deps.txt)

    find_package(Python3 COMPONENTS Interpreter)
    if(Python3_Interpreter_FOUND)
        file(LOCK ${CMAKE_CURRENT_SOURCE_DIR} DIRECTORY GUARD FILE)
        if(${json_dep_file}          IS_NEWER_THAN ${cmake_dep_file} OR
           ${CMDEP_GENERATOR_SCRIPT} IS_NEWER_THAN ${cmake_dep_file})
            execute_process(
                    COMMAND ${Python3_EXECUTABLE} ${CMDEP_GENERATOR_SCRIPT}
                    INPUT_FILE  ${json_dep_file}
                    OUTPUT_FILE ${cmake_dep_file})
        endif()
        file(LOCK ${CMAKE_CURRENT_SOURCE_DIR} DIRECTORY RELEASE)
    else()
        message(STATUS "Python interpreter not found. CMake dependencies will NOT update automatically.")
    endif()
    include(${cmake_dep_file})

    list(APPEND CMAKE_CONFIGURE_DEPENDS ${json_dep_file})
endfunction()

list(APPEND CMAKE_CONFIGURE_DEPENDS ${CMDEP_GENERATOR_SCRIPT})
