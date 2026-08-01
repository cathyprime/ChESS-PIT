#include <unistd.h>

int main(void) {
    char *const args[] = {
        "/home/konrad/personal/chess-bot-fight-club/.venv/bin/python",
        "/home/konrad/personal/chess-bot-fight-club/tests/fixtures/random_uci.py",
        NULL
    };
    execv(args[0], args);
    return 127;
}
