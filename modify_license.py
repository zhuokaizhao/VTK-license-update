import os
import sys
import codecs
import functools
import argparse
import fileinput
import numpy as np
from time import sleep

def get_file_paths(root_dir, verbose):
    all_paths = []
    additional_paths = []
    for path in os.scandir(root_dir):
        # skip third party folder
        if path.name == 'ThirdParty':
            print(path.name + ' has been skipped.')
            continue

        full_path = root_dir + os.sep + path.name
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
    start_sign = None
    stop_sign = None
    result = []

    for cur_line in fileinput.input(file_path, inplace=1):
        for i in range(len(all_start_signs)):
            if (start == 0) and (all_start_signs[i] in cur_line):
                start = 1
                start_sign = cur_line
                stop_sign = None
                sys.stdout.write('')
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
            sys.stdout.write('')
        else:
            if just_change:
                sys.stdout.write('')
                just_change = 0
            else:
                sys.stdout.write(cur_line)

    if not result:
        result.append('No license information found')

    # return the unique collection
    return set(result)


def modify_file(file_path, license_info):
    if license_info[0] == 'No license information found':
        print('Warning:', file_path, 'does not have a valid license info detected.')
        return

    # start = 0
    modified = 0
    license_num = None
    for cur_line in fileinput.input(file_path, inplace=1):
        if not modified:
            for i in range(len(license_info)):
                sys.stdout.write(license_info[i][0])
                if '//====' in license_info[i][0]:
                    sys.stdout.write('// Plese check ' + license_info[i][1] + '_license.txt for license information.\n')
                    sys.stdout.write(license_info[i][0])
                else:
                    sys.stdout.write('Plese check ' + license_info[i][1] + '_license.txt for license information.')
                    sys.stdout.write(license_info[i][0][::-1] + '\n')

            modified = 1

        sys.stdout.write(cur_line)

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
        # print(cur_path)
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
