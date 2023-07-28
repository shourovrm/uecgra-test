#include "common.h"
#include "cgra_ubmark-llist.dat"

typedef struct LList {
  int data;
  struct LList *next;
} LList;

LList scratchpad[N];

int llist_find(int target, LList *head) {
  while(head) {
    if(head -> data == target)
      return head -> data;
    else
      head = head -> next;
  }
  return -1;
}

LList* llist_init(int data[], int n) {
  int i;
  LList *head = 0, *tail = 0;
  for(i = 0; i < n; i++) {
    if(tail == 0) {
      head = &scratchpad[index[i]];
      head -> data = data[i];
      head -> next = 0;
      tail = head;
    } else {
      tail -> next = &scratchpad[index[i]];
      tail -> next -> data = data[i];
      tail -> next -> next = 0;
      tail = tail -> next;
    }
  }
  return head;
}

int main(int argc, char* argv[]) {
  int ret = 0;
  LList *head = llist_init(data, N);

  test_stats_on();
  ret = llist_find(target, head);
  test_stats_off();

  if(ret != target)
    test_fail( 0, ret, target );
  else
    test_pass();

  return 0;
}
