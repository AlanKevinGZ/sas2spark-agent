# Caso 02 - PROC SORT NODUPKEY

Trampas:
1. NODUPKEY conserva la PRIMERA fila de cada grupo según el orden del sort.
   dropDuplicates() en Spark no garantiza cuál conserva.
2. Empates en updated_at (clientes C005, C012, C027): SAS mantiene el
   orden original del archivo (EQUALS por defecto) y conserva el primero.
3. customer_id nulo: SAS lo ordena primero y lo trata como un solo grupo.
4. updated_at nulo: con DESCENDING queda al final (el faltante es el menor valor).
5. El orden del output importa (check_order = true).