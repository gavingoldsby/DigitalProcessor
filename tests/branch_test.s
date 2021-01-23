addi $t0, $t0, 1
addi $t1, $t1, 2
beq $t1, $t0, test
bne $t1, $t0, test2
test:
addi $s0, $s0, 1

test2:
addi $s0, $s0, 2
addi $t2, $t2, 2
bne $t2, $t1, test3
beq $t2, $t1, test4


test3:
addi $s1, $s1, 1

test4:
addi $s1, $s1, 2