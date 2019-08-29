import argparse
import os
import fileinput
import sys
import numpy as np

def get_file_paths(root_dir, verbose):
    all_paths = []
    additional_paths = []
    for path in os.scandir(root_dir):
        full_path = root_dir + os.sep + path.name
        if path.is_file():
            if path.name.endswith('.cxx') or path.name.endswith('.h') or path.name.endswith('.cpp'):
                if verbose == 1:
                    print(full_path)
                all_paths.append(full_path)
        else:
            additional_paths += get_file_paths(full_path, verbose)

    return all_paths + additional_paths

def analyze_file(file_path, all_signs, all_possible_holders):
    start = 0
    sign = None
    result = []
    for cur_line in fileinput.input(file_path, inplace=1):
        for i in range(len(all_signs)):
            if all_signs[i] in cur_line:
                start = 1
                sign = all_signs[i]
                sys.stdout.write(cur_line)
            elif all_signs[i][::-1] in cur_line:
                start = 0
                sign = None

        if start:
            # check which organization is responsible for the license
            for i in range(len(all_possible_holders)):
                if all_possible_holders[i] in cur_line.lower():
                    result.append((sign, all_possible_holders[i]))
            sys.stdout.write('')
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

    start = 0
    license_num = None
    for cur_line in fileinput.input(file_path, inplace=1):
        for i in range(len(license_info)):
            if license_info[i][0] in cur_line:
                start = 1
                license_num = i
                sys.stdout.write(cur_line)
            elif license_info[i][0][::-1] in cur_line:
                start = 0

        if start:
            sys.stdout.write(license_info[license_num][1] + ' license' + '\n')
        else:
            sys.stdout.write(cur_line)

def main(args):
    verbose = int(args.verbose)

    # get all the eligible file paths
    file_count = 0
    all_file_paths = get_file_paths(args.path, verbose)
    file_count = len(all_file_paths)
    print(file_count, " eligible files have been found")

    # analyze the license information
    all_licenses_results = []
    all_signs = ['/*====', '/*----']
    all_possible_holders = ['kitware', 'sandia']
    for cur_path in all_file_paths:
        license_result = analyze_file(cur_path, all_signs, all_possible_holders)
        all_licenses_results.append(license_result)

    if verbose:
        print('All possible holders are:', all_possible_holders)
        print('License information with order corresponding to above files are')
        for result in all_licenses_results:
            print(result)

    # modify the files accordingly
    for i in range(len(all_file_paths)):
        license_info = list(all_licenses_results[i])
        modify_file(all_file_paths[i], license_info)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Change and replace the license information in VTK or paraview source folders.'
    )
    parser.add_argument('path', help='path that includes the source fiels')
    parser.add_argument('verbose', help='extra print outs')
    args = parser.parse_args()

    main(args)
