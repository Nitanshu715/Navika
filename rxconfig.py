import reflex as rx
from reflex.plugins.sitemap import SitemapPlugin

config = rx.Config(
    app_name="Navika",
    disable_plugins=[SitemapPlugin],
)

