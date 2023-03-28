# Generated by Django 4.1.7 on 2023-03-17 08:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_remove_pctdata_filled_countrypy_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pctdata',
            old_name='filled_country',
            new_name='filed_country',
        ),
        migrations.RemoveField(
            model_name='pctdata',
            name='published_or_filled_date',
        ),
        migrations.AddField(
            model_name='pctdata',
            name='published_or_filed_date',
            field=models.DateField(default='2001-09-20', help_text='The date when the patent was published or filed by the office.'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='pctdata',
            name='granted',
            field=models.BooleanField(help_text="Whether the patent is published and granted or it's just filed."),
        ),
    ]