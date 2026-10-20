/*==================================================================
  03 - MERGE con IN=: cuentas enriquecidas con datos del cliente
==================================================================*/

proc import datafile="data/accounts.csv" out=work.accounts dbms=csv replace;
    getnames=yes;
run;

proc import datafile="data/customers.csv" out=work.customers dbms=csv replace;
    getnames=yes;
run;

proc sort data=work.accounts;  by customer_id; run;
proc sort data=work.customers; by customer_id; run;

data work.acct_enriched;
    merge work.accounts(in=a) work.customers(in=b);
    by customer_id;
    if a;
    has_customer = b;
run;