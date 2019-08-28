import argparse
import os
import fileinput
import sys

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

def replace_file(file_path, new_content):
    start = 0
    for cur_line in fileinput.input(file_path, inplace=1):
        # check if we are in the range
        if '/*====' in cur_line:
            sys.stdout.write(cur_line)
            start = 1
        elif '====*/' in cur_line:
            start = 0
            sys.stdout.write(new_content[0])
        elif '/*----' in cur_line:
            sys.stdout.write(cur_line)
            start = 1
        elif '----*/' in cur_line:
            start = 0
            sys.stdout.write(new_content[1])

        if start:
            sys.stdout.write('')
        else:
            sys.stdout.write(cur_line)

def main(args):
    verbose = int(args.verbose)

    # get all the eligible file paths
    file_count = 0
    all_file_paths = get_file_paths(args.path, verbose)
    file_count = len(all_file_paths)
    print(file_count, " eligible files have been found")

    # change all the files accordingly
    new_content = ['New license information 1\n',
                    'New license information 2\n']
    for cur_path in all_file_paths:
        replace_file(cur_path, new_content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Change and replace the license information in VTK or paraview source folders.'
    )
    parser.add_argument('path', help='path that includes the source fiels')
    parser.add_argument('verbose', help='extra print outs')
    args = parser.parse_args()

    main(args)
