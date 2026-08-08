#include <stdio.h>
#include <string.h>

int main(void) {
    char line[4096];
    while (fgets(line, sizeof(line), stdin)) {
        if (strncmp(line, "uci", 3) == 0) {
            puts("id name ChESSPIT Minimal Fixture");
            puts("id author ChESSPIT");
            puts("uciok");
        } else if (strncmp(line, "isready", 7) == 0) {
            puts("readyok");
        } else if (strncmp(line, "go", 2) == 0) {
            puts("bestmove 0000");
        } else if (strncmp(line, "quit", 4) == 0) {
            break;
        }
        fflush(stdout);
    }
    return 0;
}
