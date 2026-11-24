from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("knowledge", "0002_questionanswer_expanded_terms"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionanswer",
            name="expansion_method",
            field=models.CharField(default="none", max_length=20, verbose_name="روش گسترش پرسش"),
        ),
    ]
