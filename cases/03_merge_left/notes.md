# Caso 03 - MERGE con IN=

Trampas:
1. `if a` = left join (se quedan todas las cuentas).
2. MERGE empata llaves nulas entre sí (un join normal no).
3. Columna común `branch`: en la PRIMERA fila del grupo gana customers;
   en las siguientes filas del mismo grupo gana accounts
   (customers ya no se vuelve a leer).
4. Si customers.branch es faltante, sobrescribe con faltante (C003).
5. has_customer = b → 1 si el cliente existe, 0 si no (C030).
6. Output ordenado por customer_id (nulos primero) y, dentro del grupo,
   en el orden original de accounts.