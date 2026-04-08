from django.contrib import admin
from .models import Mood, Color, Advice, StartLog, SuggestedColor, EndLog


@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
    list_display = (
        'mood_id',
        'mood_name',
        'emoji',
        'category',
        'get_base_colors'
    )
    list_filter = ('category',)
    search_fields = ('mood_name',)

    def get_base_colors(self, obj):
        """Moodに紐づくColor(HSL)をまとめて表示"""
        colors = [c.hsl_value for c in [obj.base_color1, obj.base_color2, obj.base_color3] if c]
        return ", ".join(colors) if colors else "-"
    get_base_colors.short_description = "Base Colors (HSL)"


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('color_id', 'color_name', 'hsl_value', 'description')
    search_fields = ('color_name', 'hsl_value')


@admin.register(Advice)
class AdviceAdmin(admin.ModelAdmin):
    list_display = ('advice_id', 'mood', 'advice_text')
    search_fields = ('advice_text',)
    list_filter = ('mood',)


@admin.register(StartLog)
class StartLogAdmin(admin.ModelAdmin):
    list_display = ('startlog_id', 'user', 'mood', 'intensity', 'advice', 'created_at')
    list_filter = ('mood', 'created_at')
    search_fields = ('startlog_note',)


@admin.register(SuggestedColor)
class SuggestedColorAdmin(admin.ModelAdmin):
    list_display = ('suggested_color_id', 'startlog', 'suggested_color_hsl', 'order_index')
    list_filter = ('order_index',)
    ordering = ('startlog', 'order_index')


@admin.register(EndLog)
class EndLogAdmin(admin.ModelAdmin):
    list_display = ('endlog_id', 'startlog', 'user', 'mood', 'created_at')
    list_filter = ('mood', 'created_at')
    search_fields = ('endlog_note',)
