10 REM ===================================
20 REM RETROCPU BASIC HELLO WORLD PROGRAM
30 REM ===================================
40 REM
50 REM This is a simple example BASIC program
60 REM for testing paste functionality via UART
70 REM with XON/XOFF flow control.
80 REM
90 PRINT "HELLO FROM RETROCPU!"
100 PRINT "THIS PROGRAM WAS PASTED VIA UART"
110 PRINT ""
120 PRINT "FLOW CONTROL TEST:"
130 FOR I = 1 TO 10
140   PRINT "LINE "; I
150 NEXT I
160 PRINT ""
170 PRINT "TEST COMPLETE!"
180 END
