from random import randint

def dump( f, name, N, mode = 'random' ):
  f.write(f'int {name}[{N}] = {{' + '\n')
  for i in range(N):
    if mode == 'random':
      f.write(f'  {randint(0, 256)},' + '\n')
    elif mode == 'inc':
      f.write(f'  {i},' + '\n')
    elif mode == 'dec':
      f.write(f'  {N-i-1},' + '\n')
  f.write('};' + '\n')
  f.write('\n')

if __name__ == '__main__':
  with open('dump', 'w') as f:
    dump(f, 'cp_array', 100+1, 'dec')
