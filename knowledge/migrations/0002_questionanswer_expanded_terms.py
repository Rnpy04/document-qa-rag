from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("knowledge", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionanswer",
            name="expanded_terms",
            field=models.JSONField(blank=True, default=list, verbose_name="عبارت‌های مرتبط برای جست‌وجو"),
        ),
    ]
