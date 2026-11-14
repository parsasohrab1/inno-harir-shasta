# HarirSmart AI

سامانه هوشمند بهینه‌سازی چندهدفه آبگیری و خشک‌کن خط تولید تیشو برای شرکت حریر خوزستان.

## مستندات
- [BRS — نیازمندی‌های کسب‌وکار](docs/BRS/BRS-HarirSmart-AI.md)
- [SRS — نیازمندی‌های نرم‌افزار](docs/SRS/SRS-HarirSmart-AI.md)

## رویکرد نسخه نخست
نسخه اول read-only و Advisory است: داده‌های مجاز را دریافت می‌کند، کیفیت داده را می‌سنجد، رطوبت و انرژی را پیش‌بینی می‌کند، سناریوها را در دوقلوی دیجیتال ارزیابی می‌کند و پیشنهاد مقید به اپراتور می‌دهد. هیچ فرمانی به PLC/DCS ارسال نمی‌شود.

## دامنه اصلی
- Dewatering optimization
- Dryer/Yankee and steam optimization (subject to actual machine configuration)
- Moisture and quality prediction
- Digital twin and constrained multi-objective optimization
- Offline RL training and policy evaluation
- Data validation/reconciliation, KPI dashboards and audit trail

## شروع پروژه
قبل از طراحی تفصیلی باید tag list، نقشه فرایند، مشخصات ماشین، حدود مجاز سازنده، داده تاریخی، نتایج آزمایشگاه، کنتورهای بخار/انرژی و سیاست امنیت OT از کارفرما دریافت شوند.

## نکته مهم
اهداف ۱۰–۲۰٪ کاهش انرژی، اهداف آزمایشی پایلوت هستند و تا زمان اندازه‌گیری baseline نرمال‌شده و آزمون کنترل‌شده، تضمین عملکرد محسوب نمی‌شوند. RL در محیط شبیه‌سازی آموزش داده می‌شود؛ exploration روی ماشین واقعی مجاز نیست.

## وضعیت
اسناد نسخه 1.0 برای کشف نیاز و تأیید ذی‌نفعان آماده شده‌اند. جزئیات سخت‌افزار، پروتکل و حدود فرایندی هنوز نیازمند تأیید کارخانه هستند.
