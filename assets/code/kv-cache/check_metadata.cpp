#include <iostream>
#include <algorithm>
#include <type_traits>
#include "llama-kv-cells.h"
int main() {
    llama_kv_cells original;
    original.resize(256);
    original.pos_set(0, 42);
    original.seq_add(0, 0);
    llama_kv_cells copied = original;
    std::cout << "before: size=" << copied.size() << " used=" << copied.get_used()
              << " empty0=" << copied.is_empty(0) << " seq0=" << copied.seq_has(0, 0) << '\n';
    copied.resize(512);
    std::cout << "after: size=" << copied.size() << " used=" << copied.get_used()
              << " empty0=" << copied.is_empty(0) << " seq0=" << copied.seq_has(0, 0) << '\n';
    return copied.is_empty(0) && copied.get_used() == 0 ? 0 : 1;
}
