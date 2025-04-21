# taskmanager/serializers.py

from rest_framework import serializers
from .models import User, Category, Task, TaskComment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'profile_picture', 'password']
        read_only_fields = ['id']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        """Create a new user with encrypted password"""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user, correctly handling the password"""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'color']
        read_only_fields = ['id']


class TaskCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = TaskComment
        fields = ['id', 'task', 'user', 'user_name', 'content', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username


class TaskSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    assigned_to_names = serializers.SerializerMethodField()
    category_names = serializers.SerializerMethodField()
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'created_by', 'created_by_name',
            'assigned_to', 'assigned_to_names', 'priority', 'priority_display',
            'status', 'status_display', 'due_date', 'created_at', 'updated_at',
            'categories', 'category_names'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        user = obj.created_by
        return f"{user.first_name} {user.last_name}".strip() or user.username
    
    def get_assigned_to_names(self, obj):
        return [
            f"{user.first_name} {user.last_name}".strip() or user.username
            for user in obj.assigned_to.all()
        ]
    
    def get_category_names(self, obj):
        return [category.name for category in obj.categories.all()]
    
    def create(self, validated_data):
        assigned_to = validated_data.pop('assigned_to', [])
        categories = validated_data.pop('categories', [])
        
        # Set the created_by field to the current user
        validated_data['created_by'] = self.context['request'].user
        
        # Create the task
        task = Task.objects.create(**validated_data)
        
        # Add assigned users and categories
        if assigned_to:
            task.assigned_to.set(assigned_to)
        if categories:
            task.categories.set(categories)
        
        return task


class TaskDetailSerializer(TaskSerializer):
    """Extended task serializer with comments"""
    comments = TaskCommentSerializer(many=True, read_only=True)
    
    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ['comments']