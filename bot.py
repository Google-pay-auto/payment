import telebot
from telebot import types
import sqlite3

# إعداد البوت
API_TOKEN = '8968589592:AAHmfyCRkM4Xladdy3c7ct8qalchU4OFI-s'  # ⚠️ يفضل عمل Revoke وتغييره لاحقاً للأمان
ADMIN_USERNAME = '@mbvvhjjbb'
ADMIN_ID = 5437487652  # ⚠️ ضع هنا الأيدي الرقمي الخاص بحسابك لتلقي إشعارات الدفع

# رابط صفحة الـ HTML الخاصة بك على GitHub Pages
WEB_APP_URL = "https://google-pay-auto.github.io/payment/auto.html"

# --- عناوين وأسعار طرق الدفع ---
BINANCE_ADDRESS = "1210403690"
SHAMCASH_ADDRESS = "6bf82cecf71637705f0cf2f728da48e4"
SHAMCASH_BARCODE_NOTE ="99999999999999"
SHAMCASH_RATE_SYP_PER_USD = 13500
USDT_TRC20_ADDRESS = "TDQrnJPFyXA26M8PE16tqfRDn8SLDZ7p6v"
SYRIATEL_CASH_NUMBERS = "15321231"
SYRIATEL_CASH_MIN_SYP = 1350

bot = telebot.TeleBot(API_TOKEN)

# --- فئات الشحن ---
CATEGORIES = {
    "buy_100k": {"label": "100,000", "price": 10},
    "buy_220k": {"label": "220,000", "price": 20},
    "buy_330k": {"label": "330,000", "price": 30},
    "buy_1m":   {"label": "1,000,000", "price": 80},
    "buy_2m":   {"label": "2,000,000", "price": 150},
}

# --- إعداد قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recharge_orders
                      (order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id INTEGER,
                       method TEXT,
                       tx_id TEXT,
                       amount_usd REAL,
                       raw_amount REAL,
                       status TEXT DEFAULT 'pending')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS purchase_orders
                      (order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id INTEGER,
                       category TEXT,
                       price REAL,
                       game_id TEXT,
                       status TEXT DEFAULT 'pending')''')
    conn.commit()
    conn.close()

init_db()

# --- دوال قاعدة البيانات ---

def create_recharge_order(user_id, method, tx_id, amount_usd, raw_amount):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO recharge_orders (user_id, method, tx_id, amount_usd, raw_amount)
                      VALUES (?, ?, ?, ?, ?)''', (user_id, method, tx_id, amount_usd, raw_amount))
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    return order_id

def get_recharge_order(order_id):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, user_id, method, tx_id, amount_usd, raw_amount, status FROM recharge_orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if not row: return None
    keys = ["order_id", "user_id", "method", "tx_id", "amount_usd", "raw_amount", "status"]
    return dict(zip(keys, row))

def set_recharge_status(order_id, status):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE recharge_orders SET status = ? WHERE order_id = ?", (status, order_id))
    conn.commit()
    conn.close()

def create_purchase_order(user_id, category, price, game_id):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO purchase_orders (user_id, category, price, game_id)
                      VALUES (?, ?, ?, ?)''', (user_id, category, price, game_id))
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    return order_id

def get_purchase_order(order_id):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, user_id, category, price, game_id, status FROM purchase_orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if not row: return None
    keys = ["order_id", "user_id", "category", "price", "game_id", "status"]
    return dict(zip(keys, row))

def set_purchase_status(order_id, status):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE purchase_orders SET status = ? WHERE order_id = ?", (status, order_id))
    conn.commit()
    conn.close()

def update_user(user_id):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def add_balance(user_id, amount):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def deduct_balance(user_id, amount):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def user_display(message_from_user, chat_id):
    username = message_from_user.username if message_from_user.username else 'بدون يوزر'
    return f"@{username} ({chat_id})"

# --- القوائم ومولدات الأزرار ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ إضافة رصيد في البوت", callback_data="add_balance"))
    for key, c in CATEGORIES.items():
        markup.add(types.InlineKeyboardButton(f"{c['label']} -> {c['price']}$", callback_data=key))
    markup.add(types.InlineKeyboardButton("💰 الاستعلام عن الرصيد", callback_data="check_balance"))
    return markup

def recharge_methods_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🟡 Binance", callback_data="pay_binance"),
        types.InlineKeyboardButton("💵 Sham Cash (USD / SYP)", callback_data="pay_shamcash"),
        types.InlineKeyboardButton("📱 Syriatel Cash", callback_data="pay_syriatel"),
        types.InlineKeyboardButton("🔷 Usdt Trc20", callback_data="pay_usdt_trc20"),
        types.InlineKeyboardButton("⬅️ عودة للقائمة الرئيسية", callback_data="start_menu")
    )
    return markup

def back_to_main_only():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ عودة للقائمة الرئيسية", callback_data="start_menu"))
    return markup

def admin_recharge_decision_markup(order_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ قبول", callback_data=f"approve_{order_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{order_id}")
    )
    return markup

def admin_purchase_shipped_markup(order_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📦 تم الشحن", callback_data=f"shipped_{order_id}"))
    return markup

# --- المعالجات الأساسية للبوت ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    update_user(message.chat.id)
    bot.send_message(message.chat.id, "اهلا بك في متجر جواكر اختر العملية:", reply_markup=types.ReplyKeyboardRemove())
    bot.send_message(message.chat.id, "القائمة الرئيسية:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id

    if call.data == "start_menu":
        bot.edit_message_text("اهلا بك في متجر جواكر اختر العملية:", chat_id, call.message.message_id, reply_markup=main_menu())

    elif call.data == "add_balance":
        bot.edit_message_text("اختر طريقة الدفع:", chat_id, call.message.message_id, reply_markup=recharge_methods_menu())

    elif call.data == "check_balance":
        balance = get_balance(chat_id)
        bot.edit_message_text(f"💰 رصيدك الحالي: *{balance}$*", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=back_to_main_only())

    # ---- طرق شحن الرصيد اليدوية ----
    elif call.data == "pay_binance":
        bot.edit_message_text("ارسل ♦️ Usdt حصرا ♦️ الى العنوان :\n" f"{BINANCE_ADDRESS}\n\n" "ثم أدخل رقم عملية التحويل :", chat_id, call.message.message_id)
        bot.register_next_step_handler_by_chat_id(chat_id, lambda m: receive_tx_id(m, "binance"))

    elif call.data == "pay_shamcash":
        bot.edit_message_text("♦️⚠️ انتبه لعنواااان الحساب جيدا ⚠️♦️\n\n" "♦️ اي تحويل على حساب قديم لسنا مسؤولين عنه ♦️\n\n" f"ارسل إلى العنوان التالي أو عن طريق باركود شام كاش :\n{SHAMCASH_ADDRESS}\n{SHAMCASH_BARCODE_NOTE}\n\n" f"ثم ادخل رقم العملية :\n1 ShamCash USD = {SHAMCASH_RATE_SYP_PER_USD} SYP", chat_id, call.message.message_id)
        bot.register_next_step_handler_by_chat_id(chat_id, lambda m: receive_tx_id(m, "shamcash"))

    elif call.data == "pay_syriatel":
        bot.edit_message_text(f"ارسل الى احد الارقام التالية بطريقة الدفع اليدوي\n\n{SYRIATEL_CASH_NUMBERS}\n\n" f"اقل قيمة للشحن هي {SYRIATEL_CASH_MIN_SYP} ليرة سورية جديدة\n\n" "ثم ادخل رقم عملية التحويل 👇", chat_id, call.message.message_id)
        bot.register_next_step_handler_by_chat_id(chat_id, lambda m: receive_tx_id(m, "syriatel"))

    elif call.data == "pay_usdt_trc20":
        bot.edit_message_text(f"ارسل Usdt عبر شبكة trc20 حصرا إلى العنوان:\n{USDT_TRC20_ADDRESS}\n\n" "ثم ادخل رقم عملية التحويل:", chat_id, call.message.message_id)
        bot.register_next_step_handler_by_chat_id(chat_id, lambda m: receive_tx_id(m, "usdt_trc20"))

    # ---- شراء فئات جواكر ----
    elif call.data in CATEGORIES:
        handle_category_purchase(call, call.data)

    elif call.data.startswith("usebalance_"):
        category_key = call.data.replace("usebalance_", "")
        start_balance_purchase(call, category_key)

    # ---- تفاعل أزرار قبول ورفض شحن الرصيد اليدوي ----
    elif call.data.startswith("approve_") or call.data.startswith("reject_"):
        handle_recharge_decision(call)

    # ---- تفاعل أزرار الشحن الفوري للفئات ----
    elif call.data.startswith("shipped_"):
        handle_purchase_shipped(call)

    # 🌟 [تم التحديث]: مطابقة البيانات بدقة مع كود الـ HTML لتفعيل أزرار الفيزا بنجاح
    elif call.data.startswith("cc_app_") or call.data.startswith("cc_rej_"):
        parts = call.data.split("_")
        action = parts[1]
        target_user_id = parts[2]
        
        if action == "app":
            try:
                bot.send_message(target_user_id, "✅ تم قبول طلب الدفع الخاص بك وشحن حسابك بنجاح!")
            except Exception as e:
                print(f"فشل إرسال رسالة للمستخدم: {e}")
            bot.edit_message_text(call.message.text + "\n\n🟢 تم الشحن والموافقة من الإدارة", call.message.chat.id, call.message.message_id)
        else:
            try:
                bot.send_message(target_user_id, "❌ تم رفض طلب الدفع بالبطاقة، يرجى التأكد من بيانات الدفع الخاصة بك.")
            except Exception as e:
                print(f"فشل إرسال رسالة للمستخدم: {e}")
            bot.edit_message_text(call.message.text + "\n\n🔴 تم الرفض من الإدارة", call.message.chat.id, call.message.message_id)
        
        bot.answer_callback_query(call.id)


def receive_tx_id(message, method):
    chat_id = message.chat.id
    tx_id = message.text.strip()
    bot.send_message(chat_id, "أدخل المبلغ الذي قمت بتحويله :")
    bot.register_next_step_handler_by_chat_id(chat_id, lambda m: receive_amount(m, method, tx_id))


def receive_amount(message, method, tx_id):
    chat_id = message.chat.id
    raw_amount_text = message.text.strip()

    try:
        raw_amount = float(raw_amount_text)
    except ValueError:
        bot.send_message(chat_id, "الرجاء إدخال رقم صحيح للمبلغ.")
        bot.register_next_step_handler_by_chat_id(chat_id, lambda m: receive_amount(m, method, tx_id))
        return

    method_labels = {"binance": "Binance (USDT)", "shamcash": "Sham Cash", "usdt_trc20": "Usdt Trc20", "syriatel": "Syriatel Cash"}

    if method == "shamcash":
        amount_usd = round(raw_amount / SHAMCASH_RATE_SYP_PER_USD, 2)
        amount_display = f"{raw_amount} SYP (≈ {amount_usd}$)"
    else:
        amount_usd = raw_amount
        amount_display = f"{raw_amount}$"

    order_id = create_recharge_order(chat_id, method, tx_id, amount_usd, raw_amount)
    bot.send_message(chat_id, "تم ارسال الطلب يرجى الانتظار", reply_markup=main_menu())

    bot.send_message(
        ADMIN_ID,
        f"🔔 طلب إضافة رصيد جديد\n\n👤 {user_display(message.from_user, chat_id)}\n💳 الطريقة: {method_labels[method]}\n🔢 رقم العملية: {tx_id}\n💵 المبلغ: {amount_display}\n\nرقم الطلب: #{order_id}",
        reply_markup=admin_recharge_decision_markup(order_id)
    )


def handle_recharge_decision(call):
    action, order_id_str = call.data.split("_", 1)
    order_id = int(order_id_str)
    order = get_recharge_order(order_id)

    if not order or order["status"] != "pending":
        bot.answer_callback_query(call.id, "هذا الطلب غير موجود أو تمت معالجته مسبقاً.")
        return

    user_id = order["user_id"]

    if action == "approve":
        add_balance(user_id, order["amount_usd"])
        set_recharge_status(order_id, "approved")
        bot.send_message(user_id, f"✅ تم قبول طلبك وإضافة {order['amount_usd']}$ إلى رصيدك بنجاح.")
        bot.edit_message_text(call.message.text + "\n\n✅ تم القبول", call.message.chat.id, call.message.message_id)
    else:
        set_recharge_status(order_id, "rejected")
        bot.send_message(user_id, "❌ يرجى التأكد من رقم العملية أو المبلغ المدخل.")
        bot.edit_message_text(call.message.text + "\n\n❌ تم الرفض", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)


def handle_category_purchase(call, category_key):
    chat_id = call.message.chat.id
    category = CATEGORIES[category_key]
    balance = get_balance(chat_id)

    markup = types.InlineKeyboardMarkup(row_width=1)
    if balance >= category["price"]:
        markup.add(types.InlineKeyboardButton("✅ الدفع من رصيد البوت", callback_data=f"usebalance_{category_key}"))
    
    markup.add(types.InlineKeyboardButton("ادفع بالبطاقة-credit card", url=WEB_APP_URL))
    markup.add(types.InlineKeyboardButton("⬅️ عودة للقائمة الرئيسية", callback_data="start_menu"))

    if balance >= category["price"]:
        text = f"الفئة المختارة: {category['label']} -> {category['price']}$\nاختر طريقة الدفع:"
    else:
        text = f"الفئة المختارة: {category['label']} -> {category['price']}$\nرصيدك غير كاف، يمكنك الدفع مباشرة بالبطاقة."

    bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, disable_web_page_preview=True)


def start_balance_purchase(call, category_key):
    chat_id = call.message.chat.id
    category = CATEGORIES[category_key]
    balance = get_balance(chat_id)

    if balance < category["price"]:
        bot.answer_callback_query(call.id, "رصيدك غير كاف.")
        return

    bot.edit_message_text(f"الفئة: {category['label']} -> {category['price']}$\nأدخل الآيدي تبعك على اللعبة :", chat_id, call.message.message_id)
    bot.register_next_step_handler_by_chat_id(chat_id, lambda m: receive_game_id(m, category_key))


def receive_game_id(message, category_key):
    chat_id = message.chat.id
    game_id = message.text.strip()
    category = CATEGORIES[category_key]

    balance = get_balance(chat_id)
    if balance < category["price"]:
        bot.send_message(chat_id, "رصيدك غير كاف قم بشحن رصيدك في البوت اولا", reply_markup=back_to_main_only())
        return

    deduct_balance(chat_id, category["price"])
    order_id = create_purchase_order(chat_id, category["label"], category["price"], game_id)

    bot.send_message(chat_id, "تم ارسال طلبك بنجاح ✅ العملية قيد التنفيذ", reply_markup=main_menu())

    bot.send_message(
        ADMIN_ID,
        f"🛒 طلب شراء جديد\n\n👤 {user_display(message.from_user, chat_id)}\n📦 الفئة: {category['label']}\n🎮 آيدي اللعبة: {game_id}\n\nرقم الطلب: #{order_id}",
        reply_markup=admin_purchase_shipped_markup(order_id)
    )


def handle_purchase_shipped(call):
    order_id = int(call.data.split("_", 1)[1])
    order = get_purchase_order(order_id)

    if not order or order["status"] != "pending":
        bot.answer_callback_query(call.id, "هذا الطلب غير موجود أو تمت معالجته مسبقاً.")
        return

    set_purchase_status(order_id, "shipped")
    bot.send_message(order["user_id"], "✅ تم تنفيذ العملية بنجاح.")
    bot.edit_message_text(call.message.text + "\n\n📦 تم الشحن", call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)


# تشغيل البوت
print("البوت كاملاً يعمل الآن بنجاح مع كافة التحديثات المترابطة...")
bot.infinity_polling()
