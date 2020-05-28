# PZZ compressor &amp; unpacker
[PS2] GioGio’s Bizarre Adventure / JoJo no Kimyō na Bōken: Ōgon no Kaze
## Usage
1. Extract .pzz files from AFS_DATA.AFS.
2. Unpack [.dat] files from .pzz (only Python version). Compressed files: *_compressed.dat.
3. Decompress. The last zero bytes are skipped.
4. Compress. Add padding.
5. ???
### Python 3 version
pzz_comp_jojo.py

Unpack
```
pzz_comp_jojo.py -u file.pzz dir
pzz_comp_jojo.py -bu *.pzz dir
```
Decompress
```
pzz_comp_jojo.py -d file.dat file.bin
pzz_comp_jojo.py -bd *.dat dir
```
Compress
```
pzz_comp_jojo.py -c file.bin file.dat
pzz_comp_jojo.py -bc *.bin dir
```
### C version (faster)
pzzcomp_jojo.exe (see releases)

Decompress
```
pzzcomp_jojo -d file.dat file.bin
```
Compress
```
pzzcomp_jojo -c file.bin file.dat
```
### C version batch
pzzcomp_jojo_batch.py

Decompress
```
pzzcomp_jojo_batch.py -d Unpacked\*_compressed.dat Uncompressed --extension .bin
```
Compress
```
pzzcomp_jojo_batch.py -c Uncompressed\*.bin dir --extension .dat
```
**Note**: a path that starts with `\` or `/` is absolute. Example for Windows: `\dir` or `/dir` -> `C:\dir`.
