from celery import shared_task
from django.db import transaction

from backend.users.models import CourseAccess, User, Whitelist


@shared_task
def sync_access_from_whitelist(phone_number_str: str):
    with transaction.atomic():
        try:
            user = User.objects.get(phone_number=phone_number_str)
        except User.DoesNotExist:
            return False

        try:
            whitelist_entry = Whitelist.objects.prefetch_related("courses").get(
                phone_number=phone_number_str
            )

            courses_in_whitelist_ids = set(
                whitelist_entry.courses.values_list("id", flat=True)
            )

            current_access_ids = set(
                user.course_accesses.values_list("course_id", flat=True)
            )

            ids_to_add = courses_in_whitelist_ids - current_access_ids
            ids_to_remove = current_access_ids - courses_in_whitelist_ids

            if ids_to_remove:
                CourseAccess.objects.filter(user=user, course_id__in=ids_to_remove).delete()

            if ids_to_add:
                new_accesses = [
                    CourseAccess(user=user, course_id=course_id) for course_id in ids_to_add
                ]
                CourseAccess.objects.bulk_create(new_accesses)

            return True

        except Whitelist.DoesNotExist:
            user.course_accesses.all().delete()
            return False
