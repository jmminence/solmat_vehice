from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from accounts.models import Profile


class State(models.Model):
    """
    Stores information about a State for a :model:`workflows.Form`.

    - Name is optional.

    """

    name = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return str(self.name)


class Flow(models.Model):
    """
    Stores information for a proccess flow, and it's relation to parent process.

    - Name is optional.
    - Parent is a recursive relationship :model:`workflows.Flow`.

    """

    name = models.CharField(max_length=250, null=True, blank=True)
    parent = models.ForeignKey(
        "self", null=True, related_name="child", on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.name)


PERMISSION = (("w", "Write"), ("a", "Authorize"), ("r", "Read"))


class Permission(models.Model):
    """
    Permissions define the required permission to move from a State to another :model:`workflows.State`

    - Name is optional.
    - Type Permission is a choice.
    - From State is the source State.
    - To State is the target State.

    """

    name = models.CharField(max_length=250, null=True, blank=True)
    type_permission = models.CharField(max_length=1, choices=PERMISSION)
    from_state = models.ForeignKey(
        State,
        null=True,
        on_delete=models.SET_NULL,
        related_name="permission_from_state",
    )
    to_state = models.ForeignKey(
        State, null=True, on_delete=models.SET_NULL, related_name="permission_to_state"
    )

    def __str__(self):
        return str(self.name)


class Actor(models.Model):
    """
    Actor is a description of a user role in the Workflows environment.
    It connects to Accounts profiles :model:`accounts.Profile`

    - Name is optional.
    - Permission is list of available permissions to Actor :model:`workflows.Permission`.
    - Profile is the related :model:`accounts.Profile`.

    """

    name = models.CharField(max_length=250, null=True, blank=True)
    permission = models.ManyToManyField(Permission)
    profile = models.ForeignKey(Profile, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return str(self.name)


class Step(models.Model):
    """
    Step stores information about single part of a :model:`workflows.Flow`,
    alongside the :model:`workflows.Actor` that can take part in it and the
    :model:`workflows.State` in which the Flow is.

    - Name is optional.
    - Tag is optional.
    - Route is optional.
    - Order indicates where in a flow the Step is located. Optional.
    - State is a related :model:`workflows.State`.
    - Flow is the parent :model:`workflows.Flow`.
    - Actors is a list of :model:`workflows.Actor`

    """

    name = models.CharField(max_length=250, null=True, blank=True)
    tag = models.CharField(max_length=250, null=True, blank=True)
    state = models.OneToOneField(
        State,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    flow = models.ForeignKey(Flow, null=True, on_delete=models.SET_NULL)
    route = models.CharField(max_length=250, null=True, blank=True)
    order = models.PositiveIntegerField(null=True)
    actors = models.ManyToManyField(Actor)

    class Meta:
        unique_together = ("flow", "order")
        ordering = ["order"]

    def __str__(self):
        return str(self.name)


class Form(models.Model):
    """
    Form encapsules an entire process, details it's status and stores changes alongside it's origin.

    - Flow is related :model:`workflows.Flow`.
    - State is related :model:`workflows.State`.
    - Form Closed is optional.
    - Form Reopened is optional.
    - Parent is a recursive relation.
    - Content Type is the model that originated the change.
    - Object Id is the id for Content Type model.
    - Cancelled defaults to False.
    - Cancelled At is optional.
    - Closed At is optional

    """

    flow = models.ForeignKey(Flow, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    form_closed = models.BooleanField(default=False)
    form_reopened = models.BooleanField(default=False)
    parent = models.ForeignKey(
        "self", related_name="children", null=True, blank=True, on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey()
    cancelled = models.BooleanField(default=False, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    reception_finished = models.BooleanField(default=False, blank=True)
    reception_finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.content_type)
