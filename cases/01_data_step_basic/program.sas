/*==================================================================
  01 - DATA step básico: leer, filtrar, columnas nuevas, IF/ELSE
  Input : data/transactions.csv
  Output: work.trx_clean   -> expected/01_trx_clean.csv
==================================================================*/

proc import datafile="data/transactions.csv"
            out=work.trx
            dbms=csv
            replace;
    getnames=yes;
run;

data work.trx_clean;
    set work.trx;
    where status ne 'CANCELLED';
    length segment $6;
    amount_mxn = amount * fx_rate;
    if amount_mxn >= 10000 then segment = 'HIGH';
    else if amount_mxn >= 1000 then segment = 'MEDIUM';
    else segment = 'LOW';
    trx_month = intnx('month', trx_date, 0, 'b');
    format trx_month yymmdd10.;
    if channel = 'ATM' and amount_mxn > 8000 then flag_atm = 1;
    else flag_atm = 0;
    keep trx_id customer_id trx_date trx_month amount_mxn
         segment channel status flag_atm;
run;