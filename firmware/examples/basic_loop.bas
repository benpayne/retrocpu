10 REM ===================================
20 REM RETROCPU BASIC LOOP DEMONSTRATION
30 REM ===================================
40 REM
50 REM This program demonstrates a simple
60 REM infinite loop that can be stopped
70 REM with the BREAK key (Escape on PS/2).
80 REM
90 REM Useful for testing dual I/O modes:
100 REM - Paste via UART (I 0 0)
110 REM - Run and view on Display (I 1 1)
120 REM
130 PRINT "STARTING LOOP..."
140 PRINT "PRESS BREAK TO STOP"
150 PRINT ""
160 LET N = 0
170 N = N + 1
180 PRINT "COUNT: "; N
190 IF N < 1000 THEN GOTO 170
200 PRINT ""
210 PRINT "LOOP COMPLETE (1000 ITERATIONS)"
220 END
