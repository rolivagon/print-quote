create extension if not exists btree_gist;

alter table public.plotter_pricing
  add constraint plotter_pricing_paper_no_overlaps
  exclude using gist (paper_id with =, billing_metric with =,
    numrange(minimum, maximum, '[]') with &&) where (paper_id is not null);

alter table public.plotter_pricing
  add constraint plotter_pricing_finish_no_overlaps
  exclude using gist (finish_id with =, billing_metric with =,
    numrange(minimum, maximum, '[]') with &&) where (finish_id is not null);
