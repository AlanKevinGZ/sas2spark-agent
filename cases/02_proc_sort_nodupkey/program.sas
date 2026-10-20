/*==================================================================
  02 - PROC SORT + NODUPKEY: último registro por cliente
==================================================================*/

proc import datafile="data/customer_snapshots.csv"
            out=work.snap
            dbms=csv
            replace;
    getnames=yes;
run;

/* 1) Ordenar por cliente y la actualización más reciente primero */
proc sort data=work.snap out=work.snap_sorted;
    by customer_id descending updated_at;
run;

/* 2) Un registro por cliente: el primero de cada grupo */
proc sort data=work.snap_sorted out=work.latest nodupkey;
    by customer_id;
run;