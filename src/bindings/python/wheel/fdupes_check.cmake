# Copyright (C) 2018-2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

foreach(var PYTHON_EXECUTABLE WORKING_DIRECTORY REPORT_FILE WHEEL_VERSION PACKAGE_FILE CMAKE_SHARED_LIBRARY_SUFFIX)
    if(NOT DEFINED ${var})
        message(FATAL_ERROR "Variable ${var} is not defined")
    endif()
endforeach()

# find programs

find_program(fdupes_PROGRAM NAMES fdupes DOC "Path to fdupes")
if(NOT fdupes_PROGRAM)
    message(WARNING "Failed to find 'fdupes' tool, use 'sudo apt-get install fdupes' to install it")
    return()
endif()

# execute

get_filename_component(wheel_name "${PACKAGE_FILE}" NAME)

execute_process(COMMAND ${PYTHON_EXECUTABLE} -m wheel unpack ${PACKAGE_FILE}
                WORKING_DIRECTORY ${WORKING_DIRECTORY}
                OUTPUT_VARIABLE output_message
                ERROR_VARIABLE error_message
                RESULT_VARIABLE exit_code
                OUTPUT_STRIP_TRAILING_WHITESPACE)

if(NOT exit_code EQUAL 0)
    message(FATAL_ERROR "Failed to unpack wheel package")
endif()

set(WORKING_DIRECTORY "${WORKING_DIRECTORY}/openvino-${WHEEL_VERSION}")
if(NOT EXISTS "${WORKING_DIRECTORY}")
    message(FATAL_ERROR "Failed to find ${WORKING_DIRECTORY}")
endif()

execute_process(COMMAND ${fdupes_PROGRAM} -f -r "${WORKING_DIRECTORY}"
                OUTPUT_VARIABLE duplicated_files
                ERROR_VARIABLE error_message
                RESULT_VARIABLE exit_code
                OUTPUT_STRIP_TRAILING_WHITESPACE)

# remove unpacked directory
file(REMOVE_RECURSE "${WORKING_DIRECTORY}")

# filtering of 'duplicated_files'

foreach(duplicated_file IN LISTS duplicated_files)
    if(duplicated_file MATCHES ".*${CMAKE_SHARED_LIBRARY_SUFFIX}.*")
        set(duplicated_libraries "${duplicated_file}\n${duplicated_libraries}")
    endif()
endforeach()

# write output

file(WRITE "${REPORT_FILE}" "${duplicated_libraries}")

if(duplicated_libraries)
    message(FATAL_ERROR "${duplicated_libraries}")
endif()
