/*==================================================================
  04 - PROC SQL: resumen de transacciones chicas por cliente
==================================================================*/

proc import datafile="data/transactions.csv" out=work.trx dbms=csv replace;
    getnames=yes;
run;

proc sql;
    create table work.cust_summary as
    select customer_id,
           count(*)        as n_trx,
           count(amount)   as n_with_amount,
           sum(amount)     as total_amount,
           avg(amount)     as avg_amount,
           max(trx_date)   as last_trx format=yymmdd10.,
           sum(case when channel = 'ATM' then 1 else 0 end) as n_atm
    from work.trx
    where amount < 1000
    group by customer_id
    having calculated n_trx >= 2
    order by customer_id;
quit;