addi $t0, $t0, 4
addi $t1, $t1, 3
mult $t0, $t1
mflo $s0
addi $t2, $t2, 0xacbd0000
mult $t2, $t1
mflo $s1
mfhi $s2