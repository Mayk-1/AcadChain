# Generated manually to add digital signatures (Proof of Authority, nivel 2)

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blockchain', '0004_authtoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='bloquemodel',
            name='firmante',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bloques_firmados', to=settings.AUTH_USER_MODEL, verbose_name='Autoridad que selló el bloque'),
        ),
        migrations.AddField(
            model_name='bloquemodel',
            name='firma_digital',
            field=models.TextField(blank=True, editable=False, null=True, verbose_name='Firma digital (base64)'),
        ),
        migrations.CreateModel(
            name='AutoridadClave',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('llave_privada_pem', models.TextField(editable=False)),
                ('llave_publica_pem', models.TextField(editable=False)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='autoridad_clave', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
