# HarirSmart AI

سامانه هوشمند بهینه‌سازی چندهدفه آبگیری و خشک‌کن خط تولید تیشو برای شرکت حریر خوزستان.

## مستندات
- [BRS — نیازمندی‌های کسب‌وکار](docs/BRS/BRS-HarirSmart-AI.md)
- [SRS — نیازمندی‌های نرم‌افزار](docs/SRS/SRS-HarirSmart-AI.md)
- [معماری اجرایی MVP و مرزهای ایمنی](docs/ARCHITECTURE/MVP-Architecture.md)

## وضعیت MVP نسخه 0.1.0
- FastAPI backend با APIهای health، sample ingestion، dashboard، optimization advisory و audit.
- شبیه‌ساز داده مصنوعی برای تست محلی.
- DVR اولیه: کنترل فیلدهای الزامی، نوع/محدوده عددی، تازگی timestamp و سازگاری رطوبت.
- KPIهای نمایشی و یک بهینه‌ساز grid-search شفاف برای سناریوهای what-if.
- داشبورد فارسی RTL.
- تست‌های واحد برای کیفیت داده و منطق پیشنهاد.

## اجرای محلی
~~~bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
~~~

داشبورد: http://127.0.0.1:8000  
مستند API: http://127.0.0.1:8000/docs

اجرای تست‌ها:
~~~bash
pytest -q
~~~

## مرز ایمنی و اعتبار داده
نسخه نخست فقط **Read-only / Advisory** است و هیچ مسیر نوشتن یا ارسال فرمان به PLC/DCS ندارد. ثبت پذیرش/رد پیشنهاد صرفاً ثبت رویداد است و اجرای فرایندی ایجاد نمی‌کند. RL در این نسخه پیاده‌سازی نشده؛ هرگونه RL آتی فقط در شبیه‌ساز و به‌صورت آفلاین مجاز است و exploration روی ماشین واقعی ممنوع خواهد بود.

تمام مقادیر، بازه‌های plausibility، ضرایب مدل و deltaهای بهینه‌ساز در این MVP مصنوعی و صرفاً برای آزمایش نرم‌افزار هستند؛ آن‌ها حدود مجاز واقعی ماشین یا setpoint تأییدشده نیستند. پیش از پایلوت باید tag list، پیکربندی ماشین، حدود OEM، کنتورهای کالیبره، داده کیفیت و الزامات IT/OT/HSE از کارخانه اخذ و تأیید شوند.

هدف تحقیقاتی ۱۰–۲۰٪ کاهش انرژی ویژه خشک‌کن فقط فرضیه قابل ارزیابی در پایلوت با baseline نرمال‌شده است و تضمین عملکرد نیست.
