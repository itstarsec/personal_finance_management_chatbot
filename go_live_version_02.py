# TOKEN = '1042835941:AAGB6qaHY8ml-GspYcSpKi3_119mtLumySo'
# -*- coding: utf-8 -*-

from locale import setlocale, LC_ALL
import logging
import time
from datetime import datetime, timezone, timedelta
import re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import sqlite3
from sqlite3 import connect, Row

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def init_database():
    conn = connect('budget_bot.db', check_same_thread=False)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS budget (
            user_id INTEGER PRIMARY KEY,
            expenses INTEGER,
            savings INTEGER
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expense_history (
            user_id INTEGER,
            title TEXT,
            amount INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            user_id INTEGER,
            amount INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.row_factory = Row
    return conn

def get_sqlite_connection():
    if not hasattr(get_sqlite_connection, 'connection'):
        get_sqlite_connection.connection = init_database()
    return get_sqlite_connection.connection
    
def get_total_budget(user_id):
    connection = get_sqlite_connection()
    with connection:
        cursor = connection.cursor()
        cursor.execute('SELECT expenses FROM budget WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result is not None:
            expenses = result['expenses']
            return expenses
        else:
            return 0
            
def get_total_expenses(user_id):
    connection = get_sqlite_connection()
    with connection:
        cursor = connection.cursor()
        cursor.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        total_expenses = result[0] if result[0] is not None else 0
        return total_expenses
# Hàm định dạng số có dấu phẩy
def format_number(number):
    setlocale(LC_ALL, 'en_US.UTF-8')  # Đặt ngôn ngữ sang tiếng Anh để sử dụng định dạng số có dấu phẩy
    return "{:,.0f}".format(number)
    
# Hàm kiểm tra số tiền đã tiêu
def check_remaining_budget(update, context):
    user_id = update.message.from_user.id
    total_budget = get_total_budget(user_id)
    total_expense_history = get_total_expense_history(user_id)

    remaining_budget = total_budget - total_expense_history
    formatted_total_expense_history = format_number(total_expense_history)
    formatted_remaining_budget = format_number_with_commas(remaining_budget)

    update.message.reply_text(f'Tổng số tiền đã chi tiêu từ lịch sử: {formatted_total_expense_history}\n'
                              f'Số tiền còn lại có thể chi tiêu là {formatted_remaining_budget}.')

   

def get_total_expense_history(user_id):
    connection = get_sqlite_connection()
    with connection:
        cursor = connection.cursor()
        cursor.execute('SELECT SUM(amount) FROM expense_history WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        total_expense_history = result[0] if result[0] is not None else 0
        return total_expense_history

def get_remaining_budget(user_id):
    connection = get_sqlite_connection()
    with connection:
        cursor = connection.cursor()
        cursor.execute('SELECT expenses, savings FROM budget WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result is not None:
            expenses = result['expenses']
            # savings = result['savings']

            # Lấy tổng chi tiêu từ bảng expenses
            total_expenses = get_total_expenses(user_id)

            remaining_budget = expenses - total_expenses
            return remaining_budget
        else:
            return 0

def format_number_with_commas(number):
    return '{:,.0f}'.format(number)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Chào mừng bạn đến với Budget Bot! Hãy bắt đầu bằng cách sử dụng /set.')

def set_budget(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    connection = get_sqlite_connection()
    with connection:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM budget WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result:
            update.message.reply_text('Bạn đã thiết lập ngân sách trước đó. Sử dụng /update để cập nhật.')
        else:
            context.user_data['setting_budget'] = True
            update.message.reply_text('Hãy nhập số tiền bạn muốn dành cho chi phí hàng tháng:')

def update_budget(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    connection = get_sqlite_connection()
    with connection:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM budget WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

    if not result:
        update.message.reply_text('Bạn chưa thiết lập ngân sách. Hãy sử dụng /set để bắt đầu.')
        return

    context.user_data['updating_budget'] = True
    update.message.reply_text('Hãy nhập số tiền bạn muốn cập nhật cho chi phí hàng tháng:')

def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if context.user_data.get('setting_budget', False):
        try:
            expenses = int(update.message.text.replace(',', ''))
            connection = get_sqlite_connection()
            with connection:
                cursor = connection.cursor()
                cursor.execute('INSERT OR REPLACE INTO budget (user_id, expenses, savings) VALUES (?, ?, 0)', (user_id, expenses))
            context.user_data['setting_budget'] = False
            remaining_budget = get_remaining_budget(user_id)
            formatted_remaining_budget = format_number_with_commas(remaining_budget)
            update.message.reply_text(f'Ngân sách đã được thiết lập thành công. Số tiền có thể chi tiêu còn lại là {formatted_remaining_budget}đ.\nHãy sử dụng lệnh /help để xem danh sách lệnh')
        except ValueError:
            update.message.reply_text('Vui lòng nhập số nguyên hợp lệ cho ngân sách. (ví dụ: 1000000)')

    elif context.user_data.get('updating_budget', False):
        try:
            expenses = int(update.message.text.replace(',', ''))
            connection = get_sqlite_connection()
            with connection:
                cursor = connection.cursor()
                cursor.execute('UPDATE budget SET expenses = ? WHERE user_id = ?', (expenses, user_id))
            context.user_data['updating_budget'] = False
            remaining_budget = get_remaining_budget(user_id)
            formatted_remaining_budget = format_number_with_commas(remaining_budget)
            update.message.reply_text(f'Ngân sách đã được cập nhật thành công. Số tiền có thể chi tiêu còn lại là {formatted_remaining_budget}đ.\nHãy sử dụng lệnh /help để xem danh sách lệnh')
        except ValueError:
            update.message.reply_text('Vui lòng nhập số nguyên hợp lệ cho ngân sách.')

    else:
        try:
            regex_pattern = r"(.*?)\s+(\d+)$"
            match = re.match(regex_pattern, update.message.text.lower())
            title = match.group(1).strip()
            amount = int(match.group(2))
            save_expense_history(user_id, title, amount)
            update_budget_info(user_id, amount)
            remaining_budget = get_remaining_budget(user_id)
            formatted_remaining_budget = format_number_with_commas(remaining_budget)
            update.message.reply_text(f'Dữ liệu chi tiêu đã được cập nhật.')
        except (AttributeError, ValueError):
            update.message.reply_text('Vui lòng nhập định dạng hợp lệ, ví dụ: "Tiền ăn 200".')

# Hàm lưu lịch sử chi tiêu
def save_expense_history(user_id, title, amount):
    connection = get_sqlite_connection()
    with connection:
        cursor = connection.cursor()
        cursor.execute('INSERT INTO expense_history (user_id, title, amount, date) VALUES (?, ?, ?, ?)', (user_id, title, amount, int(time.time())))
        
# Hàm cập nhật thông tin ngân sách
def update_budget_info(user_id, amount):
    connection = get_sqlite_connection()
    with connection:
        cursor = connection.cursor()
        cursor.execute('INSERT INTO expenses (user_id, amount, date) VALUES (?, ?, ?)',
                       (user_id, amount, datetime.now()))        

# Hàm xem lịch sử chi tiêu
def view_expense_history(update, context):
    user_id = update.message.from_user.id
    expense_history = get_expense_history(user_id)
    if expense_history:
        total_expense_history = get_total_expense_history(user_id)
        message = f"Lịch sử chi tiêu (Tổng số tiền đã chi tiêu: {format_number(total_expense_history)}):\n"
        for expense in expense_history:
            formatted_date = convert_to_str(expense['date'])
            message += f"{formatted_date} - {expense['title']}: {format_number(expense['amount'])}đ\n"
        update.message.reply_text(message)
    else:
        update.message.reply_text("Không có dữ liệu lịch sử chi tiêu.")        
        
# Hàm chuyển đổi ngày thành chuỗi
def convert_to_str(date):
    if isinstance(date, int):
        utc_time = datetime.utcfromtimestamp(date)
        hanoi_time = utc_time.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=7)))
        return hanoi_time.strftime("%Y-%m-%d %H:%M:%S")
    return date
# Hàm lấy lịch sử chi tiêu
def get_expense_history(user_id):
    connection = get_sqlite_connection()
    with connection:
        cursor = connection.cursor()
        cursor.execute('SELECT title, amount, date FROM expense_history WHERE user_id = ?', (user_id,))
        result = cursor.fetchall()
        return result        

def clear_all_expense_history(user_id):
    connection = get_sqlite_connection()
    with connection:
        cursor = connection.cursor()
        cursor.execute('DELETE FROM expense_history WHERE user_id = ?', (user_id,))

def show_help(update: Update, context: CallbackContext) -> None:
    help_message = '''
    Các lệnh sử dụng với Budget Bot:    
    /help - Hiển thị các lệnh sử dụng của bot.    
    /set - Thiết lập ngân sách chi tiêu.
    /update - Cập nhật ngân sách chi tiêu.
    /check - Kiểm tra số tiền có thể chi tiêu còn lại.
    /history - Xem lịch sử chi tiêu.
    /delete - Xoá một thông tin chi tiêu gần nhất.    
    /reset - Reset tất cả thông tin và quay lại bước thiết lập ngân sách.
    '''
    update.message.reply_text(help_message)
def reset_expenses(user_id):
    connection = get_sqlite_connection()
    with connection:
        cursor = connection.cursor()
        cursor.execute('DELETE FROM expenses WHERE user_id = ?', (user_id,))

def reset_all_data(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    clear_all_expense_history(user_id)
    reset_budget(user_id)
    reset_expenses(user_id)
    update.message.reply_text("Tất cả thông tin đã được reset. Bạn có thể bắt đầu lại bằng cách sử dụng /set.")

def delete_last_expense_history(user_id):
    connection = get_sqlite_connection()
    
    with connection:
        cursor = connection.cursor()
        cursor.execute('DELETE FROM expense_history WHERE user_id = ? AND date = (SELECT MAX(date) FROM expense_history WHERE user_id = ?)', (user_id, user_id))
        
def delete_last_expense(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    connection = get_sqlite_connection()
    
    with connection:
        cursor = connection.cursor()
        cursor.execute('SELECT amount, date FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 1', (user_id,))
        result = cursor.fetchone()

        if result:
            amount = result['amount']
            date = result['date']
            cursor.execute('DELETE FROM expenses WHERE user_id = ? AND date = ?', (user_id, date))
            delete_last_expense_history(user_id)
            remaining_budget = get_remaining_budget(user_id)
            formatted_remaining_budget = format_number_with_commas(remaining_budget)
            update.message.reply_text(f'Chi tiêu gần nhất đã được xoá. Số tiền có thể chi tiêu còn lại là {formatted_remaining_budget}đ.')
        else:
            update.message.reply_text('Không có chi tiêu nào để xoá.')
    
def reset_budget(user_id):
    connection = get_sqlite_connection()
    with connection:
        cursor = connection.cursor()
        cursor.execute('DELETE FROM budget WHERE user_id = ?', (user_id,))

def main() -> None:
    updater = Updater("6408491360:AAHJMkUb8fc8NZWTKXrSEITpa1SJ4D0LNf0")
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("set", set_budget))
    dispatcher.add_handler(CommandHandler("update", update_budget))
    dispatcher.add_handler(CommandHandler("check", check_remaining_budget))
    dispatcher.add_handler(CommandHandler("history", view_expense_history))
    dispatcher.add_handler(CommandHandler("help", show_help))
    dispatcher.add_handler(CommandHandler("delete", delete_last_expense))  
    dispatcher.add_handler(CommandHandler("reset", reset_all_data))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
