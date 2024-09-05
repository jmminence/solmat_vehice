# -*- coding: utf-8 -*-
from models import *

def profile_processor(request):
    if request.user:
        try:
            user = request.user
            profile = UserProfile.objects.get(user=user)
            return {'profile': profile}
        except Exception as e:
            return {'profile': {}}
    else:
        return {'profile': {}}