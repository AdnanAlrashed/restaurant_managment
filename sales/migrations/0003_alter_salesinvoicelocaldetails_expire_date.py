# Generated by Django 3.2.6 on 2023-09-09 17:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0002_remove_salesinvoicelocaldetails_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salesinvoicelocaldetails',
            name='expire_date',
            field=models.CharField(default=1, max_length=50, verbose_name='expire date'),
            preserve_default=False,
        ),
    ]