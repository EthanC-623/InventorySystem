# Inventory System
> This project is intended as a easy to use Django site for managing the inventory and sales of a Tabletop shop, handling users and generating reports.

## Seeding the database
> If example data is needed then generate it using the following commands.
### Generate data
```
python manage.py seed --products 500
```
### Optionally delete old data before seeding new data
```
python manage.py seed --clear --products 500
```