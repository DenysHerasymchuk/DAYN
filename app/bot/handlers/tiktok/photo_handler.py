"""
Photo-specific handler for TikTok photo posts.
This contains logic extracted from the main TikTok handler.
"""
import os
import logging

from aiogram import Router
from aiogram.types import Message, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext

from app.bot.keyboards.tiktok_kb import get_audio_button
from app.bot.utils.logger import user_logger

logger = logging.getLogger(__name__)
router = Router()


async def send_tiktok_photos(
        message: Message,
        images: list,
        author_link: str,
        bot_username: str,
        state: FSMContext,
        user_id: int
):
    """
    Send TikTok photos without captions in media group.
    Only final summary message gets caption with info.

    Args:
        message: Original message object
        images: List of image file paths
        author_link: HTML formatted author link
        bot_username: Bot's username
        state: FSM context
        user_id: Telegram user ID for logging
    """
    total_photos = len(images)
    batch_size = 10  # Telegram media group limit

    # Log photo sending start
    user_logger.log_user_action(
        "photo_handler.send_tiktok_photos",
        user_id,
        f"Sending {total_photos} TikTok photos",
        f"Author: {author_link}"
    )

    # Send photos in batches of 10 WITHOUT CAPTIONS
    for batch_num, i in enumerate(range(0, total_photos, batch_size), 1):
        batch = images[i:i + batch_size]

        media_group = []
        for img_path in batch:
            if not os.path.exists(img_path):
                logger.warning(f"Image file not found: {img_path}")
                continue

            # Check if file is valid
            try:
                file_size = os.path.getsize(img_path)
                if file_size == 0:
                    logger.error(f"Empty image file: {img_path}")
                    continue
            except OSError as e:
                logger.error(f"Could not read image file {img_path}: {e}")
                continue

            # NO CAPTION - just send the photo
            media_group.append(
                InputMediaPhoto(
                    media=FSInputFile(img_path)
                )
            )

        if media_group:
            try:
                await message.reply_media_group(media=media_group)
                logger.debug(f"✓ Sent batch {batch_num} with {len(media_group)} photos")

                # Log batch sent
                user_logger.log_user_action(
                    "photo_handler.send_tiktok_photos",
                    user_id,
                    f"Photo batch {batch_num} sent",
                    f"Photos: {len(media_group)}"
                )

            except Exception as e:
                logger.error(f"✗ Failed to send batch {batch_num}: {e}")
                user_logger.log_user_error(
                    "photo_handler.send_tiktok_photos",
                    user_id,
                    f"Failed to send photo batch {batch_num}: {str(e)}"
                )

                # Fallback: send photos one by one
                for img_path in batch:
                    if os.path.exists(img_path):
                        try:
                            await message.reply_photo(FSInputFile(img_path))
                        except Exception as e2:
                            logger.error(f"Failed to send individual photo: {e2}")

    # Send final summary message with audio button
    final_msg = await message.reply(
        f"📸 TikTok Photos ({total_photos} images)\n"
        f"👤 {author_link}\n\n"
        f"{bot_username}",
        parse_mode="HTML",
        reply_markup=get_audio_button()
    )

    # Store state for audio extraction
    await state.update_data(
        final_message_id=final_msg.message_id,
        total_photos=total_photos,
        user_id=user_id  # Store user_id for callback context
    )

    logger.info(f"✓ Sent final summary with audio button for {total_photos} photos")

    # Log final message sent
    user_logger.log_user_action(
        "photo_handler.send_tiktok_photos",
        user_id,
        "Final summary sent",
        f"Total photos: {total_photos} | Message ID: {final_msg.message_id}"
    )

    return final_msg


async def handle_single_photo(
        message: Message,
        image_path: str,
        author_link: str,
        bot_username: str,
        state: FSMContext,
        user_id: int
):
    """
    Handle single TikTok photo download.

    Args:
        message: Original message object
        image_path: Path to the single image
        author_link: HTML formatted author link
        bot_username: Bot's username
        state: FSM context
        user_id: Telegram user ID for logging
    """
    try:
        # Log single photo handling
        user_logger.log_user_action(
            "photo_handler.handle_single_photo",
            user_id,
            "Sending single TikTok photo",
            f"Author: {author_link}"
        )

        # Send single photo with caption and button
        photo_msg = await message.reply_photo(
            photo=FSInputFile(image_path),
            caption=f"📸 TikTok Photo\n👤 {author_link}\n\nDownloaded via:\n{bot_username}",
            parse_mode="HTML",
            reply_markup=get_audio_button()
        )

        # Store state for audio extraction
        await state.update_data(
            photo_message_id=photo_msg.message_id,
            total_photos=1,
            user_id=user_id
        )

        # Log success
        user_logger.log_user_action(
            "photo_handler.handle_single_photo",
            user_id,
            "Single photo sent",
            f"Message ID: {photo_msg.message_id}"
        )

        return photo_msg

    except Exception as e:
        user_logger.log_user_error(
            "photo_handler.handle_single_photo",
            user_id,
            f"Failed to send single photo: {str(e)}"
        )
        raise