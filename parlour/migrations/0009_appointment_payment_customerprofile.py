# Generated manually for BeautyQ enhancements

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('parlour', '0008_review_message'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=15)),
                ('preferred_category', models.CharField(blank=True, default='hair', max_length=50)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='customer_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='appointment',
            name='amount_paid',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='appointment',
            name='customer_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appointments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='appointment',
            name='payment_status',
            field=models.CharField(choices=[('unpaid', 'Unpaid'), ('paid', 'Paid'), ('refunded', 'Refunded')], default='unpaid', max_length=20),
        ),
        migrations.AddField(
            model_name='appointment',
            name='promo_code',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='appointment',
            name='queue_position',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='appointment',
            name='stripe_session_id',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='appointment',
            name='turn_notified',
            field=models.BooleanField(default=False),
        ),
    ]
