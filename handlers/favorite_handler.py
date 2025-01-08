from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db_operations import DatabaseManager
from handlers.auth_handler import require_auth
import os
import telegram

db = DatabaseManager()

@require_auth
async def toggle_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('\n\n----toggle_favorite----\n\n')
    query = update.callback_query
    await query.answer()
    
    recipe_id = int(query.data.split('_')[1])
    user_id = update.effective_user.id
    
    print('toggle_favorite query.data', recipe_id, user_id)
    
    is_favorite = db.is_favorite(user_id, recipe_id)
    
    print('is_favorite', is_favorite)
    
    if is_favorite:
        success = db.remove_from_favorites(user_id, recipe_id)
        message = "از علاقه‌مندی‌ها حذف شد ❌"
        new_button_text = "⭐️ افزودن به علاقه‌مندی‌ها"
    else:
        success = db.add_to_favorites(user_id, recipe_id)
        message = "به علاقه‌مندی‌ها اضافه شد ⭐️"
        new_button_text = "⭐️ حذف از علاقه‌مندی‌ها"
    
    if success:
        # Update the favorite button
        keyboard = []
        for row in query.message.reply_markup.inline_keyboard:
            new_row = []
            for button in row:
                if button.callback_data.startswith('favorite_'):
                    # Create new button with updated text
                    new_button = InlineKeyboardButton(new_button_text, callback_data=button.callback_data)
                    new_row.append(new_button)
                else:
                    new_row.append(button)
            keyboard.append(new_row)
            
        try:
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        except telegram.error.BadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise e
        
        await query.message.reply_text(message)
    else:
        await query.message.reply_text("خطا در انجام عملیات. لطفاً دوباره تلاش کنید.")

@require_auth
async def view_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    favorites = db.get_user_favorites(user_id)
    
    if not favorites:
        await update.message.reply_text("شما هنوز دستور پختی را به علاقه‌مندی‌ها اضافه نکرده‌اید! ⭐️")
        return
    
    await update.message.reply_text("📚 لیست دستور پخت‌های مورد علاقه شما:")
    
    for recipe in favorites:
        recipe_id, title, ingredients, cooking_time, skill_level, calories, image_path, owner_username = recipe
        
        message = (
            f"🍳 {title}\n"
            f"👨‍🍳 آشپز: {owner_username or 'ناشناس'}\n"
            f"⏱ زمان پخت: {cooking_time} دقیقه\n"
            f"📊 سطح دشواری: {skill_level}\n"
            f"🔥 کالری: {calories}\n\n"
            f"📝 مواد لازم:\n{ingredients[:100]}..."
        )
        
        keyboard = [
            [InlineKeyboardButton("👁 مشاهده کامل", callback_data=f"view_recipe_{recipe_id}")],
            [InlineKeyboardButton("⭐️ حذف از علاقه‌مندی‌ها", callback_data=f"favorite_{recipe_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=message,
                        reply_markup=reply_markup
                    )
            except Exception:
                await update.message.reply_text(
                    message,
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(
                message,
                reply_markup=reply_markup
            ) 