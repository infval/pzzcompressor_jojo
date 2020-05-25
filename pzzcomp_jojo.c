#define _CRT_SECURE_NO_WARNINGS

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <assert.h>

#define VERSION_STR "v1.0.0"

void   PZZ_Decompress(const uint8_t* src, uint8_t* dst, size_t src_len);
size_t PZZ_GetDecompressedSize(const uint8_t* src, size_t size);
size_t PZZ_Compress(const uint8_t* src, uint8_t* dst, size_t src_len);
size_t PZZ_GetCompressedMaxSize(size_t src_len);

void PZZ_Decompress(const uint8_t* src, uint8_t* dst, size_t src_len)
{
    size_t offset, count;
    size_t spos = 0, dpos = 0;
    uint16_t cb = 0;
    int8_t cb_bit = -1;

    src_len = src_len / 2 * 2;
    while (spos < src_len) {
        if (cb_bit < 0) {
            cb  = src[spos++] << 0;
            cb |= src[spos++] << 8;
            cb_bit = 15;
        }

        int compress_flag = cb & (1 << cb_bit);
        cb_bit--;

        if (compress_flag) {
            count  = src[spos++] << 0;
            count |= src[spos++] << 8;
            offset = (count & 0x7FF) * 2;
            if (offset == 0) {
                break; // End of the compressed data
            }
            count >>= 11;
            if (count == 0) {
                count  = src[spos++] << 0;
                count |= src[spos++] << 8;
            }
            count *= 2;
            for (size_t j = 0; j < count; j++) {
                dst[dpos] = dst[dpos - offset];
                dpos++;
            }
        }
        else {
            dst[dpos++] = src[spos++];
            dst[dpos++] = src[spos++];
        }
    }
}

size_t PZZ_GetDecompressedSize(const uint8_t* src, size_t src_len)
{
#define CHECK_SPOS if (spos >= src_len) return -1;
    size_t offset, count;
    size_t spos = 0, dpos = 0;
    uint16_t cb = 0;
    int8_t cb_bit = -1;

    src_len = src_len / 2 * 2;
    while (spos < src_len) {
        if (cb_bit < 0) {
            CHECK_SPOS
            cb  = src[spos++] << 0;
            CHECK_SPOS
            cb |= src[spos++] << 8;
            cb_bit = 15;
        }

        int compress_flag = cb & (1 << cb_bit);
        cb_bit--;

        if (compress_flag) {
            CHECK_SPOS
            count  = src[spos++] << 0;
            CHECK_SPOS
            count |= src[spos++] << 8;
            offset = (count & 0x7FF) * 2;
            if (offset == 0) {
                break; // End of the compressed data
            }
            count >>= 11;
            if (count == 0) {
                CHECK_SPOS
                count  = src[spos++] << 0;
                CHECK_SPOS
                count |= src[spos++] << 8;
            }
            count *= 2;
            if (dpos < offset) return -1;
            dpos += count;
        }
        else {
            CHECK_SPOS
            spos++;
            CHECK_SPOS
            spos++;
            dpos += 2;
        }
    }

    return dpos;
#undef CHECK_SPOS
}

size_t PZZ_GetCompressedMaxSize(size_t src_len)
{
    return (2 + 2)      // Last 0x0000
        + src_len       //
        + src_len / 16; // 0x0000 for every 32 bytes
}

size_t PZZ_Compress(const uint8_t* src, uint8_t* dst, size_t src_len)
{
    size_t spos = 0, dpos = 0;
    uint16_t cb = 0;
    int8_t cb_bit = 15;
    size_t cb_pos = 0;

    src_len = src_len / 2 * 2;

    dst[dpos++] = 0x00;
    dst[dpos++] = 0x00;
    while (spos < src_len) {
        size_t offset = 0;
        size_t length = 0;

        for (size_t i = (spos >= 0x7FF * 2 ? (intptr_t)spos - 0x7FF * 2 : 0); i < spos; i += 2) {
            if (src[i] == src[spos] && src[i + 1] == src[spos + 1]) {
                size_t cur_len = 0;
                do {
                    cur_len += 2;
                } while ((cur_len < 0xFFFF * 2)
                    && (spos + cur_len < src_len)
                    && src[i + cur_len] == src[spos + cur_len]
                    && src[i + 1 + cur_len] == src[spos + 1 + cur_len]);

                if (cur_len > length) {
                    offset = spos - i;
                    length = cur_len;
                    if (length >= 0xFFFF * 2) {
                        break;
                    }
                }
            }
        }

        uint16_t compress_flag = 0;
        if (length >= 4) {
            compress_flag = 1;
            offset /= 2;
            length /= 2;
            size_t c = offset;
            if (length <= 0x1F) {
                c |= length << 11;
                dst[dpos++] = c & 0xFF;
                dst[dpos++] = c >> 8;
            }
            else {
                dst[dpos++] = c & 0xFF;
                dst[dpos++] = c >> 8;
                dst[dpos++] = length & 0xFF;
                dst[dpos++] = length >> 8;
            }
            spos += length * 2;
        }
        else {
            dst[dpos++] = src[spos++];
            dst[dpos++] = src[spos++];
        }

        cb |= compress_flag << cb_bit;
        cb_bit--;

        if (cb_bit < 0) {
            dst[cb_pos + 0] = cb & 0xFF;
            dst[cb_pos + 1] = cb >> 8;
            cb = 0x0000;
            cb_bit = 15;
            cb_pos = dpos;
            dst[dpos++] = 0x00;
            dst[dpos++] = 0x00;
        }
    }

    cb |= 1 << cb_bit;
    dst[cb_pos + 0] = cb & 0xFF;
    dst[cb_pos + 1] = cb >> 8;
    dst[dpos++] = 0x00;
    dst[dpos++] = 0x00;

    return dpos;
}

// Max: 2 GB
long GetFileSize(FILE* file)
{
    fseek(file, 0, SEEK_END);
    long size = ftell(file);
    fseek(file, 0, SEEK_SET);
    return size;
}

int main(int argc, char* argv[])
{
    if (argc < 4) {
        printf("PZZ (de)compressor - [PS2] JoJo no Kimyou na Bouken - Ougon no Kaze || " VERSION_STR " by infval\n"
               "Usage: program.exe (-d | -c) INPUT OUTPUT\n"
               "-d - decompress, -c - compress");
        return 0;
    }

    FILE* finput = fopen(argv[2], "rb");
    if (finput == NULL) {
        fprintf(stderr, "Can't open: %s", argv[2]);
        return 1;
    }
    size_t size = GetFileSize(finput);
    uint8_t* source = (uint8_t*)malloc(size);
    if (source == NULL) {
        fprintf(stderr, "Error: malloc()");
        return 2;
    }
    size_t readBytes = fread(source, 1, size, finput);
    if (readBytes != size) {
        fprintf(stderr, "Can't open: %s", argv[2]);
        return 3;
    }
    fclose(finput);

    size_t dsize = 0;
    uint8_t* dest = NULL;
    if (!strcmp(argv[1], "-c")) {
        size_t maxsize = PZZ_GetCompressedMaxSize(size);
        dest = (uint8_t*)malloc(maxsize);
        if (dest == NULL) {
            fprintf(stderr, "Error: malloc()");
            return 5;
        }
        dsize = PZZ_Compress(source, dest, size);
        assert(dsize <= maxsize);
    }
    else { // !strcmp(argv[1], "-d")
        dsize = PZZ_GetDecompressedSize(source, size);
        if (dsize == (size_t)-1) {
            fprintf(stderr, "Bad PZZ file");
            return 4;
        }
        dest = (uint8_t*)malloc(dsize);
        if (dest == NULL) {
            fprintf(stderr, "Error: malloc()");
            return 5;
        }
        PZZ_Decompress(source, dest, size);
    }

    FILE* fout = fopen(argv[3], "wb");
    if (fout == NULL) {
        fprintf(stderr, "Can't open: %s", argv[3]);
        return 6;
    }
    size_t writeBytes = fwrite(dest, 1, dsize, fout);
    if (writeBytes != dsize) {
        fprintf(stderr, "Can't write: %s", argv[3]);
        return 7;
    }
    fclose(fout);

    free(dest);
    free(source);
    return 0;
}
