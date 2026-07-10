# Generated manually to add the Merkle proof field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockchain', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificadomodel',
            name='merkle_proof',
            field=models.JSONField(blank=True, default=list, verbose_name='Prueba de Merkle'),
        ),
    ]
