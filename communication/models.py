from django.db import models
from django.conf import settings
from core.models import Employee, Department
from django.urls import reverse

class InAppEmail(models.Model):
    sender = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='sent_emails', verbose_name="Sender")
    recipients = models.ManyToManyField(Employee, related_name='received_emails', verbose_name="Recipients")
    cc = models.ManyToManyField(Employee, related_name='cc_emails', blank=True, verbose_name="CC")
    bcc = models.ManyToManyField(Employee, related_name='bcc_emails', blank=True, verbose_name="BCC")
    subject = models.CharField(max_length=255, verbose_name="Subject")
    body = models.TextField(verbose_name="Email Body")
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="Sent At")
    is_read = models.ManyToManyField(Employee, related_name='read_emails', blank=True, verbose_name="Read By")
    parent_email = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies', verbose_name="Parent Email")
    is_draft = models.BooleanField(default=False, verbose_name="Is Draft")
    
    class Meta:
        verbose_name = "In-App Email"
        verbose_name_plural = "In-App Emails"
        ordering = ['-sent_at']

    def __str__(self):
        return f"From: {self.sender} - Subject: {self.subject}"

class EmailAttachment(models.Model):
    email = models.ForeignKey(InAppEmail, on_delete=models.CASCADE, related_name='attachments', verbose_name="Email")
    file = models.FileField(upload_to='email_attachments/', verbose_name="File")
    filename = models.CharField(max_length=255, verbose_name="File Name")

    class Meta:
        verbose_name = "Email Attachment"
        verbose_name_plural = "Email Attachments"

    def __str__(self):
        return self.filename

class InAppChat(models.Model):
    participants = models.ManyToManyField(Employee, related_name='chats', verbose_name="Participants")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    is_group_chat = models.BooleanField(default=False, verbose_name="Is Group Chat")
    group_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Group Name")

    class Meta:
        verbose_name = "In-App Chat"
        verbose_name_plural = "In-App Chats"

    def get_chat_name(self, user):
        if self.is_group_chat:
            return self.group_name or f"Group Chat {self.id}"
        else:
            other_participant = self.participants.exclude(id=user.id).first()
            return f"{other_participant.get_full_name()}" if other_participant else "Chat"
    
    def get_absolute_url(self):
        return reverse('communication:chat_room', args=[str(self.id)])
    
    def __str__(self):
        if self.is_group_chat:
            return f"Group Chat: {self.group_name}"
        return f"Chat between {', '.join(str(p) for p in self.participants.all())}"

class ChatMessage(models.Model):
    chat = models.ForeignKey(InAppChat, on_delete=models.CASCADE, related_name='messages', verbose_name="Chat")
    sender = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='sent_chat_messages', verbose_name="Sender")
    content = models.TextField(verbose_name="Message Content")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Sent At")
    is_read = models.ManyToManyField(Employee, related_name='read_chat_messages', blank=True, verbose_name="Read By")


    class Meta:
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"
        ordering = ['timestamp']

    def __str__(self):
        return f"Message in {self.chat} by {self.sender} at {self.timestamp}"

class ChatAttachment(models.Model):
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='attachments', verbose_name="Chat Message")
    file = models.FileField(upload_to='chat_attachments/', verbose_name="File")
    filename = models.CharField(max_length=255, verbose_name="File Name")

    class Meta:
        verbose_name = "Chat Attachment"
        verbose_name_plural = "Chat Attachments"

    def __str__(self):
        return self.filename

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('MESSAGE', 'New Message'),
        ('TASK', 'Task Assignment'),
        ('REMINDER', 'Reminder'),
        ('ANNOUNCEMENT', 'Announcement'),
        ('SYSTEM', 'System Notification'),
    ]

    recipient = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='notifications', verbose_name="Recipient")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name="Notification Type")
    title = models.CharField(max_length=255, verbose_name="Title")
    content = models.TextField(verbose_name="Content")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    is_read = models.BooleanField(default=False, verbose_name="Is Read")
    related_object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="Related Object ID")
    related_object_type = models.CharField(max_length=100, null=True, blank=True, verbose_name="Related Object Type")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.notification_type} for {self.recipient} - {self.title}"

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    title = models.CharField(max_length=255, verbose_name="Title")
    description = models.TextField(verbose_name="Description")
    assigned_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assigned_tasks', verbose_name="Assigned By")
    assigned_to = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks', verbose_name="Assigned To")
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.CASCADE, related_name='department_tasks', verbose_name="Department")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM', verbose_name="Priority")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    due_date = models.DateTimeField(verbose_name="Due Date")
    created_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='created_tasks', verbose_name="Created By")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.title} - Assigned to: {self.assigned_to}"

class Subtask(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES, default='PENDING')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['due_date', 'created_at']

class DepartmentAnnouncement(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='announcements', verbose_name="Department")
    title = models.CharField(max_length=255, verbose_name="Title")
    content = models.TextField(verbose_name="Content")
    author = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='authored_announcements', verbose_name="Author")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        verbose_name = "Department Announcement"
        verbose_name_plural = "Department Announcements"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.department} - {self.title}"

class Newsletter(models.Model):
    title = models.CharField(max_length=255, verbose_name="Title")
    content = models.TextField(verbose_name="Content")
    author = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='authored_newsletters', verbose_name="Author")
    departments = models.ManyToManyField(Department, related_name='newsletters', blank=True, verbose_name="Target Departments")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Published At")
    is_published = models.BooleanField(default=False, verbose_name="Is Published")

    class Meta:
        verbose_name = "Newsletter"
        verbose_name_plural = "Newsletters"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {'Published' if self.is_published else 'Draft'}"

class CommunicationLog(models.Model):
    ACTION_TYPES = [
        ('EMAIL_SENT', 'Email Sent'),
        ('EMAIL_READ', 'Email Read'),
        ('CHAT_MESSAGE_SENT', 'Chat Message Sent'),
        ('CHAT_MESSAGE_READ', 'Chat Message Read'),
        ('SENT', 'Message Sent'),
        ('READ', 'Message Read'),
        ('TASK_CREATED', 'Task Created'),
        ('TASK_UPDATED', 'Task Updated'),
        ('ANNOUNCEMENT_CREATED', 'Announcement Created'),
        ('NEWSLETTER_PUBLISHED', 'Newsletter Published'),
    ]

    user = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='communication_logs', verbose_name="User")
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name="Action Type")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    details = models.TextField(blank=True, verbose_name="Details")

    class Meta:
        verbose_name = "Communication Log"
        verbose_name_plural = "Communication Logs"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action_type} at {self.timestamp}"