import os
import io
import sys
import codecs
import functools
import argparse
import fileinput
import numpy as np
from time import sleep

def inplace(orig_path, encoding='utf-8', error='ignore'):
    new_path = orig_path + '.modified'
    with codecs.open(orig_path, encoding=encoding, errors=error) as orig, \
        codecs.open(new_path, 'w', encoding=encoding, errors=error) as new:

        for line in orig:
            yield line, new

    os.rename(new_path, orig_path)

def get_file_paths(root_dir, verbose):
    all_paths = []
    additional_paths = []
    for path in os.scandir(root_dir):
        # # skip these directories
        full_path = root_dir + os.sep + path.name

        if 'Utilities/MetaIO' in full_path \
            or 'Utilities/KWSys' in full_path \
            or 'Utilities/KWIML' in full_path \
            or 'ThirdParty/' in full_path:

            print(path.name + ' directory has been skipped.')
            continue

        if path.is_file():
            if path.name.endswith('.cxx') or path.name.endswith('.h') or path.name.endswith('.cpp'):
                if verbose == 1:
                    print(full_path)
                all_paths.append(full_path)
        else:
            additional_paths += get_file_paths(full_path, verbose)

    return all_paths + additional_paths

def analyze_file(file_path, all_start_signs, all_stop_signs, all_possible_holders):
    # check if file is empty
    if os.stat(file_path).st_size == 0:
        print('Warning: ' + file_path + ' is empty.')
        result = []
        result.append('No license information found')
        return result

    start = 0
    just_change = 0
    finished = 0
    start_sign = None
    stop_sign = None
    result = []
    # for cur_line in fileinput.input(file_path, inplace=1):
    for cur_line, new_file in inplace(file_path):
        # when we see include starts, license stuff is done
        if '#include' in cur_line:
            finished = 1

        if finished:
            new_file.write(cur_line)
            continue

        for i in range(len(all_start_signs)):
            if (start == 0) and (all_start_signs[i] in cur_line):
                start = 1
                start_sign = cur_line
                stop_sign = None
                new_file.write('')
                break
            elif (start == 1) and (all_stop_signs[i] in cur_line):
                start = 0
                start_sign = None
                stop_sign = cur_line
                just_change = 1
                break

        if start:
            # check which organization is responsible for the license
            for i in range(len(all_possible_holders)):
                if all_possible_holders[i] in cur_line.lower():
                    result.append((start_sign, all_possible_holders[i], stop_sign))
            new_file.write('')
        else:
            if just_change:
                new_file.write('')
                just_change = 0
            else:
                new_file.write(cur_line)

    if not result:
        result.append('No license information found')

    # return the unique collection
    return set(result)


def modify_file(file_path, license_info):
    if license_info[0] == 'No license information found':
        print('Warning:', file_path, 'does not have a valid license info detected.')
        return

    modified = 0
    start = '/*===========================================================================*/\n'
    start += '/* Distributed under OSI-approved BSD 3-Clause License.                      */\n'
    start += '/* For copyright, see the following accompanying files or https://vtk.org:   */\n'

    end = '/*===========================================================================*/\n'
    # for cur_line in fileinput.input(file_path, inplace=1):
    for cur_line, new_file in inplace(file_path):
        if not modified:
            new_file.write(start)
            for i in range(len(license_info)):
                if license_info[i][1] == 'kitware':
                    new_file.write('/* - VTK-Copyright.txt                                                       */\n')
                if license_info[i][1] == 'sandia':
                    new_file.write('/* - Sandia-Copyright.txt                                                    */\n')

            new_file.write(end)
            modified = 1

        new_file.write(cur_line)

def main(args):
    verbose = int(args.verbose)

    # get all the eligible file paths
    print('Finding all eligible files')
    file_count = 0
    all_file_paths = get_file_paths(args.path, verbose)
    file_count = len(all_file_paths)
    print(file_count, "eligible files have been found")

    # analyze the license information
    all_licenses_results = []
    all_start_signs = ['/*====', '/*----', '//====', '/*\n']
    all_stop_signs = ['====*/', '----*/', '//====', '*/']
    # start and stop signs need to be the same sized
    if (len(all_start_signs) != len(all_stop_signs)):
        print('Error: start and stop signs need to be the same sized')

    all_possible_holders = ['kitware', 'sandia']
    for cur_path in all_file_paths:
        license_result = analyze_file(cur_path, all_start_signs, all_stop_signs, all_possible_holders)
        all_licenses_results.append(license_result)

    if verbose:
        print('All possible holders are:', all_possible_holders)
        print('License information with order corresponding to above files are')
        for result in all_licenses_results:
            print(result)

    # modify the files accordingly
    print('Modifying all the eligible files')
    for i in range(len(all_file_paths)):
        percent = float((i+1)/len(all_file_paths))
        sys.stdout.write('\r')
        license_info = list(all_licenses_results[i])
        modify_file(all_file_paths[i], license_info)
        sys.stdout.write('[%-40s] %d%%' % ('='*int(percent*40), 100*percent))
        sys.stdout.flush()
        sleep(0.05)

    sys.stdout.write('\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Change and replace the license information in VTK or paraview source folders.'
    )
    parser.add_argument('path', help='path that includes the source fiels')
    parser.add_argument('verbose', help='extra print outs')
    args = parser.parse_args()

    main(args)
