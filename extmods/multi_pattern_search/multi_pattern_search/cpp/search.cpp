#include "search.hpp"

void acsm_free(ACSM_STRUCT2 * acsm) {
    if (acsm) {
        acsmFree2(acsm);
    }
}

int match_recall(void * id, int index, void *data) {
    KeyWord& key=*(KeyWord*)id;
    if (0==key.count) {
        ((vec_key_ptr*)(data))->push_back(&key);
    }
    key.count+=1;
    return 0;
}
int exist_recall(void * id, int index, void *data) {
    return 1;
}
