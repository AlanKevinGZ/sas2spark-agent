# Caso 05 - RETAIN + FIRST./LAST.

Trampas:
1. sum(running_total, amount): la FUNCIÓN sum() ignora faltantes.
   Si el primer amount del cliente es nulo, running_total = 0 (no nulo).
2. Empates en trx_date dentro de un cliente (C003, C007, C011):
   PROC SORT es estable, conserva el orden original del archivo.
3. customer_id nulo: un solo grupo, va primero.
4. `n_seq + 1;` es un sum statement: retenido, se reinicia en first.
5. is_last = last.customer_id → 1 en la última fila del grupo, 0 en las demás.
6. trx_date nula (C005): va primero dentro de su grupo.
7. El orden del output importa (check_order = true).