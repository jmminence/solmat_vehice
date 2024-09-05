from django.test import TestCase
from lab.services import *
from backend.models import Unit


class LabServicesTestCase(TestCase):
    def setUp(self):
        self.units = Unit.objects.order_by("-id")[:100]

    def test_generate_differences(self):
        for unit in self.units:
            cassettes_pk = unit.cassettes.all().values_list("id", flat=True)
            cassettes_organs = list(
                CassetteOrgan.objects.filter(cassette_id__in=cassettes_pk)
                .values("organ")
                .annotate(organ_count=Count("organ"))
                .order_by()
            )
            unit_organs = list(
                unit.organunit_set.values("organ")
                .annotate(organ_count=Count("organ"))
                .order_by()
            )
            difference, organs = generate_differences(unit)
            self.assertIn(difference, [True, False])
