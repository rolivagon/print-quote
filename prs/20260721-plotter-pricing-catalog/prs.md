# PRS: Catálogo de precios Plotter

**Status:** Done

## Propósito

Incorporar un catálogo de precios Plotter cargable desde la planilla proporcionada y permitir que las cotizaciones Plotter calculen importes netos en CLP según su métrica de cobro, tramo facturable y tarifas explícitamente disponibles.

## Requisitos (EARS)

1. **Cuando** se ejecute la carga del catálogo Plotter con la planilla proporcionada, **el sistema deberá** incorporar de forma aditiva los sustratos y las terminaciones contenidos en ella, sin eliminar ni modificar el catálogo existente de Digital u Offset.
2. **Cuando** se ejecute más de una vez la misma carga del catálogo Plotter, **el sistema deberá** dejar un catálogo equivalente al obtenido tras una sola ejecución, sin duplicar sus registros ni sus tarifas.
3. **Cuando** se cargue un material Plotter desde la planilla, **el sistema deberá** registrarlo con `weight` igual a 1.
4. **Cuando** se carguen sustratos o terminaciones ubicados en el bloque **TERMINACIONES DE PLOTTER**, **el sistema deberá** asociarles cobro por metros cuadrados facturables.
5. **Cuando** se carguen terminaciones ubicadas bajo el bloque **TERMINACION POR CANTIDADES**, **el sistema deberá** asociarles cobro por cantidad del trabajo.
6. **Cuando** una cotización Plotter incluya un ítem cobrado por metros cuadrados, **el sistema deberá** calcular sus metros cuadrados facturables como `max(1, (ancho_cm × alto_cm / 10000) × cantidad)`.
7. **Cuando** una cotización Plotter incluya un ítem cobrado por cantidad, **el sistema deberá** calcular su importe usando la cantidad del trabajo como métrica facturable.
8. **Cuando** los metros cuadrados facturables de un ítem Plotter sean de 1.00 a 5.00 inclusive, **el sistema deberá** usar la tarifa explícita de ese tramo.
9. **Cuando** los metros cuadrados facturables de un ítem Plotter sean de 5.01 a 20.00 inclusive, **el sistema deberá** usar la tarifa explícita de ese tramo; por ejemplo, 5.2 deberá usar esta tarifa.
10. **Cuando** los metros cuadrados facturables de un ítem Plotter sean de 20.01 a 100.00 inclusive, **el sistema deberá** usar la tarifa explícita de ese tramo.
11. **Cuando** un tramo de la planilla Plotter no tenga un precio explícito, **el sistema no deberá** crear una tarifa para ese tramo ni reutilizar o extender el precio de otro tramo.
12. **Cuando** una cotización Plotter requiera una tarifa de un tramo que no esté cargada, **el sistema deberá** reportar ausencia de tarifa para el ítem afectado.
13. **Cuando** una cotización Plotter requiera una tarifa por metros cuadrados para más de 100.00 m², **el sistema deberá** reportar ausencia de tarifa.
14. **Cuando** el sistema calcule o exponga importes del catálogo Plotter, **el sistema deberá** expresarlos en CLP netos, sin IVA.
15. **Cuando** se incorporen rangos de tarifa Plotter, **el sistema deberá** persistir límites decimales y una métrica de cobro que permitan distinguir rangos por m² y por cantidad, sin alterar el comportamiento de cotización Digital u Offset.
16. **Cuando** se modifique el cálculo de cotizaciones Plotter, **el sistema deberá** aplicar las reglas de precio fuera de la capa API.
17. **Cuando** se ejecute la carga local del catálogo Plotter, **el sistema deberá** poder ejecutarla mediante un objetivo de Makefile usando el entorno local configurado.
18. **Cuando** se ejecute la carga del catálogo Plotter contra producción, **el sistema deberá** poder ejecutarla mediante un objetivo de Makefile con las variables de `.env.prod` cargadas explícitamente, de modo que el `DATABASE_URL` de producción prevalezca sobre la configuración local.

## Tareas (TDD primero)

1. Añadir pruebas unitarias que fallen para la selección de tarifa Plotter por m²: mínimo de 1 m², límites 5.00/5.01/20.00/20.01/100.00, 5.2, tramo sin tarifa y más de 100 m².
2. Añadir pruebas unitarias que fallen para el cálculo de m² facturables y para el cobro por cantidad; implementar el comportamiento mínimo en la capa de pricing usando valores monetarios `Decimal`; refactorizar sin cambiar el comportamiento.
3. Añadir pruebas de carga que fallen para la clasificación de los dos bloques de la planilla, `weight=1`, importes CLP netos, creación exclusiva de precios explícitos y ejecución repetida idempotente; implementar la carga aditiva mínima y refactorizar sin cambiar el comportamiento.
4. Añadir una prueba de integración que falle para la persistencia y consulta de rangos decimales con métrica de cobro, incluyendo la coexistencia de datos Digital y Offset; crear una migración Supabase comprobada y el soporte de persistencia mínimo.
5. Añadir pruebas que fallen para que una cotización Plotter comunique la ausencia de tarifa sin trasladar reglas de precio a API; integrar el comportamiento a través de las capas correspondientes y refactorizar sin cambiarlo.
6. Añadir verificaciones automatizadas que fallen para la ejecución de la carga mediante Makefile en entorno local y con `.env.prod` cargado explícitamente; incorporar los objetivos necesarios sin incluir valores de entorno en el repositorio ni en este PRS.

## Comprobaciones de aceptación

- La carga local mediante el objetivo Makefile incorpora los sustratos y terminaciones de la planilla Plotter, es aditiva y una segunda ejecución no duplica datos ni tarifas.
- La carga con `.env.prod` cargado explícitamente y el objetivo Makefile usa la configuración de producción sin documentar ni revelar secretos.
- Todo material Plotter cargado tiene `weight=1`, precios netos en CLP y la métrica que corresponde a su bloque de origen.
- Sólo existen tarifas para celdas de tramo con precio explícito; una cotización que cae en un tramo vacío o supera 100.00 m² informa ausencia de tarifa.
- Para ítems por m², las cotizaciones verifican `max(1, (ancho_cm × alto_cm / 10000) × cantidad)` y seleccionan los tramos 1.00–5.00, 5.01–20.00 y 20.01–100.00, incluido 5.2 en el segundo tramo.
- Para terminaciones por cantidad, las cotizaciones usan la cantidad del trabajo como métrica facturable.
- La migración Supabase permite rangos decimales y métricas de cobro, y las pruebas confirman que Digital y Offset conservan su comportamiento.
- Las pruebas de pricing son unitarias y las pruebas de migración/persistencia se ejecutan contra Supabase/PostgreSQL local.
- Se ejecutan, en este orden, `make fmt`, `make lint` y `make test`; se ejecuta también `make test-supabase` para la migración y la persistencia.

## Restricciones aplicables

- La planilla proporcionada es la única fuente de datos para los sustratos, terminaciones y precios Plotter; no se inventarán precios ni se completarán celdas vacías.
- No existe tarifa Plotter para más de 100.00 m².
- Las reglas de cálculo y selección de precios pertenecen a la capa `pricing`; la API sólo compone servicios, estrategias y repositorios.
- Todos los valores monetarios usan `Decimal` y los cambios de esquema público se realizan exclusivamente mediante migraciones versionadas en `supabase/migrations/`; no se usa Alembic.
- La persistencia en ejecución usa PostgreSQL/Supabase; no hay alternativa SQLite en runtime.
- La carga no debe introducir comportamiento de compatibilidad sin una necesidad concreta de datos persistidos, comportamiento publicado o consumidores externos.
- Las pruebas deben residir en la capa propietaria del comportamiento y reutilizar fixtures y helpers existentes cuando corresponda.
- Las operaciones se ejecutan mediante objetivos Makefile y `.env.prod` no se copia, expone ni documenta con valores en el repositorio o este PRS.
- Se debe preferir el cambio mínimo correcto y evitar duplicación, compartiendo lógica repetida sólo cuando sea una unidad reutilizable clara.

## Verificaciones ejecutadas

- `make fmt` — correcto.
- `make lint` — correcto.
- `make test-unit` — 117 pruebas correctas.
- `make test` — 224 pruebas correctas, 22 omitidas.
- `make test-supabase` — 123 pruebas correctas, 1 omitida y 1 xfailed.
