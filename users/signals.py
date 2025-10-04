from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Employee, LeaveType, LeaveBalance
from datetime import date
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Employee)
def create_leave_balances_for_new_employee(sender, instance, created, **kwargs):
    """
    Automatically create leave balances for newly created employees
    """
    if created and not instance.is_superuser:
        try:
            current_year = date.today().year
            leave_types = LeaveType.objects.all()
            
            for leave_type in leave_types:
                LeaveBalance.objects.create(
                    employee=instance,
                    leave_type=leave_type,
                    year=current_year,
                    total_days=leave_type.default_days,
                    used_days=0
                )
                logger.info(
                    f"Created {leave_type.name} balance ({leave_type.default_days} days) "
                    f"for new employee: {instance.get_full_name()}"
                )
            
            logger.info(f"Successfully created all leave balances for {instance.get_full_name()}")
        except Exception as e:
            logger.error(f"Error creating leave balances for {instance.get_full_name()}: {str(e)}")
