from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = 'blog'
    # 分页
    paginate = 10
    # 页面设置
    excerpt_separator = '<!-- more -->'

    def to_dict(self):
        keys = (
            'name',
            'excerpt_separator',
        )

        return {k: getattr(self, k, None) for k in keys}
