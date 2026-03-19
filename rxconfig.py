import reflex as rx
from reflex.plugins.sitemap import SitemapPlugin

config = rx.Config(
    app_name="Navika",
    api_url="https://navika-gold-star.reflex.run",
    deploy_url="https://navika-gold-star.reflex.run",
    disable_plugins=[SitemapPlugin],
)