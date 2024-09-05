import numpy as np

from backend.models import AnalysisForm, Identification, Sample, SampleExams, Unit
from lab.models import Slide


class Analysis(AnalysisForm):
    """
    Proxy class to add aditional functionalities to :model:`backend.AnalysisForm`
    without modifying original implementation.
    """

    @property
    def organs(self):
        samples = Sample.objects.filter(entryform=self.entryform)
        samples_pk = samples.values_list("id", flat=True)
        organs_exam = SampleExams.objects.filter(
            sample_id__in=samples_pk,
            exam=self.exam,
            stain=self.stain,
        )

        return organs_exam

    @property
    def organs_count(self):
        return self.organs.count()

    @property
    def week_finished(self):
        if self.pre_report_ended and self.pre_report_ended_at:
            return self.pre_report_ended_at.isocalendar()[1]
        return None

    @property
    def week_closed(self):
        if self.manual_closing_date:
            return self.manual_closing_date.isocalendar()[1]
        return None

    def days_processing(self, holidays=[]):
        entryform = self.entryform
        identifications = Identification.objects.filter(entryform=entryform)
        units = Unit.objects.filter(identification__in=identifications)
        slide = (
            Slide.objects.filter(unit__in=units, released_at__isnull=False)
            .order_by("-released_at")
            .first()
        )

        if slide:
            date_start = entryform.created_at.date()
            date_end = slide.released_at.date()

            days = np.busday_count(
                begindates=date_start, enddates=date_end, weekmask="1111110"
            )

            return max(int(days), 0)

        return -1

    def days_assigning(self, holidays=[]):
        entryform = self.entryform
        identifications = Identification.objects.filter(entryform=entryform)
        units = Unit.objects.filter(identification__in=identifications)
        slide = (
            Slide.objects.filter(unit__in=units, released_at__isnull=False)
            .order_by("-released_at")
            .first()
        )

        if slide:
            date_start = slide.released_at.date()
            date_end = self.assignment_done_at.date()

            days = np.busday_count(
                begindates=date_start, enddates=date_end, weekmask="1111110"
            )

            return max(int(days), 0)

        return -1

    def days_waiting(self, holidays=[]):
        entryform = self.entryform
        identifications = Identification.objects.filter(entryform=entryform)
        units = Unit.objects.filter(identification__in=identifications)
        slide = (
            Slide.objects.filter(unit__in=units, released_at__isnull=False)
            .order_by("-released_at")
            .first()
        )

        if slide:
            date_slide = slide.released_at.date()
            date_assignment = self.assignment_done_at.date()
            date_start = (
                date_assignment if date_assignment >= date_slide else date_slide
            )
            date_end = self.pre_report_started_at.date()

            days = np.busday_count(
                begindates=date_start, enddates=date_end, weekmask="1111110"
            )

            return max(int(days), 0)
        else:
            date_start = self.assignment_done_at.date()
            date_end = self.pre_report_started_at.date()

            days = np.busday_count(
                begindates=date_start, enddates=date_end, weekmask="1111110"
            )

            return max(int(days), 0)

    def days_reading(self, holidays=[]):
        date_start = self.pre_report_started_at.date()
        date_end = self.pre_report_ended_at.date()

        days = np.busday_count(
            begindates=date_start, enddates=date_end, weekmask="1111110"
        )

        return max(int(days), 0)

    def days_reviewing(self, holidays=[]):
        date_start = self.pre_report_ended_at.date()
        date_end = self.manual_closing_date.date()

        days = np.busday_count(
            begindates=date_start, enddates=date_end, weekmask="1111110"
        )

        return max(int(days), 0)

    @property
    def pathologist_name(self):
        return f"{self.patologo.first_name} {self.patologo.last_name}"

    class Meta:
        proxy = True
