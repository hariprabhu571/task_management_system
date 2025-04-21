# taskmanager/views.py
import rest_framework
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from .models import User, Category, Task, TaskComment
from .serializers import (
    UserSerializer, CategorySerializer, 
    TaskSerializer, TaskDetailSerializer, 
    TaskCommentSerializer
)
from .permissions import IsAdmin, IsManagerOrAdmin, IsOwnerOrAssignee


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users management
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    def get_permissions(self):
        """
        Allow user registration without authentication,
        but require authentication for other actions.
        """
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['me', 'update_profile']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdmin]
        return [permission() for permission in permission_classes]
    
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Get the current user profile
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        """
        Update the current user profile
        """
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for task categories
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tasks management
    """
    queryset = Task.objects.all().prefetch_related('assigned_to', 'categories')
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'categories', 'assigned_to']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority', 'status']
    
    def get_queryset(self):
        """
        Filter tasks based on user role:
        - Admins see all tasks
        - Managers see all tasks
        - Employees see only tasks they created or are assigned to
        """
        user = self.request.user
        if user.is_admin or user.is_manager:
            return self.queryset
        else:
            return self.queryset.filter(
                models.Q(created_by=user) | models.Q(assigned_to=user)
            ).distinct()
    
    def get_serializer_class(self):
        """
        Use TaskDetailSerializer for retrieve action
        """
        if self.action == 'retrieve':
            return TaskDetailSerializer
        return TaskSerializer
    
    def get_permissions(self):
        """
        Custom permission logic:
        - Create: IsAuthenticated
        - Update/Delete: IsOwnerOrAssignee or IsManagerOrAdmin
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            # Create a custom compound permission class on the fly
            class OrPermission(permissions.BasePermission):
                def has_permission(self, request, view):
                    return True  # We'll check object permissions
                        
                def has_object_permission(self, request, view, obj):
                    return IsOwnerOrAssignee().has_object_permission(request, view, obj) or \
                        IsManagerOrAdmin().has_object_permission(request, view, obj)
                        
            return [permissions.IsAuthenticated(), OrPermission()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """
        Get tasks assigned to the current user
        """
        tasks = self.queryset.filter(assigned_to=request.user)
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def created_tasks(self, request):
        """
        Get tasks created by the current user
        """
        tasks = self.queryset.filter(created_by=request.user)
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


class TaskCommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for task comments
    """
    queryset = TaskComment.objects.all()
    serializer_class = TaskCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter comments by task if task_id is provided in URL
        """
        task_id = self.request.query_params.get('task')
        if task_id:
            return self.queryset.filter(task_id=task_id)
        return self.queryset
    
    def perform_create(self, serializer):
        """
        Set the comment author to the current user
        """
        serializer.save(user=self.request.user)