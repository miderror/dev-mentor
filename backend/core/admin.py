from django.conf import settings
from django.contrib import admin


class MyAdminSite(admin.AdminSite):
    def get_app_list(self, request, app_label=None):
        app_dict = self._build_app_dict(request)

        ordering_config = settings.ADMIN_REORDER

        app_order = {item["app"]: i for i, item in enumerate(ordering_config)}

        app_list = sorted(
            app_dict.values(), key=lambda x: app_order.get(x["app_label"], 999)
        )

        for app in app_list:
            app_config = next(
                (
                    item
                    for item in ordering_config
                    if item.get("app") == app["app_label"]
                ),
                None,
            )

            if app_config and "models" in app_config:
                model_order = {
                    model_name: i for i, model_name in enumerate(app_config["models"])
                }
                app["models"].sort(
                    key=lambda x: model_order.get(f"{x['object_name'].lower()}", 999)
                )

        return app_list


site = MyAdminSite()
