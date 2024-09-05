import json

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from backend.models import Customer
from random import randint
from review.models import (
    Analysis,
    AnalysisMailList,
    File,
    MailList,
    Recipient,
    RecipientMail,
    Stage,
)


class AnalysisTestCase(TestCase):
    def setUp(self):
        Analysis.objects.create(pre_report_started=True, exam_id=66)
        Analysis.objects.create(
            pre_report_started=True, pre_report_ended=True, exam_id=66
        )

    def test_manager_stage(self):
        waiting = Analysis.objects.stage(0)
        analysis = Analysis.objects.filter(stages__state=0)

        self.assertGreaterEqual(
            waiting.count(),
            analysis.count(),
            "Response should contain as expected or more results.",
        )

    def test_view_index(self):
        client = Client()
        client.login(username="jmonagas", password="vehice1234")
        response = client.get(reverse("review:index"))

        self.assertTemplateUsed(
            response, "index.html", "Response must use expected template."
        )

    def test_view_list_stage(self):
        client = Client()
        client.login(username="jmonagas", password="vehice1234")
        response = client.get(reverse("review:list", kwargs={"index": 0}))
        analysis = Analysis.objects.stage(0)

        self.assertGreaterEqual(
            len(json.dumps(response.json())),
            analysis.count(),
            "Response must contain expected data.",
        )

    def test_view_list_waiting(self):
        client = Client()
        client.login(username="jmonagas", password="vehice1234")
        response = client.get(reverse("review:list", kwargs={"index": 9}))
        analysis = Analysis.objects.waiting()

        self.assertGreaterEqual(
            len(json.dumps(response.json())),
            analysis.count(),
            "Response must contain expected data.",
        )

    def test_update_stage(self):
        client = Client()
        client.login(username="jmonagas", password="vehice1234")

        user = User.objects.get(pk=1)

        stage = Stage.objects.create(
            analysis=Analysis.objects.last(), state=0, created_by=user
        )
        response = client.post(
            reverse("review:stage", kwargs={"pk": stage.analysis.id}),
            json.dumps({"state": 1}),
            content_type="application/json",
        )

        stage = json.loads(response.json())[0]

        self.assertTrue(stage, "Response must contain create or updated Stage.")

        self.assertDictContainsSubset(
            {"model": "review.stage"},
            stage,
            "Response must contain created or updated Stage.",
        )

    def test_get_files(self):
        client = Client()
        client.login(username="jmonagas", password="vehice1234")

        analysis = Analysis.objects.all().last()
        files = analysis.external_reports.all()
        review_files = File.objects.filter(analysis=analysis)

        response = client.get(reverse("review:files", kwargs={"pk": analysis.pk}))

        prereports = response.json()["prereports"]
        reviews = response.json()["reviews"]

        self.assertGreaterEqual(
            len(prereports),
            files.count(),
            "Response must contain expected result.",
        )

        self.assertGreaterEqual(
            len(reviews),
            review_files.count(),
            "Response must contain expected result.",
        )


class MailListTestCase(TestCase):
    def setUp(self):
        Analysis.objects.create(pre_report_started=True, exam_id=66)
        Analysis.objects.create(
            pre_report_started=True, pre_report_ended=True, exam_id=66
        )

    def test_mail_list_get(self):
        client = Client()
        client.login(username="jmonagas", password="vehice1234")

        analysis = Analysis.objects.all().last()
        customer = analysis.entryform.customer
        mail_lists = MailList.objects.create(customer=customer, name="Test")

        response = client.get(reverse("review:mail_list", kwargs={"pk": analysis.id}))

        response_json = response.json()

        self.assertTrue(
            "mail_lists" in str(response_json),
            "Response must contain expected data.",
        )

    def test_mail_list_post(self):
        client = Client()
        client.login(username="jmonagas", password="vehice1234")

        analysis = Analysis.objects.all().last()
        customer = analysis.entryform.customer
        MailList.objects.bulk_create(
            [
                MailList(customer=customer, name="Test1"),
                MailList(customer=customer, name="Test2"),
            ]
        )
        mail_lists = MailList.objects.all().only("id")

        response = client.post(
            reverse("review:mail_list", kwargs={"pk": analysis.id}),
            json.dumps([mail_list.id for mail_list in mail_lists]),
            content_type="application/json",
        )

        body = response.json()

        self.assertDictContainsSubset(
            {"status": "OK"}, body, "Response must contain expected data."
        )

        response = client.post(
            reverse("review:mail_list", kwargs={"pk": analysis.id}),
            json.dumps([999999]),
            content_type="application/json",
        )

        body = response.json()

        self.assertDictContainsSubset(
            {"status": "ERR"}, body, "Response must contain expected data."
        )

    def test_recipients_email(self):
        Recipient.objects.bulk_create(
            [
                Recipient(email="test1@mail.cl", first_name="Lacreo1"),
                Recipient(email="test2@mail.cl", first_name="Lacreo2"),
                Recipient(email="test3@mail.cl", first_name="Lacreo3", is_deleted=True),
            ]
        )
        customer = Customer.objects.all().last()
        analysis = Analysis.objects.all().last()
        mail_list = MailList.objects.create(name="Lacreo", customer=customer)

        for recipient in Recipient.objects.all():
            RecipientMail.objects.create(
                mail_list=mail_list, recipient=recipient, is_main=randint(0, 1)
            )

        AnalysisMailList.objects.create(analysis=analysis, mail_list=mail_list)

        self.assertGreaterEqual(
            len(mail_list.recipients_email), 2, "Response must contain expected data."
        )

    def test_current_email(self):
        Recipient.objects.bulk_create(
            [
                Recipient(email="test1@mail.cl", first_name="Lacreo1"),
                Recipient(email="test2@mail.cl", first_name="Lacreo2"),
                Recipient(email="test3@mail.cl", first_name="Lacreo3"),
            ]
        )
        customer = Customer.objects.all().last()
        analysis = Analysis.objects.all().last()
        mail_list = MailList.objects.create(name="Lacreo", customer=customer)

        for recipient in Recipient.objects.all():
            RecipientMail.objects.create(
                mail_list=mail_list, recipient=recipient, is_main=randint(0, 1)
            )
        AnalysisMailList.objects.create(analysis=analysis, mail_list=mail_list)

        client = Client()
        client.login(username="jmonagas", password="vehice1234")

        response = client.get(
            reverse("review:analysis_emails", kwargs={"pk": analysis.id})
        )

        self.assertDictContainsSubset(
            {"name": "Lacreo"},
            json.loads(response.json())[0],
            "Response must contain expected data.",
        )

    def test_send_email(self):
        Recipient.objects.bulk_create(
            [
                Recipient(email="test1@mail.cl", first_name="Lacreo1"),
                Recipient(email="test2@mail.cl", first_name="Lacreo2"),
                Recipient(email="test3@mail.cl", first_name="Lacreo3"),
            ]
        )
        customer = Customer.objects.all().last()
        analysis = Analysis.objects.all().last()
        mail_list = MailList.objects.create(name="Lacreo", customer=customer)

        for recipient in Recipient.objects.all():
            RecipientMail.objects.create(
                mail_list=mail_list, recipient=recipient, is_main=randint(0, 1)
            )
        AnalysisMailList.objects.create(analysis=analysis, mail_list=mail_list)

        client = Client()
        client.login(username="jmonagas", password="vehice1234")

        response = client.post(reverse("review:send_email", kwargs={"pk": analysis.id}))

        self.assertDictContainsSubset(
            {"status": "OK"}, response.json(), "Response must contain expected data."
        )

    def test_analysis_recipients(self):
        Recipient.objects.bulk_create(
            [
                Recipient(email="test1@mail.cl", first_name="Lacreo1"),
                Recipient(email="test2@mail.cl", first_name="Lacreo2"),
                Recipient(email="test3@mail.cl", first_name="Lacreo3", is_deleted=True),
            ]
        )
        customer = Customer.objects.all().last()
        analysis = Analysis.objects.all().last()
        mail_list = MailList.objects.create(name="Lacreo", customer=customer)

        for recipient in Recipient.objects.all():
            RecipientMail.objects.create(
                mail_list=mail_list, recipient=recipient, is_main=randint(0, 1)
            )

        AnalysisMailList.objects.create(analysis=analysis, mail_list=mail_list)

        self.assertGreaterEqual(
            len(mail_list.recipients_email), 2, "Response must contain expected data."
        )
