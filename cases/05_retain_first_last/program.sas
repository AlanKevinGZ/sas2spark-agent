/*==================================================================
  05 - RETAIN + FIRST./LAST.: acumulado por cliente
==================================================================*/

proc import datafile="data/transactions.csv" out=work.trx dbms=csv replace;
    getnames=yes;
run;

proc sort data=work.trx out=work.trx_s;
    by customer_id trx_date;
run;

data work.cust_running;
    set work.trx_s;
    by customer_id;
    retain running_total;

    if first.customer_id then do;
        running_total = 0;
        n_seq = 0;
    end;

    running_total = sum(running_total, amount);   /* sum() ignora faltantes */
    n_seq + 1;                                    /* sum statement: retenido */
    is_last = last.customer_id;

    keep customer_id trx_id trx_date amount running_total n_seq is_last;
run;