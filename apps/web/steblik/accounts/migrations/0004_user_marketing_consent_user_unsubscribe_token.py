import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_announcement_post_slug_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="marketing_consent",
            field=models.BooleanField(
                default=False,
                help_text="User has explicitly opted in to marketing email (PECR).",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="unsubscribe_token",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                help_text="Stable token for one-click unsubscribe links (RFC 8058).",
                unique=True,
            ),
        ),
    ]
