"""Notification service for study reminders."""
import logging
import platform
from datetime import datetime, time
from typing import Optional
import schedule
import threading
import time as time_module

from src.config import config, DATA_DIR

logger = logging.getLogger(__name__)

_is_initialized = False
_scheduler_thread: Optional[threading.Thread] = None


def _get_notification_title() -> str:
    return "Пора учить русский!"


def _get_notification_message(due_count: int) -> str:
    if due_count == 0:
        return "Сегодня нет карточек на повторение. Отличный день!"
    elif due_count == 1:
        return "1 карточка ждёт повторения"
    elif due_count < 5:
        return f"{due_count} карточки ждут повторения"
    else:
        return f"{due_count} карточек ждут повторения"


def _send_desktop_notification(title: str, message: str) -> bool:
    """Send notification using plyer."""
    try:
        from plyer import notification

        notification.notify(
            title=title,
            message=message,
            app_name="Russian Flashcards",
            timeout=10,
        )
        return True
    except Exception as e:
        logger.warning(f"Failed to send notification: {e}")
        return False


def _send_android_notification(title: str, message: str) -> bool:
    """Send Android notification with proper permissions."""
    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        NotificationManager = autoclass("android.app.NotificationManager")
        NotificationBuilder = autoclass("android.app.Notification$Builder")
        Context = autoclass("android.content.Context")

        activity = PythonActivity.mActivity
        nm = activity.getSystemService(Context.NOTIFICATION_SERVICE)

        builder = NotificationBuilder(activity)
        builder.setContentTitle(title)
        builder.setContentText(message)
        builder.setSmallIcon(activity.getResources().getIdentifier("ic_launcher", "mipmap", activity.getPackageName()))
        builder.setAutoCancel(True)

        notification = builder.build()
        nm.notify(1, notification)
        return True
    except Exception as e:
        logger.debug(f"Android notification not available: {e}")
        return False


def send_notification(title: str, message: str) -> bool:
    """Send platform-appropriate notification."""
    if platform.system() == "Android":
        return _send_android_notification(title, message)
    return _send_desktop_notification(title, message)


async def check_and_notify() -> None:
    """Check for due reviews and send notification."""
    try:
        from src.data.user_progress import get_due_cards

        due = await get_due_cards(limit=100)
        due_count = len(due)

        if due_count > 0 or config.notification_enabled:
            title = _get_notification_title()
            message = _get_notification_message(due_count)
            send_notification(title, message)
            logger.info(f"Notification sent: {due_count} cards due")
    except Exception as e:
        logger.error(f"Failed to check and notify: {e}")


def _schedule_job() -> None:
    """Run the scheduler loop in a background thread."""
    while True:
        schedule.run_pending()
        time_module.sleep(60)


def start_scheduler() -> None:
    """Start the notification scheduler."""
    global _is_initialized, _scheduler_thread

    if _is_initialized:
        return

    if config.notification_enabled:
        # Schedule daily notification
        notify_time = time(
            config.notification_hour,
            config.notification_minute,
        )
        schedule.every().day.at(notify_time.strftime("%H:%M")).do(_daily_notification_job)

        # Start scheduler thread
        _scheduler_thread = threading.Thread(target=_schedule_job, daemon=True)
        _scheduler_thread.start()
        _is_initialized = True
        logger.info(f"Notification scheduler started at {notify_time}")


def _daily_notification_job() -> None:
    """Daily job to send notification."""
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(check_and_notify())
        loop.close()
    except Exception as e:
        logger.error(f"Daily notification job failed: {e}")


def stop_scheduler() -> None:
    """Stop the notification scheduler."""
    global _is_initialized, _scheduler_thread
    schedule.clear()
    _is_initialized = False
    logger.info("Notification scheduler stopped")
