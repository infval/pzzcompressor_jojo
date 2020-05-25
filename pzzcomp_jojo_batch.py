#!/usr/bin/env python3
import argparse
from pathlib import Path
from os import system

parser = argparse.ArgumentParser(description='pzzcomp_jojo helper')
parser.add_argument('input_pattern', metavar='INPUT', help='relative pattern; e.g. AFS_DATA\\*_compressed.dat')
parser.add_argument('output_dir', metavar='OUTPUT', help='directory')
parser.add_argument('-e', '--extension', metavar='EXT', help='output; .bin, .dat, .pzz, etc')
parser.add_argument('-y', '--yes', action='store_true', help='overwrite')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-c', '--compress', action='store_true')
group.add_argument('-d', '--decompress', action='store_true')
args = parser.parse_args()

p_output = Path(args.output_dir)
p_output.mkdir(exist_ok=True)

for path in Path('.').glob(args.input_pattern):
    print(path)

    if args.extension:
        ext = args.extension
    elif args.compress:
        ext = ".dat"
    else:
        ext = ".bin"
    other_path = (p_output / path.name).with_suffix(ext)

    if other_path.exists() and not args.yes:
        answer = input("File '{}' already exists. Overwrite ? [y/N]".format(other_path))
        if answer.strip().lower() != 'y':
            continue
    
    print(">", other_path)
    if args.compress:
        system(r'pzzcomp_jojo -c "{}" "{}"'.format(path, other_path))
    elif args.decompress:
        system(r'pzzcomp_jojo -d "{}" "{}"'.format(path, other_path))
