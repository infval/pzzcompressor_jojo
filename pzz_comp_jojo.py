#!/usr/bin/env python3
__version__ = "1.0.1"
__author__  = "infval"

from pathlib import Path
from struct import unpack


def pzz_decompress(b):
    bout = bytearray()
    size_b = len(b) // 2 * 2

    cb = 0  # Control bytes
    cb_bit = -1
    i = 0
    while i < size_b:
        if cb_bit < 0:
            cb  = b[i + 0]
            cb |= b[i + 1] << 8
            cb_bit = 15
            i += 2
            continue

        compress_flag = cb & (1 << cb_bit)
        cb_bit -= 1

        if compress_flag:
            c  = b[i + 0]
            c |= b[i + 1] << 8
            offset = (c & 0x7FF) * 2
            if offset == 0:
                break # End of the compressed data
            count = (c >> 11) * 2
            if count == 0:
                i += 2
                c  = b[i + 0]
                c |= b[i + 1] << 8
                count = c * 2

            index = len(bout) - offset
            for j in range(count):
                bout.append(bout[index + j])
        else:
            bout.extend(b[i: i + 2])
        i += 2

    return bout


def pzz_compress(b):
    bout = bytearray()
    size_b = len(b) // 2 * 2

    cb = 0  # Control bytes
    cb_bit = 15
    cb_pos = 0
    bout.extend(b"\x00\x00")

    i = 0
    while i < size_b:
        start = max(i - 0x7FF * 2, 0)
        count_r = 0
        max_i = -1
        tmp = b[i: i + 2]
        init_count = len(tmp)
        while True:
            start = b.find(tmp, start, i + 1)
            if start != -1 and start % 2 != 0:
                start += 1
                continue
            if start != -1:
                count = init_count
                while i < size_b - count \
                    and count < 0xFFFF * 2 \
                    and b[start + count    ] == b[i + count    ] \
                    and b[start + count + 1] == b[i + count + 1]:
                    count += 2
                if count_r < count:
                    count_r = count
                    max_i = start
                start += 2
            else:
                break
        start = max_i

        compress_flag = 0
        if count_r >= 4:
            compress_flag = 1
            offset = i - start
            offset //= 2
            count_r //= 2
            c = offset
            if count_r <= 0x1F:
                c |= count_r << 11
                bout.append(c & 0xFF)
                bout.append((c >> 8))
            else:
                bout.append(c & 0xFF)
                bout.append((c >> 8))
                bout.append(count_r & 0xFF)
                bout.append((count_r >> 8))
            i += count_r * 2
        else:
            bout.extend(b[i: i + 2])
            i += 2
        cb |= (compress_flag << cb_bit)
        cb_bit -= 1
        if cb_bit < 0:
            bout[cb_pos + 0] = cb & 0xFF
            bout[cb_pos + 1] = cb >> 8
            cb = 0x0000
            cb_bit = 15
            cb_pos = len(bout)
            bout.extend(b"\x00\x00")

    cb |= (1 << cb_bit)
    bout[cb_pos + 0] = cb & 0xFF
    bout[cb_pos + 1] = cb >> 8
    bout.extend(b"\x00\x00")

    return bout


def pzz_unpack(path, dir_path):
    """ BMS script: https://zenhax.com/viewtopic.php?f=9&t=8724&p=39437#p39437
    """
    with open(path, "rb") as f:
        file_count = f.read(4)
        file_count, = unpack("<I", file_count)
        size = f.read(file_count * 4)
        size = unpack("<{}I".format(file_count), size)

        print("File count:", file_count)

        offset = 0x800
        for i, s in enumerate(size):
            is_compressed = (s & 0x80000000) != 0
            s &= 0x7FFFFFFF
            s *= 0x800
            if s == 0:
                continue
            comp_str = ""
            if is_compressed:
                comp_str = "_compressed"
            filename = "{}_{:03}{}".format(Path(path).stem, i, comp_str)
            p = (Path(dir_path) / filename).with_suffix(".dat")

            print("Offset: {:010} - {}".format(offset, p))

            f.seek(offset)
            p.write_bytes(f.read(s))
            offset += s


def get_argparser():
    import argparse
    parser = argparse.ArgumentParser(description='PZZ (de)compressor & unpacker - [PS2] GioGio’s Bizarre Adventure / JoJo no Kimyō na Bōken: Ōgon no Kaze || v' + __version__)
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('input_path', metavar='INPUT', help='only relative if -bu, -bc, -bd')
    parser.add_argument('output_path', metavar='OUTPUT', help='directory if -u, -bu, -bc, -bd')
    group = parser.add_mutually_exclusive_group(required=True)
    #group.add_argument('-p', '--pack', action='store_true')
    group.add_argument('-u', '--unpack', action='store_true', help='PZZ files from AFS')
    group.add_argument('-c', '--compress', action='store_true')
    group.add_argument('-d', '--decompress', action='store_true', help='Unpacked files from PZZ')
    #group.add_argument('-bp', '--batch-pack', action='store_true')
    group.add_argument('-bu', '--batch-unpack', action='store_true', help='INPUT relative pattern; e.g. AFS_DATA\\*.pzz')
    group.add_argument('-bc', '--batch-compress', action='store_true', help='INPUT relative pattern; e.g. AFS_DATA\\*.bin')
    group.add_argument('-bd', '--batch-decompress', action='store_true', help='INPUT relative pattern; e.g. AFS_DATA\\*_compressed.dat')
    return parser


if __name__ == '__main__':
    import sys
    parser = get_argparser()
    args = parser.parse_args()

    p_input = Path(args.input_path)
    p_output = Path(args.output_path)
    if args.compress:
        print("### Compress")
        p_output.write_bytes(pzz_compress(p_input.read_bytes()))
    elif args.decompress:
        print("### Decompress")
        p_output.write_bytes(pzz_decompress(p_input.read_bytes()))
    elif args.batch_compress:
        print("### Batch Compress")
        p_output.mkdir(exist_ok=True)

        p = Path('.')
        for filename in p.glob(args.input_path):
            print(filename)
            b = filename.read_bytes()
            (p_output / filename.name).with_suffix(".dat").write_bytes(pzz_compress(b))
    elif args.batch_decompress:
        print("### Batch Decompress")
        p_output.mkdir(exist_ok=True)

        p = Path('.')
        for filename in p.glob(args.input_path):
            print(filename)
            try:
                b = filename.read_bytes()
                (p_output / filename.name).with_suffix(".bin").write_bytes(pzz_decompress(b))
            except IndexError:
                print("! Wrong PZZ file")
    #elif args.pack:
    #    pass
    elif args.unpack:
        print("### Unpack")
        p_output.mkdir(exist_ok=True)
        pzz_unpack(p_input, p_output)
    #elif args.batch_pack:
    #    pass
    elif args.batch_unpack:
        print("### Batch Unpack")
        p_output.mkdir(exist_ok=True)

        p = Path('.')
        for filename in p.glob(args.input_path):
            print(filename)
            pzz_unpack(filename, p_output)

