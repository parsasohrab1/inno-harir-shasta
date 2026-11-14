# HarirSmart AI

سامانه هوشمند بهینه‌سازی چندهدفه آبگیری و خشک‌کن خط تولید تیشو برای شرکت حریر خوزستان.

## مستندات
- [BRS — نیازمندی‌های کسب‌وکار](docs/BRS/BRS-HarirSmart-AI.md)
- [SRS — نیازمندی‌های نرم‌افزار](docs/SRS/SRS-HarirSmart-AI.md)
- [معماری اجرایی MVP و مرزهای ایمنی](docs/ARCHITECTURE/MVP-Architecture.md)
- [معماری پیاده‌سازی نسخه 0.2 و مدل داده](docs/ARCHITECTURE/MVP-Implementation-v0.2.md)
- [وضعیت پیاده‌سازی و محدودیت‌ها](docs/IMPLEMENTATION-STATUS.md)
- [بسته آمادگی پایلوت صنعتی و درخواست داده](docs/PILOT/Pilot-Data-Readiness-Pack.md)

## وضعیت MVP نسخه 0.2
- FastAPI backend با health، ingestion، history، dashboard، DVR، Digital Twin، optimizer چندهدفه، تصمیم اپراتور و audit.
- قرارداد ReadOnlyTagAdapter و SimulatorAdapter برای جداکردن منبع داده از لایه ingestion؛ هیچ متد نوشتن در قرارداد آداپتور وجود ندارد.
- SQLite برای نگهداری پایدار نمونه‌های خام، نتیجه کیفیت/DVR، پیشنهادها و رویدادهای ممیزی؛ مسیر فایل با HARIRSMART_DB_PATH قابل تنظیم است.
- DVR تگ‌محور با کنترل واحد، محدوده نمایشی، timestamp، تازگی، duplicate/missing و source quality؛ مقدار خام حفظ می‌شود و اصلاح خودکار انجام نمی‌شود.
- شبیه‌ساز داده مصنوعی و Digital Twin تجربی برای what-if؛ مدل صریحاً کالیبره‌نشده است.
- جست‌وجوی سناریو و Pareto با سه هدف نمایشی: کمینه‌سازی بخار ویژه proxy، کمینه‌سازی خطای رطوبت و بیشینه‌سازی نرخ تولید proxy.
- داشبورد فارسی RTL با روند داده، وضعیت DVR، خروجی Twin، پیشنهاد و رویدادهای ممیزی.
- RL همچنان فقط scaffold آفلاین و مبتنی بر transitionهای از پیش ثبت‌شده است؛ هیچ online exploration یا تعامل تجهیز وجود ندارد.

## مرحله بعد: آمادگی پایلوت صنعتی
بسته `docs/PILOT/` برای دریافت و تأیید داده واقعی تهیه شده است:
- `Pilot-Data-Readiness-Pack.md`: گردش کار، stage gateها، قرارداد داده، DVR، موازنه جرم/انرژی، کالیبراسیون و اعتبارسنجی مستقل Twin.
- `templates/tag-register.csv`: ثبت Tag List، واحدها، timestamp، کیفیت، کالیبراسیون و تأیید مالک.
- `templates/historian-sample.csv`: قالب فراداده و نمونه‌های Historian.
- `templates/lab-results.csv`: نتایج آزمایشگاه با پیوند نمونه/رول/بچ.
- `templates/oem-envelope.csv`: ثبت حدود OEM با مرجع سند و تأییدیه.

این فایل‌های CSV فقط header/template هستند و حاوی داده واقعی کارخانه نیستند. اتصال OT، کالیبراسیون Twin و محاسبه plant-grade موازنه‌ها تا دریافت و تأیید ورودی‌های واقعی مسدود می‌مانند.

## اجرای محلی
1. Python 3.10 یا بالاتر نصب باشد.
2. در ریشه مخزن:

    python -m venv .venv

    Windows: .venv\Scripts\activate

    Linux/macOS: source .venv/bin/activate

    pip install -r requirements.txt

    uvicorn app.main:app --reload

3. داشبورد: http://127.0.0.1:8000
4. مستند API: http://127.0.0.1:8000/docs
5. تست‌ها: pytest -q

پایگاه داده به‌صورت پیش‌فرض در data/harirsmart.db ساخته می‌شود. برای تغییر مسیر، متغیر محیطی HARIRSMART_DB_PATH را تنظیم کنید.

## APIهای اصلی
- GET /api/v1/health
- GET /api/v1/simulator/sample
- POST /api/v1/samples
- GET /api/v1/history
- POST /api/v1/dvr/validate
- GET /api/v1/dashboard
- POST /api/v1/twin/simulate
- POST /api/v1/optimize
- POST /api/v1/proposals/{proposal_id}/decision
- GET /api/v1/audit

## مرز ایمنی و اعتبار داده
نسخه نخست فقط **Read-only / Advisory** است و هیچ مسیر نوشتن یا ارسال فرمان به PLC/DCS ندارد. ثبت پذیرش/رد پیشنهاد صرفاً ثبت رویداد است و اجرای فرایندی ایجاد نمی‌کند. چارچوب RL فقط به‌صورت scaffold آفلاین و مبتنی بر transitionهای از پیش ثبت‌شده است؛ هیچ تعامل با محیط زنده ندارد و منبع live را رد می‌کند. exploration روی ماشین واقعی ممنوع است.

تمام مقادیر، بازه‌های plausibility، ضرایب Digital Twin و deltaهای بهینه‌ساز در این MVP مصنوعی و صرفاً برای آزمایش نرم‌افزار هستند؛ آن‌ها حدود مجاز واقعی ماشین یا setpoint تأییدشده نیستند. پیش از پایلوت باید tag list، پیکربندی ماشین، حدود OEM، کنتورهای کالیبره، داده کیفیت و الزامات IT/OT/HSE از کارخانه اخذ و تأیید شوند.

هدف تحقیقاتی ۱۰–۲۰٪ کاهش انرژی ویژه خشک‌کن فقط فرضیه قابل ارزیابی در پایلوت با baseline نرمال‌شده است و تضمین عملکرد نیست.
