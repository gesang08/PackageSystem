# coding=utf-8

import sys

if __name__ == "__main__":
    # 读取第一行的T
    T = int(sys.stdin.readline().strip())
    if not 1 <= T <= 20:
        raise AttributeError('The integer T is not in 1-20.')
    n, k = sys.stdin.readline().strip().split(' ')
    n, k = int(n), int(k)
    A=[]
    for i in range(n):
        line = sys.stdin.readline().strip().split(' ')
        A.append([int(line[0]),int(line[1]),int(line[2])])
    print(A)


