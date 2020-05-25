all:
	gcc -O3 -Wall -Wextra -static -static-libgcc pzzcomp_jojo.c -o pzzcomp_jojo.exe
release:
	gcc -O3 -Wall -Wextra -static -static-libgcc pzzcomp_jojo.c -o pzzcomp_jojo.exe -DNDEBUG
debug:
	gcc -g3 -Wall -Wextra -static -static-libgcc pzzcomp_jojo.c -o pzzcomp_jojo.exe
