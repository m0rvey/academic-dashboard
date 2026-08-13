from src.core.logger import setup_logger

logger = setup_logger("notifications")


def notify_mac(title: str, subtitle: str, message: str):
    """Отправка системного уведомления на macOS через AppleScript (osascript) в фоновом потоке."""
    import subprocess
    import threading

    title_esc = title.replace('"', '\\"')
    sub_esc = subtitle.replace('"', '\\"')
    msg_esc = message.replace('"', '\\"')

    script = f'display notification "{msg_esc}" with title "{title_esc}" subtitle "{sub_esc}" sound name "Glass"'

    def run():
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True)
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления macOS: {e}", exc_info=True)

    threading.Thread(target=run, daemon=True).start()


def send_desktop_notifications(
    db,
    notified_task_ids,
    active_notification_tasks,
    _on_notification_done,
    last_notification_date_ref,
):
    """Отправляет уведомления macOS для задач с дедлайном сегодня или завтра."""
    from datetime import date, timedelta

    today_date = date.today()
    if today_date != last_notification_date_ref[0]:
        notified_task_ids.clear()
        last_notification_date_ref[0] = today_date

    tomorrow_date = today_date + timedelta(days=1)
    try:
        today_tasks = db.get_tasks_by_date(today_date.isoformat())
        tomorrow_tasks = db.get_tasks_by_date(tomorrow_date.isoformat())
    except Exception as e:
        logger.warning(f"Error fetching tasks for notifications: {e}")
        today_tasks, tomorrow_tasks = [], []

    for t in today_tasks:
        if t.id not in notified_task_ids:
            notify_mac(
                title="Academic Dashboard",
                subtitle="Дедлайн сегодня!",
                message=f"Задача по предмету '{t.subject}': {t.description}",
            )
            notified_task_ids.add(t.id)

    for t in tomorrow_tasks:
        if t.id not in notified_task_ids:
            notify_mac(
                title="Academic Dashboard",
                subtitle="Дедлайн завтра",
                message=f"Задача по предмету '{t.subject}': {t.description}",
            )
            notified_task_ids.add(t.id)
