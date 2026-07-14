# Generated manually to add the PDF binary storage field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockchain', '0002_certificadomodel_merkle_proof'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificadomodel',
            name='archivo_pdf',
            field=models.BinaryField(blank=True, editable=False, null=True, verbose_name='Archivo PDF (binario)'),
        ),
    ]
