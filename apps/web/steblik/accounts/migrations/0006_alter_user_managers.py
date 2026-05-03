import steblik.accounts.models
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_remove_username_unique_email"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="user",
            managers=[
                ("objects", steblik.accounts.models.UserManager()),
            ],
        ),
    ]
