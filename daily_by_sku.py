import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


def main():
    totals = defaultdict(lambda: [0, Decimal(0)])
    seen = {}

    with Path('sales.csv').open(encoding='utf-8-sig', newline='') as source:
        for line, row in enumerate(csv.DictReader(source), start=2):
            try:
                order_id = row['order_id'].strip()
                sku = row['sku'].strip()
                order_date = row['order_date'].strip()
                status = row['status'].strip().lower()
                status = {'canceled': 'cancelled'}.get(status, status)
                if not order_id or not sku or status not in {'delivered', 'cancelled'}:
                    raise ValueError('missing order ID or SKU, or unknown status')
                date.fromisoformat(order_date)
                quantity = Decimal(row['quantity'].strip()) if row['quantity'].strip() else None
                price = Decimal(row['price'].strip()) if row['price'].strip() else None
                if status == 'delivered' and (quantity is None or price is None):
                    raise ValueError('delivered order has no quantity or price')
                if any(value is not None and (not value.is_finite() or value < 0)
                       for value in (quantity, price)):
                    raise ValueError('invalid quantity or price')
                order = (order_date, sku, quantity, price, status)
                if order_id in seen:
                    if seen[order_id] != order:
                        raise ValueError(f'conflicting data for order {order_id}')
                    continue
                seen[order_id] = order
                total = totals[sku, order_date]
                total[0] += 1
                if status == 'delivered':
                    total[1] += quantity * price
            except (KeyError, ValueError, InvalidOperation) as error:
                raise ValueError(f'Invalid data on CSV line {line}: {error}') from error

    with Path('daily_by_sku.csv').open('w', encoding='utf-8', newline='') as result:
        writer = csv.writer(result)
        writer.writerow(['sku', 'order_date', 'orders', 'revenue'])
        for (sku, order_date), (orders, revenue) in sorted(totals.items()):
            writer.writerow([sku, order_date, orders, revenue])


if __name__ == '__main__':
    main()
