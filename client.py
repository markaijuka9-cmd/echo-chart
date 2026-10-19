
import asyncio

import aiohttp
import flet as ft

from client_config import API_BASE


async def api_request(path, method="GET", token=None, data=None, form=None):
    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.request(
            method,
            f"{API_BASE}/{path.lstrip('/')}",
            headers=headers,
            json=data,
            data=form,
        ) as response:
            try:
                result = await response.json()
            except (ValueError, aiohttp.ContentTypeError):
                result = {"detail": await response.text()}

            if response.status >= 400:
                detail = result.get("detail", "Request failed.")
                raise RuntimeError(str(detail))

            return result


async def main(page: ft.Page):
    page.title = "EchoChat"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#080808"
    page.padding = 20

    token = None
    username = None

    title = ft.Text(
        "EchoChat",
        size=32,
        weight=ft.FontWeight.BOLD,
        color="#00FF88",
    )

    status = ft.Text("Welcome! Register or log in.")
    username_field = ft.TextField(label="Username")
    email_field = ft.TextField(label="Email (for registration)")
    password_field = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
    )

    chat_input = ft.TextField(
        label="Write a message",
        expand=True,
        multiline=True,
        min_lines=1,
        max_lines=4,
    )

    chat_history = ft.Column(
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    async def register(e):
        try:
            result = await api_request(
                "/auth/register",
                method="POST",
                data={
                    "username": username_field.value or "",
                    "email": email_field.value or "",
                    "password": password_field.value or "",
                },
            )
            status.value = (
                f"Account created for {result['username']}. "
                "Now log in."
            )
        except Exception as exc:
            status.value = f"Registration failed: {exc}"

        page.update()

    async def login(e):
        nonlocal token, username

        try:
            form = aiohttp.FormData()
            form.add_field("username", username_field.value or "")
            form.add_field("password", password_field.value or "")

            result = await api_request(
                "/auth/login",
                method="POST",
                form=form,
            )

            token = result["access_token"]
            username = username_field.value or "User"

            status.value = f"Logged in as {username}."
            show_chat()
        except Exception as exc:
            status.value = f"Login failed: {exc}"
            page.update()

    async def send_message(e):
        message = (chat_input.value or "").strip()

        if not message:
            return

        if not token:
            status.value = "Please log in first."
            page.update()
            return

        chat_history.controls.append(
            ft.Text(f"You: {message}", color="#00FF88")
        )
        chat_input.value = ""
        status.value = "Waiting for the AI service..."
        page.update()

        try:
            result = await api_request(
                "/ai/chat",
                method="POST",
                token=token,
                data={"message": message},
            )

            chat_history.controls.append(
                ft.Text(f"EchoChat AI: {result['answer']}")
            )
            status.value = "Message complete."
        except Exception as exc:
            chat_history.controls.append(
                ft.Text(f"Error: {exc}", color="#FF7777")
            )
            status.value = "Could not get an AI response."

        page.update()

    def show_chat():
        page.clean()
        page.add(
            title,
            ft.Text(f"Signed in as {username}"),
            status,
            ft.Divider(),
            chat_history,
            ft.Row([chat_input, ft.IconButton(
                icon=ft.Icons.SEND,
                on_click=send_message,
                tooltip="Send message",
            )]),
        )
        page.update()

    page.add(
        title,
        ft.Text("Your social world, in one place."),
        username_field,
        email_field,
        password_field,
        ft.Row(
            [
                ft.ElevatedButton(
                    "Register",
                    on_click=register,
                ),
                ft.ElevatedButton(
                    "Log in",
                    on_click=login,
                ),
            ]
        ),
        status,
    )


if __name__ == "__main__":
    ft.app(target=main)
