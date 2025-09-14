# About

This file will contain information on how you can analyze the finances from the sqlite database.

# Using Sqlite

The database I am using is in `data/secret_finances.db`. To open it in sqlite, from the root folder run
```bash
sqlite data/secret_finances.db
```

# Querying All Money Transfers

These are all meant to be done after opening the terminal for sqlite.

To view all receipts (any money I have paid), run
```sql
select * from receipts;
```

To view all disbursements (any money I have receipts), run
```sql
select * from disbursements;
```

# Other Use Cases

## Receiving Payments After Paying for a Group

To view all of the related payments I got back and the matched receipt, run
```sql
select r.store, r.price, r.date as receipt_date, d.entity as refunded_by, d.amount as refund_amount, d.date_received from receipts r inner join disbursements d on r.id = d.refunded_from_receipt;
```

To view the total amount paid back for a receipt and the net amount that I paid, run
```sql
select r.id, r.store, r.price as original_paid, r.date as receipt_date, sum(d.amount) as total_refunded, r.price - sum(d.amount) as net_paid
from receipts r inner join disbursements d on r.id = d.refunded_from_receipt
group by r.id, r.store, r.price, r.date;
```
