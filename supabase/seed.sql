-- Deterministic local/CI data. These Auth identities have no password and
-- cannot authenticate until provisioned through Supabase Auth.
insert into auth.users (
  id, aud, role, email, encrypted_password, email_confirmed_at,
  raw_app_meta_data, raw_user_meta_data, created_at, updated_at
)
values
  (
    '00000000-0000-0000-0000-000000000001', 'authenticated', 'authenticated',
    'seed-admin@example.com', null, timezone('utc', now()),
    '{"provider":"email","providers":["email"]}', '{"name":"Seed Administrator"}',
    timezone('utc', now()), timezone('utc', now())
  ),
  (
    '00000000-0000-0000-0000-000000000002', 'authenticated', 'authenticated',
    'seed-seller@example.com', null, timezone('utc', now()),
    '{"provider":"email","providers":["email"]}', '{"name":"Seed Seller"}',
    timezone('utc', now()), timezone('utc', now())
  )
on conflict (id) do nothing;

update public.users
set role = 'ADMIN'
where id = '00000000-0000-0000-0000-000000000001';

insert into public.clients (
  id, client_type, tax_id, company_name, created_by_id, created_at
)
values (
  1000, 'COMPANY', '99.999.999-9', 'Seed Company',
  '00000000-0000-0000-0000-000000000002', timezone('utc', now())
)
on conflict (id) do nothing;

insert into public.quotes (
  id, quote_number, status, seller_id, client_id, subtotal, tax, total, created_at
)
values (
  1000, 'SEED-0001', 'DRAFT', '00000000-0000-0000-0000-000000000002', 1000,
  0, 0, 0, timezone('utc', now())
)
on conflict (id) do nothing;

select setval(pg_get_serial_sequence('public.clients', 'id'), 1000, true);
select setval(pg_get_serial_sequence('public.quotes', 'id'), 1000, true);
