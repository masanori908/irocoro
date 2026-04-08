from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Color(models.Model):
    color_id = models.AutoField(primary_key=True)
    color_name = models.CharField(max_length=50)
    hsl_value = models.CharField(max_length=20)  # 例: "hsl(45, 100%, 50%)"
    description = models.TextField(blank=True, null=True)  # 色の解説

    def __str__(self):
        return f"{self.color_name} ({self.hsl_value})"


class Mood(models.Model):
    mood_id = models.AutoField(primary_key=True)
    mood_name = models.CharField(max_length=50)
    emoji = models.CharField(max_length=10)
    category = models.CharField(max_length=50, blank=True, null=True)
    base_color1 = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, related_name='moods_base1')
    base_color2 = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, related_name='moods_base2')
    base_color3 = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, related_name='moods_base3')

    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        # ★ 並び順に基づいて表示
        ordering = ['sort_order']

    def __str__(self):
        return self.mood_name


class Advice(models.Model):
    advice_id = models.AutoField(primary_key=True)
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE)
    advice_text = models.TextField()

    def __str__(self):
        return f"Advice for {self.mood.mood_name}"


class StartLog(models.Model):
    startlog_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE)
    intensity = models.IntegerField(default=50)
    advice = models.ForeignKey(Advice, on_delete=models.SET_NULL, null=True, blank=True)
    startlog_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"StartLog #{self.startlog_id} - {self.user.username}"


class SuggestedColor(models.Model):
    suggested_color_id = models.AutoField(primary_key=True)
    startlog = models.ForeignKey(StartLog, on_delete=models.CASCADE)
    suggested_color_hsl = models.CharField(max_length=30)  # 例: "hsl(210, 80%, 55%)"
    order_index = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['order_index']

    def __str__(self):
        return f"{self.suggested_color_hsl} (StartLog {self.startlog.startlog_id})"


class EndLog(models.Model):
    endlog_id = models.AutoField(primary_key=True)
    startlog = models.ForeignKey(StartLog, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood = models.ForeignKey(Mood, on_delete=models.CASCADE)
    selected_color = models.ForeignKey(SuggestedColor, on_delete=models.SET_NULL, null=True, blank=True)
    endlog_note = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='endlog_photos/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"EndLog #{self.endlog_id} ({self.user.username})"
