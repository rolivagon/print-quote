-- Keep persisted quote headers consistent with their rounded item amounts.
UPDATE public.quotes AS quote
SET
    subtotal = totals.subtotal,
    tax = totals.tax,
    total = totals.total
FROM (
    SELECT
        quote_id,
        SUM(total_final - iva_amount) AS subtotal,
        SUM(iva_amount) AS tax,
        SUM(total_final) AS total
    FROM public.quote_items
    GROUP BY quote_id
) AS totals
WHERE quote.id = totals.quote_id
  AND (quote.subtotal, quote.tax, quote.total)
      IS DISTINCT FROM (totals.subtotal, totals.tax, totals.total);
