from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.views import View
from django.utils import timezone
from django.utils.timezone import make_aware
from datetime import date, datetime
from .models import StartLog, Mood, Advice, SuggestedColor, EndLog
from django.db.models import Count, Max
import re
import calendar
import colorsys



class SignupView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = "signup.html"
    success_url = reverse_lazy("careapp:login")


class IndexView(LoginRequiredMixin, View):
    login_url = "/login/"
    template_name = "index.html"

    # 画面表示用メソッド
    def get(self, request):
        """GET時の処理（フォームまたは結果表示）"""
        user = self.request.user
        today = timezone.localdate()

        start_log = StartLog.objects.filter(user=user, created_at__date=today).first()
        end_log = EndLog.objects.filter(user=user, created_at__date=today).first()


        # 当日すでにEndLog入力済み → スタートログ・エンドログ比較表示
        if end_log:
            context = self.get_endlog_context(end_log)
            context["has_today_endlog"] = True

        # 未入力 → スタートログ入力or未入力の分岐へ
        else:
            context = {
                "has_today_endlog": False,
                "moods": Mood.objects.all(),
            }

            # 当日すでにスタートログ入力済み → 入力結果・提案結果表示
            if start_log:
                context = self.get_startlog_context(start_log)
                context["has_today_startlog"] = True

            # 未入力 → スタートログ入力フォーム表示
            else:
                context = {
                    "has_today_startlog": False,
                    "moods": Mood.objects.all(),
                }

        context.update(self.get_sidebar_context(user))
        context.update(self.get_month_summary_context(user))

        return render(request, self.template_name, context)


    # フォーム送信用メソッド
    def post(self, request):
        """POST時の処理（フォーム送信時）"""
        user = self.request.user
        today = timezone.localdate()

        # スタートログ入力内容変更処理
        if "reset" in request.POST:
            start_log = StartLog.objects.filter(user=user, created_at__date=today).first()
            if start_log:
                context = {
                    "has_today_startlog": False,
                    "moods": Mood.objects.all(),
                    "prev_mood": start_log.mood.mood_name,
                    "prev_intensity": start_log.intensity,
                    "prev_comment": start_log.startlog_note or "",
                }
            else:
                context = {
                    "has_today_startlog": False,
                    "moods": Mood.objects.all(),
                }

            context.update(self.get_sidebar_context(user))
            context.update(self.get_month_summary_context(user))

            return render(request, self.template_name, context)

        # 通常の保存処理
        mood_name = request.POST.get("mood")
        intensity = request.POST.get("intensity")
        comment = request.POST.get("comment", "")

        # None → 数値変換エラーを防止
        try:
            intensity = int(intensity)
        except (TypeError, ValueError):
            intensity = 50

        mood = Mood.objects.filter(mood_name=mood_name).first()
        advice = (Advice.objects
                    .filter(mood=mood)
                    .order_by("?")
                    .first()
                    )

        # 既存レコードがあれば上書き、なければ新規
        existing_log = StartLog.objects.filter(user=user, created_at__date=today).first()

        if existing_log:
            # 上書き更新
            existing_log.mood = mood
            existing_log.advice = advice
            existing_log.startlog_note = comment
            existing_log.intensity = intensity
            existing_log.save()
            start_log = existing_log
        else:
            # 新規作成
            start_log = StartLog.objects.create(
                user = user,
                mood = mood,
                advice = advice,
                startlog_note = comment,
                intensity = intensity,
            )

        # 提案カラー生成
        colors = self.suggest_colors(mood, intensity)

        # SuggestedColor 保存処理
        # 旧データ削除
        SuggestedColor.objects.filter(startlog=start_log).delete()

        # 新データ挿入（順番付き）
        for idx, color_hsl in enumerate(colors, start=1):
            SuggestedColor.objects.create(
                startlog=start_log,
                suggested_color_hsl=color_hsl,
                order_index=idx
            )

        color_descriptions = self.get_color_descriptions(mood)
        colors_with_names = [
            {"hsl": hsl, "name": cd["color_name"]}
            for hsl, cd in zip(colors, color_descriptions)
        ]
        context = {
            "has_today_startlog": True,
            "mood": mood,
            "advice": advice,
            "colors": colors,
            "colors_with_names": colors_with_names,
            "comment": start_log.startlog_note,
            "color_descriptions": color_descriptions,
        }
        context.update(self.get_sidebar_context(user))
        context.update(self.get_month_summary_context(user))

        return render(request, self.template_name, context)


    # スタートログ入力結果参照用メソッド
    def get_startlog_context(self, start_log):
        """入力済みデータの結果表示用コンテキスト生成"""
        mood = start_log.mood
        advice = start_log.advice
        comment = start_log.startlog_note
        colors = list(
            start_log.suggestedcolor_set
            .filter(order_index__lt=99)
            .order_by("order_index")
            .values_list("suggested_color_hsl", flat=True)
    )
        color_descriptions = self.get_color_descriptions(mood)
        colors_with_names = [
            {"hsl": hsl, "name": cd["color_name"]}
            for hsl, cd in zip(colors, color_descriptions)
        ]
        return {
            "mood": mood,
            "advice": advice,
            "colors": colors,
            "colors_with_names": colors_with_names,
            "comment": comment,
            "color_descriptions": color_descriptions,
        }

    # エンドログ入力結果参照用メソッド
    def get_endlog_context(self, end_log):
        start_log = end_log.startlog
        start_colors = list(
            start_log.suggestedcolor_set
            .filter(order_index__lt=99)
            .order_by("order_index")
            .values_list("suggested_color_hsl", flat=True)
        )
        return {
            "start_mood": start_log.mood,
            "start_comment": start_log.startlog_note,
            "start_colors": start_colors,
            "end_mood": end_log.mood,
            "end_selected_color": end_log.selected_color,
            "end_comment": end_log.endlog_note,
            "end_photo": end_log.photo,
        }


    def get_color_descriptions(self, mood):
        """Moodに紐づく3色の解説リストを返す"""
        base_colors = [mood.base_color1, mood.base_color2, mood.base_color3]
        return [
            {"color_name": c.color_name, "description": c.description or ""}
            for c in base_colors if c
        ]

    # 色の提案に関するメソッド
    def suggest_colors(self, mood, intensity):
        """Moodに紐づくColorモデルをもとにHSL値を調整して提案カラーを生成"""

        def parse_hsl(hsl_str):
            match = re.match(r"hsl\((\d+),\s*(\d+)%?,\s*(\d+)%?\)", hsl_str)
            if not match:
                return (0, 0, 0)
            return map(int, match.groups())

        # Colorモデルからhsl_valueを取得
        base_colors = [
            mood.base_color1.hsl_value if mood.base_color1 else "hsl(0, 0%, 50%)",
            mood.base_color2.hsl_value if mood.base_color2 else "hsl(0, 0%, 50%)",
            mood.base_color3.hsl_value if mood.base_color3 else "hsl(0, 0%, 50%)",
        ]

        def adjust_color(h, s, l, intensity):
            # 強度による彩度・明度調整（中心50）
            delta = (intensity - 50) / 50  # -1〜+1
            s = max(20, min(90, s - delta * 15))    # 強→彩度↓
            l = max(30, min(85, l + delta * 10))    # 強→明度↑
            return f"hsl({h}, {int(s)}%, {int(l)}%)"

        # 3色を調整して返す
        colors = []
        for hsl_str in base_colors:
            h, s, l = parse_hsl(hsl_str)
            colors.append(adjust_color(h, s, l, intensity))

        return colors


    # 左カラム用共通コンテキスト
    def get_sidebar_context(self, user):
        today = timezone.localdate()

        # 直近3日間
        yesterday = today - timezone.timedelta(days=1)
        three_days_ago = today - timezone.timedelta(days=3)

        three_days_startlogs = StartLog.objects.filter(
            user=user,
            created_at__date__range=(three_days_ago, yesterday)
        )

        three_days_results = []
        for i in range(3):
            target_date = yesterday - timezone.timedelta(days=i)
            log = three_days_startlogs.filter(created_at__date=target_date).first()
            three_days_results.append({
                "date": target_date,
                "log": log
            })

        # 今週
        start_of_week = today - timezone.timedelta(days=today.weekday())
        end_of_week = start_of_week + timezone.timedelta(days=6)

        week_endlogs = EndLog.objects.filter(
            user=user,
            created_at__date__range=(start_of_week, end_of_week)
        )

        logs_dict = {timezone.localtime(log.created_at).date(): log for log in week_endlogs}

        WEEKDAYS_JP = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        week_data = []
        for i in range(7):
            day = start_of_week + timezone.timedelta(days=i)
            week_data.append({
                "date": day,
                "weekday": WEEKDAYS_JP[day.weekday()],
                "log": logs_dict.get(day, "-"),
            })

        return {
            "three_days_startlogs": three_days_results,
            "week_data": week_data,
        }


    # 月内の気分傾向を分析する共通メソッド
    def analyze_mood_flow(self, logs):
        if not logs.exists():
            return "-"

        mood_counts = (
            logs
            .values("mood__mood_name")
            .annotate(count=Count("startlog_id"))
            .order_by("-count")
        )

        top_count = mood_counts[0]["count"]
        total = sum(m["count"] for m in mood_counts)

        # 気分が1種類に集中している
        if top_count / total >= 0.6:
            name = mood_counts[0]["mood__mood_name"]
            if name in ["ふつう", "穏やか"]:
                return "穏やかな気分多め"
            elif name in ["楽しい"]:
                return "前向きな気分多め"
            elif name in ["疲れ気味", "悲しい"]:
                return "少し疲れ気味"
            else:
                return "気分は比較的一定"

        # 複数気分が混在
        return "気分にゆらぎあり"


    # 右カラム
    # 今月の振り返り用コンテキスト
    def get_month_summary_context(self, user, target_date=None):
        if target_date is None:
            target_date = timezone.localdate()

        month_start = target_date.replace(day=1)

        if target_date.month == 12:
            month_end = target_date.replace(year=target_date.year + 1, month=1, day=1) - timezone.timedelta(days=1)
        else:
            month_end = target_date.replace(month=target_date.month + 1, day=1) - timezone.timedelta(days=1)

        month_logs = StartLog.objects.filter(
            user=user,
            created_at__date__range=(month_start, month_end)
        )

        # 記録日数
        log_days = month_logs.count()

        # 月の日数
        _, month_days = calendar.monthrange(target_date.year, target_date.month)

        # 気分集計
        mood_counts = (
            month_logs
            .values("mood__emoji", "mood__mood_name")
            .annotate(
                count=Count("startlog_id"),
                last_date=Max("created_at"),
            )
            .order_by("-count", "-last_date")
        )
        main_mood = mood_counts[0] if mood_counts else None

        # --- 総評文作成 ---
        summary_text = None
        if main_mood:
            name = main_mood["mood__mood_name"]

            if name in ["ふつう", "穏やか"]:
                summary_text = "全体的に落ち着いた気分で過ごせています。"
            elif name in ["楽しい"]:
                summary_text = "前向きな気分の日が多いですね。"
            elif name in ["疲れ気味", "悲しい"]:
                summary_text = "少し頑張りすぎているかもしれません。"
            else:
                summary_text = "気分に少しゆらぎがあるようです。"


        month_days_total = (month_end - month_start).days + 1

        early_end = month_start + timezone.timedelta(days=month_days_total // 3)
        middle_end = month_start + timezone.timedelta(days=month_days_total * 2 // 3)

        early_logs = month_logs.filter(created_at__date__lte=early_end)
        middle_logs = month_logs.filter(
            created_at__date__gt=early_end,
            created_at__date__lte=middle_end
        )
        late_logs = month_logs.filter(created_at__date__gt=middle_end)

        month_flow = {
            "early": self.analyze_mood_flow(early_logs),
            "middle": self.analyze_mood_flow(middle_logs),
            "late": self.analyze_mood_flow(late_logs),
        }


        return {
            "month_year": target_date.year,
            "month_month": target_date.month,
            "month_log_days": log_days,
            "month_total_days": month_days,
            "month_main_mood": main_mood,
            "month_summary_text": summary_text,
            "month_flow": month_flow,
        }


class EndLogView(LoginRequiredMixin, View):
    login_url = "/login/"
    template_name = "endlog.html"

    def get(self, request):
        """今日のStartLogに基づいて提案色を表示"""
        user = request.user
        today = timezone.localdate()

        # StartLogを取得
        start_log = StartLog.objects.filter(user=user, created_at__date=today).first()
        if not start_log:
            return render(request, self.template_name, {"error": "本日のスタートログが見つかりません。"})

        # EndLogが既に存在する場合はTOPにリダイレクト
        existing_endlog = EndLog.objects.filter(user=user, startlog=start_log).first()
        if existing_endlog:
            return redirect("careapp:index")

        suggested_colors = start_log.suggestedcolor_set.order_by("order_index")
        moods = Mood.objects.all()

        context = {
            "suggested_colors": suggested_colors,
            "moods": moods,
        }
        return render(request, self.template_name, context)

    def post(self, request):

        def hex_to_hsl(hex_color):
            hex_color = hex_color.lstrip("#")
            r = int(hex_color[0:2], 16) / 255
            g = int(hex_color[2:4], 16) / 255
            b = int(hex_color[4:6], 16) / 255

            h, l, s = colorsys.rgb_to_hls(r, g, b)

            return f"hsl({int(h*360)}, {int(s*100)}%, {int(l*100)}%)"

        """選択内容をEndLogに保存"""
        user = request.user
        today = timezone.localdate()
        start_log = StartLog.objects.filter(user=user, created_at__date=today).first()
        if not start_log:
            return render(request, self.template_name, {"error": "スタートログが存在しません。"})

        # --- すでにEndLogがあれば入力禁止 ---
        if EndLog.objects.filter(user=user, startlog=start_log).exists():
            return redirect("careapp:index")

        # --- 入力値取得 ---
        selected_color_id = request.POST.get("selected_color")
        other_color_hex = request.POST.get("other_color_hex")
        mood_id = request.POST.get("mood")
        note = request.POST.get("endlog_note", "")
        photo = request.FILES.get("photo")

        #  色未選択チェック
        if not selected_color_id:
            suggested_colors = start_log.suggestedcolor_set.order_by("order_index")
            moods = Mood.objects.all()
            context = {
                "suggested_colors": suggested_colors,
                "moods": moods,
                "error": "色を選択してください。",
                "prev_mood_id": mood_id,
                "prev_note": note,
            }
            return render(request, self.template_name, context)

        if selected_color_id == "other":
            # カラーパレット未選択防止
            if not other_color_hex:
                return render(request, self.template_name, {
                    "suggested_colors": start_log.suggestedcolor_set.order_by("order_index"),
                    "moods": Mood.objects.all(),
                    "error": "色を選択してください。",
                    "prev_color_id": "other",
                    "prev_other_color": other_color_hex,
                    "prev_mood_id": mood_id,
                    "prev_note": note,
                })
            hsl_value = hex_to_hsl(other_color_hex)

            # SuggestedColor として保存
            selected_color = SuggestedColor.objects.create(
                startlog=start_log,
                suggested_color_hsl=hsl_value,
                order_index=99  # その他は最後扱い
            )
        else:
            selected_color = SuggestedColor.objects.filter(
                pk=int(selected_color_id)
            ).first()


        mood = Mood.objects.filter(pk=mood_id).first() if mood_id else None

        end_log = EndLog.objects.create(
                    startlog=start_log,
                    user=user,
                    mood=mood,
                    selected_color=selected_color,
                    endlog_note=note,
                    photo=photo,
                )

        context = {
            "end_log": end_log
        }
        return render(request, "result.html", context)


class ResultView(View):
    template_name = "result.html"

    def post(self, request):
        """結果ページ表示"""
        return render(request, self.template_name)


class CalendarView(LoginRequiredMixin, View):
    login_url = "/login/"
    template_name = "calendar.html"

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        view_type = request.GET.get("view", "month")

        context = {"today": today, "view_type": view_type}

        if view_type == "year":
            # 年表示用の前後年計算
            prev_year = year - 1
            next_year = year + 1

            # 12か月リストを作成
            months = list(range(1, 13))

            # 1列4か月×3行に分割
            month_rows = [months[i:i+4] for i in range(0, 12, 4)]

            # 各月のカレンダーの日付を生成
            month_calendars = {}
            cal = calendar.Calendar(firstweekday=6)
            for m in months:
                month_days = list(cal.itermonthdates(year, m))
                # 週ごとに分割
                weeks = []
                week = []
                for day in month_days:
                    week.append(day)
                    if len(week) == 7:
                        weeks.append(week)
                        week = []
                if week:
                    weeks.append(week)
                month_calendars[m] = weeks  # 月番号をキーにして保存


            context.update({
                "year": year,
                "prev_year": prev_year,
                "next_year": next_year,
                "month_rows": month_rows,
                "month_calendars": month_calendars,
                "weekday_names": ["日", "月", "火", "水", "木", "金", "土"],
            })

        else:
            # --- 月表示 ---
            cal = calendar.Calendar(firstweekday=6)
            month_days = list(cal.itermonthdates(year, month))

            logs = StartLog.objects.filter(user=user, created_at__year=year, created_at__month=month)

            # StartLog に対応する EndLog が存在する StartLog の ID セットを取得
            complete_startlog_ids = set(
                EndLog.objects.filter(user=user, startlog__in=logs)
                .values_list("startlog_id", flat=True)
            )

            emoji_map = {}        # 完了日（StartLog + EndLog 両方あり）
            incomplete_map = {}   # 未完了日（StartLog のみ、EndLog なし）
            for log in logs:
                day_key = timezone.localtime(log.created_at).date().isoformat()
                if log.startlog_id in complete_startlog_ids:
                    emoji_map[day_key] = log.mood.emoji
                else:
                    incomplete_map[day_key] = log.mood.emoji

            weeks = []
            week = []
            for day in month_days:
                week.append(day)
                if len(week) == 7:
                    weeks.append(week)
                    week = []
            if week:
                weeks.append(week)

            prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
            next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

            context.update({
                "year": year,
                "month": month,
                "weeks": weeks,
                "emoji_map": emoji_map,
                "incomplete_map": incomplete_map,
                "prev_month": prev_month,
                "prev_year": prev_year,
                "next_month": next_month,
                "next_year": next_year,
                "weekday_names": ["日", "月", "火", "水", "木", "金", "土"],
            })

        return render(request, self.template_name, context)


class HistoryDetailView(LoginRequiredMixin, View):
    login_url = "/login/"
    template_name = "history_detail.html"

    def get(self, request, year, month, day):
        user = request.user
        target_date = date(year, month, day)

        start_log = StartLog.objects.filter(user=user, created_at__date=target_date).first()
        end_log = EndLog.objects.filter(user=user, created_at__date=target_date).first()
        start_colors = list(start_log.suggestedcolor_set
                            .filter(order_index__lt=99)
                            .order_by("order_index")) if start_log else []
        context = {
            "date": target_date,
            "start_log": start_log,
            "end_log": end_log,
            "start_colors": start_colors,
        }

        return render(request, self.template_name, context)


class GraphView(LoginRequiredMixin, View):
    login_url = "/login/"
    template_name = "graph.html"

    def get(self, request):
        user = request.user
        today = timezone.localdate()

        view_type = request.GET.get("view", "month")

        # 空文字対応
        year_param = request.GET.get("year")
        month_param = request.GET.get("month")

        year = int(year_param) if year_param else today.year
        month = int(month_param) if month_param else today.month

        context = {
            "view_type": view_type,
            "year": year,
        }

        # 年表示
        if view_type == "year":
            context.update({
                "months": list(range(1, 13)),
                "prev_year": year - 1,
                "next_year": year + 1,
            })
            return render(request, self.template_name, context)


        # 月表示
        first_day = date(year, month, 1)
        last_day = (first_day + timezone.timedelta(days=31)).replace(day=1) - timezone.timedelta(days=1)

        logs = StartLog.objects.filter(
            user=user,
            created_at__date__range=(first_day, last_day)
        ).order_by("created_at")

        CUSTOM_MOOD_ORDER = [1, 2, 3, 4, 5]

        moods = Mood.objects.filter(mood_id__in=CUSTOM_MOOD_ORDER)
        mood_dict = {m.mood_id: f"{m.emoji} {m.mood_name}" for m in moods}
        mood_labels = [mood_dict[mid] for mid in CUSTOM_MOOD_ORDER]

        dates = []
        mood_values = []
        mood_colors = []

        for log in logs:
            dates.append(log.created_at.day)
            mood_values.append(
                mood_dict.get(log.mood.mood_id) if log.mood else None
            )
            if log.mood and log.mood.base_color1:
                mood_colors.append(log.mood.base_color1.hsl_value)
            else:
                mood_colors.append("hsl(0, 0%, 70%)")

        prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
        next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

        context.update({
            "month": month,
            "dates": dates,
            "mood_values": mood_values,
            "mood_colors": mood_colors,
            "mood_labels": mood_labels,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
        })

        return render(request, self.template_name, context)


class PastLogView(LoginRequiredMixin, View):
    login_url = "/login/"
    template_name = "past_log.html"

    def get(self, request, year, month, day):
        user = request.user
        today = timezone.localdate()
        target_date = date(year, month, day)

        if target_date > today:
            return redirect("careapp:calendar")

        start_log = StartLog.objects.filter(user=user, created_at__date=target_date).first()
        end_log = EndLog.objects.filter(user=user, created_at__date=target_date).first()

        if start_log and end_log:
            return redirect("careapp:history_detail", year=year, month=month, day=day)

        moods = Mood.objects.all()
        context = {
            "target_date": target_date,
            "moods": moods,
            "start_log": start_log,
        }

        if start_log:
            context["suggested_colors"] = start_log.suggestedcolor_set.order_by("order_index")

        return render(request, self.template_name, context)

    def _suggest_colors(self, mood, intensity):
        def parse_hsl(hsl_str):
            match = re.match(r"hsl\((\d+),\s*(\d+)%?,\s*(\d+)%?\)", hsl_str)
            if not match:
                return (0, 0, 0)
            return map(int, match.groups())

        base_colors = [
            mood.base_color1.hsl_value if mood.base_color1 else "hsl(0, 0%, 50%)",
            mood.base_color2.hsl_value if mood.base_color2 else "hsl(0, 0%, 50%)",
            mood.base_color3.hsl_value if mood.base_color3 else "hsl(0, 0%, 50%)",
        ]

        def adjust_color(h, s, l, intensity):
            delta = (intensity - 50) / 50
            s = max(20, min(90, s - delta * 15))
            l = max(30, min(85, l + delta * 10))
            return f"hsl({h}, {int(s)}%, {int(l)}%)"

        colors = []
        for hsl_str in base_colors:
            h, s, l = parse_hsl(hsl_str)
            colors.append(adjust_color(h, s, l, intensity))
        return colors

    def _hex_to_hsl(self, hex_color):
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return f"hsl({int(h*360)}, {int(s*100)}%, {int(l*100)}%)"

    def post(self, request, year, month, day):
        user = request.user
        today = timezone.localdate()
        target_date = date(year, month, day)

        if target_date > today:
            return redirect("careapp:calendar")

        target_datetime = make_aware(datetime(year, month, day, 12, 0, 0))
        start_log = StartLog.objects.filter(user=user, created_at__date=target_date).first()

        # --- 朝のログ未保存 → 朝のログを保存して夜の入力フォームへ ---
        if not start_log:
            mood_name = request.POST.get("mood")
            intensity = int(request.POST.get("intensity", 50))
            comment = request.POST.get("comment", "")

            mood = Mood.objects.filter(mood_name=mood_name).first()
            advice = Advice.objects.filter(mood=mood).order_by("?").first()

            start_log = StartLog.objects.create(
                user=user,
                mood=mood,
                advice=advice,
                startlog_note=comment,
                intensity=intensity,
                created_at=target_datetime,
            )

            colors = self._suggest_colors(mood, intensity)
            for idx, color_hsl in enumerate(colors, start=1):
                SuggestedColor.objects.create(
                    startlog=start_log,
                    suggested_color_hsl=color_hsl,
                    order_index=idx,
                )

            context = {
                "target_date": target_date,
                "moods": Mood.objects.all(),
                "start_log": start_log,
                "suggested_colors": start_log.suggestedcolor_set.order_by("order_index"),
            }
            return render(request, self.template_name, context)

        # --- 朝のログ保存済み → 夜のログを保存 ---
        if EndLog.objects.filter(user=user, startlog=start_log).exists():
            return redirect("careapp:history_detail", year=year, month=month, day=day)

        selected_color_id = request.POST.get("selected_color")
        other_color_hex = request.POST.get("other_color_hex")
        mood_id = request.POST.get("mood")
        note = request.POST.get("endlog_note", "")
        photo = request.FILES.get("photo")

        if not selected_color_id:
            context = {
                "target_date": target_date,
                "moods": Mood.objects.all(),
                "start_log": start_log,
                "suggested_colors": start_log.suggestedcolor_set.order_by("order_index"),
                "error": "色を選択してください。",
            }
            return render(request, self.template_name, context)

        if selected_color_id == "other":
            hsl_value = self._hex_to_hsl(other_color_hex) if other_color_hex else "hsl(0, 0%, 80%)"
            selected_color = SuggestedColor.objects.create(
                startlog=start_log,
                suggested_color_hsl=hsl_value,
                order_index=99,
            )
        else:
            selected_color = SuggestedColor.objects.filter(pk=int(selected_color_id)).first()

        mood = Mood.objects.filter(pk=mood_id).first() if mood_id else None

        EndLog.objects.create(
            startlog=start_log,
            user=user,
            mood=mood,
            selected_color=selected_color,
            endlog_note=note,
            photo=photo,
            created_at=target_datetime,
        )

        return redirect("careapp:history_detail", year=year, month=month, day=day)
