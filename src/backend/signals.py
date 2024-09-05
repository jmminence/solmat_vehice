import inspect
from datetime import datetime

from django.forms.models import model_to_dict
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType


def on_model_pre_save(sender, instance, **kwargs) -> None:
    """
    :sender: Model which is getting saved.
    :instance: Actual instance which is going to be saved.
    This is a callback for the pre_save signal which is connected to some backend models
    in the AppConfig.
    """
    request = None
    for frame_record in inspect.stack():
        if frame_record[3] == 'get_response':
            request = frame_record[0].f_locals['request']
            break

    if request:

        try:
            model = sender.objects.get(pk=instance.id)
        except sender.DoesNotExist:
            model = type(instance).__name__
            sender_type = ContentType.objects.get(app_label="backend", model=model)
            log = LogEntry.objects.create(
                action_time=datetime.now(),
                user=request.user,
                content_type=sender_type,
                object_id=instance.id,
                object_repr=repr(instance),
                action_flag=ADDITION,
                change_message=model_to_dict(instance)
            )
        else:
            serialized_model = model_to_dict(model)
            serialized_instance = model_to_dict(instance)

            diffdict = {
                key: (serialized_model.get(key, None), serialized_instance.get(key, None))
                for key in serialized_model.keys() | serialized_instance.keys()
            }

            if serialized_model != serialized_instance:
                model = type(instance).__name__
                sender_type = ContentType.objects.get(app_label="backend", model=model)
                log = LogEntry.objects.create(
                    action_time=datetime.now(),
                    user=request.user,
                    content_type=sender_type,
                    object_id=instance.id,
                    object_repr=repr(instance),
                    action_flag=CHANGE,
                    change_message=diffdict
                )



def on_model_post_delete(sender, instance, **kwargs) -> None:
    """
    :sender: Model that has been deleted.
    :instance: Actual instance that was deleted from the database .
    This is a callback for the post_delete signal which is connected to some backend models
    in the AppConfig.
    """

    request = None
    for frame_record in inspect.stack():
        if frame_record[3] == 'get_response':
            request = frame_record[0].f_locals['request']
            break

    if request:
        model = type(instance).__name__
        sender_type = ContentType.objects.get(app_label="backend", model=model)
        log = LogEntry.objects.create(
            action_time=datetime.now(),
            user=request.user,
            content_type=sender_type,
            object_id=instance.id,
            object_repr=repr(instance),
            action_flag=DELETION,
            change_message=model_to_dict(instance)
        )
