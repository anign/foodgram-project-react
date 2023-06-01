from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrAdminOrModerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.method == 'POST':
            return request.user.is_authenticated

        return request.user.is_authenticated and (
                request.user == obj.author
                or request.user.is_moderator
                or request.user.is_admin
        )


class CurrentUserPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class ReadOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS
