# taskmanager/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """Extended User model with role-based permissions"""
    ADMIN = 'admin'
    MANAGER = 'manager'
    EMPLOYEE = 'employee'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
        (EMPLOYEE, 'Employee'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=EMPLOYEE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == self.ADMIN
    
    @property
    def is_manager(self):
        return self.role == self.MANAGER


class Category(models.Model):
    """Model to categorize tasks"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default="#007bff")  # Hex color code
    
    def __str__(self):
        return self.name
    
    # class Meta:
    #     verbose_name_plural = "Categories"
    class Meta:
        ordering = ['name']


class Task(models.Model):
    """Task model with all required fields"""
    # Priority choices
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    
    PRIORITY_CHOICES = [
        (LOW, 'Low'),
        (MEDIUM, 'Medium'),
        (HIGH, 'High'),
    ]
    
    # Status choices
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
    ]
    
    # Task fields
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_to = models.ManyToManyField(User, related_name='assigned_tasks', blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=MEDIUM)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=PENDING)
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField(Category, related_name='tasks', blank=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']


class TaskComment(models.Model):
    """Model for task comments"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"
    
    class Meta:
        ordering = ['created_at']