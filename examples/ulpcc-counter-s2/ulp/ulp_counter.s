.data
    .global counter
counter:
.long 0x0
    .global entry
.text
entry:
	move r2,counter
	ld r1,r2,0
	add r1,r1,1
	st r1,r2,0
L.1:

halt
