expects a .env file in the root directory when launching via docker compose
```
drodos_postgres_user=pogger
drodos_postgres_password=mypoggerpassword
```

remember need to create super user again after DB reset (if you want to access django admin):
`sudo docker compose exec web python manage.py createsuperuser`
