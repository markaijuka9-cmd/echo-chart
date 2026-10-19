
import aiohttp
import flet as ft

from client_config import API_BASE


async def load_reels():
    timeout = aiohttp.ClientTimeout(total=20)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(
            f"{API_BASE}/reels/"
        ) as response:
            if response.status != 200:
                raise RuntimeError("Could not load Reels.")

            return await response.json()


def build_reels_screen(page: ft.Page):
    content = ft.Column(
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    status = ft.Text("Loading Reels...")

    async def refresh(e=None):
        content.controls.clear()

        try:
            reels = await load_reels()

            if not reels:
                content.controls.append(
                    ft.Text("No Reels available yet.")
                )

            for reel in reels:
                content.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    reel.get("title", "Untitled Reel"),
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    f"Posted by user "
                                    f"{reel.get('user_id', '?')}"
                                ),
                                ft.Text(
                                    reel.get("video_url", ""),
                                    selectable=True,
                                ),
                            ],
                            spacing=6,
                        ),
                        padding=12,
                        border=ft.Border.all(1, "#333333"),
                        border_radius=12,
                    )
                )

            status.value = f"{len(reels)} Reels loaded."

        except Exception as exc:
            status.value = f"Could not load Reels: {exc}"

        page.update()

    refresh_button = ft.ElevatedButton(
        "Refresh Reels",
        on_click=refresh,
    )

    page.run_task(refresh)

    return ft.Column(
        [
            ft.Text(
                "EchoChat Reels",
                size=26,
                weight=ft.FontWeight.BOLD,
                color="#00FF88",
            ),
            refresh_button,
            status,
            content,
        ],
        expand=True,
    )
