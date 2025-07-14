from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and  not request.user.is_staff

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsAnonymous(BasePermission):

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS

class IsModeratorPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_staff:
            if request.method != "POST":
                return True
        return False
    def has_object_permission(self, request, view, obj):
        return True
