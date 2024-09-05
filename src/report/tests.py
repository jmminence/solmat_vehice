import json

from django.test import Client, TestCase
from django.urls import reverse
from faker import Faker
from datetime import date
from dateutil.relativedelta import relativedelta

from backend.models import AnalysisForm


class PathologistsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.fake = Faker()

    def test_show_correct_template(self):
        self.client.login(username="jmonagas", password="vehice1234")
        response = self.client.get(reverse("report:pathologist"))

        self.assertTemplateUsed(
            response,
            "pathologist/home.html",
            "Response must contain expected template.",
        )

    def test_no_date_start(self):
        self.client.login(username="jmonagas", password="vehice1234")
        response = self.client.post(
            reverse("report:pathologist"),
            json.dumps(
                {
                    "date_end": date.today().isoformat(),
                    "date_start": "",
                    "user_id": 10,
                }
            ),
            content_type="application/json",
        )

        self.assertIn("report", response.json(), "Result must contain expected data.")

    def test_no_date_end(self):
        self.client.login(username="jmonagas", password="vehice1234")
        response = self.client.post(
            reverse("report:pathologist"),
            json.dumps(
                {
                    "date_end": "",
                    "date_start": (date.today() + relativedelta(months=-3)).isoformat(),
                    "user_id": 10,
                }
            ),
            content_type="application/json",
        )

        self.assertIn("report", response.json(), "Result must contain expected data.")

    def test_no_user_id(self):
        self.client.login(username="jmonagas", password="vehice1234")
        response = self.client.post(
            reverse("report:pathologist"),
            json.dumps(
                {
                    "date_end": date.today().isoformat(),
                    "date_start": (date.today() + relativedelta(months=-3)).isoformat(),
                    "user_id": "",
                }
            ),
            content_type="application/json",
        )

        self.assertIn("report", response.json(), "Result must contain expected data.")

    def test_no_data(self):
        self.client.login(username="jmonagas", password="vehice1234")
        response = self.client.post(
            reverse("report:pathologist"),
            json.dumps(
                {
                    "date_end": "",
                    "date_start": "",
                    "user_id": "",
                }
            ),
            content_type="application/json",
        )

        self.assertIn("report", response.json(), "Result must contain expected data.")

    def test_all_filters(self):
        self.client.login(username="jmonagas", password="vehice1234")
        response = self.client.post(
            reverse("report:pathologist"),
            json.dumps(
                {
                    "date_end": date.today().isoformat(),
                    "date_start": (date.today() + relativedelta(months=-3)).isoformat(),
                    "user_id": 10,
                }
            ),
            content_type="application/json",
        )

        self.assertIn("report", response.json(), "Result must contain expected data.")


class ControlTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.faker = Faker()

    def test_show_correct_template(self):
        self.client.login(username="jmonagas", password="vehice1234")
        response = self.client.get(reverse("report:control"))

        self.assertTemplateUsed(
            response,
            "control/home.html",
            "Response must contain expected template.",
        )

    def test_expected_data(self):
        self.client.login(username="jmonagas", password="vehice1234")
        response = self.client.post(reverse("report:control"), {})

        self.assertIn(
            "pending", response.json(), "Response must contain expected data."
        )
        self.assertIn(
            "unassigned", response.json(), "Response must contain expected data."
        )
