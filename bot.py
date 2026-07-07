import telebot
from telebot import types
from math import radians, cos
import json


TOKEN = "8925085252:AAG_Si0ZFNQWpCsaFIFXTVTHqyWBgahVJCg"  # ← PUT YOUR REAL TOKEN HERE
bot = telebot.TeleBot(TOKEN)

TEAM_MEMBERS = [
    {"name": "Akmal", "chat_id": 1234567890, "lat": 41.2995, "lon": 69.2401, "zone": "Tashkent Center"},
    {"name": "Bekzod", "chat_id": 1133559937, "lat": 41.2646, "lon": 69.2163, "zone": "Tashkent South"},
    {"name": "Abduvoris", "chat_id": 1133559937, "lat": 41.3111, "lon": 69.2797, "zone": "Tashkent North"},
]

user_data = {}
saved_users = {}
orders_today = []
order_counter = 0
pending_orders = {}

TEXTS = {
    "uz": {
        "choose_lang": "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык",
        "name": "👤 Ismingizni kiriting:",
        "last_name": "👤 Familiyangizni kiriting:",
        "phone": "📞 Telefon raqamingizni yuboring:",
        "phone_button": "📱 Telefon raqamni yuborish",
        "location": "📍 Iltimos, joylashuvingizni yuboring:",
        "location_button": "📍 Geolokatsiyani yuborish",
        "problem": "❓ Qanday muammo yuz berdi?",
        "problem_choices": ["🚗 Mashina eshigi", "🏠 Uy eshigi", "🔋 Akkumulyator"],
        "urgency": "⚠️ Vaziyat qanchalik shoshilinch?",
        "details_car": "🚘 Mashina markasi va raqamini kiriting [misol: Matiz 01U717VC]:",
        "details_home": "🏠 Uy manzilini kiriting:",
        "details_battery": "🚘 Mashina raqamini va qo'shimcha ma'lumot kiriting:",
        "details_other": "📝 Qo'shimcha ma'lumot kiriting:",
        "confirm": "✅ Ma'lumotlaringiz qabul qilindi! Eng yaqin usta siz bilan bog'lanadi.",
        "closest_found": "Sizga eng yaqin usta: {name} ({zone})",
        "alert": "🚨 YANGI BUYURTMA!\n\n👤 Mijoz: {name} {last}\n📞 Telefon: {phone}\n📍 Joylashuv: {location_link}\n❓ Muammo: {problem}\n⚠️ Shoshilinchligi: {urgency}\n📝 Qo'shimcha: {details}",
        "back": "⬅️ Orqaga",
        "welcome_back": "Xush kelibsiz, {name}! Avvalgi ma'lumotlaringiz saqlangan.",
    },
    "ru": {
        "choose_lang": "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык",
        "name": "👤 Введите ваше имя:",
        "last_name": "👤 Введите вашу фамилию:",
        "phone": "📞 Отправьте ваш номер телефона:",
        "phone_button": "📱 Отправить номер",
        "location": "📍 Отправьте ваше местоположение:",
        "location_button": "📍 Отправить геолокацию",
        "problem": "❓ Какая проблема?",
        "problem_choices": ["🚗 Дверь машины", "🏠 Дверь дома", "🔋 Аккумулятор"],
        "urgency": "⚠️ Насколько срочно?",
        "details_car": "🚘 Введите марку и номер машины [пример: Matiz 01U717VC]:",
        "details_home": "🏠 Введите адрес дома:",
        "details_battery": "🚘 Введите номер машины и доп. информацию:",
        "details_other": "📝 Введите дополнительную информацию:",
        "confirm": "✅ Данные приняты! Мастер свяжется с вами.",
        "closest_found": "Ближайший мастер: {name} ({zone})",
        "alert": "🚨 НОВЫЙ ЗАКАЗ!\n\n👤 Клиент: {name} {last}\n📞 Телефон: {phone}\n📍 Местоположение: {location_link}\n❓ Проблема: {problem}\n⚠️ Срочность: {urgency}\n📝 Детали: {details}",
        "back": "⬅️ Назад",
        "welcome_back": "С возвращением, {name}! Ваши данные сохранены.",
    }
}


def calculate_distance(lat1, lon1, lat2, lon2):
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    return ((dlat * 111.32)**2 + (dlon * 111.32 * cos(radians(lat1)))**2) ** 0.5


def find_nearest_team_member(client_lat, client_lon):
    nearest = TEAM_MEMBERS[0]
    min_dist = float("inf")
    for member in TEAM_MEMBERS:
        dist = calculate_distance(client_lat, client_lon, member["lat"], member["lon"])
        if dist < min_dist:
            min_dist = dist
            nearest = member
    if nearest is None:
        nearest = list(team_members_dynamic.values())[0]
    return nearest


def make_back_button(lang):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(TEXTS[lang]["back"])
    return keyboard

# ---------- ORDER MANAGEMENT ----------

def calculate_eta_km(distance_km):
    """Calculate estimated arrival time based on distance"""
    avg_speed = 40  # km/h in city
    time_hours = distance_km / avg_speed
    time_minutes = int(time_hours * 60)
    if time_minutes < 1:
        time_minutes = 1
    return time_minutes, distance_km


def get_all_team_members_except(exclude_chat_id=None):
    """Get all team members, optionally excluding one"""
    members = []
    for chat_id, member in team_members_dynamic.items():
        if chat_id != exclude_chat_id:
            members.append(member)
    return members


def send_order_to_member(order_id, member, data, lang):
    """Send order to a team member with Accept/Reject buttons"""
    distance = calculate_distance(data['lat'], data['lon'], member['lat'], member['lon'])
    eta_minutes, dist_km = calculate_eta_km(distance)
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("✅ Qabul qilish / Принять", callback_data=f"accept_{order_id}"),
        types.InlineKeyboardButton("❌ Rad etish / Отклонить", callback_data=f"reject_{order_id}")
    )
    
    alert_text = (
        f"🚨 YANGI BUYURTMA #{order_id}!\n\n"
        f"👤 Mijoz: {data['name']} {data['last_name']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"📍 Masofa: {dist_km:.1f} km (~{eta_minutes} daqiqa)\n"
        f"❓ Muammo: {data['problem']}\n"
        f"⚠️ Shoshilinchligi: {data['urgency']}\n"
        f"📝 Qo'shimcha: {data['details']}\n\n"
        f"📍 Joylashuv: https://maps.google.com/?q={data['lat']},{data['lon']}"
    )
    
    try:
        bot.send_message(member["chat_id"], alert_text, reply_markup=keyboard)
        return True
    except Exception as e:
        print(f"Failed to send to {member['name']}: {e}")
        return False


# ---------- CALLBACK HANDLER FOR ACCEPT/REJECT ----------

@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_') or call.data.startswith('reject_'))
def handle_order_response(call):
    chat_id = call.message.chat.id
    action, order_id_str = call.data.split('_')
    order_id = int(order_id_str)
    
    print(f"ACTION: {action}, ORDER: {order_id}, USER: {chat_id}")
    
    if order_id not in pending_orders:
        bot.answer_callback_query(call.id, "Bu buyurtma allaqachon bajarilgan")
        return
    
    order_data = pending_orders[order_id]
    lang = order_data.get('lang', 'uz')
    
    if action == 'accept':
        member_name = team_members_dynamic[chat_id]['name']
        
        distance = calculate_distance(
            order_data['lat'], order_data['lon'],
            team_members_dynamic[chat_id]['lat'],
            team_members_dynamic[chat_id]['lon']
        )
        eta_minutes, dist_km = calculate_eta_km(distance)
        
        if lang == "uz":
            client_text = (
                f"✅ Usta topildi!\n\n"
                f"👤 {member_name} sizga yordam beradi\n"
                f"📍 Masofa: {dist_km:.1f} km\n"
                f"⏳ Taxminiy yetib borish vaqti: {eta_minutes} daqiqa\n"
                f"📞 Aloqaga chiqadi..."
            )
        else:
            client_text = (
                f"✅ Мастер найден!\n\n"
                f"👤 {member_name} поможет вам\n"
                f"📍 Расстояние: {dist_km:.1f} км\n"
                f"⏳ Примерное время: {eta_minutes} мин\n"
                f"📞 Свяжется с вами..."
            )
        bot.send_message(order_data['client_chat_id'], client_text)
        
        order_data['status'] = 'accepted'
        order_data['accepted_by'] = member_name
        
        if lang == "uz":
            bot.send_message(chat_id, f"✅ Siz #{order_id} buyurtmani qabul qildingiz! Mijozga xabar yuborildi.")
        else:
            bot.send_message(chat_id, f"✅ Вы приняли заказ #{order_id}! Клиент уведомлен.")
        
        bot.answer_callback_query(call.id, f"#{order_id} buyurtma qabul qilindi!")
        
        # NOTIFY ALL OTHERS - ACCEPTED
        for mem_id, member in team_members_dynamic.items():
            if mem_id != chat_id:
                try:
                    if lang == "uz":
                        bot.send_message(mem_id, f"✅ #{order_id} buyurtma {member_name} tomonidan qabul qilindi.")
                    else:
                        bot.send_message(mem_id, f"✅ Заказ #{order_id} принят {member_name}.")
                except Exception as e:
                    print(f"Failed to notify {member['name']}: {e}")
        
        del pending_orders[order_id]
        
    elif action == 'reject':
        member_name = team_members_dynamic[chat_id]['name']
        
        if lang == "uz":
            bot.send_message(chat_id, f"❌ Siz #{order_id} buyurtmani rad etdingiz.")
        else:
            bot.send_message(chat_id, f"❌ Вы отклонили заказ #{order_id}.")
        
        bot.answer_callback_query(call.id, f"#{order_id} rad etildi")
        
        # NOTIFY ALL OTHERS - REJECTED
        for mem_id, member in team_members_dynamic.items():
            if mem_id != chat_id:
                try:
                    if lang == "uz":
                        bot.send_message(mem_id, f"❌ {member_name} #{order_id} buyurtmani rad etdi.")
                    else:
                        bot.send_message(mem_id, f"❌ {member_name} отклонил заказ #{order_id}.")
                except Exception as e:
                    print(f"Failed to notify {member['name']}: {e}")
        
        if 'tried_members' not in order_data:
            order_data['tried_members'] = []
        order_data['tried_members'].append(chat_id)
        
        # Find next nearest
        nearest = None
        min_dist = float("inf")
        for mem_id, member in team_members_dynamic.items():
            if mem_id not in order_data['tried_members']:
                dist = calculate_distance(order_data['lat'], order_data['lon'], member['lat'], member['lon'])
                if dist < min_dist:
                    min_dist = dist
                    nearest = member
        
        if nearest:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("✅ Qabul qilish / Принять", callback_data=f"accept_{order_id}"),
                types.InlineKeyboardButton("❌ Rad etish / Отклонить", callback_data=f"reject_{order_id}")
            )
            try:
                if lang == "uz":
                    bot.send_message(nearest["chat_id"], f"🚨 BUYURTMA #{order_id} SIZGA YUBORILDI!\n\nOldingi usta rad etdi.", reply_markup=keyboard)
                    bot.send_message(order_data['client_chat_id'], "⏳ Birinchi usta band, boshqa usta qidirilmoqda...")
                else:
                    bot.send_message(nearest["chat_id"], f"🚨 ЗАКАЗ #{order_id} ОТПРАВЛЕН ВАМ!\n\nПредыдущий мастер отказался.", reply_markup=keyboard)
                    bot.send_message(order_data['client_chat_id'], "⏳ Первый мастер занят, ищем другого...")
            except:
                pass
        else:
            if lang == "uz":
                bot.send_message(order_data['client_chat_id'], "❌ Kechirasiz, hozircha barcha ustalar band.")
            else:
                bot.send_message(order_data['client_chat_id'], "❌ Извините, сейчас все мастера заняты.")
            del pending_orders[order_id]


# ---------- ADMIN PANEL ----------

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    chat_id = message.chat.id
    
    # Check if admin (you can set specific chat_ids here)
    # For now, any team member can access
    if chat_id not in team_members_dynamic:
        bot.send_message(chat_id, "❌ Ruxsat yo'q / Нет доступа")
        return
    
    text = "📊 *ADMIN PANEL*\n\n"
    
    # Today's orders
    text += f"📅 *Bugungi buyurtmalar:* {len(orders_today)} ta\n\n"
    
    if orders_today:
        for order in orders_today[-5:]:  # Last 5 orders
            status = order.get('status', 'yuborilgan')
            text += f"#{order['id']} | {order['name']} | {order['problem']} | {status}\n"
    else:
        text += "Hozircha buyurtmalar yo'q\n"
    
    text += "\n━━━━━━━━━━━━━━━\n\n"
    text += "📍 *Jamoa a'zolari:*\n\n"
    
    for mem_id, member in team_members_dynamic.items():
        text += f"👤 {member['name']} ({member['zone']})\n"
        text += f"📍 {member['lat']:.4f}, {member['lon']:.4f}\n\n"
    
    text += "━━━━━━━━━━━━━━━\n\n"
    text += "Buyruqlar:\n"
    text += "/admin - Admin panel\n"
    text += "/history - Buyurtmalar tarixi\n"
    text += "/track - Lokatsiyani yangilash\n"
    
    bot.send_message(chat_id, text, parse_mode="Markdown")


# ---------- ORDER HISTORY ----------

@bot.message_handler(commands=['history'])
def order_history(message):
    chat_id = message.chat.id
    
    if chat_id in team_members_dynamic:
        # Team member history
        text = "📋 *SIZ QABUL QILGAN BUYURTMALAR*\n\n"
        member_orders = [o for o in orders_today if o.get('accepted_by') == team_members_dynamic[chat_id]['name']]
        if member_orders:
            for order in member_orders[-10:]:
                text += (
                    f"#{order['id']} | {order.get('problem', 'N/A')}\n"
                    f"👤 {order.get('name', 'N/A')} {order.get('last_name', '')}\n"
                    f"📞 {order.get('phone', 'N/A')}\n"
                    f"📝 {order.get('details', 'N/A')}\n"
                    f"━━━━━━━━━━━━━━━\n"
                )
        else:
            text += "Buyurtmalar yo'q"
        bot.send_message(chat_id, text, parse_mode="Markdown")
        return
    
    # Client history
    text = "📋 *SIZNING BUYURTMALARINGIZ*\n\n"
    client_orders = [o for o in orders_today if o.get('client_chat_id') == chat_id]
    
    if client_orders:
        for order in client_orders[-5:]:
            status = order.get('status', 'yuborilgan')
            if status == 'accepted':
                status_text = "✅ Qabul qilindi"
            elif status == 'rejected':
                status_text = "❌ Rad etildi"
            else:
                status_text = "⏳ Kutilmoqda"
            
            text += (
                f"#{order['id']} | {order.get('problem', 'N/A')}\n"
                f"📝 {order.get('details', 'N/A')}\n"
                f"📌 Holat: {status_text}\n"
                f"━━━━━━━━━━━━━━━\n"
            )
    else:
        text += "Hozircha buyurtmalaringiz yo'q"
    
    bot.send_message(chat_id, text, parse_mode="Markdown")

def process_name(message):
    if not hasattr(message, 'chat'):
        return
    chat_id = message.chat.id
    if chat_id not in user_data:
        return
    if hasattr(message, 'text') and message.text and message.text.startswith('/'):
     return
    if hasattr(message, 'location') and message.location is not None:
        bot.send_message(chat_id, "❌ Iltimos, ismingizni kiriting / Введите имя")
        bot.register_next_step_handler(message, process_name)
        return
    
    lang = user_data[chat_id]["lang"]
    if message.text == TEXTS[lang]["back"]:
        start(message)
        return
    user_data[chat_id]["name"] = message.text
    bot.send_message(chat_id, TEXTS[lang]["last_name"], reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, process_last_name)


def process_last_name(message):
    if not hasattr(message, 'chat'):
        return
    chat_id = message.chat.id
    if chat_id not in user_data:
        return
    if hasattr(message, 'text') and message.text and message.text.startswith('/'):
     return
    if hasattr(message, 'location') and message.location is not None:
        bot.send_message(chat_id, "❌ Iltimos, familiyangizni kiriting / Введите фамилию")
        bot.register_next_step_handler(message, process_last_name)
        return
    
    lang = user_data[chat_id]["lang"]
    if message.text == TEXTS[lang]["back"]:
        bot.send_message(chat_id, TEXTS[lang]["name"], reply_markup=make_back_button(lang))
        bot.register_next_step_handler(message, process_name)
        return
    user_data[chat_id]["last_name"] = message.text
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton(TEXTS[lang]["phone_button"], request_contact=True)
    keyboard.add(button)
    bot.send_message(chat_id, TEXTS[lang]["phone"], reply_markup=keyboard)
    bot.register_next_step_handler(message, process_phone)


def process_phone(message):
    if not hasattr(message, 'chat'):
        return
    chat_id = message.chat.id
    if chat_id not in user_data:
        return
    if hasattr(message, 'text') and message.text and message.text.startswith('/'):
     return
    if hasattr(message, 'location') and message.location is not None:
        bot.send_message(chat_id, "❌ Iltimos, telefon raqamingizni kiriting / Отправьте номер телефона")
        bot.register_next_step_handler(message, process_phone)
        return
    
    lang = user_data[chat_id]["lang"]
    if hasattr(message, 'text') and message.text == TEXTS[lang]["back"]:
        bot.send_message(chat_id, TEXTS[lang]["last_name"], reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_last_name)
        return
    if hasattr(message, 'contact') and message.contact is not None:
        user_data[chat_id]["phone"] = message.contact.phone_number
    else:
        user_data[chat_id]["phone"] = message.text
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton(TEXTS[lang]["location_button"], request_location=True)
    keyboard.add(button)
    keyboard.add(TEXTS[lang]["back"])
    bot.send_message(chat_id, TEXTS[lang]["location"], reply_markup=keyboard)
    bot.register_next_step_handler(message, process_location)


def process_location(message):
    if not hasattr(message, 'chat'):
        return
    chat_id = message.chat.id
    if hasattr(message, 'text') and message.text and message.text.startswith('/'):
     return
    lang = user_data[chat_id]["lang"]
    if hasattr(message, 'text') and message.text == TEXTS[lang]["back"]:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button = types.KeyboardButton(TEXTS[lang]["phone_button"], request_contact=True)
        keyboard.add(button)
        keyboard.add(TEXTS[lang]["back"])
        bot.send_message(chat_id, TEXTS[lang]["phone"], reply_markup=keyboard)
        bot.register_next_step_handler(message, process_phone)
        return
    if not hasattr(message, 'location') or message.location is None:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button = types.KeyboardButton(TEXTS[lang]["location_button"], request_location=True)
        keyboard.add(button)
        keyboard.add(TEXTS[lang]["back"])
        bot.send_message(chat_id, "📍 Lokatsiya yuboring / Отправьте геолокацию", reply_markup=keyboard)
        bot.register_next_step_handler(message, process_location)
        return
    user_data[chat_id]["lon"] = message.location.longitude
    nearest = find_nearest_team_member(user_data[chat_id]["lat"], user_data[chat_id]["lon"])
    user_data[chat_id]["nearest_member"] = nearest
    bot.send_message(chat_id, TEXTS[lang]["closest_found"].format(name=nearest["name"], zone=nearest["zone"]),
                     reply_markup=types.ReplyKeyboardRemove())
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for choice in TEXTS[lang]["problem_choices"]:
        keyboard.add(choice)
    keyboard.add(TEXTS[lang]["back"])
    bot.send_message(chat_id, TEXTS[lang]["problem"], reply_markup=keyboard)
    bot.register_next_step_handler(message, process_problem)
    if chat_id in team_members_dynamic:
        return


def process_problem(message):
    if not hasattr(message, 'chat'):
        return
    chat_id = message.chat.id
    if hasattr(message, 'text') and message.text and message.text.startswith('/'):
     return
    if hasattr(message, 'location') and message.location is not None:
        bot.send_message(chat_id, "❌ Iltimos, tugmalardan birini tanlang / Выберите один из вариантов")
        bot.register_next_step_handler(message, process_problem)
        return
    if hasattr(message, 'contact') and message.contact is not None:
        bot.send_message(chat_id, "❌ Iltimos, tugmalardan birini tanlang / Выберите один из вариантов")
        bot.register_next_step_handler(message, process_problem)
        return
    lang = user_data[chat_id]["lang"]
    if message.text == TEXTS[lang]["back"]:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button = types.KeyboardButton(TEXTS[lang]["location_button"], request_location=True)
        keyboard.add(button)
        keyboard.add(TEXTS[lang]["back"])
        bot.send_message(chat_id, TEXTS[lang]["location"], reply_markup=keyboard)
        bot.register_next_step_handler(message, process_location)
        return
    user_data[chat_id]["problem"] = message.text
    problem = message.text
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    car_options = ["🚗 Mashina eshigi", "🚗 Дверь машины"]
    home_options = ["🏠 Uy eshigi", "🏠 Дверь дома"]
    battery_options = ["🔋 Akkumulyator", "🔋 Аккумулятор"]
    if problem in car_options:
        user_data[chat_id]["problem_type"] = "car"
        urgency_list = ["👶 Bolalar mashinada", "⏳ Shoshilinchman", "✅ Shoshilinch emasman"] if lang == "uz" else ["👶 Дети в машине", "⏳ Срочно", "✅ Не срочно"]
    elif problem in home_options:
        user_data[chat_id]["problem_type"] = "home"
        urgency_list = ["👶 Bolalar uyda", "🔥 Favqulodda holat", "⏳ Shoshilinchman", "✅ Shoshilinch emasman"] if lang == "uz" else ["👶 Дети дома", "🔥 ЧП", "⏳ Срочно", "✅ Не срочно"]
    elif problem in battery_options:
        user_data[chat_id]["problem_type"] = "battery"
        urgency_list = ["⏳ Shoshilinchman", "✅ Shoshilinch emasman"] if lang == "uz" else ["⏳ Срочно", "✅ Не срочно"]
    else:
        user_data[chat_id]["problem_type"] = "other"
        urgency_list = ["👶 Bolalar ichkarida", "🔥 Favqulodda holat", "⏳ Shoshilinchman", "✅ Shoshilinch emasman"] if lang == "uz" else ["👶 Дети внутри", "🔥 ЧП", "⏳ Срочно", "✅ Не срочно"]
    for choice in urgency_list:
        keyboard.add(choice)
    keyboard.add(TEXTS[lang]["back"])
    bot.send_message(chat_id, TEXTS[lang]["urgency"], reply_markup=keyboard)
    bot.register_next_step_handler(message, process_urgency)


def process_urgency(message):
    if not hasattr(message, 'chat'):
        return
    chat_id = message.chat.id
    if hasattr(message, 'text') and message.text and message.text.startswith('/'):
     return
    if hasattr(message, 'contact') and message.contact is not None:
      bot.send_message(chat_id, "❌ Iltimos, tugmalardan birini tanlang / Выберите один из вариантов")
      bot.register_next_step_handler(message, process_problem)
      return
    lang = user_data[chat_id]["lang"]
    if message.text == TEXTS[lang]["back"]:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for choice in TEXTS[lang]["problem_choices"]:
            keyboard.add(choice)
        keyboard.add(TEXTS[lang]["back"])
        bot.send_message(chat_id, TEXTS[lang]["problem"], reply_markup=keyboard)
        bot.register_next_step_handler(message, process_problem)
        return
    user_data[chat_id]["urgency"] = message.text
    problem_type = user_data[chat_id].get("problem_type", "other")
    if problem_type == "car":
        detail_text = TEXTS[lang]["details_car"]
    elif problem_type == "home":
        detail_text = TEXTS[lang]["details_home"]
    elif problem_type == "battery":
        detail_text = TEXTS[lang]["details_battery"]
    else:
        detail_text = TEXTS[lang]["details_other"]
    bot.send_message(chat_id, detail_text, reply_markup=make_back_button(lang))
    bot.register_next_step_handler(message, process_details)


def process_details(message):
    if not hasattr(message, 'chat'):
        return
    chat_id = message.chat.id
    if chat_id not in user_data:
        return
    if hasattr(message, 'text') and '/language' in message.text:
        return language_anywhere(message)
    if hasattr(message, 'text') and message.text and message.text.startswith('/'):
     return
    if hasattr(message, 'location') and message.location is not None:
        bot.send_message(chat_id, "❌ Iltimos, tugmalardan birini tanlang / Выберите один из вариантов")
        bot.register_next_step_handler(message, process_urgency)
        return
    if hasattr(message, 'contact') and message.contact is not None:
        bot.send_message(chat_id, "❌ Iltimos, tugmalardan birini tanlang / Выберите один из вариантов")
        bot.register_next_step_handler(message, process_problem)
        return
        
    lang = user_data[chat_id]["lang"] 
    
    if message.text == TEXTS[lang]["back"]:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        problem_type = user_data[chat_id].get("problem_type", "other")
        if problem_type == "car":
            urgency_list = ["👶 Bolalar mashinada", "⏳ Shoshilinchman", "✅ Shoshilinch emasman"] if lang == "uz" else ["👶 Дети в машине", "⏳ Срочно", "✅ Не срочно"]
        elif problem_type == "home":
            urgency_list = ["👶 Bolalar uyda", "🔥 Favqulodda holat", "⏳ Shoshilinchman", "✅ Shoshilinch emasman"] if lang == "uz" else ["👶 Дети дома", "🔥 ЧП", "⏳ Срочно", "✅ Не срочно"]
        elif problem_type == "battery":
            urgency_list = ["⏳ Shoshilinchman", "✅ Shoshilinch emasman"] if lang == "uz" else ["⏳ Срочно", "✅ Не срочно"]
        else:
            urgency_list = ["👶 Bolalar ichkarida", "🔥 Favqulodda holat", "⏳ Shoshilinchman", "✅ Shoshilinch emasman"] if lang == "uz" else ["👶 Дети внутри", "🔥 ЧП", "⏳ Срочно", "✅ Не срочно"]
        for choice in urgency_list:
            keyboard.add(choice)
        keyboard.add(TEXTS[lang]["back"])
        bot.send_message(chat_id, TEXTS[lang]["urgency"], reply_markup=keyboard)
        bot.register_next_step_handler(message, process_urgency)
        return
    
    user_data[chat_id]["details"] = message.text
    data = user_data[chat_id]
    
    # Save user for returning
    saved_users[chat_id] = {
        "lang": data["lang"],
        "name": data["name"],
        "last_name": data["last_name"],
        "phone": data["phone"]
    }
    save_users_to_file()

    
    # Create order
    global order_counter
    order_counter += 1
    order_id = order_counter
    
    nearest = data["nearest_member"]
    distance = calculate_distance(data['lat'], data['lon'], nearest['lat'], nearest['lon'])
    eta_minutes, dist_km = calculate_eta_km(distance)
    
    order_info = {
        "id": order_id,
        "client_chat_id": chat_id,
        "name": data["name"],
        "last_name": data["last_name"],
        "phone": data["phone"],
        "lat": data["lat"],
        "lon": data["lon"],
        "problem": data["problem"],
        "urgency": data["urgency"],
        "details": data["details"],
        "status": "sent",
        "lang": lang,
        "nearest_member": nearest["name"]
    }
    
    orders_today.append(order_info)
    
    # Check if emergency
    is_emergency = "Bolalar" in data["urgency"] or "Дети" in data["urgency"] or "Favqulodda" in data["urgency"] or "ЧП" in data["urgency"]
    
    # Notify client
    if is_emergency:
        if lang == "uz":
           bot.send_message(chat_id, "🚨 Favqulodda holat! BARCHA ustalarga xabar yuborildi!", reply_markup=types.ReplyKeyboardRemove())
        else:
          bot.send_message(chat_id, "🚨 Чрезвычайная ситуация! ВСЕМ мастерам отправлено!", reply_markup=types.ReplyKeyboardRemove())

    else:
        if lang == "uz":
            bot.send_message(chat_id, f"✅ Buyurtma #{order_id} yuborildi! Ustalar javob kutmoqda...",
                         reply_markup=types.ReplyKeyboardRemove())
        else:
            bot.send_message(chat_id, f"✅ Заказ #{order_id} отправлен! Мастера ждут...", reply_markup=types.ReplyKeyboardRemove())
    # Send to ALL team members
    for mem_id, member in team_members_dynamic.items():
        # Check if this member is the nearest
        is_nearest = (member["name"] == nearest["name"])
        
        # Create keyboard with Accept/Reject
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✅ Qabul qilish / Принять", callback_data=f"accept_{order_id}"),
            types.InlineKeyboardButton("❌ Rad etish / Отклонить", callback_data=f"reject_{order_id}")
        )
        
        # Build alert message
        alert_text = f"🚨 YANGI BUYURTMA #{order_id}!\n\n"
        if is_nearest:
            alert_text += "⭐ SIZ ENG YAQIN USTASIZ!\n"
            alert_text += f"📍 Masofa: {dist_km:.1f} km (~{eta_minutes} daqiqa)\n\n"
        
        alert_text += (
            f"👤 Mijoz: {data['name']} {data['last_name']}\n"
            f"📞 Telefon: {data['phone']}\n"
            f"❓ Muammo: {data['problem']}\n"
            f"⚠️ Shoshilinchligi: {data['urgency']}\n"
            f"📝 Qo'shimcha: {data['details']}\n\n"
            f"📍 Joylashuv: https://maps.google.com/?q={data['lat']},{data['lon']}"
        )
        
        if is_emergency:
            alert_text = "🚨 FAVQULODDA HOLAT!\n\n" + alert_text
        
        try:
            bot.send_message(member["chat_id"], alert_text, reply_markup=keyboard)
        except Exception as e:
            print(f"Failed to send to {member['name']}: {e}")
    
    # Save pending order
    pending_orders[order_id] = order_info
    pending_orders[order_id]['tried_members'] = []
    
    # Clean up
    if chat_id in user_data:
        del user_data[chat_id]

@bot.message_handler(func=lambda msg: hasattr(msg, 'text') and msg.text == '/language')
def language_anywhere(message):
    chat_id = message.chat.id
    
    current_lang = "uz"
    if chat_id in saved_users and "lang" in saved_users[chat_id]:
        current_lang = saved_users[chat_id]["lang"]
    elif chat_id in user_data and "lang" in user_data[chat_id]:
        current_lang = user_data[chat_id]["lang"]
    
    new_lang = "ru" if current_lang == "uz" else "uz"
    
    if chat_id in saved_users:
        saved_users[chat_id]["lang"] = new_lang
    if chat_id in user_data:
        user_data[chat_id]["lang"] = new_lang
    
    if new_lang == "uz":
        bot.send_message(chat_id, "✅ Til o'zbekchaga o'zgartirildi")
    else:
        bot.send_message(chat_id, "✅ Язык изменен на русский")
    save_users_to_file()

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    
    saved = None
    if str(chat_id) in saved_users:
        saved = saved_users[str(chat_id)]
        lang = saved["lang"]
        user_data[chat_id] = {
            "lang": lang,
            "name": saved["name"],
            "last_name": saved["last_name"],
            "phone": saved["phone"],
        }
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button = types.KeyboardButton(TEXTS[lang]["location_button"], request_location=True)
        keyboard.add(button)
        
        bot.send_message(chat_id, TEXTS[lang]["welcome_back"].format(name=saved["name"]),
                         reply_markup=types.ReplyKeyboardRemove())
        bot.send_message(chat_id, TEXTS[lang]["location"], reply_markup=keyboard)
        bot.register_next_step_handler(message, process_location)
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add("🇺🇿 O'zbekcha", "🇷🇺 Русский")
        bot.send_message(chat_id, "Tilni tanlang / Выберите язык", reply_markup=keyboard)


@bot.message_handler(func=lambda msg: msg.text in ["🇺🇿 O'zbekcha", "🇷🇺 Русский"])
def choose_language(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]["lang"] = "uz" if "O'zbekcha" in message.text else "ru"
    lang = user_data[chat_id]["lang"]
    
    bot.send_message(chat_id, TEXTS[lang]["name"], reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, process_name)

@bot.message_handler(commands=['refill'])
def refill_info(message):
    chat_id = message.chat.id
    
    # Keep existing language or default to Uzbek
    lang = "uz"
    if chat_id in saved_users:
        lang = saved_users[chat_id].get("lang", "uz")
    
    user_data[chat_id] = {"lang": lang}
    
    bot.send_message(chat_id, TEXTS[lang]["name"], reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, refill_name)


def refill_name(message):
    chat_id = message.chat.id
    if hasattr(message, 'text') and message.text and message.text.startswith('/'):
     return
    user_data[chat_id]["name"] = message.text
    lang = user_data[chat_id]["lang"]
    bot.send_message(chat_id, TEXTS[lang]["last_name"])
    bot.register_next_step_handler(message, refill_last_name)


def refill_last_name(message):
    chat_id = message.chat.id
    if hasattr(message, 'text') and message.text and message.text.startswith('/'):
     return
    user_data[chat_id]["last_name"] = message.text
    lang = user_data[chat_id]["lang"]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton(TEXTS[lang]["phone_button"], request_contact=True)
    keyboard.add(button)
    bot.send_message(chat_id, TEXTS[lang]["phone"], reply_markup=keyboard)
    bot.register_next_step_handler(message, refill_phone)


def refill_phone(message):
    chat_id = message.chat.id
    if hasattr(message, 'text') and message.text and message.text.startswith('/'):
     return
    lang = user_data[chat_id]["lang"]
    
    if hasattr(message, 'contact') and message.contact is not None:
        user_data[chat_id]["phone"] = message.contact.phone_number
    else:
        user_data[chat_id]["phone"] = message.text
    
    # Save permanently
    saved_users[chat_id] = {
        "lang": lang,
        "name": user_data[chat_id]["name"],
        "last_name": user_data[chat_id]["last_name"],
        "phone": user_data[chat_id]["phone"]
    }
    save_users_to_file()


    # Confirmation
    if lang == "uz":
        confirm = f"✅ Ma'lumotlaringiz yangilandi:\n\n👤 Ism: {saved_users[chat_id]['name']}\n👤 Familiya: {saved_users[chat_id]['last_name']}\n📞 Telefon: {saved_users[chat_id]['phone']}"
    else:
        confirm = f"✅ Данные обновлены:\n\n👤 Имя: {saved_users[chat_id]['name']}\n👤 Фамилия: {saved_users[chat_id]['last_name']}\n📞 Телефон: {saved_users[chat_id]['phone']}"
    
    bot.send_message(chat_id, confirm, reply_markup=types.ReplyKeyboardRemove())
    
    if chat_id in user_data:
        del user_data[chat_id]

# Store team members with dynamic locations
team_members_dynamic = {}

# Initialize from static list
for member in TEAM_MEMBERS:
    team_members_dynamic[member["chat_id"]] = member

    # ---------- SAVE / LOAD USER DATA ----------
def save_users_to_file():
    """Save saved_users to a JSON file"""
    try:
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(saved_users, f, ensure_ascii=False, indent=2)
        print("✅ Users saved to file")
    except Exception as e:
        print(f"❌ Failed to save users: {e}")


def load_users_from_file():
    global saved_users
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            loaded = json.load(f)
        saved_users = {}
        for key, value in loaded.items():
            # Keep keys as strings for safety
            saved_users[key] = value
        print(f"✅ Loaded {len(saved_users)} users from file")
    except FileNotFoundError:
        print("📝 No saved users file found, starting fresh")
        saved_users = {}
    except Exception as e:
        print(f"❌ Failed to load users: {e}")
        saved_users = {}


@bot.message_handler(commands=['track'])
def start_tracking(message):
    chat_id = message.chat.id
    if chat_id not in team_members_dynamic:
        bot.send_message(chat_id, "❌ Siz jamoa a'zosi emassiz / Вы не член команды")
        return
    
    bot.send_message(
        chat_id,
        "📍 Iltimos, jonli lokatsiyangizni yuboring:\n\n"
        "1. 📎 qistirgichni bosing\n"
        "2. 'Lokatsiya' ni tanlang\n"
        "3. 'Jonli lokatsiyani ulashish' ni bosing\n"
        "4. Vaqtni 8 soat qilib qo'ying\n\n"
        "📍 Отправьте живую геолокацию:\n\n"
        "1. Нажмите 📎\n"
        "2. Выберите 'Геолокация'\n"
        "3. Нажмите 'Делиться живой геолокацией'\n"
        "4. Установите время на 8 часов",
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(content_types=['location'])
def handle_team_location(message):
    chat_id = message.chat.id
    
    # Only process team members
    if chat_id not in team_members_dynamic:
        return
    
    # Check if it's a live location (has live_period)
    is_live = hasattr(message.location, 'live_period') and message.location.live_period is not None
    
    # Update location
    team_members_dynamic[chat_id]["lat"] = message.location.latitude
    team_members_dynamic[chat_id]["lon"] = message.location.longitude
    
    if is_live:
        print(f"🔄 Live location from {team_members_dynamic[chat_id]['name']}: {message.location.latitude}, {message.location.longitude}")
        
        # Send confirmation only the FIRST time (when live_period is set)
        bot.send_message(
            chat_id,
            "✅ Jonli lokatsiya yoqildi!\n"
            "📍 Joylashuvingiz avtomatik yangilanadi\n"
            "⏳ Lokatsiya 8 soat davomida kuzatiladi\n\n"
            "✅ Живая геолокация включена!\n"
            "📍 Ваше местоположение обновляется автоматически\n"
            "⏳ Геолокация отслеживается 8 часов",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        print(f"📍 Static location from {team_members_dynamic[chat_id]['name']}: {message.location.latitude}, {message.location.longitude}")
        bot.send_message(
            chat_id,
            "✅ Joylashuv yangilandi!\n\n"
            "⚠️ Bu oddiy lokatsiya, jonli emas!\n"
            "Jonli lokatsiya uchun:\n"
            "📎 → Lokatsiya → Jonli lokatsiyani ulashish\n\n"
            "✅ Местоположение обновлено!\n\n"
            "⚠️ Это обычная геолокация, не живая!\n"
            "Для живой геолокации:\n"
            "📎 → Геолокация → Делиться живой геолокацией",
            reply_markup=types.ReplyKeyboardRemove()
        )


@bot.message_handler(content_types=['edited_message'])
def handle_edited_location(message):
    chat_id = message.chat.id
    
    if chat_id not in team_members_dynamic:
        return
    
    # Check if edited message contains location
    if hasattr(message, 'location') and message.location:
        team_members_dynamic[chat_id]["lat"] = message.location.latitude
        team_members_dynamic[chat_id]["lon"] = message.location.longitude
        print(f"🔄 Live update from {team_members_dynamic[chat_id]['name']}: {message.location.latitude}, {message.location.longitude}")

# Override the old location handler to ignore team members' locations
# Add this check at the TOP of process_location function

load_users_from_file()

print("✅ Bot is running...")
bot.infinity_polling()
