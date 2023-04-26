from rest_framework.permissions import BasePermission


class IsTheUser(BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.user == request.user:
            return True
        return False
